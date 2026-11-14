"""
ComfyUI-JSNodes

A collection of custom nodes for ComfyUI, focusing on audio-video synchronization
and other utility functions for creative workflows.

Author: rongsam
Repository: https://github.com/rongsam/ComfyUI-JSNodes
License: MIT
"""

from .audio_nodes import AudioPadToFrames, SaveSRT
from .video_nodes import VideoStitching, SubtitleBurnIn
from .image_nodes import SaveImageOptional
from .api_nodes import OllamaReleaseVRAM
from .h3_nodes import H3VideoPreset, H3LongVideoSize, H3CenterCropVideo
from .digital_human_nodes import (
    DemoClipInputs, DemoClipResult, DemoClipTrim, DemoFinishVideo, DemoInfiniteTalkClips,
    DemoTalkAudioFeatures,
)

# Central registry for all nodes in this package
NODE_CLASS_MAPPINGS = {
    "AudioPadToFrames": AudioPadToFrames,
    "VideoStitching": VideoStitching,
    "SubtitleBurnIn": SubtitleBurnIn,
    "SaveImageOptional": SaveImageOptional,
    "SaveSRT": SaveSRT,
    "OllamaReleaseVRAM": OllamaReleaseVRAM,
    "H3VideoPreset": H3VideoPreset,
    "H3LongVideoSize": H3LongVideoSize,
    "H3CenterCropVideo": H3CenterCropVideo,
    "DemoInfiniteTalkClips": DemoInfiniteTalkClips,
    "DemoClipInputs": DemoClipInputs,
    "DemoClipTrim": DemoClipTrim,
    "DemoClipResult": DemoClipResult,
    "DemoFinishVideo": DemoFinishVideo,
    "DemoTalkAudioFeatures": DemoTalkAudioFeatures,
}

# Display names that appear in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioPadToFrames": "🔇 Audio Pad to Frames",
    "VideoStitching": "🎬 Video Stitching",
    "SubtitleBurnIn": "📝 Subtitle Burn-In",
    "SaveImageOptional": "💾 Save Image Optional",
    "SaveSRT": "💾 Save SRT",
    "OllamaReleaseVRAM": "🧠 Release VRAM from Ollama",
}

# Package metadata
__version__ = "0.4.0"
WEB_DIRECTORY = "./web"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print(f"ComfyUI-JSNodes v{__version__}: loaded {len(NODE_CLASS_MAPPINGS)} custom nodes.")
