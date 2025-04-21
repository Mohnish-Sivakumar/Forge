const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

// Determine if we're on Windows to handle commands differently
const isWindows = os.platform() === 'win32';

// Create a function to start a process
function startProcess(name, command, args, cwd) {
  console.log(`Starting ${name}...`);
  
  const proc = spawn(command, args, {
    cwd,
    shell: true,
    stdio: 'pipe',
    env: { 
      ...process.env,
      FLASK_APP: 'backend/app.py',
      FLASK_ENV: 'development',
      PYTHONUNBUFFERED: '1'
    }
  });
  
  proc.stdout.on('data', (data) => {
    console.log(`[${name}] ${data.toString().trim()}`);
  });
  
  proc.stderr.on('data', (data) => {
    console.error(`[${name}] ${data.toString().trim()}`);
  });
  
  proc.on('close', (code) => {
    console.log(`${name} process exited with code ${code}`);
  });
  
  return proc;
}

// Start Flask backend
const backendProc = startProcess(
  'Backend',
  isWindows ? 'python' : 'python3',
  ['-m', 'flask', 'run', '--port=5001'],
  process.cwd()
);

// Start React frontend
const frontendProc = startProcess(
  'Frontend',
  isWindows ? 'npm.cmd' : 'npm',
  ['start'],
  path.join(process.cwd(), 'my-voice-assistant')
);

// Handle process termination
process.on('SIGINT', () => {
  console.log('Stopping all processes...');
  backendProc.kill();
  frontendProc.kill();
  process.exit(0);
});

console.log('\nDevelopment environment is starting...');
console.log('- Backend will be available at: http://localhost:5001');
console.log('- Frontend will be available at: http://localhost:3000');
console.log('- API requests from frontend will be proxied to backend\n');
console.log('Press Ctrl+C to stop all processes\n'); 