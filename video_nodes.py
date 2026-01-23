"""
Video processing nodes for ComfyUI-JSNodes

This module contains custom nodes for video manipulation and processing.
"""

import os
import re
import json
import subprocess
from pathlib import Path


class SubtitleBurnIn:
    """
    Subtitle Burn-In Node

    Burns subtitles into video files using ffmpeg with customizable styling.

    This node takes a video file and subtitle file (SRT format), then creates
    a new video with the subtitles permanently embedded (burned-in).

    Features:
    - Preserves original video encoding, bitrate, and resolution
    - Customizable font size, color, outline, and position
    - Sequential numbering for output files
    - Saves in same directory as source video

    Inputs:
        video_path (STRING): Full path to input video file (.mp4)
        subtitle_path (STRING): Full path to subtitle file (.srt)
        filename_prefix (STRING): Prefix for output filename
        font_size (INT): Size of subtitle font (default: 24)
        font_color (STRING): Color of subtitle text (default: "white")
        outline_color (STRING): Color of text outline (default: "black")
        outline_width (INT): Width of text outline (default: 2)
        position (COMBO): Vertical position of subtitles
        margin_v (INT): Vertical margin from edge in pixels

    Outputs:
        output_path (STRING): Path to the generated video file

    Output Format:
        <filename_prefix>_00001.mp4 (sequential numbering)

    Example:
        video_path: C:/videos/movie.mp4
        subtitle_path: C:/videos/movie.srt
        filename_prefix: "movie_subbed"
        → Output: C:/videos/movie_subbed_00001.mp4
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Full path to input video file (.mp4)"
                }),
                "subtitle_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Full path to subtitle file (.srt)"
                }),
                "filename_prefix": ("STRING", {
                    "default": "subtitled",
                    "multiline": False,
                    "tooltip": "Prefix for output filename"
                }),
                "font_size": ("INT", {
                    "default": 24,
                    "min": 8,
                    "max": 72,
                    "step": 1,
                    "tooltip": "Size of subtitle font"
                }),
                "font_color": (["white", "yellow", "black", "red", "green", "blue", "cyan", "magenta"], {
                    "default": "white",
                    "tooltip": "Color of subtitle text"
                }),
                "outline_color": (["black", "white", "dark_gray", "none"], {
                    "default": "black",
                    "tooltip": "Color of text outline"
                }),
                "outline_width": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "tooltip": "Width of text outline (0 = no outline)"
                }),
                "position": (["bottom", "top", "middle"], {
                    "default": "bottom",
                    "tooltip": "Vertical position of subtitles"
                }),
                "margin_v": ("INT", {
                    "default": 20,
                    "min": 0,
                    "max": 200,
                    "step": 5,
                    "tooltip": "Vertical margin from edge in pixels"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "burn_subtitles"
    CATEGORY = "JSNodes/Video"
    OUTPUT_NODE = True

    def burn_subtitles(self, video_path, subtitle_path, filename_prefix,
                      font_size, font_color, outline_color, outline_width,
                      position, margin_v):
        """
        Main execution function that burns subtitles into video.

        Args:
            video_path (str): Path to input video file
            subtitle_path (str): Path to subtitle file
            filename_prefix (str): Prefix for output filename
            font_size (int): Font size for subtitles
            font_color (str): Color of subtitle text
            outline_color (str): Color of text outline
            outline_width (int): Width of text outline
            position (str): Position of subtitles (bottom/top/middle)
            margin_v (int): Vertical margin from edge

        Returns:
            tuple: Path to the output video file
        """
        try:
            # Clean up paths - remove surrounding quotes that Windows Explorer's
            # "Copy as path" feature may add
            video_path = video_path.strip().strip('"')
            subtitle_path = subtitle_path.strip().strip('"')

            # Validate input files
            video_file = Path(video_path)
            subtitle_file = Path(subtitle_path)

            if not video_file.exists():
                raise ValueError(f"Video file not found: {video_path}")
            if not subtitle_file.exists():
                raise ValueError(f"Subtitle file not found: {subtitle_path}")

            print(f"🎬 Input video: {video_file.name}")
            print(f"📄 Subtitle file: {subtitle_file.name}")

            # Get output directory (same as input video)
            output_dir = video_file.parent

            # Find next available sequential number
            counter = 1
            while True:
                output_filename = f"{filename_prefix}_{counter:05d}.mp4"
                output_path = output_dir / output_filename
                if not output_path.exists():
                    break
                counter += 1

            print(f"📝 Output will be: {output_filename}")

            # Burn subtitles using ffmpeg
            self._burn_subtitles_ffmpeg(
                video_file,
                subtitle_file,
                output_path,
                font_size,
                font_color,
                outline_color,
                outline_width,
                position,
                margin_v
            )

            print(f"✅ Subtitle burn-in completed: {output_path}")
            return (str(output_path),)

        except Exception as e:
            error_msg = f"❌ Error during subtitle burn-in: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)

    def _burn_subtitles_ffmpeg(self, video_file, subtitle_file, output_path,
                               font_size, font_color, outline_color, outline_width,
                               position, margin_v):
        """
        Use ffmpeg to burn subtitles into video.

        Args:
            video_file (Path): Input video file
            subtitle_file (Path): Subtitle file
            output_path (Path): Output video file
            font_size (int): Font size
            font_color (str): Font color
            outline_color (str): Outline color
            outline_width (int): Outline width
            position (str): Position (bottom/top/middle)
            margin_v (int): Vertical margin
        """
        # Color mapping to ASS format (BGR format in hex)
        color_map = {
            "white": "&H00FFFFFF",
            "yellow": "&H0000FFFF",
            "black": "&H00000000",
            "red": "&H000000FF",
            "green": "&H0000FF00",
            "blue": "&H00FF0000",
            "cyan": "&H00FFFF00",
            "magenta": "&H00FF00FF",
            "dark_gray": "&H00404040",
            "none": "&H00000000"
        }

        # Position alignment (ASS format)
        # Alignment: 1=left, 2=center, 3=right
        # + 0=bottom, 4=middle, 8=top
        position_map = {
            "bottom": 2,  # Bottom center
            "middle": 6,  # Middle center
            "top": 8      # Top center
        }

        # Build subtitle style string
        primary_color = color_map.get(font_color, "&H00FFFFFF")
        outline_col = color_map.get(outline_color, "&H00000000")
        alignment = position_map.get(position, 2)

        # Escape special characters for Windows paths in ffmpeg filter
        subtitle_path_escaped = str(subtitle_file.absolute()).replace('\\', '/').replace(':', '\\:')

        # Build force_style parameters
        style_params = [
            f"FontSize={font_size}",
            f"PrimaryColour={primary_color}",
            f"OutlineColour={outline_col}",
            f"Outline={outline_width}",
            f"Alignment={alignment}",
            f"MarginV={margin_v}",
            "Bold=0",
            "BorderStyle=1"  # Outline + shadow
        ]

        force_style = ",".join(style_params)

        # Build ffmpeg command
        # Use subtitles filter to burn in srt file
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', str(video_file),
            '-vf', f"subtitles='{subtitle_path_escaped}':force_style='{force_style}'",
            '-c:v', 'libx264',           # Use H.264 codec
            '-crf', '18',                 # High quality (lower = better, 18 = visually lossless)
            '-preset', 'medium',          # Encoding speed/quality balance
            '-c:a', 'copy',               # Copy audio without re-encoding
            '-y',                         # Overwrite output file
            str(output_path)
        ]

        print(f"🎨 Font: {font_size}pt {font_color} with {outline_color} outline")
        print(f"📍 Position: {position} (margin: {margin_v}px)")
        print(f"🎥 Running ffmpeg to burn subtitles...")

        try:
            # Run ffmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            print(f"✅ ffmpeg completed successfully")

        except subprocess.CalledProcessError as e:
            error_msg = f"ffmpeg failed: {e.stderr}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Please install ffmpeg and add it to your PATH."
            )


class VideoStitching:
    """
    Video Stitching Node

    Automatically finds and stitches multiple video files with the same prefix
    into a single continuous video using ffmpeg.

    This node parses the output from VHS Video Combine node, extracts the video
    file path, finds all related videos with the same prefix pattern, and
    concatenates them without re-encoding for maximum speed and quality.

    Inputs:
        video_info (STRING): JSON text output from VHS Video Combine node
        output_prefix (STRING): Filename prefix for the stitched output video

    Outputs:
        output_path (STRING): Path to the stitched video file

    Example:
        If VHS generates "video_00003.mp4", this node will find all files like
        "video_00001.mp4", "video_00002.mp4", "video_00003.mp4", etc., and stitch
        them into a single file named "{output_prefix}_stitched.mp4"
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_info": ("VHS_FILENAMES",),  # Connectable input from VHS Video Combine
                "output_prefix": ("STRING", {
                    "default": "stitched",
                    "multiline": False,
                    "tooltip": "Filename prefix for the output video"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "stitch_videos"
    CATEGORY = "JSNodes/Video"
    OUTPUT_NODE = True

    def stitch_videos(self, video_info, output_prefix):
        """
        Main execution function that stitches multiple videos into one.

        Args:
            video_info: VHS_FILENAMES data structure from VHS Video Combine
            output_prefix (str): Prefix for the output filename

        Returns:
            tuple: Path to the stitched video file, or empty string if skipped
        """
        try:
            # Parse the data from VHS Video Combine
            video_path = self._parse_video_info(video_info)

            # Check if video was persisted (None means temp file only)
            if not video_path:
                print("⏭️ Skipping video stitching (video not persisted or only in temp folder)")
                return ("",)  # Return empty string to indicate skip

            print(f"📹 Source video: {video_path}")

            # Extract directory and filename pattern
            video_file = Path(video_path)
            video_dir = video_file.parent
            file_pattern = self._extract_prefix_pattern(video_file.name)

            print(f"🔍 Searching for pattern: {file_pattern}* in {video_dir}")

            # Find all videos with the same prefix
            video_files = self._find_matching_videos(video_dir, file_pattern)

            if not video_files:
                print("⚠️ No matching videos found, returning original video")
                return (str(video_path),)

            print(f"✅ Found {len(video_files)} video(s) to stitch:")
            for vf in video_files:
                print(f"   - {vf.name}")

            # Stitch videos using ffmpeg
            output_path = self._stitch_with_ffmpeg(
                video_files,
                video_dir,
                output_prefix
            )

            print(f"🎬 Stitched video created: {output_path}")
            return (str(output_path),)

        except Exception as e:
            error_msg = f"❌ Error during video stitching: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)

    def _parse_video_info(self, video_info):
        """
        Parse the output from VHS Video Combine node.

        VHS Video Combine returns format like:
        (
            True/False,  # Persistence flag: True = saved permanently, False = temp only
            [
                "C:\\path\\to\\video_00003.png",
                "C:\\path\\to\\video_00003.mp4"
            ]
        )

        Args:
            video_info: Can be a tuple/list (direct from VHS) or JSON string

        Returns:
            str: Video file path, or None if video not persisted
        """
        # DEBUG: Print what we actually received
        print(f"🔍 DEBUG: video_info type = {type(video_info)}")
        print(f"🔍 DEBUG: video_info value = {video_info}")

        data = video_info

        # If it's a string, try to parse as JSON
        if isinstance(video_info, str):
            try:
                data = json.loads(video_info)
            except json.JSONDecodeError:
                # If not JSON, assume it's a direct file path
                video_info = video_info.strip()
                if video_info:
                    print(f"✓ Using direct path: {video_info}")
                    return video_info
                raise ValueError("Unable to parse video_info")

        # Handle VHS Video Combine format: (bool, [png_path, mp4_path])
        if isinstance(data, (list, tuple)) and len(data) >= 2:
            # Check if first element is a boolean indicating persistence
            if isinstance(data[0], bool):
                if not data[0]:
                    # Video not persisted (only in temp folder), skip stitching
                    print("⚠️ Video not persisted (temporary file), skipping stitching")
                    return None
                else:
                    print("✓ Video is persisted, proceeding with stitching")

            # Second element should be array of file paths
            if isinstance(data[1], (list, tuple)) and len(data[1]) >= 2:
                # Find the .mp4 file (should be second item)
                for file_path in data[1]:
                    if isinstance(file_path, str) and file_path.lower().endswith('.mp4'):
                        print(f"✓ Parsed VHS output, found MP4: {file_path}")
                        return file_path
                # If no .mp4 found, take the last item
                return data[1][-1]

        # Handle dict format (legacy or other sources)
        elif isinstance(data, dict):
            path = data.get('filename') or data.get('path')
            if path:
                print(f"✓ Extracted from dict: {path}")
                return path

        # Handle simple string in array
        elif isinstance(data, list) and len(data) > 0:
            path = str(data[0])
            print(f"✓ Extracted from list: {path}")
            return path

        raise ValueError("Unable to parse video_info. Expected VHS Video Combine output format.")

    def _extract_prefix_pattern(self, filename):
        """
        Extract the prefix pattern from a filename.

        Examples:
            "video_00003.mp4" -> "video"
            "output_0001.mp4" -> "output"
            "render_00042.mp4" -> "render"

        Args:
            filename (str): Video filename

        Returns:
            str: Extracted prefix
        """
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]

        # Match pattern: prefix followed by underscore and numbers
        # e.g., "video_00003" -> "video"
        match = re.match(r'^(.+?)_\d+$', name_without_ext)

        if match:
            return match.group(1)
        else:
            # If no pattern found, return the whole name without extension
            return name_without_ext

    def _find_matching_videos(self, directory, prefix):
        """
        Find all video files in directory matching the prefix pattern.

        Args:
            directory (Path): Directory to search
            prefix (str): Filename prefix to match

        Returns:
            list: Sorted list of Path objects for matching videos
        """
        # Find all files matching the pattern: {prefix}_*.mp4
        pattern = f"{prefix}_*.mp4"
        matching_files = list(directory.glob(pattern))

        # Sort by filename (natural sort order)
        matching_files.sort(key=lambda x: x.name)

        return matching_files

    def _stitch_with_ffmpeg(self, video_files, output_dir, output_prefix):
        """
        Stitch multiple videos using ffmpeg concat demuxer (no re-encoding).

        Args:
            video_files (list): List of Path objects for videos to stitch
            output_dir (Path): Output directory
            output_prefix (str): Prefix for output filename

        Returns:
            Path: Path to the stitched output video
        """
        # Find next available sequential number for output filename
        counter = 1
        while True:
            output_filename = f"{output_prefix}_{counter:05d}.mp4"
            output_path = output_dir / output_filename
            if not output_path.exists():
                break
            counter += 1

        print(f"📝 Output will be: {output_filename}")

        # Create a temporary file list for ffmpeg concat
        concat_file = output_dir / f"{output_prefix}_concat_list.txt"

        # Write the concat file format required by ffmpeg
        with open(concat_file, 'w', encoding='utf-8') as f:
            for video in video_files:
                # Use absolute path and escape special characters for ffmpeg
                # Convert Windows backslashes to forward slashes
                escaped_path = str(video.absolute()).replace('\\', '/')
                f.write(f"file '{escaped_path}'\n")

        # Build ffmpeg command (concat without re-encoding)
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'concat',           # Use concat demuxer
            '-safe', '0',              # Allow absolute paths
            '-i', str(concat_file),    # Input concat file
            '-c', 'copy',              # Copy codec (no re-encoding)
            '-y',                      # Overwrite output file
            str(output_path)           # Output file
        ]

        print(f"🎥 Running ffmpeg to stitch {len(video_files)} videos...")

        try:
            # Run ffmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Clean up concat file
            if concat_file.exists():
                concat_file.unlink()

            return output_path

        except subprocess.CalledProcessError as e:
            error_msg = f"ffmpeg failed: {e.stderr}"
            print(f"❌ {error_msg}")

            # Clean up concat file even on failure
            if concat_file.exists():
                concat_file.unlink()

            raise RuntimeError(error_msg)
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Please install ffmpeg and add it to your PATH."
            )


# Export nodes from this module
__all__ = ['SubtitleBurnIn', 'VideoStitching']
