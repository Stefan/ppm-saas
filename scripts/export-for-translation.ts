#!/usr/bin/env tsx
/**
 * Export Batch 2 keys for translation
 * Creates a CSV file that can be sent to translators
 */

import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.join(process.cwd(), 'public', 'locales');
const OUTPUT_FILE = path.join(process.cwd(), 'BATCH2_TRANSLATION_WORKBOOK.csv');

// Read English file
const enFile = path.join(LOCALES_DIR, 'en.json');
const enData = JSON.parse(fs.readFileSync(enFile, 'utf-8'));

if (!enData.changes) {
  console.error('❌ No changes object found');
  process.exit(1);
}

// Flatten the changes object to get all keys and values
function flattenObject(obj: any, prefix = ''): Array<{key: string, value: string}> {
  const result: Array<{key: string, value: string}> = [];
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (typeof value === 'string') {
      result.push({ key: fullKey, value });
    } else if (typeof value === 'object' && value !== null) {
      result.push(...flattenObject(value, fullKey));
    }
  }
  
  return result;
}

console.log('📤 Exporting Batch 2 keys for translation...\n');

const flatKeys = flattenObject(enData.changes, 'changes');

console.log(`✅ Found ${flatKeys.length} keys to translate\n`);

// Create CSV content
const csvLines = [
  'Key,English,German (de),French (fr),Spanish (es),Polish (pl),Swiss German (gsw),Notes'
];

for (const {key, value} of flatKeys) {
  // Escape commas and quotes in values
  const escapedValue = value.replace(/"/g, '""');
  csvLines.push(`"${key}","${escapedValue}","","","","","",""`);
}

const csvContent = csvLines.join('\n');

// Write CSV file
fs.writeFileSync(OUTPUT_FILE, csvContent, 'utf-8');

console.log(`✅ Created translation workbook: ${OUTPUT_FILE}`);
console.log(`\n📊 Statistics:`);
console.log(`   - Total keys: ${flatKeys.length}`);
console.log(`   - Languages: 5 (de, fr, es, pl, gsw)`);
console.log(`   - Format: CSV`);
console.log(`\n💡 Next steps:`);
console.log(`   1. Open ${OUTPUT_FILE} in Excel or Google Sheets`);
console.log(`   2. Fill in translations for each language column`);
console.log(`   3. Use import script to integrate translations back\n`);
