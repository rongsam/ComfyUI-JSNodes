"""
API integration nodes for ComfyUI-JSNodes

This module contains custom nodes for integrating with external APIs and services.
"""

import urllib.request
import urllib.error
import json


class OllamaReleaseVRAM:
    """
    Release VRAM from Ollama

    Connects to Ollama's API, finds all currently loaded models, and unloads them
    to free up GPU VRAM. This is useful when you need to reclaim GPU memory for
    other tasks like image generation.

    Ollama keeps models loaded in VRAM for faster subsequent inference. This node
    forces all models to be unloaded, releasing that memory back to the system.

    Inputs:
        ollama_url (STRING): Base URL for Ollama API (default: http://localhost:11434)
        trigger (optional): Any input to trigger execution in a workflow

    Outputs:
        result (STRING): Summary of unloaded models and freed resources
    """

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ollama_url": ("STRING", {
                    "default": "http://localhost:11434",
                    "multiline": False,
                    "tooltip": "Base URL for Ollama API server"
                }),
            },
            "optional": {
                "trigger": ("*", {
                    "tooltip": "Optional input to trigger execution after other nodes complete"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "*")
    RETURN_NAMES = ("result", "passthrough")
    FUNCTION = "release_vram"
    CATEGORY = "JSNodes/API"
    OUTPUT_NODE = True

    def _api_request(self, url, data=None, method="GET"):
        """
        Make an HTTP request to the Ollama API.

        Args:
            url (str): Full URL for the API endpoint
            data (dict): Optional JSON data for POST requests
            method (str): HTTP method (GET or POST)

        Returns:
            dict: Parsed JSON response
        """
        headers = {"Content-Type": "application/json"}

        if data is not None:
            data = json.dumps(data).encode("utf-8")
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        else:
            request = urllib.request.Request(url, headers=headers, method=method)

        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_loaded_models(self, base_url):
        """
        Get list of currently loaded models from Ollama.

        Args:
            base_url (str): Base URL for Ollama API

        Returns:
            list: List of loaded model info dictionaries
        """
        url = f"{base_url.rstrip('/')}/api/ps"
        response = self._api_request(url)
        return response.get("models", [])

    def _unload_model(self, base_url, model_name):
        """
        Unload a specific model from Ollama's VRAM.

        Sends a generate request with keep_alive=0 to immediately unload the model.

        Args:
            base_url (str): Base URL for Ollama API
            model_name (str): Name of the model to unload

        Returns:
            bool: True if successful
        """
        url = f"{base_url.rstrip('/')}/api/generate"
        data = {
            "model": model_name,
            "keep_alive": 0,  # Immediately unload the model
            "prompt": "",     # Empty prompt, we just want to trigger unload
        }
        self._api_request(url, data=data)
        return True

    def release_vram(self, ollama_url, trigger=None):
        """
        Main execution function that unloads all models from Ollama.

        Args:
            ollama_url (str): Base URL for Ollama API
            trigger: Optional trigger input (unused, just for workflow ordering)

        Returns:
            tuple: Summary string of the operation
        """
        results = []

        try:
            # Get currently loaded models
            print(f"🔍 Checking Ollama at {ollama_url} for loaded models...")
            loaded_models = self._get_loaded_models(ollama_url)

            if not loaded_models:
                msg = "No models currently loaded in Ollama VRAM."
                print(f"✓ {msg}")
                return (msg, trigger)

            print(f"📋 Found {len(loaded_models)} loaded model(s)")

            # Unload each model
            unloaded_count = 0
            total_size = 0

            for model_info in loaded_models:
                model_name = model_info.get("name", "unknown")
                model_size = model_info.get("size", 0)
                size_gb = model_size / (1024 ** 3) if model_size else 0

                try:
                    print(f"🔄 Unloading: {model_name} ({size_gb:.2f} GB)...")
                    self._unload_model(ollama_url, model_name)
                    results.append(f"✓ Unloaded: {model_name} ({size_gb:.2f} GB)")
                    unloaded_count += 1
                    total_size += model_size
                    print(f"✓ Successfully unloaded: {model_name}")

                except Exception as e:
                    error_msg = f"✗ Failed to unload {model_name}: {str(e)}"
                    results.append(error_msg)
                    print(f"⚠️ {error_msg}")

            # Summary
            total_gb = total_size / (1024 ** 3)
            summary = f"Released {unloaded_count} model(s), ~{total_gb:.2f} GB VRAM freed"
            results.append(f"\n{summary}")
            print(f"🎉 {summary}")

            return ("\n".join(results), trigger)

        except urllib.error.URLError as e:
            error_msg = f"❌ Cannot connect to Ollama at {ollama_url}: {str(e)}"
            print(error_msg)
            return (error_msg, trigger)

        except Exception as e:
            error_msg = f"❌ Error releasing Ollama VRAM: {str(e)}"
            print(error_msg)
            return (error_msg, trigger)


# Export nodes from this module
__all__ = ['OllamaReleaseVRAM']
