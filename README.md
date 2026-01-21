# ComfyUI-JSNodes

A collection of custom nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that enhance audio-video workflows and provide utility functions for creative projects.

## 📦 Installation

### Method 1: Via ComfyUI Manager (Recommended)
1. Open ComfyUI Manager
2. Search for "ComfyUI-JSNodes"
3. Click Install

### Method 2: Manual Installation
1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/rongsam/ComfyUI-JSNodes.git
   ```

3. Install dependencies:
   ```bash
   cd ComfyUI-JSNodes
   pip install -r requirements.txt
   ```

4. **Install ffmpeg** (required for Video Stitching node):
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **Linux**: `sudo apt install ffmpeg`
   - **Mac**: `brew install ffmpeg`

5. Restart ComfyUI

## 🎵 Available Nodes

### Audio Nodes

#### 🔇 Audio Pad to Frames
Automatically synchronizes audio duration with video frame count.

**Location:** `JSNodes/Audio`

**What it does:**
- Pads audio with silence if it's too short for your video
- Trims audio if it's too long
- Ensures perfect audio-video synchronization

**Inputs:**
- `audio` (AUDIO): Input audio waveform
- `target_frame_count` (INT): Number of frames in your video (default: 121)
- `fps` (FLOAT): Video frame rate (default: 24.0)

**Outputs:**
- `padded_audio` (AUDIO): Audio adjusted to match exact video duration

**Use Case:**
Perfect for video generation workflows where you need audio to match exactly with your generated frames. For example, if you're generating a 5-second video at 24fps (120 frames), this node ensures your audio is exactly 5 seconds long.

**Example:**
```
Video: 120 frames at 24fps = 5 seconds
Audio: 3 seconds → Pads 2 seconds of silence
Audio: 7 seconds → Trims last 2 seconds
```

---

### Video Nodes

#### 🎬 Video Stitching
Automatically finds and stitches multiple video files with the same naming pattern into a single continuous video.

**Location:** `JSNodes/Video`

**What it does:**
- Parses VHS Video Combine node output
- Finds all videos with the same filename prefix pattern
- Stitches them together using ffmpeg (no re-encoding for speed)
- Outputs a single concatenated video file

**Inputs:**
- `video_info` (STRING): JSON output from VHS Video Combine node
- `output_prefix` (STRING): Filename prefix for the output video (default: "stitched")

**Outputs:**
- `output_path` (STRING): Path to the stitched video file

**How it works:**
1. Extracts video path from VHS Video Combine JSON output
2. Identifies the filename pattern (e.g., `video_0003.mp4` → prefix is `video`)
3. Searches for all files matching `{prefix}_*.mp4` in the same directory
4. Sorts them by filename in ascending order
5. Uses ffmpeg concat demuxer to stitch without re-encoding
6. Outputs as `{output_prefix}_stitched.mp4`

**Use Case:**
Perfect for batch video generation workflows where ComfyUI generates multiple video segments (e.g., `video_0001.mp4`, `video_0002.mp4`, `video_0003.mp4`) and you want to combine them into one continuous video automatically.

**Example:**
```
Input: VHS generates "output_0005.mp4"
Found files: output_0001.mp4, output_0002.mp4, output_0003.mp4, output_0004.mp4, output_0005.mp4
Output: stitched_stitched.mp4 (all 5 videos combined)
```

**Requirements:**
- ffmpeg must be installed and available in PATH
- All videos must have the same codec/encoding for seamless stitching
- Videos must follow the pattern: `{prefix}_{number}.mp4`

---

## 🛠️ Development

### Project Structure
```
ComfyUI-JSNodes/
├── __init__.py              # Package initialization and node registry
├── audio_nodes.py           # Audio processing nodes
├── video_nodes.py           # Video processing nodes
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
└── .gitignore             # Git ignore rules
```

### Adding New Nodes

1. Create a new module file (e.g., `image_nodes.py`, `utility_nodes.py`)
2. Implement your node class following ComfyUI conventions
3. Import and register in `__init__.py`:
   ```python
   from .your_module import YourNode

   NODE_CLASS_MAPPINGS["YourNode"] = YourNode
   NODE_DISPLAY_NAME_MAPPINGS["YourNode"] = "Your Display Name"
   ```

### Node Development Guidelines

- Use clear, descriptive class names
- Add comprehensive docstrings
- Include input tooltips for better UX
- Use appropriate CATEGORY paths (e.g., "JSNodes/Audio", "JSNodes/Image")
- Print informative messages during execution
- Handle edge cases gracefully

## 📋 Requirements

- Python >= 3.8
- PyTorch >= 2.0.0
- ComfyUI (latest version recommended)
- ffmpeg (for Video Stitching node)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - The amazing UI for Stable Diffusion
- [VHS (Video Helper Suite)](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Video processing for ComfyUI
- ComfyUI community for inspiration and support

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/rongsam/ComfyUI-JSNodes/issues)
- Check existing issues for solutions

## 🔄 Changelog

### v0.2.0 (Latest)
- ✨ Added `Video Stitching` node for automatic video concatenation
- 🎥 Supports VHS Video Combine workflow integration
- ⚡ Fast stitching without re-encoding using ffmpeg

### v0.1.0 (Initial Release)
- ✨ Added `Audio Pad to Frames` node for audio-video synchronization

---

**Made with ❤️ for the ComfyUI community**
