#!/usr/bin/env node
/**
 * ============================================================
 * sync-renderer — one renderer, copied rather than maintained twice
 * F-Keys | www.f-keys.com
 * ------------------------------------------------------------
 * WHY THIS EXISTS
 *
 * keyj/app.html and keyj/desktop/src/index.html were two hand-written
 * implementations of the same product. Three shipped defects came directly
 * out of that: Vibrato crashed one build and not the other, every tone
 * button was dead on the desktop because applyPreset wrote to an object
 * that build does not have, and neither was noticed because fixing one file
 * never touched the other.
 *
 * So src/index.html is a build artifact now. Edit keyj/app.html and run
 * this. The window chrome and the global-capture switch, which were the
 * only genuinely desktop-only parts, are built at runtime by the v1.8
 * block when the Electron bridge is present.
 *
 * Run:  node sync-renderer.js          write src/index.html
 *       node sync-renderer.js --check  fail if it is out of date (CI)
 * ============================================================
 */

const fs = require('fs');
const path = require('path');

const SOURCE = path.join(__dirname, '..', 'app.html');
const TARGET = path.join(__dirname, 'src', 'index.html');

const HEADER = [
  '<!--',
  '  GENERATED FILE - DO NOT EDIT.',
  '',
  '  This is keyj/app.html, copied by keyj/desktop/sync-renderer.js.',
  '  Edit app.html and run `node sync-renderer.js`. Editing this file',
  '  directly recreates the two-codebase problem it exists to remove.',
  '-->',
  ''
].join('\n');

function build() {
  const src = fs.readFileSync(SOURCE, 'utf8');
  // The banner goes after the doctype so the document still parses as HTML5.
  const i = src.indexOf('\n', src.indexOf('<!DOCTYPE'));
  return src.slice(0, i + 1) + HEADER + src.slice(i + 1);
}

function main() {
  const wanted = build();
  const check = process.argv.indexOf('--check') !== -1;
  const current = fs.existsSync(TARGET) ? fs.readFileSync(TARGET, 'utf8') : null;

  if (current === wanted) {
    console.log('  renderer is in sync');
    return 0;
  }
  if (check) {
    console.error('  src/index.html is out of date with app.html.');
    console.error('  Run: node keyj/desktop/sync-renderer.js');
    return 1;
  }
  fs.writeFileSync(TARGET, wanted);
  const kb = Math.round(wanted.length / 1024);
  console.log('  src/index.html written from app.html (' + kb + ' KB)');
  return 0;
}

process.exit(main());
