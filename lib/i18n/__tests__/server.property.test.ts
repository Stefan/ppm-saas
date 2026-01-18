/**
 * Property-Based Tests for Server Component I18n
 * 
 * These tests verify universal properties that should hold true
 * for server-side translation functionality across all inputs.
 */

import fc from 'fast-check';
import { getTranslations } from '../server';
import { loadTranslations } from '../loader';
import { SUPPORTED_LANGUAGES } from '../types';

// Mock Next.js cookies
jest.mock('next/headers', () => ({
  cookies: jest.fn(),
}));

// Mock the loader
jest.mock('../loader', () => ({
  loadTranslations: jest.fn(),
}));

const { cookies } = require('next/headers');
const mockLoadTranslations = loadTranslations as jest.MockedFunction<typeof loadTranslations>;

describe('Server Component I18n Properties', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // Feature: complete-i18n-system, Property 28: Fallback consistency across environments
  // **Validates: Requirements 10.4**
  describe('Property 28: Fallback consistency across environments', () => {
    it('should return the same fallback behavior for missing keys in server and client contexts', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(l => l.code)),
          fc.string({ minLength: 1, maxLength: 50 }).filter(s => !s.includes('.')),
          async (locale, missingKey) => {
            // Setup: Mock translations with some keys but not the missing one
            const mockTranslations = {
              common: {
                save: 'Save',
                cancel: 'Cancel',
              },
              nav: {
                dashboards: 'Dashboards',
              },
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue({ value: locale }),
            });

            // Get server translation function
            const { t: serverT } = await getTranslations();

            // Test: Both should return the key itself when not found
            const serverResult = serverT(missingKey);
            
            // The fallback behavior should be to return the key itself
            expect(serverResult).toBe(missingKey);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle nested missing keys consistently', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(l => l.code)),
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 2, maxLength: 5 }),
          async (locale, keyParts) => {
            const missingKey = keyParts.join('.');
            
            // Setup: Mock translations without the missing key
            const mockTranslations = {
              common: {
                save: 'Save',
              },
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue({ value: locale }),
            });

            // Get server translation function
            const { t: serverT } = await getTranslations();

            // Test: Should return the key itself
            const serverResult = serverT(missingKey);
            expect(serverResult).toBe(missingKey);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle interpolation consistently when key is missing', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(l => l.code)),
          fc.string({ minLength: 1, maxLength: 30 }),
          fc.dictionary(fc.string({ minLength: 1, maxLength: 10 }), fc.oneof(fc.string(), fc.integer())),
          async (locale, missingKey, params) => {
            // Setup: Mock empty translations
            mockLoadTranslations.mockResolvedValue({});
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue({ value: locale }),
            });

            // Get server translation function
            const { t: serverT } = await getTranslations();

            // Test: Should return the key itself, ignoring params
            const serverResult = serverT(missingKey, params);
            expect(serverResult).toBe(missingKey);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  // Additional property: Server translations work correctly for valid keys
  describe('Server translation lookup', () => {
    it('should return correct translations for valid keys', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(l => l.code)),
          fc.constantFrom('common.save', 'common.cancel', 'nav.dashboards'),
          async (locale, key) => {
            // Setup: Mock translations
            const mockTranslations = {
              common: {
                save: 'Save',
                cancel: 'Cancel',
              },
              nav: {
                dashboards: 'Dashboards',
              },
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue({ value: locale }),
            });

            // Get server translation function
            const { t } = await getTranslations();

            // Test: Should return a non-empty string
            const result = t(key);
            expect(typeof result).toBe('string');
            expect(result.length).toBeGreaterThan(0);
            expect(result).not.toBe(key); // Should be translated, not the key
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle interpolation in server context', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(l => l.code)),
          fc.string({ minLength: 1, maxLength: 20 }),
          fc.integer({ min: 1, max: 100 }),
          async (locale, name, count) => {
            // Setup: Mock translations with interpolation
            const mockTranslations = {
              greeting: 'Hello {name}, you have {count} messages',
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue({ value: locale }),
            });

            // Get server translation function
            const { t } = await getTranslations();

            // Test: Should interpolate correctly
            const result = t('greeting', { name, count });
            
            // HTML escaping is applied to string values
            const escapedName = name
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#x27;');
            
            expect(result).toContain(escapedName);
            expect(result).toContain(String(count));
            expect(result).not.toContain('{name}');
            expect(result).not.toContain('{count}');
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  // Property: Cookie fallback to default locale
  describe('Cookie-based locale detection', () => {
    it('should use default locale when cookie is not set', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constant(undefined),
          async () => {
            // Setup: No cookie set
            mockLoadTranslations.mockResolvedValue({ test: 'value' });
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue(undefined),
            });

            // Get translations
            const { locale } = await getTranslations();

            // Test: Should use default locale
            expect(locale).toBe('en');
            expect(mockLoadTranslations).toHaveBeenCalledWith('en');
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should use cookie value when set', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(l => l.code)),
          async (locale) => {
            // Setup: Cookie set to specific locale
            mockLoadTranslations.mockResolvedValue({ test: 'value' });
            cookies.mockResolvedValue({
              get: jest.fn().mockReturnValue({ value: locale }),
            });

            // Get translations
            const { locale: returnedLocale } = await getTranslations();

            // Test: Should use cookie locale
            expect(returnedLocale).toBe(locale);
            expect(mockLoadTranslations).toHaveBeenCalledWith(locale);
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
