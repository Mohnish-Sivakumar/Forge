#!/usr/bin/env python3
"""
Cleanup utility to remove unused voice files and temporary files
to keep the storage usage within limits for Render deployment.
"""

import os
import shutil
import sys
import time

# Define essential voice files - these match what we defined in index.py
ESSENTIAL_VOICES = {
    'af_heart.pt',    # Default female voice
    'am_michael.pt',  # Male voice 1
}

def cleanup_voice_files():
    """Remove any voice files that aren't in our essential list."""
    voice_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_files")
    
    if not os.path.exists(voice_dir):
        print(f"Voice directory {voice_dir} does not exist, creating it.")
        os.makedirs(voice_dir, exist_ok=True)
        return 0
    
    bytes_removed = 0
    for filename in os.listdir(voice_dir):
        if filename.endswith('.pt') and filename not in ESSENTIAL_VOICES:
            file_path = os.path.join(voice_dir, filename)
            try:
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                bytes_removed += file_size
                print(f"Removed non-essential voice file: {filename} ({file_size / 1024 / 1024:.2f} MB)")
            except Exception as e:
                print(f"Error removing file {filename}: {e}")
    
    return bytes_removed

def cleanup_cache():
    """Clean up cache directories that might take up space."""
    cache_dirs = [
        os.path.expanduser("~/.cache/huggingface"),
        os.path.expanduser("~/.cache/torch"),
        os.path.expanduser("~/.cache/pip")
    ]
    
    bytes_removed = 0
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                dir_size = get_dir_size(cache_dir)
                shutil.rmtree(cache_dir)
                bytes_removed += dir_size
                print(f"Removed cache directory: {cache_dir} ({dir_size / 1024 / 1024:.2f} MB)")
            except Exception as e:
                print(f"Error removing cache directory {cache_dir}: {e}")
    
    return bytes_removed

def cleanup_temp_files():
    """Remove temporary files."""
    temp_dir = "/tmp"
    bytes_removed = 0
    
    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            if filename.startswith('tmp') or filename.endswith('.wav'):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        mtime = os.path.getmtime(file_path)
                        # Only remove files older than 1 hour
                        if time.time() - mtime > 3600:
                            os.remove(file_path)
                            bytes_removed += file_size
                            print(f"Removed temp file: {filename} ({file_size / 1024:.2f} KB)")
                except Exception as e:
                    print(f"Error processing temp file {filename}: {e}")
    
    return bytes_removed

def get_dir_size(path):
    """Get the size of a directory in bytes."""
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def main():
    print("=== Starting storage cleanup ===")
    
    # Clean up voice files
    voice_bytes = cleanup_voice_files()
    
    # Clean up cache
    cache_bytes = cleanup_cache()
    
    # Clean up temp files
    temp_bytes = cleanup_temp_files()
    
    # Calculate total savings
    total_mb = (voice_bytes + cache_bytes + temp_bytes) / 1024 / 1024
    print(f"\nTotal space saved: {total_mb:.2f} MB")
    
    print("=== Cleanup complete ===")

if __name__ == "__main__":
    main() 