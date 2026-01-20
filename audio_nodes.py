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


# Export nodes from this module
__all__ = ['AudioPadToFrames']
