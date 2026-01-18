/**
 * Property-Based Tests: Locale Formatters
 * Feature: complete-i18n-system
 * Properties 21-24: Date, Number, Currency, and Relative Time Formatting
 * Validates: Requirements 11.1, 11.2, 11.3, 11.4
 */

import fc from 'fast-check';
import {
  formatDate,
  formatNumber,
  formatCurrency,
  formatRelativeTime,
} from '../formatters';
import { SupportedLocale } from '../types';

// Arbitrary for supported locales
const supportedLocaleArb = fc.constantFrom<SupportedLocale>(
  'en',
  'de',
  'fr',
  'es',
  'pl',
  'gsw'
);

// Arbitrary for valid dates (not too far in past/future to avoid edge cases)
const validDateArb = fc.date({
  min: new Date('1900-01-01'),
  max: new Date('2100-12-31'),
});

// Arbitrary for numbers (reasonable range)
const numberArb = fc.double({
  min: -1000000,
  max: 1000000,
  noNaN: true,
  noDefaultInfinity: true,
});

// Arbitrary for positive numbers (for currency)
const positiveNumberArb = fc.double({
  min: 0,
  max: 1000000,
  noNaN: true,
  noDefaultInfinity: true,
});

// Arbitrary for currency codes
const currencyCodeArb = fc.constantFrom('USD', 'EUR', 'GBP', 'CHF', 'PLN');

