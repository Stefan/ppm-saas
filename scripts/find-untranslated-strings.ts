#!/usr/bin/env tsx
/**
 * Find Untranslated Strings
 * 
 * Scans the codebase for hardcoded strings that should be translated.
 * Helps identify missing translations and improve i18n coverage.
 * 
 * Usage: npm run find-untranslated
 */

import * as fs from 'fs';
import * as path from 'path';

// Configuration
const SCAN_DIRECTORIES = ['app', 'components', 'hooks'];
const FILE_EXTENSIONS = ['.tsx', '.ts'];
const EXCLUDE_PATTERNS = [
  /node_modules/,
  /__tests__/,
  /\.test\./,
  /\.spec\./,
  /\.d\.ts$/,
];

// Patterns to find hardcoded strings
const STRING_PATTERNS = [
  // JSX text content: >text<
  />\s*([A-Z][^<>{}\n]{2,50})\s*</g,
  // Common attributes
  /placeholder=["']([^"']+)["']/g,
  /title=["']([^"']+)["']/g,
  /aria-label=["']([^"']+)["']/g,
  /alt=["']([^"']+)["']/g,
  /label=["']([^"']+)["']/g,
];

// Patterns to exclude (not user-facing strings)
const EXCLUDE_STRING_PATTERNS = [
  /^https?:\/\//i,           // URLs
  /^\/[a-z-/]+$/,            // Paths
  /^[a-z-]+\.[a-z]+$/i,      // File names
  /^[A-Z_]+$/,               // Constants
  /^\d+$/,                   // Numbers only
  /^[a-z-]+$/,               // CSS classes (lowercase with dashes)
  /^className$/,             // React props
  /^onClick$/,               // Event handlers
  /^onChange$/,
  /^onSubmit$/,
  /^data-/,                  // Data attributes
  /^aria-/,                  // ARIA attributes (when not user-facing)
  /^[{}\[\]()]/,             // Code syntax
  /t\(/,                     // Already translated
  /useTranslations/,         // Translation hook
  /TranslationKey/,          // Type references
];

interface Finding {
  file: string;
  line: number;
  string: string;
  context: string;
  suggestedKey: string;
  priority: 'high' | 'medium' | 'low';
}

/**
 * Check if a string should be excluded
 */
function shouldExcludeString(str: string): boolean {
  // Empty or very short strings
  if (!str || str.trim().length < 3) return true;
  
  // Check against exclude patterns
  return EXCLUDE_STRING_PATTERNS.some(pattern => pattern.test(str));
}

/**
 * Generate a suggested translation key from a string
 */
function generateSuggestedKey(str: string, file: string): string {
  // Determine component/section from file path
  const pathParts = file.split('/');
  let section = 'common';
  
  if (pathParts.includes('components')) {
    const componentIndex = pathParts.indexOf('components') + 1;
    if (pathParts[componentIndex] === 'shared') {
      section = 'common';
    } else if (pathParts[componentIndex]) {
      section = pathParts[componentIndex];
    }
  } else if (pathParts.includes('app')) {
    const appIndex = pathParts.indexOf('app') + 1;
    if (pathParts[appIndex] && pathParts[appIndex] !== 'page.tsx') {
      section = pathParts[appIndex];
    }
  }
  
  // Convert string to key format
  const key = str
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .trim()
    .split(/\s+/)
    .slice(0, 3) // Max 3 words
    .join('_');
  
  return `${section}.${key}`;
}

/**
 * Determine priority based on context
 */
function determinePriority(str: string, context: string): 'high' | 'medium' | 'low' {
  // High priority: User-facing labels, buttons, titles
  if (context.includes('placeholder') || context.includes('title') || context.includes('aria-label')) {
    return 'high';
  }
  
  // High priority: Starts with capital letter (likely user-facing)
  if (/^[A-Z]/.test(str)) {
    return 'high';
  }
  
  // Medium priority: Alt text, labels
  if (context.includes('alt') || context.includes('label')) {
    return 'medium';
  }
  
  return 'low';
}

/**
 * Scan a file for untranslated strings
 */
function scanFile(filePath: string): Finding[] {
  const findings: Finding[] = [];
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  // Skip files that already use translations extensively
  if (content.includes('useTranslations()') || content.includes('const t = useTranslations')) {
    // Still scan but with lower priority
  }
  
  lines.forEach((line, index) => {
    STRING_PATTERNS.forEach(pattern => {
      const matches = line.matchAll(pattern);
      
      for (const match of matches) {
        const str = match[1];
        
        if (!shouldExcludeString(str)) {
          const suggestedKey = generateSuggestedKey(str, filePath);
          const priority = determinePriority(str, line);
          
          findings.push({
            file: filePath,
            line: index + 1,
            string: str,
            context: line.trim(),
            suggestedKey,
            priority,
          });
        }
      }
    });
  });
  
  return findings;
}

/**
 * Recursively scan directory
 */
function scanDirectory(dir: string): Finding[] {
  let findings: Finding[] = [];
  
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    
    // Check exclude patterns
    if (EXCLUDE_PATTERNS.some(pattern => pattern.test(fullPath))) {
      continue;
    }
    
    if (entry.isDirectory()) {
      findings = findings.concat(scanDirectory(fullPath));
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (FILE_EXTENSIONS.includes(ext)) {
        findings = findings.concat(scanFile(fullPath));
      }
    }
  }
  
  return findings;
}

