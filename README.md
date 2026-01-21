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

4. **Install ffmpeg** (required for Video nodes):
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
- `video_info` (VHS_FILENAMES): Connected from VHS Video Combine node's "filenames" output
- `output_prefix` (STRING): Filename prefix for the output video (default: "stitched")

**Outputs:**
- `output_path` (STRING): Path to the stitched video file

**How it works:**
1. Extracts video path from VHS Video Combine output
2. Identifies the filename pattern (e.g., `video_00003.mp4` → prefix is `video`)
3. Searches for all files matching `{prefix}_*.mp4` in the same directory
4. Sorts them by filename in ascending order
5. Uses ffmpeg concat demuxer to stitch without re-encoding
6. Outputs as `{output_prefix}_00001.mp4` with sequential numbering

**Use Case:**
Perfect for batch video generation workflows where ComfyUI generates multiple video segments (e.g., `video_00001.mp4`, `video_00002.mp4`, `video_00003.mp4`) and you want to combine them into one continuous video automatically.

**Example:**
```
Input: VHS generates "output_00005.mp4"
Found files: output_00001.mp4, output_00002.mp4, output_00003.mp4, output_00004.mp4, output_00005.mp4
Output: stitched_00001.mp4 (all 5 videos combined)
```

**Requirements:**
- ffmpeg must be installed and available in PATH
- All videos must have the same codec/encoding for seamless stitching
- Videos must follow the pattern: `{prefix}_{number}.mp4`

---

#### 📝 Subtitle Burn-In
Burns subtitles permanently into video files with professional styling options.

**Location:** `JSNodes/Video`

**What it does:**
- Embeds SRT subtitles directly into video using ffmpeg
- Customizable font size, color, outline, and position
- Preserves original video quality and resolution
- Sequential numbering for output files

**Inputs:**
- `video_path` (STRING): Full path to input video file (.mp4)
- `subtitle_path` (STRING): Full path to subtitle file (.srt)
- `filename_prefix` (STRING): Prefix for output filename (default: "subtitled")
- `font_size` (INT): Subtitle font size, 8-72pt (default: 24)
- `font_color` (COMBO): Text color - white, yellow, black, red, green, blue, cyan, magenta
- `outline_color` (COMBO): Outline color - black, white, dark_gray, none
- `outline_width` (INT): Outline thickness, 0-10px (default: 2)
- `position` (COMBO): Vertical position - bottom, top, middle
- `margin_v` (INT): Distance from edge, 0-200px (default: 20)

**Outputs:**
- `output_path` (STRING): Path to video with burned-in subtitles

**Output Format:**
- Filename: `{filename_prefix}_00001.mp4` (sequential numbering)
- Saved in same directory as source video
- High quality H.264 encoding (CRF 18, visually lossless)
- Audio copied without re-encoding

**Use Case:**
Create videos with permanent subtitles for distribution, ensuring subtitles display correctly on all platforms without requiring external subtitle files.

**Styling Examples:**
```
Classic: white text, black outline, bottom position
High Visibility: yellow text, 3px black outline, 28pt
Minimalist: white text, no outline
Top Position: Any color, top alignment with custom margin
```

---

### Image Nodes

#### 💾 Save Image Optional
Conditionally saves images to PNG files with customizable naming and subfolder support.

**Location:** `JSNodes/Image`

**What it does:**
- Saves images only when `save_output` is enabled
- Custom filename prefix and suffix
- Automatic subfolder creation
- Sequential numbering to prevent overwrites
- Pass-through node (returns image unchanged)

**Inputs:**
- `image` (IMAGE): Input image from connected node
- `filename_prefix` (STRING): Prefix for filename, supports subfolders (default: "image")
- `filename_suffix` (STRING): Optional suffix (default: "")
- `save_output` (BOOLEAN): Toggle saving on/off (default: True)

**Outputs:**
- `image` (IMAGE): Pass-through of input image

**Filename Format:**
```
<filename_prefix>_<sequence>_<filename_suffix>.png

Examples:
- Prefix: "render", Suffix: "preview" → render_00001_preview.png
- Prefix: "image", Suffix: "" → image_00001.png
```

**Subfolder Support:**
```
Prefix: "video/myvideo", Suffix: "preview"
→ Creates: output/video/myvideo_00001_preview.png

Prefix: "project/scene01/shot01", Suffix: "draft"
→ Creates: output/project/scene01/shot01_00001_draft.png
```

**Use Cases:**
1. **Debug Mode**: Set `save_output=False` to skip saving during testing
2. **Organized Output**: Use subfolders to organize renders by project/scene
3. **Multiple Variants**: Different suffixes for different processing stages
4. **Batch Processing**: Sequential numbering prevents overwrites

**Features:**
- Auto-creates subdirectories if they don't exist
- 5-digit zero-padded sequential numbers (00001, 00002, etc.)
- Supports batch images (saves each with index)
- PNG format with optimized compression
- Never overwrites existing files

---

## 🛠️ Development

### Project Structure
```
ComfyUI-JSNodes/
├── __init__.py              # Package initialization and node registry
├── audio_nodes.py           # Audio processing nodes
├── video_nodes.py           # Video processing nodes
├── image_nodes.py           # Image processing nodes
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
├── .gitignore             # Git ignore rules
└── .claude/
    └── rules               # Development guidelines
```

### Adding New Nodes

1. Create a new module file (e.g., `utility_nodes.py`) or add to existing module
2. Implement your node class following ComfyUI conventions
3. Import and register in `__init__.py`:
   ```python
   from .your_module import YourNode

   NODE_CLASS_MAPPINGS["YourNode"] = YourNode
   NODE_DISPLAY_NAME_MAPPINGS["YourNode"] = "Your Display Name"
   ```

### Node Development Guidelines

- Use clear, descriptive class names
- Add comprehensive docstrings with examples
- Include input tooltips for better UX
- Use appropriate CATEGORY paths (e.g., "JSNodes/Audio", "JSNodes/Video", "JSNodes/Image")
- Print informative messages during execution
- Handle edge cases gracefully
- Use sequential numbering for output files to prevent overwrites

## 📋 Requirements

- Python >= 3.8
- PyTorch >= 2.0.0
- ComfyUI (latest version recommended)
- ffmpeg (required for Video Stitching and Subtitle Burn-In nodes)
- NumPy (for image processing)
- Pillow (for image saving)

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

### v0.4.0 (Latest)
- ✨ Added `Subtitle Burn-In` node with professional styling options
  - Customizable font size, color, outline, and position
  - High quality H.264 encoding with audio passthrough
  - Sequential numbering for output files
- ✨ Added `Save Image Optional` node for conditional image saving
  - Subfolder support with automatic directory creation
  - Custom filename prefix and suffix
  - Sequential numbering to prevent overwrites
  - Pass-through functionality

### v0.3.0
- ✨ Added `Save Image Optional` node for conditional image saving
- 📁 Subfolder support with automatic directory creation
- 🔢 Sequential numbering for all output files

### v0.2.0
- ✨ Added `Video Stitching` node for automatic video concatenation
- 🎥 Supports VHS Video Combine workflow integration
- ⚡ Fast stitching without re-encoding using ffmpeg
- 🐛 Fixed VHS output parsing to handle tuple format
- 🔢 Sequential numbering for stitched videos

### v0.1.0 (Initial Release)
- ✨ Added `Audio Pad to Frames` node for audio-video synchronization

---

**Made with ❤️ for the ComfyUI community**
