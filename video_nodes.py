"""
Video processing nodes for ComfyUI-JSNodes

This module contains custom nodes for video manipulation and processing.
"""

import os
import re
import json
import subprocess
from pathlib import Path


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
            video_info (str): JSON string containing video file information
            output_prefix (str): Prefix for the output filename

        Returns:
            tuple: Path to the stitched video file
        """
        try:
            # Parse the JSON from VHS Video Combine
            video_path = self._parse_video_info(video_info)

            if not video_path:
                raise ValueError("Could not find video path in the provided JSON")

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
        [
            True,
            [
                "C:\\path\\to\\video_00003.png",
                "C:\\path\\to\\video_00003.mp4"
            ]
        ]

        Args:
            video_info: Can be a list/dict (direct from VHS) or JSON string

        Returns:
            str: Video file path
        """
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

        # Handle VHS Video Combine format: [bool, [png_path, mp4_path]]
        if isinstance(data, list) and len(data) >= 2:
            # Second element should be array of file paths
            if isinstance(data[1], list) and len(data[1]) >= 2:
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
        # Create a temporary file list for ffmpeg concat
        concat_file = output_dir / f"{output_prefix}_concat_list.txt"

        # Write the concat file format required by ffmpeg
        with open(concat_file, 'w', encoding='utf-8') as f:
            for video in video_files:
                # Use absolute path and escape special characters for ffmpeg
                # Convert Windows backslashes to forward slashes
                escaped_path = str(video.absolute()).replace('\\', '/')
                f.write(f"file '{escaped_path}'\n")

        # Output filename
        output_path = output_dir / f"{output_prefix}_stitched.mp4"

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
__all__ = ['VideoStitching']
