const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const inputHtml = path.join(__dirname, 'index.html');
const outputPdf = path.join(__dirname, 'agentic-os-control-plane-governance.pdf');

console.log('--- HIDALGO SYSTEMS LAB: PDF COMPILER ---');
console.log(`Input HTML:  ${inputHtml}`);
console.log(`Output PDF:  ${outputPdf}`);

if (!fs.existsSync(inputHtml)) {
  console.error(`Error: Input file index.html does not exist at: ${inputHtml}`);
  process.exit(1);
}

console.log('Executing Headless Google Chrome compilation pipeline...');

try {
  // Execute headless chrome print-to-pdf command
  // Note: --headless=new is the modern flag for Chrome headless execution, --disable-gpu handles sandbox environments cleanly
  const cmd = `"${chromePath}" --headless=new --disable-gpu --print-to-pdf="${outputPdf}" "file://${inputHtml}"`;
  
  console.log(`Running CLI: ${cmd}`);
  execSync(cmd, { stdio: 'inherit' });
  
  if (fs.existsSync(outputPdf)) {
    const stats = fs.statSync(outputPdf);
    console.log('\n=========================================');
    console.log('COMPILATION SUCCESSFUL!');
    console.log(`PDF File: ${outputPdf}`);
    console.log(`File Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
    console.log('=========================================');
  } else {
    throw new Error('PDF output file was not created by Chrome.');
  }
} catch (error) {
  console.error('\nCOMPILATION FAILED!');
  console.error('Error details:', error.message || error);
  process.exit(1);
}
