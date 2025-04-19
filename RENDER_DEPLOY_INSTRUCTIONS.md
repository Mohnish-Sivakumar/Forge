# Deployment Instructions for Render

This document provides step-by-step instructions for deploying the voice assistant application to Render.

## Prerequisites

- A [Render account](https://render.com)
- The source code of the application on GitHub
- Google Gemini API key

## Setup Steps

### 1. Create a New Web Service

1. Log in to your Render dashboard
2. Click "New" and select "Web Service"
3. Connect your GitHub repository or select "Deploy from GitHub" and enter your repository information

### 2. Configure the Service

Use the following settings:

- **Name**: `voice-assistant` (or a name of your choice)
- **Region**: Choose the region closest to your users
- **Branch**: `main` (or your primary branch)
- **Runtime**: `Python`
- **Build Command**: `./render-build.sh`
- **Start Command**: `./start.sh`
- **Plan**: Free or Standard (as per your requirements)

### 3. Add Environment Variables

Click on "Advanced" and add the following environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `PYTHON_VERSION`: `3.12.9` 
- `NODE_VERSION`: `18`
- `FLASK_ENV`: `production`
- `ESSENTIAL_VOICES_ONLY`: `true`

### 4. Deploy the Service

Click "Create Web Service" to start the deployment process. The initial build may take a few minutes.

## Important Files in the Repository

- `render.yaml`: Configuration file for the service
- `render-build.sh`: Script that builds both the backend and frontend
- `start.sh`: Script that starts the service
- `api/handler.py`: WSGI adapter for the HTTP server
- `verify-env.py`: Environment verification script

## Troubleshooting

If you encounter any issues with the deployment, check the following:

1. **502 Bad Gateway Errors**: Check the logs in the Render dashboard to see if the server is starting correctly. The most common issue is that the server is not properly responding to web requests.

2. **Voice not working**: Make sure your Gemini API key is correctly set in the environment variables. Also check if the Kokoro voice files are being downloaded correctly (see logs).

3. **Build failing**: Ensure that your repository contains all the necessary files, especially `render-build.sh` and `start.sh` with executable permissions.

4. **Frontend not loading**: Check if the static files are being correctly built and served.

## Checking Deployment Status

After deployment, use the following endpoints to verify the service is working correctly:

- `/health`: Should return a 200 status with a JSON response indicating the service is healthy
- `/api/debug`: Returns detailed information about the API's status
- `/`: Should load the frontend interface

If you encounter any issues, please check the logs in the Render dashboard for more information.

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