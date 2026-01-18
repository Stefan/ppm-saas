#!/usr/bin/env node

/**
 * i18n Verification Script
 * Verifies all translation files have consistent keys
 */

const fs = require('fs');
const path = require('path');

const LOCALES_DIR = path.join(__dirname, 'public', 'locales');
const LANGUAGES = ['en', 'de', 'fr', 'es', 'pl', 'gsw'];

console.log('🌍 i18n Verification Script\n');
console.log('=' .repeat(50));

// Load all translation files
const translations = {};
let hasErrors = false;

LANGUAGES.forEach(lang => {
  const filePath = path.join(LOCALES_DIR, `${lang}.json`);
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    translations[lang] = JSON.parse(content);
    console.log(`✅ Loaded ${lang}.json`);
  } catch (error) {
    console.error(`❌ Error loading ${lang}.json:`, error.message);
    hasErrors = true;
  }
});

console.log('\n' + '='.repeat(50));

if (hasErrors) {
  console.error('\n❌ Some translation files failed to load');
  process.exit(1);
}

// Get all keys from English (base language)
function getAllKeys(obj, prefix = '') {
  let keys = [];
  for (const key in obj) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
      keys = keys.concat(getAllKeys(obj[key], fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

const baseKeys = getAllKeys(translations['en']);
console.log(`\n📊 Base language (English) has ${baseKeys.length} keys\n`);

// Check each language for missing or extra keys
let allConsistent = true;

LANGUAGES.forEach(lang => {
  if (lang === 'en') return; // Skip base language
  
  const langKeys = getAllKeys(translations[lang]);
  const missing = baseKeys.filter(key => !langKeys.includes(key));
  const extra = langKeys.filter(key => !baseKeys.includes(key));
  
  if (missing.length === 0 && extra.length === 0) {
    console.log(`✅ ${lang.toUpperCase()}: All keys match (${langKeys.length} keys)`);
  } else {
    allConsistent = false;
    console.log(`❌ ${lang.toUpperCase()}: Key mismatch`);
    if (missing.length > 0) {
      console.log(`   Missing keys (${missing.length}):`);
      missing.slice(0, 5).forEach(key => console.log(`     - ${key}`));
      if (missing.length > 5) {
        console.log(`     ... and ${missing.length - 5} more`);
      }
    }
    if (extra.length > 0) {
      console.log(`   Extra keys (${extra.length}):`);
      extra.slice(0, 5).forEach(key => console.log(`     + ${key}`));
      if (extra.length > 5) {
        console.log(`     ... and ${extra.length - 5} more`);
      }
    }
  }
});

console.log('\n' + '='.repeat(50));

// Summary
console.log('\n📋 Summary:');
console.log(`   Languages: ${LANGUAGES.length}`);
console.log(`   Total keys per language: ${baseKeys.length}`);
console.log(`   Status: ${allConsistent ? '✅ All consistent' : '❌ Inconsistencies found'}`);

// Key categories
const categories = {};
baseKeys.forEach(key => {
  const category = key.split('.')[0];
  categories[category] = (categories[category] || 0) + 1;
});

console.log('\n📁 Key Categories:');
Object.entries(categories)
  .sort((a, b) => b[1] - a[1])
  .forEach(([category, count]) => {
    console.log(`   ${category}: ${count} keys`);
  });

console.log('\n' + '='.repeat(50));

if (allConsistent) {
  console.log('\n✅ All translation files are consistent!');
  console.log('🎉 i18n system is ready for production\n');
  process.exit(0);
} else {
  console.log('\n❌ Translation files have inconsistencies');
  console.log('⚠️  Please fix the issues above\n');
  process.exit(1);
}
