#!/usr/bin/env tsx
/**
 * Check translation progress for Batch 2
 * Identifies which keys are still in English (untranslated)
 */

import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.join(process.cwd(), 'public', 'locales');

// Read English file as reference
const enFile = path.join(LOCALES_DIR, 'en.json');
const enData = JSON.parse(fs.readFileSync(enFile, 'utf-8'));

if (!enData.changes) {
  console.error('❌ No changes object found in en.json');
  process.exit(1);
}

// Flatten object to get all key-value pairs
function flattenObject(obj: any, prefix = ''): Record<string, string> {
  const result: Record<string, string> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (typeof value === 'string') {
      result[fullKey] = value;
    } else if (typeof value === 'object' && value !== null) {
      Object.assign(result, flattenObject(value, fullKey));
    }
  }
  
  return result;
}

const enKeys = flattenObject(enData.changes);
const totalKeys = Object.keys(enKeys).length;

console.log('🔍 Checking Batch 2 translation progress...\n');
console.log(`📊 Total keys to translate: ${totalKeys}\n`);

const languages = [
  { code: 'de', name: 'German' },
  { code: 'fr', name: 'French' },
  { code: 'es', name: 'Spanish' },
  { code: 'pl', name: 'Polish' },
  { code: 'gsw', name: 'Swiss German' }
];

const results: Array<{
  lang: string;
  translated: number;
  untranslated: number;
  percentage: number;
}> = [];

for (const { code, name } of languages) {
  const langFile = path.join(LOCALES_DIR, `${code}.json`);
  
  if (!fs.existsSync(langFile)) {
    console.log(`⚠️  ${name} (${code}): File not found`);
    continue;
  }
  
  const langData = JSON.parse(fs.readFileSync(langFile, 'utf-8'));
  
  if (!langData.changes) {
    console.log(`⚠️  ${name} (${code}): No changes object`);
    continue;
  }
  
  const langKeys = flattenObject(langData.changes);
  
  // Count how many keys are different from English (translated)
  let translated = 0;
  let untranslated = 0;
  
  for (const [key, enValue] of Object.entries(enKeys)) {
    const langValue = langKeys[key];
    
    if (langValue && langValue !== enValue) {
      translated++;
    } else {
      untranslated++;
    }
  }
  
  const percentage = Math.round((translated / totalKeys) * 100);
  
  results.push({
    lang: `${name} (${code})`,
    translated,
    untranslated,
    percentage
  });
  
  const status = percentage === 0 ? '⏳' : percentage === 100 ? '✅' : '🔄';
  const bar = '█'.repeat(Math.floor(percentage / 5)) + '░'.repeat(20 - Math.floor(percentage / 5));
  
  console.log(`${status} ${name} (${code})`);
  console.log(`   Progress: [${bar}] ${percentage}%`);
  console.log(`   Translated: ${translated}/${totalKeys} keys`);
  console.log(`   Remaining: ${untranslated} keys\n`);
}

// Summary
console.log('📈 Summary\n');
console.log('┌─────────────────────┬────────────┬──────────────┬────────────┐');
console.log('│ Language            │ Translated │ Untranslated │ Progress   │');
console.log('├─────────────────────┼────────────┼──────────────┼────────────┤');

for (const { lang, translated, untranslated, percentage } of results) {
  const langPadded = lang.padEnd(19);
  const translatedStr = translated.toString().padStart(10);
  const untranslatedStr = untranslated.toString().padStart(12);
  const percentageStr = `${percentage}%`.padStart(10);
  
  console.log(`│ ${langPadded} │ ${translatedStr} │ ${untranslatedStr} │ ${percentageStr} │`);
}

console.log('└─────────────────────┴────────────┴──────────────┴────────────┘\n');

// Calculate overall progress
const totalTranslated = results.reduce((sum, r) => sum + r.translated, 0);
const totalPossible = totalKeys * results.length;
const overallPercentage = Math.round((totalTranslated / totalPossible) * 100);

console.log(`🎯 Overall Batch 2 Progress: ${overallPercentage}% (${totalTranslated}/${totalPossible} strings)\n`);

if (overallPercentage === 100) {
  console.log('🎉 Batch 2 translations complete! Ready to update components.\n');
} else {
  console.log(`💡 Next steps:`);
  console.log(`   1. Open BATCH2_TRANSLATION_WORKBOOK.csv`);
  console.log(`   2. Fill in translations for languages with 0% progress`);
  console.log(`   3. Run: npx tsx scripts/import-translations.ts`);
  console.log(`   4. Run this script again to check progress\n`);
}
