import os
import urllib.request
from pathlib import Path

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"Successfully downloaded {dest_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

if __name__ == "__main__":
    # Base directory for the backend
    base_dir = Path(__file__).resolve().parent.parent
    
    # Target directories
    models_dir = base_dir / "assets" / "telemetry" / "models"
    wasm_dir = models_dir / "wasm"
    
    # Create directories if they don't exist
    models_dir.mkdir(parents=True, exist_ok=True)
    wasm_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to download
    files_to_download = [
        {
            "url": "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
            "dest": models_dir / "face_landmarker.task"
        },
        {
            "url": "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm/vision_wasm_internal.wasm",
            "dest": wasm_dir / "vision_wasm_internal.wasm"
        },
        {
            "url": "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.18/wasm/vision_wasm_internal.js",
            "dest": wasm_dir / "vision_wasm_internal.js"
        }
    ]
    
    for item in files_to_download:
        download_file(item["url"], item["dest"])
    
    print("Download script finished.")
