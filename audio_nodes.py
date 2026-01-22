"""
Audio processing nodes for ComfyUI-JSNodes

This module contains custom nodes for audio manipulation and synchronization.
"""

import torch


class AudioPadToFrames:
    """
    Audio-Video Synchronization Node

    Automatically adjusts audio duration to match video frame count by either:
    - Padding with silence if audio is too short
    - Trimming excess if audio is too long

    This ensures perfect synchronization between audio and video outputs.

    Inputs:
        audio (AUDIO): Input audio waveform
        target_frame_count (INT): Number of frames in target video
        fps (FLOAT): Frames per second of the video

    Outputs:
        padded_audio (AUDIO): Audio adjusted to match exact video duration

    Example:
        For a 5-second video at 24fps (120 frames), this node will ensure
        the audio is exactly 5 seconds long by padding or trimming.
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "target_frame_count": ("INT", {
                    "default": 121,
                    "min": 1,
                    "max": 99999,
                    "tooltip": "Total number of frames in the target video"
                }),
                "fps": ("FLOAT", {
                    "default": 24.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.01,
                    "tooltip": "Frames per second of the video"
                }),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("padded_audio",)
    FUNCTION = "pad_audio"
    CATEGORY = "JSNodes/Audio"
    OUTPUT_NODE = False

    def pad_audio(self, audio, target_frame_count, fps):
        """
        Main execution function that adjusts audio duration to match video frames.

        Args:
            audio (dict): Audio data containing 'waveform' and 'sample_rate'
            target_frame_count (int): Number of video frames
            fps (float): Video frame rate

        Returns:
            tuple: Modified audio data in ComfyUI AUDIO format
        """
        waveform = audio['waveform']  # Shape: [batch, channels, samples]
        sample_rate = audio['sample_rate']

        # Calculate target duration and samples needed
        target_duration = target_frame_count / fps
        target_samples = int(target_duration * sample_rate)
        current_samples = waveform.shape[-1]

        # Determine operation needed
        if current_samples < target_samples:
            # Audio is too short - pad with silence
            pad_amount = target_samples - current_samples
            padding = torch.zeros(
                (waveform.shape[0], waveform.shape[1], pad_amount),
                dtype=waveform.dtype,
                device=waveform.device
            )
            new_waveform = torch.cat((waveform, padding), dim=-1)
            print(f"🔇 Audio Padding: Added {pad_amount} samples "
                  f"(~{pad_amount/sample_rate:.2f}s) of silence")

        elif current_samples > target_samples:
            # Audio is too long - trim excess
            new_waveform = waveform[:, :, :target_samples]
            trimmed = current_samples - target_samples
            print(f"✂️ Audio Trimming: Removed {trimmed} samples "
                  f"(~{trimmed/sample_rate:.2f}s) from end")

        else:
            # Audio duration matches perfectly
            new_waveform = waveform
            print("✓ Audio duration already matches target frame count")

        # Return in ComfyUI AUDIO format
        new_audio = {
            "waveform": new_waveform,
            "sample_rate": sample_rate
        }

        return (new_audio,)


class SaveSRT:
    """
    Save SRT Node

    Saves SRT subtitle content to a file with UTF-8 encoding, supporting Chinese
    and other Unicode characters.

    This node takes SRT subtitle text and saves it to a .srt file in the ComfyUI
    output directory with proper UTF-8 encoding to support all languages including
    Chinese, Japanese, Korean, and other Unicode characters.

    Features:
    - UTF-8 encoding for full Unicode support
    - Sequential numbering for output files
    - Subfolder support via filename_prefix
    - Saves to ComfyUI output directory

    Inputs:
        srt_content (STRING): The SRT subtitle content to save
        filename_prefix (STRING): Prefix for filename, supports subfolders (e.g., "subtitles/myvideo")

    Outputs:
        output_path (STRING): Full path to the saved SRT file

    Output Format:
        <filename_prefix>_00001.srt (sequential numbering)

    Subfolder Support:
        If filename_prefix contains "/" or "\\", creates subfolders in output directory.
        Example: "subtitles/video" creates "output/subtitles/" folder with files like "video_00001.srt"
    """

    def __init__(self):
        # Get ComfyUI's output directory
        try:
            import folder_paths
            self.output_dir = folder_paths.get_output_directory()
        except:
            # Fallback: use ComfyUI/output relative to current working directory
            import os
            self.output_dir = os.path.join(os.getcwd(), "output")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "srt_content": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "SRT subtitle content to save"
                }),
                "filename_prefix": ("STRING", {
                    "default": "subtitles",
                    "multiline": False,
                    "tooltip": "Prefix for filename, supports subfolders (e.g., 'subtitles/myvideo')"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "save_srt"
    CATEGORY = "JSNodes/Audio"
    OUTPUT_NODE = True

    def save_srt(self, srt_content, filename_prefix):
        """
        Main execution function that saves SRT content to file.

        Args:
            srt_content (str): SRT subtitle content to save
            filename_prefix (str): Prefix for output filename (can include subfolder path)

        Returns:
            tuple: Path to the saved SRT file
        """
        try:
            from pathlib import Path

            # Get output directory as Path object
            output_dir = Path(self.output_dir)

            # Handle subfolder in filename_prefix (e.g., "subtitles/myvideo")
            prefix_path = Path(filename_prefix)

            if len(prefix_path.parts) > 1:
                # Has subfolder(s)
                subfolder = prefix_path.parent
                actual_prefix = prefix_path.name

                # Create full output directory with subfolder
                full_output_dir = output_dir / subfolder
                full_output_dir.mkdir(parents=True, exist_ok=True)

                print(f"📁 Created/using subfolder: {subfolder}")
            else:
                # No subfolder, just use output directory
                full_output_dir = output_dir
                actual_prefix = filename_prefix

            # Find next available sequential number
            counter = 1
            while True:
                filename = f"{actual_prefix}_{counter:05d}.srt"
                filepath = full_output_dir / filename
                if not filepath.exists():
                    break
                counter += 1

            print(f"📝 Output will be: {filename}")

            # Save SRT content with UTF-8 encoding (critical for Chinese characters)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(srt_content)

            print(f"💾 Saved SRT file to: {filepath}")

            return (str(filepath),)

        except Exception as e:
            error_msg = f"❌ Error saving SRT file: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)


# Export nodes from this module
__all__ = ['AudioPadToFrames', 'SaveSRT']
