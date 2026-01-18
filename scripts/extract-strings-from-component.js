#!/usr/bin/env node

/**
 * Extract translatable strings from a React component
 * Usage: node scripts/extract-strings-from-component.js <file-path>
 */

const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage: node extract-strings-from-component.js <file-path>');
  process.exit(1);
}

const content = fs.readFileSync(filePath, 'utf-8');

// Patterns to match translatable strings
const patterns = [
  // JSX text content: >Text<
  />([\w\s,.'!?-]+)</g,
  // String attributes: title="Text", placeholder="Text", aria-label="Text"
  /(title|placeholder|aria-label|alt)=["']([^"']+)["']/g,
  // Button/label text
  /<(button|label)[^>]*>([^<]+)</gi,
  // Heading text
  /<h[1-6][^>]*>([^<]+)</gi,
  // Paragraph text
  /<p[^>]*>([^<]+)</gi,
];

const strings = new Set();

// Extract strings
patterns.forEach(pattern => {
  let match;
  while ((match = pattern.exec(content)) !== null) {
    const text = match[match.length - 1].trim();
    // Filter out: empty, single chars, numbers, code, variables
    if (text.length > 2 && 
        /[A-Z]/.test(text) && 
        !/^[0-9]+$/.test(text) &&
        !text.includes('{') &&
        !text.includes('className') &&
        !text.includes('const ')) {
      strings.add(text);
    }
  }
});

// Output results
console.log(`\n📝 Found ${strings.size} translatable strings in ${path.basename(filePath)}:\n`);
Array.from(strings).sort().forEach((str, i) => {
  console.log(`${i + 1}. "${str}"`);
});

console.log(`\n✅ Total: ${strings.size} strings\n`);
