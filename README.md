# Interview AI

A voice-based interview practice assistant built with React and Python.

## Deployment Instructions

### Vercel Deployment Settings

When deploying to Vercel, follow these steps to avoid URL inconsistency issues:

1. **Disable automatic system environment variables**:
   - Go to your project settings in Vercel
   - Navigate to the "Environment Variables" section
   - Uncheck "Automatically expose System Environment Variables"
   
2. **Set a custom VERCEL_URL variable**:
   - In the same Environment Variables section, add a new variable:
   - Name: `VERCEL_URL`
   - Value: Your actual deployment URL (e.g., `forge-seven-theta.vercel.app`)
   - Select all environments (Production, Preview, Development)

3. **Set the USE_CUSTOM_URLS flag**:
   - Add another environment variable:
   - Name: `USE_CUSTOM_URLS`
   - Value: `true`
   - Select all environments

This configuration prevents issues with different URLs being generated for the same deployment, which can cause CORS and API request problems.

## Local Development

Run the application locally:

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

## Project Structure

- `/api` - Python serverless functions for the backend
- `/my-voice-assistant` - React application for the frontend