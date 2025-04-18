#!/usr/bin/env python
import sys
import os
import importlib.util

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

# Check for critical modules
modules_to_check = [
    "flask", 
    "werkzeug", 
    "google.generativeai", 
    "gunicorn", 
    "numpy", 
    "requests"
]

for module_name in modules_to_check:
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {module_name}: {version}")
        else:
            print(f"❌ {module_name}: Not found")
    except ImportError:
        print(f"❌ {module_name}: Import error")
    except Exception as e:
        print(f"❌ {module_name}: Error: {e}")

# Check for TTS modules (optional)
tts_modules = ["kokoro", "torch", "soundfile"]
print("\nChecking TTS modules:")
for module_name in tts_modules:
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'available')
            print(f"✅ {module_name}: {version}")
        else:
            print(f"⚠️ {module_name}: Not found (voice features will be limited)")
    except ImportError:
        print(f"⚠️ {module_name}: Import error (voice features will be limited)")
    except Exception as e:
        print(f"⚠️ {module_name}: Error: {e}")

print("\nEnvironment variables:")
for key, value in os.environ.items():
    if key.startswith(("PYTHON", "NODE", "FLASK", "ESSENTIAL", "GEMINI", "GOOGLE")):
        print(f"  {key}={value}")

print("\nDirectory structure:")
for dir_name in ["api", "backend", "my-voice-assistant"]:
    if os.path.exists(dir_name):
        print(f"  {dir_name}/: exists")
        # List the first few files in this directory
        files = os.listdir(dir_name)[:5]
        for file in files:
            print(f"    - {file}")
        if len(os.listdir(dir_name)) > 5:
            print(f"    - ... ({len(os.listdir(dir_name)) - 5} more)")
    else:
        print(f"  {dir_name}/: MISSING")

# Check specific files
key_files = ["app.py", "backend/app.py", "api/index.py", "requirements.txt", "requirements-render.txt"]
print("\nKey files:")
for file_path in key_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"  {file_path}: ✅ ({size} bytes)")
    else:
        print(f"  {file_path}: ❌ Missing")

print("\nAll checks completed.") 