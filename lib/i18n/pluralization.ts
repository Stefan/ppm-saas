/**
 * Pluralization Module
 * 
 * This module provides pluralization support for the i18n system.
 * Different languages have different plural rules, and this module
 * implements those rules to select the correct plural form based on count.
 * 
 * Plural Forms:
 * - zero: Used for count = 0 (optional, some languages use 'other' for zero)
 * - one: Used for count = 1
 * - two: Used for count = 2 (optional, used in some languages like Arabic)
 * - few: Used for small counts (optional, e.g., 2-4 in Polish)
 * - many: Used for larger counts (optional, e.g., 5+ in Polish)
 * - other: Default form for all other counts
 */

import { SupportedLocale, PluralRules } from './types';

/**
 * Plural form type
 * Represents the different plural categories
 */
export type PluralForm = 'zero' | 'one' | 'two' | 'few' | 'many' | 'other';

/**
 * Get the plural form for a given count and locale
 * 
 * Implements language-specific plural rules according to Unicode CLDR
 * @see https://unicode-org.github.io/cldr-staging/charts/latest/supplemental/language_plural_rules.html
 * 
 * @param count - The count value
 * @param locale - The locale code
 * @returns The plural form to use
 * 
 * @example
 * getPluralForm(1, 'en'); // 'one'
 * getPluralForm(2, 'en'); // 'other'
 * getPluralForm(3, 'pl'); // 'few'
 * getPluralForm(5, 'pl'); // 'many'
 */
export function getPluralForm(count: number, locale: SupportedLocale): PluralForm {
  // Handle zero explicitly if needed
  if (count === 0) {
    // Some languages have special zero form
    if (locale === 'pl') {
      return 'many'; // Polish uses 'many' for zero
    }
    return 'other'; // Most languages use 'other' for zero
  }

  // Handle one
  if (count === 1) {
    return 'one';
  }

  // Language-specific rules for other counts
  switch (locale) {
    case 'en':
    case 'de':
    case 'es':
    case 'gsw':
      // English, German, Spanish, Swiss German: simple rule
      // one: 1, other: everything else
      return 'other';

    case 'fr':
      // French: one for 0 and 1, other for everything else
      // But we already handled 0 and 1 above, so this is 'other'
      return 'other';

    case 'pl':
      // Polish: complex rules
      // one: 1
      // few: 2-4, 22-24, 32-34, etc. (ends in 2-4 but not 12-14)
      // many: 0, 5-21, 25-31, etc. (ends in 0,1,5-9 or 12-14)
      // other: fractions
      
      // Check if it's a whole number
      if (count % 1 !== 0) {
        return 'other'; // Fractions use 'other'
      }

      const mod10 = count % 10;
      const mod100 = count % 100;

      // few: ends in 2-4 but not 12-14
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
        return 'few';
      }

      // many: everything else (0, 5-21, 25-31, etc.)
      return 'many';

    default:
      return 'other';
  }
}

/**
 * Select the appropriate plural translation
 * 
 * Given a plural rules object and a count, selects the correct form
 * and falls back to 'other' if the specific form is not available.
 * 
 * @param pluralRules - Object with different plural forms
 * @param count - The count value
 * @param locale - The locale code
 * @returns The selected plural form string
 * 
 * @example
 * const rules = {
 *   one: '{count} item',
 *   other: '{count} items'
 * };
 * selectPluralForm(rules, 1, 'en'); // '{count} item'
 * selectPluralForm(rules, 5, 'en'); // '{count} items'
 */
export function selectPluralForm(
  pluralRules: PluralRules,
  count: number,
  locale: SupportedLocale
): string {
  const form = getPluralForm(count, locale);

  // Try to get the specific form, fall back to 'other'
  const selectedForm = pluralRules[form] ?? pluralRules.other;

  return selectedForm;
}

/**
 * Check if a value is a plural rules object
 * 
 * @param value - Value to check
 * @returns True if value is a PluralRules object
 */
export function isPluralRules(value: any): value is PluralRules {
  return (
    typeof value === 'object' &&
    value !== null &&
    'other' in value &&
    typeof value.other === 'string'
  );
}

/**
 * Format a plural translation with count interpolation
 * 
 * Combines plural form selection with count interpolation.
 * This is a convenience function for the common case of pluralization
 * with count display.
 * 
 * @param pluralRules - Object with different plural forms
 * @param count - The count value
 * @param locale - The locale code
 * @returns The formatted string with count interpolated
 * 
 * @example
 * const rules = {
 *   one: '{count} item',
 *   other: '{count} items'
 * };
 * formatPlural(rules, 1, 'en'); // '1 item'
 * formatPlural(rules, 5, 'en'); // '5 items'
 */
export function formatPlural(
  pluralRules: PluralRules,
  count: number,
  locale: SupportedLocale
): string {
  const form = selectPluralForm(pluralRules, count, locale);
  
  // Replace {count} placeholder with the actual count
  return form.replace(/\{count\}/g, String(count));
}
