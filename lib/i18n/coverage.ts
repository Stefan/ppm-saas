/**
 * Translation Coverage Report Utility
 * 
 * This module provides utilities for analyzing translation coverage across
 * all supported languages. It helps identify missing translations and
 * generates reports for development purposes.
 * 
 * Features:
 * - Compare translations across all languages
 * - Identify missing keys per language
 * - Generate coverage reports
 * - Calculate coverage percentages
 */

import { loadTranslations } from './loader';
import { SUPPORTED_LANGUAGES, SupportedLocale } from './types';

/**
 * Translation key path (e.g., 'nav.dashboards')
 */
type KeyPath = string;

/**
 * Coverage report for a single language
 */
export interface LanguageCoverageReport {
  /** Language code */
  locale: SupportedLocale;
  /** Language name */
  name: string;
  /** Total number of keys in English (reference) */
  totalKeys: number;
  /** Number of translated keys */
  translatedKeys: number;
  /** Number of missing keys */
  missingKeys: number;
  /** Coverage percentage (0-100) */
  coveragePercent: number;
  /** List of missing key paths */
  missingKeyPaths: KeyPath[];
}

/**
 * Complete coverage report for all languages
 */
export interface CoverageReport {
  /** Timestamp when report was generated */
  generatedAt: Date;
  /** Reference language (English) */
  referenceLocale: SupportedLocale;
  /** Total number of keys in reference language */
  totalKeys: number;
  /** Coverage reports for each language */
  languages: LanguageCoverageReport[];
  /** Overall coverage percentage across all languages */
  overallCoverage: number;
}

/**
 * Extract all key paths from a nested translation object
 * 
 * @param obj - Translation object
 * @param prefix - Current key path prefix
 * @returns Array of all key paths
 * 
 * @example
 * extractKeyPaths({ nav: { dashboards: 'Dashboards' } })
 * // Returns: ['nav.dashboards']
 */
function extractKeyPaths(obj: any, prefix: string = ''): KeyPath[] {
  const keys: KeyPath[] = [];
  
  for (const key in obj) {
    if (!obj.hasOwnProperty(key)) continue;
    
    const fullPath = prefix ? `${prefix}.${key}` : key;
    const value = obj[key];
    
    if (typeof value === 'string') {
      // Leaf node - this is a translation key
      keys.push(fullPath);
    } else if (typeof value === 'object' && value !== null) {
      // Check if it's a plural rules object (has 'one' and 'other' keys)
      const isPluralRules = 'one' in value && 'other' in value;
      
      if (isPluralRules) {
        // Treat plural rules as a single key
        keys.push(fullPath);
      } else {
        // Nested object - recurse
        keys.push(...extractKeyPaths(value, fullPath));
      }
    }
  }
  
  return keys;
}

/**
 * Check if a key path exists in a translation object
 * 
 * @param obj - Translation object
 * @param keyPath - Dot-notation key path
 * @returns True if key exists
 */
function hasKeyPath(obj: any, keyPath: KeyPath): boolean {
  const keys = keyPath.split('.');
  let current = obj;
  
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return false;
    }
  }
  
  // Check if we found a valid translation (string or plural rules)
  if (typeof current === 'string') {
    return true;
  }
  
  // Check if it's a plural rules object
  if (typeof current === 'object' && current !== null) {
    return 'one' in current && 'other' in current;
  }
  
  return false;
}

/**
 * Generate a coverage report for a specific language
 * 
 * @param locale - Language code to analyze
 * @param referenceKeys - All keys from reference language (English)
 * @returns Coverage report for the language
 */
async function generateLanguageCoverageReport(
  locale: SupportedLocale,
  referenceKeys: KeyPath[]
): Promise<LanguageCoverageReport> {
  // Load translations for this language
  const translations = await loadTranslations(locale);
  
  // Find missing keys
  const missingKeyPaths: KeyPath[] = [];
  
  for (const keyPath of referenceKeys) {
    if (!hasKeyPath(translations, keyPath)) {
      missingKeyPaths.push(keyPath);
    }
  }
  
  const translatedKeys = referenceKeys.length - missingKeyPaths.length;
  const coveragePercent = referenceKeys.length > 0
    ? Math.round((translatedKeys / referenceKeys.length) * 100)
    : 100;
  
  // Find language name
  const language = SUPPORTED_LANGUAGES.find(lang => lang.code === locale);
  const name = language?.name || locale;
  
  return {
    locale,
    name,
    totalKeys: referenceKeys.length,
    translatedKeys,
    missingKeys: missingKeyPaths.length,
    coveragePercent,
    missingKeyPaths,
  };
}

