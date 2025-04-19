import os
import sys
import json
import traceback
from io import BytesIO
from urllib.parse import parse_qs
from api.index import test, text_to_speech, list_available_voices, generate_response

# WSGI application function that Gunicorn will use
def app(environ, start_response):
    """
    WSGI application that directly calls the functions in api/index.py
    instead of trying to instantiate the BaseHTTPRequestHandler.
    """
    # Extract request information from environ
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    query_string = environ.get('QUERY_STRING', '')
    
    # Parse the query string
    query = parse_qs(query_string)
    
    # Set up CORS headers for all responses
    cors_headers = [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
        ('Access-Control-Expose-Headers', 'X-Response-Text')
    ]
    
    try:
        # Handle OPTIONS requests (CORS preflight)
        if method == 'OPTIONS':
            start_response('200 OK', [
                ('Content-Type', 'text/plain'),
                *cors_headers
            ])
            return [b'']
        
        # Handle GET requests
        elif method == 'GET':
            # Create an event dictionary similar to what Vercel would provide
            event = {
                'path': path,
                'httpMethod': 'GET',
                'headers': {k.lower(): v for k, v in environ.items() if k.startswith('HTTP_')},
                'queryStringParameters': {k: v[0] for k, v in query.items()}
            }
            
            # Call the test function that handles routing
            response = test(event, {})
            
            # Extract status code and headers from the response
            status_code = response.get('statusCode', 200)
            headers = response.get('headers', {'Content-Type': 'application/json'})
            
            # Convert headers to the format expected by start_response
            header_list = [(k, v) for k, v in headers.items()]
            header_list.extend(cors_headers)
            
            # Start the response
            start_response(f'{status_code} {get_status_text(status_code)}', header_list)
            
            # Return the response body
            return [response.get('body', '{}').encode('utf-8')]
        
        # Handle POST requests
        elif method == 'POST':
            # Read the request body
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ.get('wsgi.input').read(content_length) if content_length > 0 else b'{}'
            
            try:
                # Parse JSON body
                body = json.loads(request_body)
            except:
                body = {}
            
            # Create an event dictionary similar to what Vercel would provide
            event = {
                'path': path,
                'httpMethod': 'POST',
                'headers': {k.lower(): v for k, v in environ.items() if k.startswith('HTTP_')},
                'queryStringParameters': {k: v[0] for k, v in query.items()},
                'body': json.dumps(body)
            }
            
            # Call the test function that handles routing
            response = test(event, {})
            
            # Extract status code and headers from the response
            status_code = response.get('statusCode', 200)
            headers = response.get('headers', {'Content-Type': 'application/json'})
            
            # Convert headers to the format expected by start_response
            header_list = [(k, v) for k, v in headers.items()]
            header_list.extend(cors_headers)
            
            # Start the response
            start_response(f'{status_code} {get_status_text(status_code)}', header_list)
            
            # Return the response body
            return [response.get('body', '{}').encode('utf-8')]
        
        # Unsupported methods
        else:
            error_response = generate_response(405, {"error": "Method not allowed"})
            headers = [(k, v) for k, v in error_response.get('headers', {}).items()]
            headers.extend(cors_headers)
            
            start_response('405 Method Not Allowed', headers)
            return [error_response.get('body', '{}').encode('utf-8')]
    
    except Exception as e:
        # Handle any exceptions
        error_message = str(e)
        trace = traceback.format_exc()
        
        print(f"Error handling request: {error_message}")
        print(f"Traceback: {trace}")
        
        # Generate error response
        headers = [
            ('Content-Type', 'application/json'),
            *cors_headers
        ]
        start_response('500 Internal Server Error', headers)
        return [json.dumps({
            "error": error_message,
            "traceback": trace,
            "status": "error"
        }).encode('utf-8')]

def get_status_text(status_code):
    """Convert HTTP status code to text representation."""
    status_texts = {
        200: 'OK',
        201: 'Created',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        405: 'Method Not Allowed',
        500: 'Internal Server Error'
    }
    return status_texts.get(status_code, 'Unknown')

# For testing the handler directly
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    
    httpd = make_server('localhost', 8000, app)
    print("Serving on port 8000...")
    httpd.serve_forever() 