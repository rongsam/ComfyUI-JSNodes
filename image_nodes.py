"""
Image processing nodes for ComfyUI-JSNodes

This module contains custom nodes for image manipulation and saving.
"""

import torch
import numpy as np
from PIL import Image
from pathlib import Path
import os


class SaveImageOptional:
    """
    Save Image Optional Node

    Conditionally saves images to PNG files with customizable naming and subfolder support.

    This node allows you to control whether images are saved during workflow execution,
    useful for debugging or when you only want to save final outputs.

    Inputs:
        image (IMAGE): Input image from connected node
        filename_prefix (STRING): Prefix for filename, supports subfolders (e.g., "video/myvideo")
        filename_suffix (STRING): Suffix for filename (e.g., "preview")
        save_output (BOOLEAN): Whether to save the image (True) or just pass through (False)

    Outputs:
        image (IMAGE): The input image (passed through unchanged)

    Filename Format:
        <filename_prefix>_<sequence>_<filename_suffix>.png
        Example: myvideo_00001_preview.png

    Subfolder Support:
        If filename_prefix contains "/" or "\\", creates subfolders in output directory.
        Example: "video/myvideo" creates "output/video/" folder with files like "myvideo_00001.png"
    """

    def __init__(self):
        # Try to get ComfyUI's output directory
        try:
            import folder_paths
            self.output_dir = folder_paths.get_output_directory()
        except:
            # Fallback: use ComfyUI/output relative to current working directory
            # Assumes ComfyUI structure
            self.output_dir = os.path.join(os.getcwd(), "output")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename_prefix": ("STRING", {
                    "default": "image",
                    "tooltip": "Prefix for filename, supports subfolders (e.g., 'video/myimage')"
                }),
                "filename_suffix": ("STRING", {
                    "default": "",
                    "tooltip": "Suffix for filename (e.g., 'preview')"
                }),
                "save_output": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Save the image to file (True) or just pass through (False)"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "save_image_optional"
    CATEGORY = "JSNodes/Image"
    OUTPUT_NODE = True

    def save_image_optional(self, image, filename_prefix, filename_suffix, save_output):
        """
        Main execution function that optionally saves the image.

        Args:
            image (torch.Tensor): Input image tensor [batch, height, width, channels]
            filename_prefix (str): Prefix for output filename (can include subfolder path)
            filename_suffix (str): Suffix for output filename
            save_output (bool): Whether to save the image to disk

        Returns:
            tuple: The input image (passed through)
        """
        # If save_output is False, just pass through the image
        if not save_output:
            print("⏭️ Save Image Optional: Skipping save (save_output=False)")
            return (image,)

        try:
            # Get output directory as Path object
            output_dir = Path(self.output_dir)

            # Handle subfolder in filename_prefix (e.g., "video/myvideo")
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
                # Build filename with pattern: prefix_00001_suffix.png
                if filename_suffix:
                    filename = f"{actual_prefix}_{counter:05d}_{filename_suffix}.png"
                else:
                    filename = f"{actual_prefix}_{counter:05d}.png"

                filepath = full_output_dir / filename
                if not filepath.exists():
                    break
                counter += 1

            print(f"📝 Output will be: {filepath.name}")

            # Process and save each image in the batch
            saved_count = 0
            for i, img_tensor in enumerate(image):
                # Adjust filename for batch index if there's more than one image
                if len(image) > 1:
                    if filename_suffix:
                        batch_filename = f"{actual_prefix}_{counter:05d}_{i:03d}_{filename_suffix}.png"
                    else:
                        batch_filename = f"{actual_prefix}_{counter:05d}_{i:03d}.png"
                    batch_filepath = full_output_dir / batch_filename
                else:
                    batch_filepath = filepath

                # Convert tensor to PIL Image and save
                self._save_tensor_as_png(img_tensor, batch_filepath)
                saved_count += 1

            print(f"💾 Saved {saved_count} image(s) to: {full_output_dir}")

            return (image,)

        except Exception as e:
            error_msg = f"❌ Error saving image: {str(e)}"
            print(error_msg)
            # Don't raise error, just pass through the image
            return (image,)

    def _save_tensor_as_png(self, img_tensor, filepath):
        """
        Convert a tensor to PIL Image and save as PNG.

        Args:
            img_tensor (torch.Tensor): Image tensor [height, width, channels]
            filepath (Path): Output file path
        """
        # Convert from torch tensor to numpy
        img_np = img_tensor.cpu().numpy()

        # Convert from float [0, 1] to uint8 [0, 255]
        img_np = (img_np * 255).clip(0, 255).astype(np.uint8)

        # Create PIL Image
        pil_image = Image.fromarray(img_np)

        # Save as PNG
        pil_image.save(filepath, format='PNG', compress_level=4)


# Export nodes from this module
__all__ = ['SaveImageOptional']