/**
 * Generate a complete translation coverage report for all languages
 * 
 * This function analyzes all translation files and generates a comprehensive
 * report showing which keys are missing in each language.
 * 
 * @returns Complete coverage report
 * 
 * @example
 * ```typescript
 * const report = await generateCoverageReport();
 * console.log(`Overall coverage: ${report.overallCoverage}%`);
 * 
 * for (const lang of report.languages) {
 *   console.log(`${lang.name}: ${lang.coveragePercent}%`);
 *   if (lang.missingKeys > 0) {
 *     console.log(`  Missing keys: ${lang.missingKeyPaths.join(', ')}`);
 *   }
 * }
 * ```
 */
export async function generateCoverageReport(): Promise<CoverageReport> {
  const referenceLocale: SupportedLocale = 'en';
  
  // Load English translations as reference
  const referenceTranslations = await loadTranslations(referenceLocale);
  const referenceKeys = extractKeyPaths(referenceTranslations);
  
  // Generate reports for all languages
  const languageReports: LanguageCoverageReport[] = [];
  
  for (const language of SUPPORTED_LANGUAGES) {
    const report = await generateLanguageCoverageReport(
      language.code,
      referenceKeys
    );
    languageReports.push(report);
  }
  
  // Calculate overall coverage (average across all non-English languages)
  const nonEnglishReports = languageReports.filter(r => r.locale !== 'en');
  const overallCoverage = nonEnglishReports.length > 0
    ? Math.round(
        nonEnglishReports.reduce((sum, r) => sum + r.coveragePercent, 0) /
        nonEnglishReports.length
      )
    : 100;
  
  return {
    generatedAt: new Date(),
    referenceLocale,
    totalKeys: referenceKeys.length,
    languages: languageReports,
    overallCoverage,
  };
}

/**
 * Print a coverage report to the console
 * 
 * @param report - Coverage report to print
 * @param showMissingKeys - Whether to show detailed missing keys
 */
export function printCoverageReport(
  report: CoverageReport,
  showMissingKeys: boolean = false
): void {
  console.log('\n=== Translation Coverage Report ===');
  console.log(`Generated: ${report.generatedAt.toISOString()}`);
  console.log(`Reference Language: ${report.referenceLocale}`);
  console.log(`Total Keys: ${report.totalKeys}`);
  console.log(`Overall Coverage: ${report.overallCoverage}%\n`);
  
  // Sort languages by coverage (lowest first to highlight issues)
  const sortedLanguages = [...report.languages].sort(
    (a, b) => a.coveragePercent - b.coveragePercent
  );
  
  for (const lang of sortedLanguages) {
    const status = lang.coveragePercent === 100 ? '✓' : '⚠';
    console.log(
      `${status} ${lang.name} (${lang.locale}): ${lang.coveragePercent}% ` +
      `(${lang.translatedKeys}/${lang.totalKeys} keys)`
    );
    
    if (showMissingKeys && lang.missingKeys > 0) {
      console.log(`  Missing keys (${lang.missingKeys}):`);
      for (const keyPath of lang.missingKeyPaths) {
        console.log(`    - ${keyPath}`);
      }
      console.log('');
    }
  }
  
  console.log('=================================\n');
}

/**
 * Get missing translations for a specific language
 * 
 * @param locale - Language code to check
 * @returns Array of missing key paths
 * 
 * @example
 * ```typescript
 * const missing = await getMissingTranslations('de');
 * if (missing.length > 0) {
 *   console.log(`German is missing ${missing.length} translations:`);
 *   console.log(missing.join(', '));
 * }
 * ```
 */
export async function getMissingTranslations(
  locale: SupportedLocale
): Promise<KeyPath[]> {
  // Load English as reference
  const referenceTranslations = await loadTranslations('en');
  const referenceKeys = extractKeyPaths(referenceTranslations);
  
  // Load target language
  const translations = await loadTranslations(locale);
  
  // Find missing keys
  const missingKeys: KeyPath[] = [];
  
  for (const keyPath of referenceKeys) {
    if (!hasKeyPath(translations, keyPath)) {
      missingKeys.push(keyPath);
    }
  }
  
  return missingKeys;
}
