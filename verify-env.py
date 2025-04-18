#!/usr/bin/env python
import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("Flask is not installed")

try:
    import werkzeug
    print(f"Werkzeug version: {werkzeug.__version__}")
except ImportError:
    print("Werkzeug is not installed")

try:
    import google.generativeai
    print("Google Generative AI is installed")
except ImportError:
    print("Google Generative AI is not installed")

print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith(("PYTHON", "NODE", "FLASK", "ESSENTIAL")):
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

print("All checks completed.") 