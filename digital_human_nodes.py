"""Frame-aligned InfiniteTalk clips for digital human narration."""

import json
import math
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import torch
import torch.nn.functional as F
import torchaudio

import folder_paths
import nodes
from comfy_execution.graph_utils import GraphBuilder

from .video_nodes import SubtitleBurnIn


FPS = 24
CATEGORY = "JSNodes/Digital Human"
SRT_START = re.compile(r"^(\d+)\s*\n(\d+):(\d{2}):(\d{2})[,.](\d{3})\s+-->",
                       re.MULTILINE)


def clip_ranges(plan, srt, samples, rate):
    starts = {}
    for number, hours, minutes, seconds, millis in SRT_START.findall(srt):
        number = int(number)
        if number in starts:
            raise ValueError(f"Duplicate SRT cue number: {number}")
        ms = ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)
        starts[number] = (ms * FPS + 500) // 1000
    if not starts:
        raise ValueError("No valid cues in adjusted SRT. Check the TTS output.")
    total = (samples * FPS + rate - 1) // rate
    cuts = []
    for line in plan.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"\s*(\d+)\s*,\s*(\d+)\s*[xX×]\s*(\d+)\s*", line)
        if not match:
            raise ValueError(f"Expected cue,widthxheight: {line}")
        cue, width, height = map(int, match.groups())
        if any(size < 64 or size > 2048 or size % 16 for size in (width, height)):
            raise ValueError(f"Width and height must be multiples of 16 (64–2048): {line}")
        if cue and cue not in starts:
            raise ValueError(f"Cue {cue} is missing from adjusted SRT.")
        cuts.append((starts[cue] if cue else 0, width, height))
    if not cuts or cuts[0][0] != 0:
        raise ValueError("The first clip must start at frame zero. Use cue 0.")
    ends = [cut[0] for cut in cuts[1:]] + [total]
    ranges = []
    for (start, width, height), end in zip(cuts, ends):
        if not start < end <= total:
            raise ValueError("Clip starts must increase and fall inside the narration.")
        if end - start > 9998:
            raise ValueError("A clip exceeds 9998 frames. Add another cut.")
        ranges.append((start, end, width, height))
    return ranges


