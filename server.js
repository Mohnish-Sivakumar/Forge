// Simple Express server to serve static files
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 10000;
const FLASK_PORT = process.env.FLASK_PORT || 5001;

// Set proper MIME types for JavaScript and CSS files
app.use((req, res, next) => {
  if (req.url.endsWith('.js')) {
    res.setHeader('Content-Type', 'application/javascript');
  } else if (req.url.endsWith('.css')) {
    res.setHeader('Content-Type', 'text/css');
  }
  next();
});

// Logging middleware for debugging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Serve static files from the React build directory
const buildPath = path.join(__dirname, 'build');
app.use(express.static(buildPath, {
  maxAge: '1d',  // Cache static assets for 1 day
  etag: true,    // Enable ETag for caching
}));

// Create API proxy to Flask backend
app.use('/api', createProxyMiddleware({
  target: `http://localhost:${FLASK_PORT}`,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api',  // keep /api prefix when forwarding
  },
  logLevel: 'debug',
  onError: (err, req, res) => {
    console.error('Proxy error:', err);
    res.status(500).json({ error: 'Proxy error', message: err.message });
  }
}));

// For all other routes, serve the main index.html file (SPA routing)
app.get('*', (req, res) => {
  res.sendFile(path.join(buildPath, 'index.html'));
});

// Start the Flask backend
console.log('Starting Flask backend...');
const flaskProcess = spawn('python', ['-m', 'flask', 'run', '--port', FLASK_PORT], {
  env: { 
    ...process.env,
    FLASK_ENV: 'production',
    LOW_MEMORY_MODE: 'true'
  }
});

flaskProcess.stdout.on('data', (data) => {
  console.log(`Flask: ${data}`);
});

flaskProcess.stderr.on('data', (data) => {
  console.error(`Flask error: ${data}`);
});

flaskProcess.on('close', (code) => {
  console.log(`Flask process exited with code ${code}`);
});

// Start Express server
app.listen(PORT, () => {
  console.log(`Express server running on port ${PORT}`);
  console.log(`Serving static files from: ${buildPath}`);
  console.log(`API requests proxied to: http://localhost:${FLASK_PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down...');
  flaskProcess.kill();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down...');
  flaskProcess.kill();
  process.exit(0);
}); 