/**
 * Group findings by file
 */
function groupByFile(findings: Finding[]): Map<string, Finding[]> {
  const grouped = new Map<string, Finding[]>();
  
  findings.forEach(finding => {
    if (!grouped.has(finding.file)) {
      grouped.set(finding.file, []);
    }
    grouped.get(finding.file)!.push(finding);
  });
  
  return grouped;
}

/**
 * Generate report
 */
function generateReport(findings: Finding[]): void {
  console.log('\n📊 Untranslated Strings Report\n');
  console.log('=' .repeat(80));
  
  // Summary
  const highPriority = findings.filter(f => f.priority === 'high').length;
  const mediumPriority = findings.filter(f => f.priority === 'medium').length;
  const lowPriority = findings.filter(f => f.priority === 'low').length;
  
  console.log(`\n📈 Summary:`);
  console.log(`   Total findings: ${findings.length}`);
  console.log(`   🔴 High priority: ${highPriority}`);
  console.log(`   🟡 Medium priority: ${mediumPriority}`);
  console.log(`   🟢 Low priority: ${lowPriority}`);
  
  // Group by file
  const grouped = groupByFile(findings);
  const sortedFiles = Array.from(grouped.keys()).sort();
  
  console.log(`\n📁 Files with untranslated strings: ${sortedFiles.length}\n`);
  
  // Show findings by priority
  const priorities: Array<'high' | 'medium' | 'low'> = ['high', 'medium', 'low'];
  const priorityEmoji = { high: '🔴', medium: '🟡', low: '🟢' };
  
  priorities.forEach(priority => {
    const priorityFindings = findings.filter(f => f.priority === priority);
    
    if (priorityFindings.length > 0) {
      console.log(`\n${priorityEmoji[priority]} ${priority.toUpperCase()} PRIORITY (${priorityFindings.length} findings)\n`);
      console.log('-'.repeat(80));
      
      // Group by file for this priority
      const priorityGrouped = groupByFile(priorityFindings);
      
      Array.from(priorityGrouped.keys()).sort().forEach(file => {
        const fileFindings = priorityGrouped.get(file)!;
        console.log(`\n📄 ${file} (${fileFindings.length} findings)`);
        
        fileFindings.slice(0, 5).forEach(finding => { // Show max 5 per file
          console.log(`   Line ${finding.line}: "${finding.string}"`);
          console.log(`   Suggested key: ${finding.suggestedKey}`);
          console.log(`   Context: ${finding.context.substring(0, 70)}...`);
          console.log('');
        });
        
        if (fileFindings.length > 5) {
          console.log(`   ... and ${fileFindings.length - 5} more\n`);
        }
      });
    }
  });
  
  console.log('\n' + '='.repeat(80));
  console.log('\n💡 Next Steps:');
  console.log('   1. Review high priority findings first');
  console.log('   2. Add translation keys to public/locales/en.json');
  console.log('   3. Update components to use useTranslations() hook');
  console.log('   4. Run npm run generate-types to update TypeScript types');
  console.log('   5. Translate to all 6 languages\n');
}

/**
 * Main execution
 */
function main() {
  console.log('🔍 Scanning for untranslated strings...\n');
  
  let allFindings: Finding[] = [];
  
  SCAN_DIRECTORIES.forEach(dir => {
    const dirPath = path.join(process.cwd(), dir);
    
    if (!fs.existsSync(dirPath)) {
      console.log(`⚠️  Directory not found: ${dir}`);
      return;
    }
    
    console.log(`📂 Scanning ${dir}/...`);
    const findings = scanDirectory(dirPath);
    allFindings = allFindings.concat(findings);
  });
  
  if (allFindings.length === 0) {
    console.log('\n✅ No untranslated strings found! Great job! 🎉\n');
    return;
  }
  
  generateReport(allFindings);
}

// Run the script
try {
  main();
} catch (error) {
  console.error('❌ Error scanning for untranslated strings:', error);
  process.exit(1);
}
