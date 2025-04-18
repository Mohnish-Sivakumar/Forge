# Render Deployment Guide

This guide will help you deploy the Voice Assistant application to Render.com.

## Prerequisites

- A Render.com account
- A Google Gemini API key

## Deployment Steps

### Using the render.yaml Blueprint (Recommended)

1. Fork or clone this repository to your GitHub account
2. Create an account on [Render](https://render.com) if you don't have one already
3. In the Render dashboard, click **New** and select **Blueprint**
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` file
6. Fill in the required environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key

That's it! Render will automatically deploy both the frontend and backend services.

### Memory Usage Considerations

To keep memory usage under the free tier limits (512MB):

1. The application is configured to use a limited set of essential voice files
2. The `ESSENTIAL_VOICES_ONLY` environment variable is set to `true` by default
3. Only the most common voice files will be downloaded automatically
4. Temporary files are cleaned up automatically

### Troubleshooting

If you encounter issues with the deployment:

1. **Build Failures**: The React build is configured to ignore ESLint warnings with the special `build:render` script
2. **Memory Issues**: The application will automatically clean up unused voice files and release memory
3. **Python Version**: The application is configured to use Python 3.12.1, which should be compatible with Render

## Testing Your Deployment

Once deployed, you can test your application by:

1. Visiting the frontend URL provided by Render (e.g., https://forge-frontend.onrender.com)
2. Testing voice functionality with different voice options
3. If voice generation fails, the app will automatically fall back to browser TTS

## Additional Configuration

If you need to modify the deployment configuration:

1. Edit the `render.yaml` file to change service names or options
2. Update the environment variables as needed
3. If you need to use more voice options, set `ESSENTIAL_VOICES_ONLY` to `false`

Note that using more voice options will increase memory usage and may exceed free tier limits. 