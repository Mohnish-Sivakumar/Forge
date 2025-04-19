// Simple Express server for serving static files
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

// Get the directory name
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// First, try to serve from backend/static if it exists
let staticDir = path.join(__dirname, 'backend/static');
if (!fs.existsSync(staticDir)) {
  // If not, try api/static
  staticDir = path.join(__dirname, 'api/static');
  if (!fs.existsSync(staticDir)) {
    // If that doesn't exist either, use the React build directory
    staticDir = path.join(__dirname, 'my-voice-assistant/build');
  }
}

console.log(`Using static directory: ${staticDir}`);

// Serve static files
app.use(express.static(staticDir));

// Serve index.html for all routes (SPA behavior)
app.get('*', (req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`Static server running on port ${PORT}`);
}); 