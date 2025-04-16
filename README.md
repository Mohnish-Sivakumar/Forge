# Interview AI - Render Deployment

A voice-based interview practice assistant built with React and Python Flask.

## Deployment Instructions for Render

This application consists of two services that need to be deployed on Render:

1. **Frontend**: A static React application
2. **Backend**: A Python Flask API 

### Option 1: Using render.yaml (Recommended)

The easiest way to deploy this application is using the `render.yaml` Blueprint:

1. Fork or clone this repository to your GitHub account
2. Create a new Render account if you don't have one
3. Go to the Render Dashboard and click on "New Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` file
6. Complete the deployment by filling in the required environment variables

### Option 2: Manual Deployment

#### Frontend Deployment

1. Go to the Render Dashboard and select "Static Site"
2. Connect your GitHub repository
3. Use the following settings:
   - **Name**: forge-frontend
   - **Build Command**: `cd my-voice-assistant && npm install && npm run build`
   - **Publish Directory**: `my-voice-assistant/build`

#### Backend Deployment  

1. Go to the Render Dashboard and select "Web Service"
2. Connect your GitHub repository
3. Use the following settings:
   - **Name**: forge-api
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements-render.txt`
   - **Start Command**: `gunicorn backend.app:app --bind 0.0.0.0:$PORT`
   - **Environment Variables**:
     - `PYTHON_VERSION`: 3.9
     - `GEMINI_API_KEY`: Your Google Gemini API key

## Environment Setup

Make sure to set the following environment variables in Render:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `NODE_VERSION`: 18 (for the frontend)
- `PYTHON_VERSION`: 3.9 (for the backend)

## Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

This will start the React frontend on port 3000 and the Flask backend on port 5001.

## API Endpoints

- `GET /api/health` - Health check endpoint
- `POST /api/text` - Text generation endpoint
- `POST /api/login` - Test login endpoint (username: test, password: password)

## Project Structure

- `/api` - Python serverless functions for the backend
- `/my-voice-assistant` - React application for the frontend