class DemoInfiniteTalkClips:
    CATEGORY = CATEGORY
    FUNCTION = "expand"
    RETURN_TYPES = ("DEMO_CLIPS",)
    RETURN_NAMES = ("clips",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "adjusted_srt": ("STRING", {"forceInput": True}),
                "model": ("WANVIDEOMODEL",),
                "vae": ("WANVAE",),
                "wav2vec": ("WAV2VECMODEL",),
                "clip_vision": ("CLIP_VISION",),
                "text_embeds": ("WANVIDEOTEXTEMBEDS",),
                "plan": ("STRING", {"multiline": True, "default": "0,832x480\n2,416x240\n3,832x480"}),
                "reference_mode": (["image", "video"],),
                "filename_prefix": ("STRING", {"default": "WorkDemo/clips/avatar"}),
                "steps": ("INT", {"default": 4, "min": 1, "max": 50}),
                "seed": ("INT", {"default": 42, "min": 0, "max": 2**64 - 1}),
                "frame_window": ("INT", {"default": 49, "min": 17, "max": 121, "step": 4}),
                "video_denoise": ("FLOAT", {"default": 0.75, "min": 0.1, "max": 1.0, "step": 0.05}),
            },
            "optional": {
                "reference_image": ("IMAGE", {"lazy": True}),
                "reference_video": ("IMAGE", {"lazy": True}),
            },
        }

    def check_lazy_status(self, reference_mode, reference_image=None, reference_video=None, **kwargs):
        if reference_mode == "image" and reference_image is None:
            return ["reference_image"]
        if reference_mode == "video" and reference_video is None:
            return ["reference_video"]
        return []

    def expand(self, audio, adjusted_srt, model, vae, wav2vec, clip_vision, text_embeds,
               plan, reference_mode, filename_prefix, steps, seed, frame_window, video_denoise,
               reference_image=None, reference_video=None):
        reference = reference_video if reference_mode == "video" else reference_image
        if reference is None or not len(reference):
            raise ValueError(f"Connect a reference {reference_mode}.")
        ranges = clip_ranges(plan, adjusted_srt, audio["waveform"].shape[-1], audio["sample_rate"])
        graph = GraphBuilder()
        previous = None
        for number, (start, end, width, height) in enumerate(ranges, 1):
            frames = end - start
            # Extra audio context covers Wav2Vec's frame rounding and very short clips.
            audio_frames = max(12, frames + 2)
            source = graph.node("DemoClipInputs", audio=audio, reference=reference, start=start,
                                end=end, audio_frames=audio_frames, video=reference_mode == "video")
            source.set_input("previous", previous)
            resized = graph.node("ImageResizeKJv2", image=source.out(1), width=width, height=height,
                                 upscale_method="lanczos", keep_proportion="crop", pad_color="0, 0, 0",
                                 crop_position="center", divisible_by=16, device="cpu")
            first = graph.node("GetImageRangeFromBatch", images=resized.out(0), start_index=0, num_frames=1)
            vision = graph.node("WanVideoClipVisionEncode", clip_vision=clip_vision, image_1=first.out(0),
                                strength_1=1.0, strength_2=1.0, crop="center", combine_embeds="average",
                                force_offload=True)
            conditioning = graph.node("WanVideoImageToVideoMultiTalk", vae=vae, width=width, height=height,
                                      start_image=first.out(0), frame_window_size=frame_window, motion_frame=9,
                                      force_offload=True, colormatch="reinhard_torch", tiled_vae=False,
                                      mode="infinitetalk", clip_embeds=vision.out(0))
            features = graph.node("DemoTalkAudioFeatures", wav2vec_model=wav2vec, audio=source.out(0),
                                  frames=audio_frames)
            sampler = graph.node("WanVideoSampler", model=model, image_embeds=conditioning.out(0),
                                 text_embeds=text_embeds, multitalk_embeds=features.out(0),
                                 steps=steps, cfg=1.0, shift=11.0, seed=seed, force_offload=True,
                                 scheduler="dpm++_sde", riflex_freq_index=0, add_noise_to_samples=True)
            if reference_mode == "video":
                encoded = graph.node("WanVideoEncode", vae=vae, image=resized.out(0), enable_vae_tiling=False,
                                     tile_x=272, tile_y=272, tile_stride_x=144, tile_stride_y=128)
                sampler.set_input("samples", encoded.out(0))
                sampler.set_input("denoise_strength", video_denoise)
            decoded = graph.node("WanVideoPassImagesFromSamples", samples=sampler.out(0))
            trim = graph.node("DemoClipTrim", images=decoded.out(0), frames=frames)
            saved = graph.node("VHS_VideoCombine", images=trim.out(0), audio=source.out(2), frame_rate=FPS,
                               loop_count=0, filename_prefix=f"{filename_prefix}_{number:02d}",
                               format="video/h264-mp4", pix_fmt="yuv420p", crf=19, save_metadata=False,
                               trim_to_audio=False, pingpong=False, save_output=True)
            entry = graph.node("DemoClipResult", filenames=saved.out(0), start=start, end=end, width=width,
                               height=height)
            entry.set_input("previous", previous)
            previous = entry.out(0)
        return {"result": (previous,), "expand": graph.finalize()}


class DemoClipInputs:
    CATEGORY = CATEGORY
    FUNCTION = "prepare"
    RETURN_TYPES = ("AUDIO", "IMAGE", "AUDIO")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"audio": ("AUDIO",), "reference": ("IMAGE",), "start": ("INT",),
                             "end": ("INT",), "audio_frames": ("INT",), "video": ("BOOLEAN",)},
                "optional": {"previous": ("DEMO_CLIPS",)}}

    def prepare(self, audio, reference, start, end, audio_frames, video, previous=None):
        rate = audio["sample_rate"]
        wave = audio["waveform"]
        start_sample = round(start * rate / FPS)
        end_sample = round(end * rate / FPS)
        clip = wave[..., start_sample:end_sample]
        clip = F.pad(clip, (0, end_sample - start_sample - clip.shape[-1]))
        # Context after a cut can be silence. The exact slice is used for export.
        driving = F.pad(clip, (0, math.ceil((audio_frames + 1) * rate / FPS) - clip.shape[-1]))
        images = reference[:1]
        if video and len(reference) > 1:
            # Ping-pong short references without repeating their endpoint frames.
            period = 2 * (len(reference) - 1)
            indices = torch.arange(start, end, device=reference.device) % period
            images = reference[torch.minimum(indices, period - indices)]
        return ({"waveform": driving, "sample_rate": rate}, images,
                {"waveform": clip, "sample_rate": rate})


