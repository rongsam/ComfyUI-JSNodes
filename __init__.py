"""
ComfyUI-JSNodes

A collection of custom nodes for ComfyUI, focusing on audio-video synchronization
and other utility functions for creative workflows.

Author: rongsam
Repository: https://github.com/rongsam/ComfyUI-JSNodes
License: MIT
"""

from .audio_nodes import AudioPadToFrames
from .video_nodes import VideoStitching
from .image_nodes import SaveImageOptional

# Central registry for all nodes in this package
NODE_CLASS_MAPPINGS = {
    "AudioPadToFrames": AudioPadToFrames,
    "VideoStitching": VideoStitching,
    "SaveImageOptional": SaveImageOptional,
}

# Display names that appear in ComfyUI interface
NODE_DISPLAY_NAME_MAPPINGS = {
    "AudioPadToFrames": "🔇 Audio Pad to Frames",
    "VideoStitching": "🎬 Video Stitching",
    "SaveImageOptional": "💾 Save Image Optional",
}

# Package metadata
__version__ = "0.3.0"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

# Print initialization message
print(f"🚀 ComfyUI-JSNodes v{__version__} loaded successfully!")
print(f"   → Loaded {len(NODE_CLASS_MAPPINGS)} custom node(s)")
