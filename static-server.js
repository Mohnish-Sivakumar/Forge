// Simple Express server for serving static files
// Used as a fallback in case the Python server fails

const express = require('express');
const path = require('path');
const fs = require('fs');
const PORT = process.env.PORT || 5000;

console.log("==> Starting static file server");

// Create Express app
const app = express();

// Find static directory
let staticDir = null;
const possibleDirs = [
  path.join(__dirname, 'my-voice-assistant', 'build'),
  path.join(__dirname, 'backend', 'static'),
  path.join(__dirname, 'api', 'static'),
];

for (const dir of possibleDirs) {
  if (fs.existsSync(dir) && fs.existsSync(path.join(dir, 'index.html'))) {
    staticDir = dir;
    break;
  }
}

if (!staticDir) {
  console.error("==> ERROR: No static directory found with index.html");
  // Create a minimal HTML page
  const tempDir = path.join(__dirname, 'temp-static');
  fs.mkdirSync(tempDir, { recursive: true });
  fs.writeFileSync(path.join(tempDir, 'index.html'), `
    <!DOCTYPE html>
    <html>
    <head>
      <title>API Server</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
        .error { color: #ff0000; }
        .info { color: #0066cc; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>API Server Running</h1>
        <p class="info">The API server is running, but no static files were found.</p>
        <p>You can access the API endpoints directly:</p>
        <ul>
          <li><code>/api/text</code> - Text generation endpoint</li>
          <li><code>/api/voice</code> - Voice generation endpoint</li>
          <li><code>/api/debug</code> - API status information</li>
        </ul>
        <p class="error">Note: The frontend static files were not found. Please check the deployment configuration.</p>
      </div>
    </body>
    </html>
  `);
  staticDir = tempDir;
}

console.log(`==> Serving static files from: ${staticDir}`);

// Serve static files
app.use(express.static(staticDir));

// Handle API routes by returning appropriate JSON
app.use('/api', (req, res) => {
  console.log(`==> API request received: ${req.method} ${req.path}`);
  
  // Handle OPTIONS requests for CORS
  if (req.method === 'OPTIONS') {
    res.set({
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    return res.status(200).end();
  }
  
  // Basic API response for all endpoints
  res.set({
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
  });
  
  // Send a response based on the endpoint
  if (req.path === '/text' || req.path === '/voice') {
    return res.json({
      status: 'error',
      message: 'Backend server unavailable. Using static file fallback server.',
      error: 'Python application not running. Please check server logs.',
      fallback: true
    });
  } else if (req.path === '/debug') {
    return res.json({
      status: 'static_fallback',
      message: 'Static file server is running as a fallback',
      staticDir: staticDir,
      nodeVersion: process.version,
      time: new Date().toISOString()
    });
  } else {
    return res.status(404).json({
      status: 'error',
      message: `Unknown endpoint: ${req.path}`,
      note: 'Running in static file fallback mode'
    });
  }
});

// Serve index.html for all other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`==> Static server running on port ${PORT}`);
}); 