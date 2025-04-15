#!/bin/bash

cat > vercel.json << 'EOL'
{
  "version": 2,
  "functions": {
    "api/index.py": {
      "memory": 1024,
      "maxDuration": 60
    }
  },
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/index.py" }
  ]
}
EOL

echo "Created vercel.json with minimal configuration" 