#!/bin/bash
# Fix script for Render deployment issues

echo "==> Running comprehensive fix script for Render deployment"

# Make all scripts executable
echo "==> Making scripts executable"
chmod +x render-build.sh start.sh deploy-to-render.sh

# Fix the environment variables and make sure GOOGLE_API_KEY is properly set
echo "==> Adding environment variables to .env file"
cat > .env << EOL
# Environment variables
SERVE_STATIC=true
PYTHON_VERSION=3.12.9
NODE_VERSION=18
EOL

# Make sure runtime.txt has the correct Python version
echo "==> Setting Python version in runtime.txt"
echo "python-3.12.9" > runtime.txt

# Make sure package.json includes the static server
echo "==> Ensuring package.json has required dependencies"
if ! grep -q "start:static" package.json; then
  npm pkg set scripts.start:static="node static-server.js"
  npm pkg set dependencies.express="^4.18.2"
  npm install
fi

# Update my-voice-assistant's package.json
echo "==> Fixing React build settings"
cd my-voice-assistant
npm pkg set homepage="."
npm pkg set scripts.build="CI=false INLINE_RUNTIME_CHUNK=false react-scripts build"
npm pkg set scripts.build:render="CI=false INLINE_RUNTIME_CHUNK=false react-scripts build"
npm pkg set eslintConfig.rules.no-unused-vars="off"
cd ..

# Clear old build directories
echo "==> Cleaning up old build artifacts"
rm -rf my-voice-assistant/build
rm -rf backend/static api/static

# Try to build the frontend to test
echo "==> Testing React build"
cd my-voice-assistant
PUBLIC_URL="/" npm run build
cd ..

# Copy the build to both potential static locations
echo "==> Setting up static files"
mkdir -p backend/static
cp -r my-voice-assistant/build/* backend/static/
if [ -d "my-voice-assistant/build/static" ]; then
  mkdir -p backend/static/static
  cp -r my-voice-assistant/build/static/* backend/static/static/
fi

mkdir -p api/static
cp -r my-voice-assistant/build/* api/static/
if [ -d "my-voice-assistant/build/static" ]; then
  mkdir -p api/static/static
  cp -r my-voice-assistant/build/static/* api/static/static/
fi

echo "==> All fixes applied!"
echo ""
echo "Next steps:"
echo "1. Push these changes to your GitHub repository"
echo "2. In Render, go to your service's Environment settings"
echo "3. Make sure GEMINI_API_KEY is set properly"
echo "4. Add GOOGLE_API_KEY with the same value as GEMINI_API_KEY (for backwards compatibility)"
echo "5. Redeploy your service"
echo ""
echo "If you still have issues, try the fallback static server by adding:"
echo "   USE_STATIC_SERVER=true"
echo "" 