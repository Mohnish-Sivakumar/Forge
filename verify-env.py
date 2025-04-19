#!/usr/bin/env python3
import sys
import os
import importlib.util
import platform

# Print basic environment info
print("==> Environment verification script")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Working directory: {os.getcwd()}")

# Check for essential environment variables
print("\n==> Checking environment variables:")
env_vars = {
    "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY", None),
    "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", None),
    "FLASK_ENV": os.environ.get("FLASK_ENV", None),
    "PORT": os.environ.get("PORT", None),
    "ESSENTIAL_VOICES_ONLY": os.environ.get("ESSENTIAL_VOICES_ONLY", None),
    "SERVE_STATIC": os.environ.get("SERVE_STATIC", None)
}

for var, value in env_vars.items():
    status = "✓ SET" if value else "✗ NOT SET"
    value_display = "<redacted>" if value and var.endswith("_KEY") else value
    print(f"  {var}: {status} {value_display if value and not var.endswith('_KEY') else ''}")

# Check for important directories
print("\n==> Checking directories:")
dirs_to_check = [
    "api",
    "backend",
    "my-voice-assistant",
    "api/static",
    "backend/static",
    "my-voice-assistant/build"
]

for dir_name in dirs_to_check:
    status = "✓ EXISTS" if os.path.exists(dir_name) else "✗ NOT FOUND"
    print(f"  {dir_name}: {status}")

# Check for important files
print("\n==> Checking files:")
files_to_check = [
    "api/index.py",
    "api/handler.py",
    "backend/app.py",
    "app.py",
    "requirements.txt",
    "requirements-render.txt",
    "start.sh",
    "my-voice-assistant/build/index.html"
]

for file_name in files_to_check:
    status = "✓ EXISTS" if os.path.exists(file_name) else "✗ NOT FOUND"
    print(f"  {file_name}: {status}")

# Try to import key modules
print("\n==> Checking key modules:")
modules_to_check = [
    "flask",
    "json",
    "google.generativeai",
    "kokoro"
]

for module_name in modules_to_check:
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            importlib.import_module(module_name)
            if module_name == "flask":
                import flask
                print(f"  {module_name}: ✓ IMPORTED (version: {flask.__version__})")
            elif module_name == "google.generativeai":
                import google.generativeai
                print(f"  {module_name}: ✓ IMPORTED")
            elif module_name == "kokoro":
                import kokoro
                print(f"  {module_name}: ✓ IMPORTED")
            else:
                print(f"  {module_name}: ✓ IMPORTED")
        else:
            print(f"  {module_name}: ✗ NOT FOUND")
    except ImportError as e:
        print(f"  {module_name}: ✗ IMPORT ERROR ({str(e)})")

# Try to verify Kokoro TTS functionality without actually running it
print("\n==> Checking Kokoro TTS configuration:")
try:
    # Just check if Kokoro can be imported and initialized
    if importlib.util.find_spec("kokoro") is not None:
        import kokoro
        # Don't actually create a pipeline as it might download models
        print(f"  Kokoro module: ✓ AVAILABLE")
        
        # Check if voice files directory exists
        voice_dirs = ["api/voice_files", "backend/voice_files", "voice_files"]
        voice_dir_exists = any(os.path.exists(d) for d in voice_dirs)
        
        if voice_dir_exists:
            print(f"  Voice files directory: ✓ EXISTS")
        else:
            print(f"  Voice files directory: ✗ NOT FOUND (voices will be downloaded on first use)")
    else:
        print(f"  Kokoro module: ✗ NOT AVAILABLE")
except Exception as e:
    print(f"  Kokoro configuration check error: {str(e)}")

print("\n==> Environment verification complete") 