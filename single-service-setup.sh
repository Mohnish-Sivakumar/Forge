#!/bin/bash

# This script sets up your project for a single-service deployment on Render
# This approach combines both the frontend and backend into a single service
# It's useful when you want to deploy everything as one unit on Render's free tier

# Create simplified requirements.txt (combines with requirements-render.txt)
cat > requirements.txt << EOL
flask==2.2.3
flask-cors==3.0.10
google-generativeai==0.3.1
gunicorn==20.1.0
EOL

echo "✅ Created requirements.txt"

# Update package.json to run the combined service
cat > package.json << EOL
{
  "name": "forge",
  "private": true,
  "scripts": {
    "build": "cd my-voice-assistant && npm install && npm run build",
    "start": "gunicorn backend.app:app --bind 0.0.0.0:\$PORT"
  },
  "engines": {
    "node": "18.x",
    "npm": "9.x"
  }
}
EOL

echo "✅ Updated package.json"

# Create run.sh script for Render
cat > run.sh << EOL
#!/bin/bash

# Export environment variables
export SERVE_STATIC=true
export PYTHON_VERSION=3.12.9

# Start the app
gunicorn backend.app:app --bind 0.0.0.0:\$PORT
EOL

chmod +x run.sh
echo "✅ Created run.sh"

# Create or update the .env file
cat > .env << EOL
# Environment variables
SERVE_STATIC=true
PYTHON_VERSION=3.12.9
NODE_VERSION=18
EOL

echo "✅ Created .env file"

echo "🚀 Setup complete!"
echo ""
echo "To deploy to Render:"
echo "1. Push this project to GitHub"
echo "2. Create a new Web Service on Render"
echo "3. Use these settings:"
echo "   - Build Command: cd my-voice-assistant && npm install && npm run build"
echo "   - Start Command: ./run.sh"
echo "   - Environment Variables:"
echo "     - SERVE_STATIC: true"
echo "     - GEMINI_API_KEY: [your API key]"
echo "     - PYTHON_VERSION: 3.12.9"
echo "     - NODE_VERSION: 18"
echo ""
echo "This will deploy a single service containing both frontend and backend!" 