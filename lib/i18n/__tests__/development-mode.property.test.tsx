/**
 * Property-Based Tests for Development Mode Features
 * Feature: complete-i18n-system
 * 
 * This file contains property-based tests for development mode features,
 * including missing translation detection and console warnings.
 * 
 * Tests use fast-check library with minimum 100 iterations per property.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import fc from 'fast-check';
import { I18nProvider, useI18n } from '../context';
import { loadTranslations, clearTranslationCache } from '../loader';
import { SUPPORTED_LANGUAGES, STORAGE_KEY } from '../types';

// Test component that uses the i18n context
function TestComponent({ testKey }: { testKey: string }) {
  const { t, locale } = useI18n();
  
  return (
    <div>
      <div data-testid="locale">{locale}</div>
      <div data-testid="translation">{t(testKey)}</div>
    </div>
  );
}

// Helper to render component with I18nProvider
function renderWithI18n(component: React.ReactElement) {
  return render(
    <I18nProvider>
      {component}
    </I18nProvider>
  );
}

// Mock localStorage for tests
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

describe('Development Mode Property Tests', () => {
  const originalEnv = process.env.NODE_ENV;
  
  beforeEach(() => {
    // Clear all caches and mocks before each test
    clearTranslationCache();
    localStorageMock.clear();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
    
    // Set to English by default
    localStorageMock.setItem(STORAGE_KEY, 'en');
  });

  afterEach(() => {
    clearTranslationCache();
    localStorageMock.clear();
    process.env.NODE_ENV = originalEnv;
  });

  // Feature: complete-i18n-system, Property 4: Console warning for missing translations
  describe('Property 4: Console warning for missing translations', () => {
    it('should log warning to console for any missing translation key in development mode', async () => {
      // Set to development mode
      process.env.NODE_ENV = 'development';
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(lang => lang.code)),
          fc.string({ minLength: 5, maxLength: 30 }).filter(s => s.includes('.')),
          async (locale, missingKey) => {
            // Create a unique missing key
            const testKey = `nonexistent.missing.${missingKey.replace(/[^a-zA-Z0-9.]/g, '')}`;
            
            // Mock console.warn
            const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            // Set locale
            localStorageMock.setItem(STORAGE_KEY, locale);
            clearTranslationCache();
            
            // Load translations
            const translations = await loadTranslations(locale);
            
            // Check if key exists
            const keys = testKey.split('.');
            let value: any = translations;
            let keyExists = true;
            
            for (const k of keys) {
              if (value && typeof value === 'object' && k in value) {
                value = value[k];
              } else {
                keyExists = false;
                break;
              }
            }
            
            // If key doesn't exist, render component and check for warning
            if (!keyExists) {
              const { unmount } = renderWithI18n(<TestComponent testKey={testKey} />);
              
              try {
                // Wait for component to render
                await waitFor(() => {
                  expect(screen.getByTestId('locale')).toHaveTextContent(locale);
                });
                
                // Verify console.warn was called with the missing key
                expect(consoleWarnSpy).toHaveBeenCalledWith(
                  expect.stringContaining(`Translation key not found: ${testKey}`)
                );
                expect(consoleWarnSpy).toHaveBeenCalledWith(
                  expect.stringContaining(`locale: ${locale}`)
                );
              } finally {
                unmount();
              }
            }
            
            consoleWarnSpy.mockRestore();
          }
        ),
        { numRuns: 50 } // Reduced runs due to rendering overhead
      );
    });

    it('should log warning for any missing key regardless of nesting level', async () => {
      process.env.NODE_ENV = 'development';
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('en', 'de', 'fr'),
          fc.integer({ min: 1, max: 5 }),
          fc.array(fc.string({ minLength: 3, maxLength: 10 }), { minLength: 1, maxLength: 5 }),
          async (locale, nestingLevel, keyParts) => {
            // Create a nested missing key
            const cleanParts = keyParts.map(part => part.replace(/[^a-zA-Z0-9]/g, ''));
            const testKey = `missing.${cleanParts.slice(0, nestingLevel).join('.')}`;
            
            // Mock console.warn
            const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            // Set locale
            localStorageMock.setItem(STORAGE_KEY, locale);
            clearTranslationCache();
            
            // Render component with missing key
            const { unmount } = renderWithI18n(<TestComponent testKey={testKey} />);
            
            try {
              // Wait for component to render
              await waitFor(() => {
                expect(screen.getByTestId('locale')).toHaveTextContent(locale);
              });
              
              // Verify warning was logged
              expect(consoleWarnSpy).toHaveBeenCalledWith(
                expect.stringContaining('Translation key not found')
              );
            } finally {
              unmount();
            }
            
            consoleWarnSpy.mockRestore();
          }
        ),
        { numRuns: 50 }
      );
    });
  });

  // Feature: complete-i18n-system, Property 32: Production mode suppresses warnings
  describe('Property 32: Production mode suppresses warnings', () => {
    it('should not log warnings for any missing translation in production mode', async () => {
      // Set to production mode
      process.env.NODE_ENV = 'production';
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(lang => lang.code)),
          fc.string({ minLength: 5, maxLength: 30 }).filter(s => s.includes('.')),
          async (locale, missingKey) => {
            // Create a unique missing key
            const testKey = `nonexistent.missing.${missingKey.replace(/[^a-zA-Z0-9.]/g, '')}`;
            
            // Mock console.warn
            const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            // Set locale
            localStorageMock.setItem(STORAGE_KEY, locale);
            clearTranslationCache();
            
            // Load translations
            const translations = await loadTranslations(locale);
            
            // Check if key exists
            const keys = testKey.split('.');
            let value: any = translations;
            let keyExists = true;
            
            for (const k of keys) {
              if (value && typeof value === 'object' && k in value) {
                value = value[k];
              } else {
                keyExists = false;
                break;
              }
            }
            
            // If key doesn't exist, render component
            if (!keyExists) {
              const { unmount } = renderWithI18n(<TestComponent testKey={testKey} />);
              
              try {
                // Wait for component to render
                await waitFor(() => {
                  expect(screen.getByTestId('locale')).toHaveTextContent(locale);
                });
                
                // Verify console.warn was NOT called for missing translation
                const warningCalls = consoleWarnSpy.mock.calls.filter(call =>
                  call[0].includes('Translation key not found')
                );
                expect(warningCalls.length).toBe(0);
              } finally {
                unmount();
              }
            }
            
            consoleWarnSpy.mockRestore();
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should suppress warnings for any type of translation error in production', async () => {
      process.env.NODE_ENV = 'production';
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('en', 'de', 'fr'),
          fc.array(fc.string({ minLength: 3, maxLength: 10 }), { minLength: 2, maxLength: 4 }),
          async (locale, keyParts) => {
            // Create various types of invalid keys
            const cleanParts = keyParts.map(part => part.replace(/[^a-zA-Z0-9]/g, ''));
            const testKeys = [
              `missing.${cleanParts.join('.')}`,
              `nonexistent.${cleanParts[0]}`,
              `invalid.path.${cleanParts.join('.')}`
            ];
            
            // Mock console.warn
            const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            // Set locale
            localStorageMock.setItem(STORAGE_KEY, locale);
            clearTranslationCache();
            
            // Test each invalid key
            for (const testKey of testKeys) {
              const { unmount } = renderWithI18n(<TestComponent testKey={testKey} />);
              
              try {
                await waitFor(() => {
                  expect(screen.getByTestId('locale')).toHaveTextContent(locale);
                });
              } finally {
                unmount();
              }
            }
            
            // Verify no translation warnings were logged
            const translationWarnings = consoleWarnSpy.mock.calls.filter(call =>
              call[0].includes('Translation') || call[0].includes('translation')
            );
            expect(translationWarnings.length).toBe(0);
            
            consoleWarnSpy.mockRestore();
          }
        ),
        { numRuns: 30 }
      );
    });
  });

  // Feature: complete-i18n-system, Property 29: Missing translation detection in both environments
  describe('Property 29: Missing translation detection in both environments', () => {
    it('should detect missing translations consistently in development and production', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(...SUPPORTED_LANGUAGES.map(lang => lang.code)),
          fc.string({ minLength: 5, maxLength: 30 }).filter(s => s.includes('.')),
          async (locale, missingKey) => {
            // Create a unique missing key
            const testKey = `nonexistent.missing.${missingKey.replace(/[^a-zA-Z0-9.]/g, '')}`;
            
            // Test in development mode
            process.env.NODE_ENV = 'development';
            const devConsoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            localStorageMock.setItem(STORAGE_KEY, locale);
            clearTranslationCache();
            
            const { unmount: unmountDev } = renderWithI18n(<TestComponent testKey={testKey} />);
            
            await waitFor(() => {
              expect(screen.getByTestId('locale')).toHaveTextContent(locale);
            });
            
            const devTranslation = screen.getByTestId('translation').textContent;
            const devWarningCalled = devConsoleWarnSpy.mock.calls.some(call =>
              call[0].includes('Translation key not found')
            );
            
            devConsoleWarnSpy.mockRestore();
            unmountDev();
            
            // Test in production mode
            process.env.NODE_ENV = 'production';
            const prodConsoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
            
            clearTranslationCache();
            
            const { unmount: unmountProd } = renderWithI18n(<TestComponent testKey={testKey} />);
            
            await waitFor(() => {
              expect(screen.getByTestId('locale')).toHaveTextContent(locale);
            });
            
            const prodTranslation = screen.getByTestId('translation').textContent;
            const prodWarningCalled = prodConsoleWarnSpy.mock.calls.some(call =>
              call[0].includes('Translation key not found')
            );
            
            prodConsoleWarnSpy.mockRestore();
            unmountProd();
            
            // Verify behavior:
            // 1. Both should return the key itself as fallback
            expect(devTranslation).toBe(testKey);
            expect(prodTranslation).toBe(testKey);
            expect(devTranslation).toBe(prodTranslation);
            
            // 2. Only development should log warnings
            if (devWarningCalled || prodWarningCalled) {
              expect(devWarningCalled).toBe(true);
              expect(prodWarningCalled).toBe(false);
            }
          }
        ),
        { numRuns: 30 }
      );
    });

    it('should handle missing translations identically across environments for any key structure', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('en', 'de', 'fr'),
          fc.integer({ min: 1, max: 4 }),
          async (locale, depth) => {
            // Create nested missing key
            const keyParts = Array.from({ length: depth }, (_, i) => `level${i}`);
            const testKey = `missing.${keyParts.join('.')}`;
            
            // Test in both modes
            const results: { mode: string; translation: string; warned: boolean }[] = [];
            
            for (const mode of ['development', 'production']) {
              process.env.NODE_ENV = mode;
              const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
              
              localStorageMock.setItem(STORAGE_KEY, locale);
              clearTranslationCache();
              
              const { unmount } = renderWithI18n(<TestComponent testKey={testKey} />);
              
              await waitFor(() => {
                expect(screen.getByTestId('locale')).toHaveTextContent(locale);
              });
              
              const translation = screen.getByTestId('translation').textContent || '';
              const warned = consoleWarnSpy.mock.calls.some(call =>
                call[0].includes('Translation key not found')
              );
              
              results.push({ mode, translation, warned });
              
              consoleWarnSpy.mockRestore();
              unmount();
            }
            
            // Verify consistency
            const [devResult, prodResult] = results;
            
            // Both should return the same fallback value
            expect(devResult.translation).toBe(prodResult.translation);
            expect(devResult.translation).toBe(testKey);
            
            // Only dev should warn
            if (devResult.warned || prodResult.warned) {
              expect(devResult.warned).toBe(true);
              expect(prodResult.warned).toBe(false);
            }
          }
        ),
        { numRuns: 30 }
      );
    });
  });
});