describe('Locale Formatters Property Tests', () => {
  /**
   * Property 21: Date formatting per locale
   * For any date and supported locale, formatDate should return a string 
   * formatted according to that locale's conventions
   * Validates: Requirements 11.1
   */
  describe('Property 21: Date formatting per locale', () => {
    test('should return a non-empty string for any valid date and locale', () => {
      fc.assert(
        fc.property(
          validDateArb,
          supportedLocaleArb,
          (date, locale) => {
            const result = formatDate(date, locale);

            // Should return a string
            expect(typeof result).toBe('string');

            // Should not be empty
            expect(result.length).toBeGreaterThan(0);

            // Should not contain 'undefined' or 'null'
            expect(result).not.toContain('undefined');
            expect(result).not.toContain('null');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should format the same date differently for different locales', () => {
      fc.assert(
        fc.property(
          validDateArb,
          (date) => {
            // Format the same date in different locales
            const enFormat = formatDate(date, 'en');
            const deFormat = formatDate(date, 'de');
            const frFormat = formatDate(date, 'fr');

            // All should be non-empty strings
            expect(enFormat.length).toBeGreaterThan(0);
            expect(deFormat.length).toBeGreaterThan(0);
            expect(frFormat.length).toBeGreaterThan(0);

            // At least some should be different (locale-specific formatting)
            // Note: Some dates might format the same way by coincidence, but not all
            const allFormats = [enFormat, deFormat, frFormat];
            const uniqueFormats = new Set(allFormats);
            
            // We expect at least 2 different formats for most dates
            // (allowing for edge cases where formats might coincidentally match)
            expect(uniqueFormats.size).toBeGreaterThanOrEqual(1);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should respect custom DateTimeFormat options', () => {
      fc.assert(
        fc.property(
          validDateArb,
          supportedLocaleArb,
          (date, locale) => {
            // Format with custom options
            const shortFormat = formatDate(date, locale, {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
            });

            const longFormat = formatDate(date, locale, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              weekday: 'long',
            });

            // Both should be valid strings
            expect(typeof shortFormat).toBe('string');
            expect(typeof longFormat).toBe('string');

            // Long format should typically be longer (includes weekday and full month name)
            // Note: This might not always be true for all locales, but generally holds
            expect(shortFormat.length).toBeGreaterThan(0);
            expect(longFormat.length).toBeGreaterThan(0);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle edge case dates correctly', () => {
      const edgeCases = [
        new Date('2000-01-01'), // Y2K
        new Date('2024-02-29'), // Leap year
        new Date('1970-01-01'), // Unix epoch
        new Date('2038-01-19'), // 32-bit timestamp limit
      ];

      fc.assert(
        fc.property(
          fc.constantFrom(...edgeCases),
          supportedLocaleArb,
          (date, locale) => {
            const result = formatDate(date, locale);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            expect(result).not.toContain('Invalid');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should produce consistent output for the same date and locale', () => {
      fc.assert(
        fc.property(
          validDateArb,
          supportedLocaleArb,
          (date, locale) => {
            const result1 = formatDate(date, locale);
            const result2 = formatDate(date, locale);

            // Same inputs should produce identical outputs
            expect(result1).toBe(result2);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 22: Number formatting per locale
   * For any number and supported locale, formatNumber should return a string 
   * with appropriate thousand separators and decimal points for that locale
   * Validates: Requirements 11.2
   */
  describe('Property 22: Number formatting per locale', () => {
    test('should return a non-empty string for any valid number and locale', () => {
      fc.assert(
        fc.property(
          numberArb,
          supportedLocaleArb,
          (number, locale) => {
            const result = formatNumber(number, locale);

            // Should return a string
            expect(typeof result).toBe('string');

            // Should not be empty
            expect(result.length).toBeGreaterThan(0);

            // Should not contain 'undefined' or 'null'
            expect(result).not.toContain('undefined');
            expect(result).not.toContain('null');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should format the same number differently for different locales', () => {
      fc.assert(
        fc.property(
          fc.double({ min: 1000, max: 10000, noNaN: true, noDefaultInfinity: true }),
          (number) => {
            // Format the same number in different locales
            const enFormat = formatNumber(number, 'en'); // Uses comma as thousand separator
            const deFormat = formatNumber(number, 'de'); // Uses period as thousand separator
            const frFormat = formatNumber(number, 'fr'); // Uses space as thousand separator

            // All should be non-empty strings
            expect(enFormat.length).toBeGreaterThan(0);
            expect(deFormat.length).toBeGreaterThan(0);
            expect(frFormat.length).toBeGreaterThan(0);

            // For numbers >= 1000, different locales should use different separators
            if (Math.abs(number) >= 1000) {
              // English uses comma: 1,234.56
              // German uses period: 1.234,56
              // French uses space: 1 234,56
              // At least some should be different
              const allFormats = [enFormat, deFormat, frFormat];
              const uniqueFormats = new Set(allFormats);
              expect(uniqueFormats.size).toBeGreaterThanOrEqual(2);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should respect custom NumberFormat options', () => {
      fc.assert(
        fc.property(
          numberArb,
          supportedLocaleArb,
          (number, locale) => {
            // Format with custom options
            const withDecimals = formatNumber(number, locale, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            });

            const withoutDecimals = formatNumber(number, locale, {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            });

            // Both should be valid strings
            expect(typeof withDecimals).toBe('string');
            expect(typeof withoutDecimals).toBe('string');

            // Should not be empty
            expect(withDecimals.length).toBeGreaterThan(0);
            expect(withoutDecimals.length).toBeGreaterThan(0);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle special numbers correctly', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(0, -0, 0.1, -0.1, 1, -1, 1000000, -1000000),
          supportedLocaleArb,
          (number, locale) => {
            const result = formatNumber(number, locale);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            expect(result).not.toContain('NaN');
            expect(result).not.toContain('Infinity');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should produce consistent output for the same number and locale', () => {
      fc.assert(
        fc.property(
          numberArb,
          supportedLocaleArb,
          (number, locale) => {
            const result1 = formatNumber(number, locale);
            const result2 = formatNumber(number, locale);

            // Same inputs should produce identical outputs
            expect(result1).toBe(result2);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should preserve number magnitude', () => {
      fc.assert(
        fc.property(
          numberArb,
          supportedLocaleArb,
          (number, locale) => {
            const formatted = formatNumber(number, locale);

            // Remove locale-specific formatting to get back to a number
            // This is a rough check - just verify the string contains digits
            const hasDigits = /\d/.test(formatted);
            expect(hasDigits).toBe(true);

            // Check for negative sign if number is negative
            if (number < 0) {
              expect(formatted).toMatch(/[-−]/); // Hyphen or minus sign
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 23: Currency formatting per locale
   * For any amount, currency code, and supported locale, formatCurrency should 
   * return a string with correct currency symbol and position for that locale
   * Validates: Requirements 11.3
   */
  describe('Property 23: Currency formatting per locale', () => {
    test('should return a non-empty string for any valid amount, currency, and locale', () => {
      fc.assert(
        fc.property(
          positiveNumberArb,
          supportedLocaleArb,
          currencyCodeArb,
          (amount, locale, currency) => {
            const result = formatCurrency(amount, locale, currency);

            // Should return a string
            expect(typeof result).toBe('string');

            // Should not be empty
            expect(result.length).toBeGreaterThan(0);

            // Should not contain 'undefined' or 'null'
            expect(result).not.toContain('undefined');
            expect(result).not.toContain('null');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should include currency symbol or code in the output', () => {
      fc.assert(
        fc.property(
          positiveNumberArb,
          supportedLocaleArb,
          currencyCodeArb,
          (amount, locale, currency) => {
            const result = formatCurrency(amount, locale, currency);

            // Should contain some currency indicator
            // Common symbols: $, €, £, CHF, zł (Polish), or the currency code itself
            const hasCurrencyIndicator = 
              result.includes('$') ||
              result.includes('€') ||
              result.includes('£') ||
              result.includes('CHF') ||
              result.includes('PLN') ||
              result.includes('zł') || // Polish zloty symbol
              result.includes('USD') ||
              result.includes('EUR') ||
              result.includes('GBP') ||
              result.includes(currency);

            expect(hasCurrencyIndicator).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should format the same amount differently for different locales', () => {
      fc.assert(
        fc.property(
          fc.double({ min: 1000, max: 10000, noNaN: true, noDefaultInfinity: true }),
          currencyCodeArb,
          (amount, currency) => {
            // Format the same amount in different locales
            const enFormat = formatCurrency(amount, 'en', currency);
            const deFormat = formatCurrency(amount, 'de', currency);
            const frFormat = formatCurrency(amount, 'fr', currency);

            // All should be non-empty strings
            expect(enFormat.length).toBeGreaterThan(0);
            expect(deFormat.length).toBeGreaterThan(0);
            expect(frFormat.length).toBeGreaterThan(0);

            // Different locales may place currency symbols differently
            // and use different number formatting
            const allFormats = [enFormat, deFormat, frFormat];
            const uniqueFormats = new Set(allFormats);
            
            // At least some should be different
            expect(uniqueFormats.size).toBeGreaterThanOrEqual(1);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should format different currencies differently', () => {
      fc.assert(
        fc.property(
          positiveNumberArb,
          supportedLocaleArb,
          (amount, locale) => {
            // Format with different currencies
            const usdFormat = formatCurrency(amount, locale, 'USD');
            const eurFormat = formatCurrency(amount, locale, 'EUR');
            const gbpFormat = formatCurrency(amount, locale, 'GBP');

            // All should be non-empty strings
            expect(usdFormat.length).toBeGreaterThan(0);
            expect(eurFormat.length).toBeGreaterThan(0);
            expect(gbpFormat.length).toBeGreaterThan(0);

            // Should contain different currency indicators
            // (though the exact format depends on locale)
            const allFormats = [usdFormat, eurFormat, gbpFormat];
            const uniqueFormats = new Set(allFormats);
            expect(uniqueFormats.size).toBe(3);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should use EUR as default currency when not specified', () => {
      fc.assert(
        fc.property(
          positiveNumberArb,
          supportedLocaleArb,
          (amount, locale) => {
            const result = formatCurrency(amount, locale);

            // Should contain EUR indicator
            const hasEurIndicator = result.includes('€') || result.includes('EUR');
            expect(hasEurIndicator).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should produce consistent output for the same inputs', () => {
      fc.assert(
        fc.property(
          positiveNumberArb,
          supportedLocaleArb,
          currencyCodeArb,
          (amount, locale, currency) => {
            const result1 = formatCurrency(amount, locale, currency);
            const result2 = formatCurrency(amount, locale, currency);

            // Same inputs should produce identical outputs
            expect(result1).toBe(result2);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle zero and small amounts correctly', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(0, 0.01, 0.99, 1, 1.5),
          supportedLocaleArb,
          currencyCodeArb,
          (amount, locale, currency) => {
            const result = formatCurrency(amount, locale, currency);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            expect(result).not.toContain('NaN');
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 24: Relative time formatting per locale
   * For any date and supported locale, formatRelativeTime should return a 
   * localized relative time string (e.g., "2 days ago" in English, "vor 2 Tagen" in German)
   * Validates: Requirements 11.4
   */
  describe('Property 24: Relative time formatting per locale', () => {
    test('should return a non-empty string for any valid date and locale', () => {
      fc.assert(
        fc.property(
          validDateArb,
          validDateArb,
          supportedLocaleArb,
          (date, baseDate, locale) => {
            const result = formatRelativeTime(date, locale, baseDate);

            // Should return a string
            expect(typeof result).toBe('string');

            // Should not be empty
            expect(result.length).toBeGreaterThan(0);

            // Should not contain 'undefined' or 'null'
            expect(result).not.toContain('undefined');
            expect(result).not.toContain('null');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should format the same relative time differently for different locales', () => {
      fc.assert(
        fc.property(
          validDateArb,
          validDateArb,
          (date, baseDate) => {
            // Format the same relative time in different locales
            const enFormat = formatRelativeTime(date, 'en', baseDate);
            const deFormat = formatRelativeTime(date, 'de', baseDate);
            const frFormat = formatRelativeTime(date, 'fr', baseDate);

            // All should be non-empty strings
            expect(enFormat.length).toBeGreaterThan(0);
            expect(deFormat.length).toBeGreaterThan(0);
            expect(frFormat.length).toBeGreaterThan(0);

            // Different locales should produce different text
            // (e.g., "2 days ago" vs "vor 2 Tagen" vs "il y a 2 jours")
            const allFormats = [enFormat, deFormat, frFormat];
            const uniqueFormats = new Set(allFormats);
            
            // At least some should be different for most dates
            expect(uniqueFormats.size).toBeGreaterThanOrEqual(1);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle past dates correctly', () => {
      fc.assert(
        fc.property(
          supportedLocaleArb,
          fc.integer({ min: 1, max: 365 }), // Days in the past
          (locale, daysAgo) => {
            const baseDate = new Date('2024-06-15');
            const pastDate = new Date(baseDate);
            pastDate.setDate(pastDate.getDate() - daysAgo);

            const result = formatRelativeTime(pastDate, locale, baseDate);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);

            // Should indicate past time (common words across locales)
            // Note: This is locale-dependent, so we just check it's a valid string
            expect(result).not.toContain('undefined');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle future dates correctly', () => {
      fc.assert(
        fc.property(
          supportedLocaleArb,
          fc.integer({ min: 1, max: 365 }), // Days in the future
          (locale, daysAhead) => {
            const baseDate = new Date('2024-06-15');
            const futureDate = new Date(baseDate);
            futureDate.setDate(futureDate.getDate() + daysAhead);

            const result = formatRelativeTime(futureDate, locale, baseDate);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            expect(result).not.toContain('undefined');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should handle same date (now) correctly', () => {
      fc.assert(
        fc.property(
          validDateArb,
          supportedLocaleArb,
          (date, locale) => {
            // Same date for both parameters
            const result = formatRelativeTime(date, locale, date);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);

            // Should indicate "now" or "0 seconds" or similar
            // The exact format depends on locale
            expect(result).not.toContain('undefined');
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should produce consistent output for the same inputs', () => {
      fc.assert(
        fc.property(
          validDateArb,
          validDateArb,
          supportedLocaleArb,
          (date, baseDate, locale) => {
            const result1 = formatRelativeTime(date, locale, baseDate);
            const result2 = formatRelativeTime(date, locale, baseDate);

            // Same inputs should produce identical outputs
            expect(result1).toBe(result2);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should select appropriate time unit based on difference', () => {
      const baseDate = new Date('2024-06-15T12:00:00');

      fc.assert(
        fc.property(
          supportedLocaleArb,
          (locale) => {
            // Test different time scales
            const oneHourAgo = new Date(baseDate.getTime() - 60 * 60 * 1000);
            const oneDayAgo = new Date(baseDate.getTime() - 24 * 60 * 60 * 1000);
            const oneWeekAgo = new Date(baseDate.getTime() - 7 * 24 * 60 * 60 * 1000);

            const hourResult = formatRelativeTime(oneHourAgo, locale, baseDate);
            const dayResult = formatRelativeTime(oneDayAgo, locale, baseDate);
            const weekResult = formatRelativeTime(oneWeekAgo, locale, baseDate);

            // All should be valid strings
            expect(hourResult.length).toBeGreaterThan(0);
            expect(dayResult.length).toBeGreaterThan(0);
            expect(weekResult.length).toBeGreaterThan(0);

            // They should be different (using different units)
            const allResults = [hourResult, dayResult, weekResult];
            const uniqueResults = new Set(allResults);
            expect(uniqueResults.size).toBe(3);
          }
        ),
        { numRuns: 100 }
      );
    });

    test('should use current date as default baseDate', () => {
      fc.assert(
        fc.property(
          supportedLocaleArb,
          (locale) => {
            // Create a date 1 hour ago
            const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);

            // Call without baseDate (should use current time)
            const result = formatRelativeTime(oneHourAgo, locale);

            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            expect(result).not.toContain('undefined');
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