class DemoClipTrim:
    CATEGORY = CATEGORY
    FUNCTION = "trim"
    RETURN_TYPES = ("IMAGE",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"images": ("IMAGE",), "frames": ("INT",)}}

    def trim(self, images, frames):
        if len(images) < frames:
            raise ValueError(f"InfiniteTalk returned {len(images)} frames for a {frames}-frame clip.")
        return (images[:frames],)


class DemoTalkAudioFeatures:
    CATEGORY = CATEGORY
    FUNCTION = "encode"
    RETURN_TYPES = ("MULTITALK_EMBEDS",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"wav2vec_model": ("WAV2VECMODEL",), "audio": ("AUDIO",), "frames": ("INT",)}}

    def encode(self, wav2vec_model, audio, frames):
        # New Transformers releases collect layer outputs on the parent model.
        # WanVideo's custom forward calls the encoder directly, bypassing that collection.
        model = wav2vec_model["model"]
        captured = []

        def collect_layer(_module, _inputs, output):
            captured.append(output[0] if isinstance(output, tuple) else output)

        def restore_hidden_states(_module, _inputs, output):
            if getattr(output, "hidden_states", None) is None and hasattr(output, "last_hidden_state"):
                # MultiTalk discards the first entry, which normally holds the encoder input.
                output.hidden_states = (None, *captured[:-1], output.last_hidden_state)

        hooks = [layer.register_forward_hook(collect_layer) for layer in model.encoder.layers]
        hooks.append(model.encoder.register_forward_hook(restore_hidden_states))
        try:
            features, _, _ = nodes.NODE_CLASS_MAPPINGS["MultiTalkWav2VecEmbeds"]().process(
                wav2vec_model=wav2vec_model, audio_1=audio, num_frames=frames, fps=float(FPS),
                normalize_loudness=False, audio_scale=1.0, audio_cfg_scale=1.0, multi_audio_type="para")
            return (features,)
        finally:
            for hook in hooks:
                hook.remove()


class DemoClipResult:
    CATEGORY = CATEGORY
    FUNCTION = "collect"
    RETURN_TYPES = ("DEMO_CLIPS",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"filenames": ("VHS_FILENAMES",), "start": ("INT",), "end": ("INT",),
                             "width": ("INT",), "height": ("INT",)},
                "optional": {"previous": ("DEMO_CLIPS",)}}

    def collect(self, filenames, start, end, width, height, previous=None):
        path = str(Path(filenames[1][-1]).resolve())
        return ((*(previous or ()), dict(file=path, start_frame=start, end_frame=end,
                                        width=width, height=height)),)


def ffmpeg(*args, cwd=None, data=None):
    run = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", *args],
                         input=data, cwd=cwd, capture_output=True)
    if run.returncode:
        raise RuntimeError(run.stderr.decode("utf-8", errors="replace"))


