#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

const vitePath = path.resolve(__dirname, 'node_modules', 'vite', 'bin', 'vite.js');

const vite = spawn('node', [vitePath, '--host', '0.0.0.0', '--port', '5173'], {
  cwd: __dirname,
  stdio: 'inherit'
});

vite.on('close', (code) => {
  process.exit(code);
});
