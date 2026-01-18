#!/usr/bin/env tsx
/**
 * Script to add Batch 2 (Change Management) translations to all language files
 * This script reads the English changes keys and adds translated versions to all languages
 */

import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.join(process.cwd(), 'public', 'locales');
const BATCH2_SOURCE = path.join(LOCALES_DIR, 'changes-batch2-keys.json');

// Language configurations
const LANGUAGES = {
  de: 'German',
  fr: 'French',
  es: 'Spanish',
  pl: 'Polish',
  gsw: 'Swiss German'
};

interface TranslationFile {
  [key: string]: any;
}

/**
 * Read JSON file safely
 */
function readJsonFile(filePath: string): TranslationFile {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`❌ Error reading ${filePath}:`, error);
    throw error;
  }
}

/**
 * Write JSON file with proper formatting
 */
function writeJsonFile(filePath: string, data: TranslationFile): void {
  try {
    const content = JSON.stringify(data, null, 2);
    fs.writeFileSync(filePath, content + '\n', 'utf-8');
    console.log(`✅ Successfully wrote ${filePath}`);
  } catch (error) {
    console.error(`❌ Error writing ${filePath}:`, error);
    throw error;
  }
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 Starting Batch 2 translation addition...\n');

  // Check if source file exists
  if (!fs.existsSync(BATCH2_SOURCE)) {
    console.error(`❌ Source file not found: ${BATCH2_SOURCE}`);
    process.exit(1);
  }

  // Read the English changes keys
  console.log('📖 Reading English changes keys...');
  const batch2Keys = readJsonFile(BATCH2_SOURCE);
  
  if (!batch2Keys.changes) {
    console.error('❌ No "changes" object found in source file');
    process.exit(1);
  }

  console.log(`✅ Found changes object with keys\n`);

  // Process each language
  for (const [langCode, langName] of Object.entries(LANGUAGES)) {
    console.log(`\n📝 Processing ${langName} (${langCode})...`);
    
    const langFile = path.join(LOCALES_DIR, `${langCode}.json`);
    
    if (!fs.existsSync(langFile)) {
      console.warn(`⚠️  Language file not found: ${langFile}, skipping...`);
      continue;
    }

    try {
      // Read existing translations
      const translations = readJsonFile(langFile);
      
      // Check if changes already exists
      if (translations.changes) {
        console.log(`⚠️  "changes" object already exists in ${langCode}.json`);
        console.log(`   Skipping to avoid overwriting existing translations...`);
        continue;
      }

      // Add the changes object
      translations.changes = batch2Keys.changes;
      
      // Write back to file
      writeJsonFile(langFile, translations);
      console.log(`✅ Added changes object to ${langName}`);
      
    } catch (error) {
      console.error(`❌ Error processing ${langName}:`, error);
      continue;
    }
  }

  console.log('\n\n✨ Batch 2 translation addition complete!');
  console.log('\n📊 Summary:');
  console.log('   - Source: changes-batch2-keys.json');
  console.log('   - Languages processed: ' + Object.keys(LANGUAGES).length);
  console.log('\n💡 Next steps:');
  console.log('   1. Review the added translations in each language file');
  console.log('   2. Replace English placeholders with proper translations');
  console.log('   3. Run: npm run generate-types');
  console.log('   4. Verify with: npm run type-check\n');
}

// Run the script
main().catch((error) => {
  console.error('❌ Script failed:', error);
  process.exit(1);
});
