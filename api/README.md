# Python Serverless Function for Vercel

This directory contains a serverless function that runs on Vercel's infrastructure. The function is built using Python and follows Vercel's serverless model.

## How It Works

1. **Entry Point**: The `index.py` file contains a handler class that processes HTTP requests.
   
2. **HTTP Methods**: The handler supports:
   - `OPTIONS` - For CORS preflight requests
   - `GET` - For retrieving data
   - `POST` - For submitting data

3. **Endpoints**:
   - `/api/text` - Text-based response endpoint
   - `/api/voice` - Voice-based response endpoint

## Testing

You can test the API using:

1. **Browser**: Visit `/api/text` directly to see the GET response
2. **API Test Page**: Visit `/api-test` to test both GET and POST requests
3. **Curl**: Use curl commands:
   ```bash
   # Test GET
   curl -v https://your-domain.vercel.app/api/text
   
   # Test POST
   curl -v -X POST -H "Content-Type: application/json" -d '{"text":"Test message"}' https://your-domain.vercel.app/api/text
   ```

## Important Notes

- Vercel's serverless functions have a maximum execution time of 10 seconds.
- Each function invocation is isolated, meaning there's no persistent state between invocations.
- The function automatically scales based on traffic. 