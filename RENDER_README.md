# Deployment Guide for Render

This guide provides instructions for deploying the Voice Assistant application on Render.com.

## Files Added/Modified for Render Deployment

- **render.yaml**: Simplified to a single service that combines both frontend and backend
- **render-build.sh**: Build script that handles both frontend and backend
- **start.sh**: Start script for running the application
- **app.py**: Main application file that serves both API and static files
- **verify-env.py**: Script to verify the environment during startup
- **requirements-render.txt**: Minimal requirements file with essential dependencies

## Deployment Steps

1. **Fork/Clone the Repository**:
   - Make sure you have your own copy of the repository on GitHub

2. **Create a Render Account**:
   - Sign up at [render.com](https://render.com) if you don't have an account

3. **Create a New Web Service**:
   - In the Render dashboard, click "New" and select "Web Service"
   - Connect to your GitHub repository
   - Choose the branch you want to deploy (usually `main`)

4. **Configure the Service**:
   - Name: Choose a name for your service
   - Runtime: Python
   - Build Command: `./render-build.sh`
   - Start Command: `./start.sh`

5. **Set Environment Variables**:
   - PYTHON_VERSION: 3.12.1
   - NODE_VERSION: 18
   - GEMINI_API_KEY: Your Google Gemini API key
   - ESSENTIAL_VOICES_ONLY: true

6. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy your application

## Troubleshooting

If you encounter issues:

1. **Check the Logs**:
   - In the Render dashboard, click on your service and then "Logs"
   - Look for error messages that might indicate the issue

2. **Verify Environment Variables**:
   - Make sure all required environment variables are set
   - Pay special attention to the GEMINI_API_KEY

3. **Manual Deployment**:
   - You can also deploy manually by pushing the changes to your GitHub repository
   - Render will automatically detect the changes and redeploy

## Structure

The application has been restructured to work better on Render:

- A single service handles both the frontend and backend
- Static files from the React build are served by the Flask application
- The application will work with either the `backend` or `api` directory structure
- Voice files are limited to essential ones to save space

## Testing

After deployment, you can test your application by:

1. Visiting the URL provided by Render
2. Testing the voice assistant functionality
3. Checking the health endpoint at `/health` 