/**
 * Property-Based Tests for Pluralization
 * 
 * These tests verify that pluralization works correctly across all languages
 * and count values using property-based testing with fast-check.
 */

import fc from 'fast-check';
import { getPluralForm, selectPluralForm, formatPlural, isPluralRules } from '../pluralization';
import { PluralRules, SupportedLocale } from '../types';

describe('Pluralization Property Tests', () => {
  // Feature: complete-i18n-system, Property 25: Plural form selection by count
  // **Validates: Requirements 13.2**
  describe('Property 25: Plural form selection by count', () => {
    it('should select correct plural form based on count and language rules', () => {
      fc.assert(
        fc.property(
          fc.constantFrom<SupportedLocale>('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          fc.integer({ min: 0, max: 100 }),
          (locale, count) => {
            const form = getPluralForm(count, locale);
            
            // Form should be one of the valid plural forms
            expect(['zero', 'one', 'two', 'few', 'many', 'other']).toContain(form);
            
            // Verify specific rules for each language
            if (count === 1) {
              expect(form).toBe('one');
            }
            
            // English, German, Spanish, Swiss German: simple rules
            if (['en', 'de', 'es', 'gsw'].includes(locale)) {
              if (count === 1) {
                expect(form).toBe('one');
              } else {
                expect(form).toBe('other');
              }
            }
            
            // French: 0 and 1 use 'other' (we handle 1 as 'one' above)
            if (locale === 'fr') {
              if (count === 1) {
                expect(form).toBe('one');
              } else {
                expect(form).toBe('other');
              }
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should always return a valid plural form', () => {
      fc.assert(
        fc.property(
          fc.constantFrom<SupportedLocale>('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          fc.integer(),
          (locale, count) => {
            const form = getPluralForm(count, locale);
            expect(form).toBeDefined();
            expect(typeof form).toBe('string');
            expect(['zero', 'one', 'two', 'few', 'many', 'other']).toContain(form);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  // Feature: complete-i18n-system, Property 26: Language-specific plural rules
  // **Validates: Requirements 13.4**
  describe('Property 26: Language-specific plural rules', () => {
    it('should apply Polish plural rules correctly', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: 0, max: 100 }),
          (count) => {
            const form = getPluralForm(count, 'pl');
            
            if (count === 1) {
              expect(form).toBe('one');
            } else if (count === 0) {
              // Polish uses 'many' for zero
              expect(form).toBe('many');
            } else {
              const mod10 = count % 10;
              const mod100 = count % 100;
              
              // few: ends in 2-4 but not 12-14
              if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
                expect(form).toBe('few');
              } else {
                // many: everything else
                expect(form).toBe('many');
              }
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle Polish special cases correctly', () => {
      // Test specific Polish cases
      expect(getPluralForm(0, 'pl')).toBe('many');
      expect(getPluralForm(1, 'pl')).toBe('one');
      expect(getPluralForm(2, 'pl')).toBe('few');
      expect(getPluralForm(3, 'pl')).toBe('few');
      expect(getPluralForm(4, 'pl')).toBe('few');
      expect(getPluralForm(5, 'pl')).toBe('many');
      expect(getPluralForm(12, 'pl')).toBe('many');
      expect(getPluralForm(13, 'pl')).toBe('many');
      expect(getPluralForm(14, 'pl')).toBe('many');
      expect(getPluralForm(22, 'pl')).toBe('few');
      expect(getPluralForm(23, 'pl')).toBe('few');
      expect(getPluralForm(24, 'pl')).toBe('few');
      expect(getPluralForm(25, 'pl')).toBe('many');
    });

    it('should handle fractions in Polish', () => {
      expect(getPluralForm(1.5, 'pl')).toBe('other');
      expect(getPluralForm(2.3, 'pl')).toBe('other');
      expect(getPluralForm(0.5, 'pl')).toBe('other');
    });
  });

  // Feature: complete-i18n-system, Property 27: Pluralization with interpolation
  // **Validates: Requirements 13.5**
  describe('Property 27: Pluralization with interpolation', () => {
    it('should format plural with count interpolation', () => {
      fc.assert(
        fc.property(
          fc.constantFrom<SupportedLocale>('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          fc.integer({ min: 0, max: 100 }),
          (locale, count) => {
            const pluralRules: PluralRules = {
              one: '{count} item',
              few: '{count} items (few)',
              many: '{count} items (many)',
              other: '{count} items'
            };
            
            const result = formatPlural(pluralRules, count, locale);
            
            // Result should contain the count
            expect(result).toContain(String(count));
            
            // Result should not contain the placeholder
            expect(result).not.toContain('{count}');
            
            // Result should be a string
            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should select correct form and interpolate count', () => {
      const pluralRules: PluralRules = {
        one: '{count} item',
        other: '{count} items'
      };
      
      expect(formatPlural(pluralRules, 1, 'en')).toBe('1 item');
      expect(formatPlural(pluralRules, 0, 'en')).toBe('0 items');
      expect(formatPlural(pluralRules, 2, 'en')).toBe('2 items');
      expect(formatPlural(pluralRules, 100, 'en')).toBe('100 items');
    });

    it('should handle Polish plurals with interpolation', () => {
      const pluralRules: PluralRules = {
        one: '{count} element',
        few: '{count} elementy',
        many: '{count} elementów',
        other: '{count} elementu'
      };
      
      expect(formatPlural(pluralRules, 1, 'pl')).toBe('1 element');
      expect(formatPlural(pluralRules, 2, 'pl')).toBe('2 elementy');
      expect(formatPlural(pluralRules, 3, 'pl')).toBe('3 elementy');
      expect(formatPlural(pluralRules, 4, 'pl')).toBe('4 elementy');
      expect(formatPlural(pluralRules, 5, 'pl')).toBe('5 elementów');
      expect(formatPlural(pluralRules, 0, 'pl')).toBe('0 elementów');
      expect(formatPlural(pluralRules, 22, 'pl')).toBe('22 elementy');
    });
  });

  describe('isPluralRules helper', () => {
    it('should correctly identify plural rules objects', () => {
      fc.assert(
        fc.property(
          fc.record({
            one: fc.string(),
            other: fc.string(),
            few: fc.option(fc.string()),
            many: fc.option(fc.string())
          }),
          (obj) => {
            // Remove undefined values
            const cleanObj = Object.fromEntries(
              Object.entries(obj).filter(([_, v]) => v !== null)
            );
            
            if ('other' in cleanObj) {
              expect(isPluralRules(cleanObj)).toBe(true);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should reject non-plural-rules objects', () => {
      expect(isPluralRules(null)).toBe(false);
      expect(isPluralRules(undefined)).toBe(false);
      expect(isPluralRules('string')).toBe(false);
      expect(isPluralRules(123)).toBe(false);
      expect(isPluralRules({})).toBe(false);
      expect(isPluralRules({ one: 'test' })).toBe(false); // Missing 'other'
      expect(isPluralRules({ other: 123 })).toBe(false); // 'other' is not a string
    });

    it('should accept valid plural rules', () => {
      expect(isPluralRules({ one: 'one', other: 'other' })).toBe(true);
      expect(isPluralRules({ one: 'one', few: 'few', many: 'many', other: 'other' })).toBe(true);
      expect(isPluralRules({ other: 'other' })).toBe(true); // Minimal valid
    });
  });

  describe('selectPluralForm', () => {
    it('should fall back to other when specific form is missing', () => {
      fc.assert(
        fc.property(
          fc.constantFrom<SupportedLocale>('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          fc.integer({ min: 0, max: 100 }),
          (locale, count) => {
            // Minimal plural rules with only 'other'
            const minimalRules: PluralRules = {
              one: 'one form',
              other: 'other form'
            };
            
            const result = selectPluralForm(minimalRules, count, locale);
            
            // Should always return a string
            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            
            // Should be either 'one form' or 'other form'
            expect(['one form', 'other form']).toContain(result);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
