#!/usr/bin/env python3
import os
import json
import requests
from pprint import pprint

# Voice file directory (same as in api/index.py)
API_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api")
VOICE_DIR = os.path.join(API_DIR, "voice_files")

# Voice mappings (same as in api/index.py)
VOICE_MAPPINGS = {
    "default": {"file": "af_bella.pt", "huggingface": "af_bella"},
    "female1": {"file": "af_sarah.pt", "huggingface": "af_sarah"},
    "female2": {"file": "af_nicole.pt", "huggingface": "af_nicole"},
    "male1": {"file": "am_michael.pt", "huggingface": "am_michael"},
    "male2": {"file": "am_adam.pt", "huggingface": "am_adam"},
    "british": {"file": "bf_isabella.pt", "huggingface": "bf_isabella"},
    "australian": {"file": "bf_emma.pt", "huggingface": "bf_emma"}
}

def check_voice_files():
    """Check if voice files exist and show information about them."""
    print(f"Checking voice files in: {VOICE_DIR}")
    
    # Create voice directory if it doesn't exist
    if not os.path.exists(VOICE_DIR):
        os.makedirs(VOICE_DIR, exist_ok=True)
        print(f"Created voice directory: {VOICE_DIR}")
    
    # Check each voice file
    voice_status = {}
    for voice_id, info in VOICE_MAPPINGS.items():
        voice_file = info["file"]
        huggingface_id = info["huggingface"]
        voice_path = os.path.join(VOICE_DIR, voice_file)
        
        exists = os.path.exists(voice_path)
        size = os.path.getsize(voice_path) if exists else 0
        size_mb = size / (1024 * 1024) if exists else 0
        
        voice_status[voice_id] = {
            "file": voice_file,
            "huggingface_id": huggingface_id,
            "exists": exists,
            "size_mb": round(size_mb, 2) if exists else 0,
            "path": voice_path
        }
    
    return voice_status

def download_voice_file(voice_id):
    """Download a voice file from HuggingFace."""
    if voice_id not in VOICE_MAPPINGS:
        print(f"Error: Unknown voice ID '{voice_id}'")
        return False
    
    voice_info = VOICE_MAPPINGS[voice_id]
    voice_file = voice_info["file"]
    huggingface_id = voice_info["huggingface"]
    voice_path = os.path.join(VOICE_DIR, voice_file)
    
    # If file already exists, skip download
    if os.path.exists(voice_path):
        print(f"Voice file '{voice_file}' already exists.")
        return True
    
    # Download the file
    print(f"Downloading voice file '{voice_file}' from HuggingFace...")
    url = f"https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/{huggingface_id}.pt"
    print(f"URL: {url}")
    
    try:
        # First create the directory if it doesn't exist
        os.makedirs(os.path.dirname(voice_path), exist_ok=True)
        
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(voice_path, 'wb') as f:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192
                
                # Show progress while downloading
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rDownloading... {percent:.1f}% ({downloaded} / {total_size} bytes)", end="")
            
            print(f"\nSuccessfully downloaded voice file '{voice_file}'")
            return True
        else:
            print(f"Failed to download voice file: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"Error downloading voice file: {e}")
        return False

def main():
    """Main function."""
    # Check voice files
    print("=== VOICE FILES STATUS ===")
    voice_status = check_voice_files()
    pprint(voice_status)
    
    # Ask user if they want to download missing files
    missing_voices = [voice_id for voice_id, info in voice_status.items() if not info["exists"]]
    if missing_voices:
        print(f"\nMissing voice files: {', '.join(missing_voices)}")
        download = input("Do you want to download missing voice files? (y/n): ").lower().strip() == 'y'
        
        if download:
            for voice_id in missing_voices:
                download_voice_file(voice_id)
            
            # Check voice files again
            print("\n=== UPDATED VOICE FILES STATUS ===")
            voice_status = check_voice_files()
            pprint(voice_status)
    else:
        print("\nAll voice files are present!")
    
    # Test the API if files exist
    if any(info["exists"] for info in voice_status.values()):
        test_api = input("\nDo you want to test the API with a voice request? (y/n): ").lower().strip() == 'y'
        if test_api:
            try:
                print("\nSending a test request to the API...")
                response = requests.post(
                    "http://localhost:5001/api/voice",
                    json={"text": "Hello, this is a test of the Kokoro voice system. How does it sound?", "voice": "default"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"API Response Status: {response.status_code}")
                    print(f"Text Response: {data.get('response', 'No text response')}")
                    if "audio" in data:
                        print(f"Audio Data: [Base64 data, length: {len(data['audio']) // 1000}KB]")
                    else:
                        print("No audio data in response")
                        if "message" in data:
                            print(f"Message: {data['message']}")
                else:
                    print(f"API Error: {response.status_code}")
                    print(response.text)
            except Exception as e:
                print(f"Error testing API: {e}")
    
    print("\nCheck complete!")

if __name__ == "__main__":
    main() 