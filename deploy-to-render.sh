#!/bin/bash
# Simple script to prepare for Render deployment

# Ensure we have the right files and permissions
echo "==> Preparing for Render deployment..."

# Make sure scripts are executable
chmod +x render-build.sh start.sh 

# Create requirements.txt symlink if it doesn't already exist
if [ ! -e requirements.txt ] || [ ! -L requirements.txt ]; then
  echo "==> Creating requirements symlink"
  ln -sf requirements-render.txt requirements.txt
fi

# Ensure Python version is set correctly
echo "==> Checking runtime.txt"
echo "python-3.12.9" > runtime.txt

# Update environment variables
echo "==> Updating .env file"
cat > .env << EOL
# Environment variables
SERVE_STATIC=true
PYTHON_VERSION=3.12.9
NODE_VERSION=18
EOL

# Check if we have a proper app.py
if [ ! -f app.py ]; then
  echo "==> WARNING: app.py not found in root directory"
  echo "    You may need to copy it from this repository"
fi

# Clean up any Vercel specific files
echo "==> Removing Vercel-specific files"
rm -f .vercelignore vercel.json

echo "==> Done preparing for Render deployment"
echo ""
echo "Next steps:"
echo "1. Push these changes to your GitHub repository"
echo "2. Create a new web service on Render using these settings:"
echo "   - Build Command: ./render-build.sh"
echo "   - Start Command: ./start.sh"
echo "   - Environment Variables:"
echo "     - PYTHON_VERSION=3.12.9"
echo "     - NODE_VERSION=18"
echo "     - GEMINI_API_KEY=[your API key]"
echo "     - FLASK_ENV=production"
echo ""
echo "For more details, see RENDER_DEPLOY_INSTRUCTIONS.md" 