import os
import sys
import json
import traceback
from http import HTTPStatus
from api.index import handler, text_to_speech, list_available_voices

# WSGI application function that Gunicorn will use
def app(environ, start_response):
    """
    WSGI application that adapts the BaseHTTPRequestHandler to work with Gunicorn.
    This allows the existing handler class to work with Render's Gunicorn server.
    """
    # Extract request information from environ
    method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    query = environ.get('QUERY_STRING', '')
    
    # Create a handler instance
    h = handler()
    
    # Set path and method
    h.path = path
    h.command = method
    
    # Setup headers
    h.headers = {
        key[5:].replace('_', '-').lower(): value 
        for key, value in environ.items() 
        if key.startswith('HTTP_')
    }
    
    # Simulate request handling
    try:
        # Handle OPTIONS requests for CORS
        if method == 'OPTIONS':
            h._set_cors_headers()
            headers = [(k, v) for k, v in h.headers_dict.items()] if hasattr(h, 'headers_dict') else [
                ('Content-Type', 'text/plain'),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            ]
            start_response('200 OK', headers)
            return [b'']
        
        # For GET requests
        elif method == 'GET':
            # Setup response capturing
            response_body = []
            
            # Original function expects to write to wfile
            class WfileMock:
                def write(self, data):
                    response_body.append(data)
            
            h.wfile = WfileMock()
            
            # Call handler method
            h.do_GET()
            
            # Get response data
            response_data = b''.join(response_body) if response_body else b'{"status":"ok"}'
            
            # Determine content type
            content_type = 'application/json'
            if isinstance(response_data, bytes) and response_data.startswith(b'\x89PNG'):
                content_type = 'image/png'
            elif isinstance(response_data, bytes) and response_data.startswith(b'RIFF'):
                content_type = 'audio/wav'
            
            # Set headers for response
            headers = [(k, v) for k, v in h.headers_dict.items()] if hasattr(h, 'headers_dict') else [
                ('Content-Type', content_type),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            ]
            
            start_response('200 OK', headers)
            return [response_data]
        
        # For POST requests
        elif method == 'POST':
            # Read request body
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ.get('wsgi.input').read(content_length) if content_length > 0 else b''
            
            # Setup input and output streams
            class RfileMock:
                def __init__(self, data):
                    self.data = data
                    self.position = 0
                
                def read(self, size=None):
                    if size is None:
                        result = self.data[self.position:]
                        self.position = len(self.data)
                    else:
                        result = self.data[self.position:self.position + size]
                        self.position += size
                    return result
            
            class WfileMock:
                def __init__(self):
                    self.data = []
                
                def write(self, data):
                    self.data.append(data)
            
            h.rfile = RfileMock(request_body)
            h.wfile = WfileMock()
            h.headers['content-type'] = environ.get('CONTENT_TYPE', 'application/json')
            h.headers['content-length'] = str(content_length)
            
            # Call handler method
            h.do_POST()
            
            # Get response data
            response_data = b''.join(h.wfile.data) if h.wfile.data else b'{"status":"ok"}'
            
            # Determine content type
            content_type = 'application/json'
            if isinstance(response_data, bytes) and response_data.startswith(b'\x89PNG'):
                content_type = 'image/png'
            elif isinstance(response_data, bytes) and response_data.startswith(b'RIFF'):
                content_type = 'audio/wav'
            
            # Set headers for response
            headers = [(k, v) for k, v in h.headers_dict.items()] if hasattr(h, 'headers_dict') else [
                ('Content-Type', content_type),
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type, Authorization'),
                ('Access-Control-Expose-Headers', 'X-Response-Text')
            ]
            
            start_response('200 OK', headers)
            return [response_data]
        
        # Unsupported methods
        else:
            headers = [('Content-Type', 'application/json')]
            start_response('405 Method Not Allowed', headers)
            return [json.dumps({"error": "Method not allowed"}).encode('utf-8')]
    
    except Exception as e:
        # Handle any exceptions
        error_message = str(e)
        trace = traceback.format_exc()
        
        print(f"Error handling request: {error_message}")
        print(f"Traceback: {trace}")
        
        headers = [('Content-Type', 'application/json')]
        start_response('500 Internal Server Error', headers)
        return [json.dumps({
            "error": error_message,
            "traceback": trace,
            "status": "error"
        }).encode('utf-8')]

# For testing the handler directly
if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    
    httpd = make_server('localhost', 8000, app)
    print("Serving on port 8000...")
    httpd.serve_forever() 