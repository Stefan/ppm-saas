/**
 * Property-Based Tests for Interpolation
 * 
 * These tests verify universal properties that should hold true
 * for interpolation functionality across all inputs.
 */

import fc from 'fast-check';
import { renderHook, act } from '@testing-library/react';
import { I18nProvider, useTranslations } from '../context';
import { loadTranslations } from '../loader';
import React from 'react';

// Mock the loader
jest.mock('../loader', () => ({
  loadTranslations: jest.fn(),
  isLanguageCached: jest.fn().mockReturnValue(false),
}));

const mockLoadTranslations = loadTranslations as jest.MockedFunction<typeof loadTranslations>;

describe('Interpolation Properties', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      clear: jest.fn(),
      removeItem: jest.fn(),
      length: 0,
      key: jest.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
  });

  // Feature: complete-i18n-system, Property 9: Variable interpolation
  // **Validates: Requirements 5.5, 12.1, 12.2**
  describe('Property 9: Variable interpolation', () => {
    it('should replace placeholders with string values', async () => {
      // Setup
      const mockTranslations = {
        greeting: 'Hello {name}!',
        message: 'You have {count} items',
        complex: '{user} sent {item} to {recipient}',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);

      // Render hook
      const { result } = renderHook(() => useTranslations(), {
        wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
      });

      // Wait for loading to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      // Test various interpolations
      const test1 = result.current.t('greeting', { name: 'John' });
      expect(test1).toBe('Hello John!');

      const test2 = result.current.t('greeting', { name: 'Alice' });
      expect(test2).toBe('Hello Alice!');
    });

    it('should replace placeholders with numeric values', async () => {
      // Setup
      const mockTranslations = {
        count: 'Total: {value}',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);

      // Render hook
      const { result } = renderHook(() => useTranslations(), {
        wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
      });

      // Wait for loading to complete
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
      });

      // Test
      const test1 = result.current.t('count', { value: 42 });
      expect(test1).toBe('Total: 42');

      const test2 = result.current.t('count', { value: 0 });
      expect(test2).toBe('Total: 0');
    });

    it('should handle numeric values correctly', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.integer({ min: -10000, max: 10000 }),
          async (count) => {
            // Setup
            const mockTranslations = {
              count: 'You have {count} items',
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for loading
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Verify
            const translated = result.current.t('count', { count });
            expect(translated).toBe(`You have ${count} items`);
            expect(translated).not.toContain('{count}');
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle string values correctly', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 50 }),
          async (name) => {
            // Setup
            const mockTranslations = {
              greeting: 'Hello {name}!',
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for loading
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute
            const translated = result.current.t('greeting', { name });

            // Verify - HTML should be escaped
            const escapedName = name
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#x27;');
            
            expect(translated).toContain(escapedName);
            expect(translated).not.toContain('{name}');
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  // Feature: complete-i18n-system, Property 10: Multiple variable interpolation
  // **Validates: Requirements 12.3**
  describe('Property 10: Multiple variable interpolation', () => {
    it('should replace all placeholders when multiple variables are provided', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 20 }),
          fc.integer({ min: 0, max: 100 }),
          fc.string({ minLength: 1, maxLength: 20 }),
          async (user, count, item) => {
            // Setup
            const mockTranslations = {
              message: '{user} has {count} {item}',
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for loading
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute
            const translated = result.current.t('message', { user, count, item });

            // Verify: All placeholders should be replaced (with HTML escaping)
            const escapedUser = user
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#x27;');
            const escapedItem = item
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#x27;');
            
            expect(translated).toContain(escapedUser);
            expect(translated).toContain(String(count));
            expect(translated).toContain(escapedItem);
            expect(translated).not.toContain('{user}');
            expect(translated).not.toContain('{count}');
            expect(translated).not.toContain('{item}');
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle arbitrary number of variables', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.dictionary(
            fc.string({ minLength: 1, maxLength: 15 }).filter(s => !s.includes('{') && !s.includes('}')),
            fc.oneof(fc.string({ minLength: 1, maxLength: 20 }), fc.integer()),
            { minKeys: 1, maxKeys: 5 }
          ),
          async (params) => {
            // Setup: Create translation with all param keys
            const template = Object.keys(params)
              .map(key => `{${key}}`)
              .join(' ');
            
            const mockTranslations = {
              test: template,
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for loading
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute
            const translated = result.current.t('test', params);

            // Verify: All placeholders should be replaced (with HTML escaping)
            Object.entries(params).forEach(([key, value]) => {
              const escapedValue = String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#x27;');
              
              expect(translated).toContain(escapedValue);
              expect(translated).not.toContain(`{${key}}`);
            });
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  // Feature: complete-i18n-system, Property 11: Missing variable handling
  // **Validates: Requirements 12.4**
  describe('Property 11: Missing variable handling', () => {
    it('should leave placeholder unchanged when variable is not provided', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 20 }).filter(s => !s.includes('{') && !s.includes('}')),
          async (varName) => {
            // Setup
            const mockTranslations = {
              message: `Hello {${varName}}!`,
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for translations to load
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute: Call without params
            const translated = result.current.t('message');

            // Verify: Placeholder should remain
            expect(translated).toContain(`{${varName}}`);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should leave placeholder unchanged when variable is in params but with different name', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 20 }).filter(s => !s.includes('{') && !s.includes('}')),
          fc.string({ minLength: 1, maxLength: 20 }).filter(s => !s.includes('{') && !s.includes('}')),
          fc.string({ minLength: 1, maxLength: 30 }),
          async (expectedVar, providedVar, value) => {
            // Only test when variable names are different
            if (expectedVar === providedVar) return;

            // Setup
            const mockTranslations = {
              message: `Hello {${expectedVar}}!`,
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for translations to load
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute: Provide wrong variable name
            const translated = result.current.t('message', { [providedVar]: value });

            // Verify: Original placeholder should remain
            expect(translated).toContain(`{${expectedVar}}`);
            // The provided value should not appear (unless it happens to be in the template)
            const escapedValue = value
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#x27;');
            // Only check if the escaped value doesn't match parts of the template
            if (!`Hello {${expectedVar}}!`.includes(escapedValue)) {
              expect(translated).not.toContain(escapedValue);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  // Feature: complete-i18n-system, Property 12: HTML escaping for XSS prevention
  // **Validates: Requirements 12.5**
  describe('Property 12: HTML escaping for XSS prevention', () => {
    it('should escape HTML tags in interpolated values', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('<script>', '</script>', '<img>', '<div>', '<a href="">'),
          async (htmlTag) => {
            // Setup
            const mockTranslations = {
              message: 'Content: {content}',
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for translations to load
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute
            const translated = result.current.t('message', { content: htmlTag });

            // Verify: HTML should be escaped
            expect(translated).not.toContain('<');
            expect(translated).not.toContain('>');
            expect(translated).toContain('&lt;');
            expect(translated).toContain('&gt;');
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should escape all HTML special characters', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.string({ minLength: 1, maxLength: 50 }),
          async (input) => {
            // Setup
            const mockTranslations = {
              message: 'Value: {value}',
            };

            mockLoadTranslations.mockResolvedValue(mockTranslations);

            // Render hook
            const { result } = renderHook(() => useTranslations(), {
              wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
            });

            // Wait for translations to load
            await act(async () => {
              await new Promise(resolve => setTimeout(resolve, 50));
            });

            // Execute
            const translated = result.current.t('message', { value: input });

            // Verify: Special characters should be escaped
            if (input.includes('<')) {
              expect(translated).toContain('&lt;');
              expect(translated).not.toContain('<');
            }
            if (input.includes('>')) {
              expect(translated).toContain('&gt;');
              expect(translated).not.toContain('>');
            }
            if (input.includes('&') && !input.includes('&lt;') && !input.includes('&gt;')) {
              expect(translated).toContain('&amp;');
            }
            if (input.includes('"')) {
              expect(translated).toContain('&quot;');
            }
            if (input.includes("'")) {
              expect(translated).toContain('&#x27;');
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should prevent XSS attacks with script injection attempts', async () => {
      const xssAttempts = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror="alert(1)">',
        '<svg onload="alert(1)">',
        'javascript:alert(1)',
        '<iframe src="javascript:alert(1)">',
      ];

      for (const xss of xssAttempts) {
        // Setup
        const mockTranslations = {
          message: 'User input: {input}',
        };

        mockLoadTranslations.mockResolvedValue(mockTranslations);

        // Render hook
        const { result } = renderHook(() => useTranslations(), {
          wrapper: ({ children }) => <I18nProvider>{children}</I18nProvider>,
        });

        // Wait for translations to load
        await act(async () => {
          await new Promise(resolve => setTimeout(resolve, 50));
        });

        // Execute
        const translated = result.current.t('message', { input: xss });

        // Verify: Should not contain executable HTML (tags should be escaped)
        expect(translated).not.toContain('<script');
        expect(translated).not.toContain('<img');
        expect(translated).not.toContain('<svg');
        expect(translated).not.toContain('<iframe');
        // Check that angle brackets are escaped
        if (xss.includes('<')) {
          expect(translated).toContain('&lt;');
        }
        if (xss.includes('>')) {
          expect(translated).toContain('&gt;');
        }
      }
    });
  });
});
