#!/usr/bin/env tsx
/**
 * Import translated keys from CSV back into language files
 */

import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.join(process.cwd(), 'public', 'locales');
const INPUT_FILE = path.join(process.cwd(), 'BATCH2_TRANSLATION_WORKBOOK.csv');

if (!fs.existsSync(INPUT_FILE)) {
  console.error(`❌ Translation workbook not found: ${INPUT_FILE}`);
  process.exit(1);
}

console.log('📥 Importing translations from CSV...\n');

// Read and parse CSV
const csvContent = fs.readFileSync(INPUT_FILE, 'utf-8');
const lines = csvContent.split('\n');

// Detect delimiter (comma or semicolon)
const firstLine = lines[0];
const delimiter = firstLine.includes(';') ? ';' : ',';
console.log(`📋 Detected CSV delimiter: "${delimiter}"\n`);

const headers = lines[0].split(delimiter).map(h => h.replace(/"/g, '').trim());

// Find column indices
const keyIdx = headers.indexOf('Key');
const deIdx = headers.indexOf('German (de)');
const frIdx = headers.indexOf('French (fr)');
const esIdx = headers.indexOf('Spanish (es)');
const plIdx = headers.indexOf('Polish (pl)');
const gswIdx = headers.indexOf('Swiss German (gsw)');

if (keyIdx === -1) {
  console.error('❌ Key column not found in CSV');
  process.exit(1);
}

// Parse CSV and build translation objects
const translations: Record<string, Record<string, string>> = {
  de: {},
  fr: {},
  es: {},
  pl: {},
  gsw: {}
};

let translatedCount = { de: 0, fr: 0, es: 0, pl: 0, gsw: 0 };

for (let i = 1; i < lines.length; i++) {
  if (!lines[i].trim()) continue;
  
  // Parse CSV line with detected delimiter
  const values = lines[i].split(delimiter).map(v => v.replace(/^"|"$/g, '').replace(/""/g, '"').trim());
  
  const key = values[keyIdx];
  if (!key || !key.startsWith('changes.')) continue;
  
  // Remove 'changes.' prefix for storage
  const shortKey = key.substring(8);
  
  if (deIdx !== -1 && values[deIdx]) {
    translations.de[shortKey] = values[deIdx];
    translatedCount.de++;
  }
  if (frIdx !== -1 && values[frIdx]) {
    translations.fr[shortKey] = values[frIdx];
    translatedCount.fr++;
  }
  if (esIdx !== -1 && values[esIdx]) {
    translations.es[shortKey] = values[esIdx];
    translatedCount.es++;
  }
  if (plIdx !== -1 && values[plIdx]) {
    translations.pl[shortKey] = values[plIdx];
    translatedCount.pl++;
  }
  if (gswIdx !== -1 && values[gswIdx]) {
    translations.gsw[shortKey] = values[gswIdx];
    translatedCount.gsw++;
  }
}

console.log('📊 Translation counts:');
console.log(`   - German: ${translatedCount.de} keys`);
console.log(`   - French: ${translatedCount.fr} keys`);
console.log(`   - Spanish: ${translatedCount.es} keys`);
console.log(`   - Polish: ${translatedCount.pl} keys`);
console.log(`   - Swiss German: ${translatedCount.gsw} keys\n`);

// Function to set nested value
function setNestedValue(obj: any, path: string, value: string) {
  const parts = path.split('.');
  let current = obj;
  
  for (let i = 0; i < parts.length - 1; i++) {
    if (!current[parts[i]]) {
      current[parts[i]] = {};
    }
    current = current[parts[i]];
  }
  
  current[parts[parts.length - 1]] = value;
}

// Update each language file
for (const [lang, langTranslations] of Object.entries(translations)) {
  if (Object.keys(langTranslations).length === 0) {
    console.log(`⏭️  Skipping ${lang} (no translations found)`);
    continue;
  }
  
  const langFile = path.join(LOCALES_DIR, `${lang}.json`);
  const data = JSON.parse(fs.readFileSync(langFile, 'utf-8'));
  
  if (!data.changes) {
    console.warn(`⚠️  No changes object in ${lang}.json, skipping...`);
    continue;
  }
  
  // Apply translations
  for (const [key, value] of Object.entries(langTranslations)) {
    setNestedValue(data.changes, key, value);
  }
  
  // Write back
  fs.writeFileSync(langFile, JSON.stringify(data, null, 2) + '\n', 'utf-8');
  console.log(`✅ Updated ${lang}.json with ${Object.keys(langTranslations).length} translations`);
}

console.log('\n✨ Import complete!\n');
