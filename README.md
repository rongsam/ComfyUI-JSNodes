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

4. Restart ComfyUI

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

## 🛠️ Development

### Project Structure
```
ComfyUI-JSNodes/
├── __init__.py              # Package initialization and node registry
├── audio_nodes.py           # Audio processing nodes
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
- ComfyUI community for inspiration and support

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/rongsam/ComfyUI-JSNodes/issues)
- Check existing issues for solutions

## 🔄 Changelog

### v0.1.0 (Initial Release)
- ✨ Added `Audio Pad to Frames` node for audio-video synchronization

---

**Made with ❤️ for the ComfyUI community**
