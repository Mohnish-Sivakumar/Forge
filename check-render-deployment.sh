#!/bin/bash
# Script to check for common Render deployment issues

echo "==> Checking for common Render deployment issues"

# Check for required files
echo "==> Checking for required files..."
REQUIRED_FILES=(
  "api/index.py"
  "api/handler.py"
  "start.sh"
  "render-build.sh"
  "verify-env.py"
  "render.yaml"
  "requirements-render.txt"
)

SUCCESS=true
for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✓ $file exists"
  else
    echo "  ✗ $file is missing"
    SUCCESS=false
  fi
done

# Check file permissions
echo "==> Checking file permissions..."
EXECUTABLE_FILES=(
  "start.sh"
  "render-build.sh"
  "check-render-deployment.sh"
)

for file in "${EXECUTABLE_FILES[@]}"; do
  if [ -f "$file" ]; then
    if [ -x "$file" ]; then
      echo "  ✓ $file is executable"
    else
      echo "  ✗ $file is not executable (run 'chmod +x $file')"
      chmod +x "$file"
      echo "    Fixed permissions for $file"
    fi
  fi
done

# Check Python version
echo "==> Checking Python version..."
PYTHON_VERSION=$(python --version)
echo "  Current Python version: $PYTHON_VERSION"
if [[ $PYTHON_VERSION == *"3."* ]]; then
  echo "  ✓ Using Python 3"
else
  echo "  ✗ Not using Python 3, this might cause issues"
  SUCCESS=false
fi

# Check requirements.txt
echo "==> Checking requirements-render.txt..."
if [ -f "requirements-render.txt" ]; then
  echo "  ✓ requirements-render.txt exists"
  # Check for required packages
  REQUIRED_PACKAGES=("flask" "google-generativeai" "kokoro" "gunicorn")
  for package in "${REQUIRED_PACKAGES[@]}"; do
    if grep -q "$package" requirements-render.txt; then
      echo "  ✓ $package found in requirements-render.txt"
    else
      echo "  ✗ $package not found in requirements-render.txt"
      SUCCESS=false
    fi
  done
else
  echo "  ✗ requirements-render.txt is missing"
  SUCCESS=false
fi

# Validate render.yaml
echo "==> Validating render.yaml..."
if [ -f "render.yaml" ]; then
  echo "  ✓ render.yaml exists"
  if grep -q "buildCommand: ./render-build.sh" render.yaml && grep -q "startCommand: ./start.sh" render.yaml; then
    echo "  ✓ render.yaml has correct build and start commands"
  else
    echo "  ✗ render.yaml is missing build or start commands"
    SUCCESS=false
  fi
else
  echo "  ✗ render.yaml is missing"
  SUCCESS=false
fi

# Check for Flask app
echo "==> Checking for valid WSGI app..."
if [ -f "api/handler.py" ]; then
  echo "  ✓ api/handler.py exists"
  if grep -q "def app(" api/handler.py || grep -q "app = " api/handler.py; then
    echo "  ✓ api/handler.py contains a WSGI app"
  else
    echo "  ✗ api/handler.py does not appear to define a WSGI app"
    SUCCESS=false
  fi
else
  echo "  ✗ api/handler.py is missing"
  SUCCESS=false
fi

# Final summary
echo ""
if [ "$SUCCESS" = true ]; then
  echo "==> All checks passed! Your application should be ready for Render deployment."
  echo "    Follow the instructions in RENDER_DEPLOY_INSTRUCTIONS.md to deploy your app."
else
  echo "==> Some issues were found that might cause problems with Render deployment."
  echo "    Please fix the issues marked with ✗ before deploying."
fi

echo ""
echo "To deploy to Render, run:"
echo "  git add ."
echo "  git commit -m 'Prepare for Render deployment'"
echo "  git push origin main"
echo "" 