# Render Deployment Instructions

## Quick Deployment

To deploy this application to Render:

1. Fork this repository to your own GitHub account
2. Log in to [Render](https://render.com)
3. Click "New" and select "Web Service"
4. Connect your GitHub account and select this repository
5. Use the following settings:
   - **Name**: forge-app (or choose your own)
   - **Environment**: Python
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `./start.sh`
6. Add the following environment variables:
   - `PYTHON_VERSION`: 3.12.9
   - `NODE_VERSION`: 18
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `FLASK_ENV`: production
   - `ESSENTIAL_VOICES_ONLY`: true
7. Click "Create Web Service"

## Troubleshooting

If deployment fails:

1. **Check the Logs**: In the Render dashboard, go to your service and click on "Logs"
2. **Verify API Key**: Make sure your Gemini API key is correct
3. **Check Python Version**: Make sure Render is using Python 3.12.9 as specified
4. **Memory Issues**: If deployment fails due to memory issues during npm install:
   - Try redeploying, sometimes it works on the second try
   - Or modify the `render-build.sh` script to use `npm install --no-optional`

## Technology Stack

- **Backend**: Python Flask API with Gemini AI integration
- **TTS**: Kokoro for text-to-speech (when available)
- **Frontend**: React application

## Manual Deployment

If you need to deploy manually:

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-directory>

# Make scripts executable
chmod +x render-build.sh start.sh

# Install Python dependencies
pip install -r requirements-render.txt

# Build the frontend
cd my-voice-assistant
npm install
npm run build
cd ..

# Start the application
./start.sh
```

## Testing

After deployment, your application will be available at the URL provided by Render.
Test the following endpoints:

- `/` - Frontend application
- `/api/debug` - API status and configuration
- `/api/text` - Text generation endpoint (POST)
- `/api/voice` - Voice generation endpoint (POST) 