class DemoFinishVideo:
    CATEGORY = CATEGORY
    FUNCTION = "finish"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "audio": ("AUDIO",),
            "subtitle_path": ("STRING", {"forceInput": True}),
            "render_video": ("BOOLEAN", {"default": True}),
            "burn_subtitles": ("BOOLEAN", {"default": False}),
            "music_enabled": ("BOOLEAN", {"default": False}),
            "music_gain": ("FLOAT", {"default": 0.12, "min": 0.0, "max": 1.0, "step": 0.01}),
            "output_width": ("INT", {"default": 832, "min": 64, "max": 4096, "step": 2}),
            "output_height": ("INT", {"default": 480, "min": 64, "max": 4096, "step": 2}),
            "subtitle_size": ("INT", {"default": 24, "min": 8, "max": 72}),
            "filename_prefix": ("STRING", {"default": "WorkDemo/demo"}),
        }, "optional": {"clips": ("DEMO_CLIPS", {"lazy": True}),
                        "music": ("AUDIO", {"lazy": True})}}

    def check_lazy_status(self, render_video, music_enabled, clips=None, music=None, **kwargs):
        needed = []
        if render_video and clips is None:
            needed.append("clips")
        if render_video and music_enabled and music is None:
            needed.append("music")
        return needed

    def finish(self, audio, subtitle_path, render_video, burn_subtitles, music_enabled, music_gain,
               output_width, output_height, subtitle_size, filename_prefix, clips=None, music=None):
        if not render_video:
            return ()
        if not clips:
            raise ValueError("Connect the InfiniteTalk clip output.")
        if music_enabled and music is None:
            raise ValueError("Connect background music or turn it off.")
        if output_width % 2 or output_height % 2:
            raise ValueError("Final video width and height must be even.")

        rate = audio["sample_rate"]
        wave = audio["waveform"].cpu().float()
        if music_enabled:
            bed = music["waveform"].cpu().float()
            if not bed.shape[-1]:
                raise ValueError("The background music file contains no audio.")
            if music["sample_rate"] != rate:
                bed = torchaudio.functional.resample(bed, music["sample_rate"], rate)
            if bed.shape[1] != wave.shape[1] and bed.shape[1] != 1 and wave.shape[1] != 1:
                bed = bed.mean(dim=1, keepdim=True)
            bed = bed.repeat(1, 1, math.ceil(wave.shape[-1] / bed.shape[-1]))[..., :wave.shape[-1]]
            wave = (wave + music_gain * bed).clamp(-1, 1)
        samples = round(clips[-1]["end_frame"] * rate / FPS)
        wave = F.pad(wave[..., :samples], (0, max(0, samples - wave.shape[-1])))
        pcm = wave[0].T.contiguous().numpy().tobytes()

        out_dir, stem, counter, subfolder, _ = folder_paths.get_save_image_path(
            filename_prefix, folder_paths.get_output_directory(), output_width, output_height)
        filename = f"{stem}_{counter:05}.mp4"
        output = Path(out_dir).resolve() / filename
        with TemporaryDirectory(dir=out_dir, prefix="demo-") as tmp:
            temp = Path(tmp).resolve()
            names = []
            # Each exported clip retains its generation size. The preview uses one canvas.
            scale = (f"scale={output_width}:{output_height}:force_original_aspect_ratio=decrease:"
                     f"force_divisible_by=2,pad={output_width}:{output_height}:(ow-iw)/2:(oh-ih)/2,setsar=1")
            for index, clip in enumerate(clips):
                name = f"clip-{index}.mp4"
                ffmpeg("-i", clip["file"], "-map", "0:v:0", "-vf", scale, "-an",
                       "-r", str(FPS), "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p",
                       name, cwd=temp)
                duration = (round(clip["end_frame"] * 1_000_000 / FPS)
                            - round(clip["start_frame"] * 1_000_000 / FPS))
                names.extend((f"file '{name}'", f"duration {duration / 1_000_000:.6f}"))
            (temp / "clips.txt").write_text("\n".join(names), encoding="ascii")
            muxed = temp / "joined.mp4"
            ffmpeg("-f", "concat", "-safe", "1", "-i", "clips.txt", "-f", "f32le",
                   "-ar", str(rate), "-ac", str(wave.shape[1]), "-i", "pipe:0",
                   "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                   "-b:a", "192k", "-movflags", "+faststart", muxed.name, cwd=temp, data=pcm)
            if burn_subtitles:
                subtitled = temp / "subtitled.mp4"
                SubtitleBurnIn()._burn_subtitles_ffmpeg(muxed, Path(subtitle_path), subtitled,
                                                       subtitle_size, "white", "black", 2, "bottom", 20)
                muxed = subtitled
            manifest = {"fps": FPS, "adjusted_srt": str(Path(subtitle_path).resolve()),
                        "clips": [{**clip, "start_seconds": clip["start_frame"] / FPS,
                                   "end_seconds": clip["end_frame"] / FPS} for clip in clips]}
            output.with_suffix(".json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                                   encoding="utf-8")
            muxed.replace(output)
        return {"ui": {"images": [{"filename": filename, "subfolder": subfolder, "type": "output"}],
                       "animated": [True]}}
