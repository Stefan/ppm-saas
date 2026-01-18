#!/usr/bin/env tsx
/**
 * Script to integrate Batch 2 translations into all language files
 * This adds the English changes object to all languages as a starting point
 * Translations should be reviewed and updated by native speakers
 */

import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.join(process.cwd(), 'public', 'locales');

// Read the English file to get the changes object
const enFile = path.join(LOCALES_DIR, 'en.json');
const enData = JSON.parse(fs.readFileSync(enFile, 'utf-8'));

if (!enData.changes) {
  console.error('❌ No changes object found in en.json');
  process.exit(1);
}

const changesObject = enData.changes;

// Languages to update (excluding English which is already done)
const languages = ['de', 'fr', 'es', 'pl', 'gsw'];

console.log('🚀 Integrating Batch 2 translations...\n');
console.log(`📦 Changes object contains ${JSON.stringify(changesObject).length} characters\n`);

for (const lang of languages) {
  const langFile = path.join(LOCALES_DIR, `${lang}.json`);
  
  console.log(`📝 Processing ${lang}.json...`);
  
  try {
    // Read existing file
    const data = JSON.parse(fs.readFileSync(langFile, 'utf-8'));
    
    // Check if changes already exists
    if (data.changes) {
      console.log(`   ⚠️  Changes object already exists, skipping...`);
      continue;
    }
    
    // Add changes object (using English as template)
    data.changes = changesObject;
    
    // Write back
    fs.writeFileSync(langFile, JSON.stringify(data, null, 2) + '\n', 'utf-8');
    console.log(`   ✅ Added changes object to ${lang}.json`);
    
  } catch (error) {
    console.error(`   ❌ Error processing ${lang}.json:`, error);
  }
}

console.log('\n✨ Integration complete!');
console.log('\n⚠️  IMPORTANT: The changes object currently contains English text.');
console.log('   Please review and translate to native language for each file.\n');
