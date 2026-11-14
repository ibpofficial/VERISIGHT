const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('--- Compiling Frontend with Vite ---');
execSync('npm --prefix frontend run build', { stdio: 'inherit' });

console.log('--- Mirroring Build Output to Root dist/ ---');
const src = path.join(__dirname, '..', 'frontend', 'dist');
const dest = path.join(__dirname, '..', 'dist');

if (fs.existsSync(src)) {
  fs.cpSync(src, dest, { recursive: true });
  console.log('✓ Successfully synced build output to ./dist');
} else {
  console.error('Error: frontend/dist not found!');
  process.exit(1);
}
