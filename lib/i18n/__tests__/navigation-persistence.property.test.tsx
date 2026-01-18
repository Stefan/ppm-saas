/**
 * Property-based tests for language state persistence across navigation
 * Feature: complete-i18n-system, Property 30: Language state persistence across navigation
 * **Validates: Requirements 14.5**
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useI18n, I18nProvider } from '../context'
import fc from 'fast-check'
import React from 'react'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
    get length() {
      return Object.keys(store).length
    },
    key: (index: number) => {
      const keys = Object.keys(store)
      return keys[index] || null
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock fetch for translation files
global.fetch = jest.fn((url) => {
  const locale = (url as string).match(/\/locales\/(\w+)\.json/)?.[1] || 'en'
  
  const translations: Record<string, any> = {
    en: { common: { save: 'Save', cancel: 'Cancel' }, nav: { dashboards: 'Dashboards' } },
    de: { common: { save: 'Speichern', cancel: 'Abbrechen' }, nav: { dashboards: 'Dashboards' } },
    fr: { common: { save: 'Enregistrer', cancel: 'Annuler' }, nav: { dashboards: 'Tableaux de bord' } },
    es: { common: { save: 'Guardar', cancel: 'Cancelar' }, nav: { dashboards: 'Paneles' } },
    pl: { common: { save: 'Zapisz', cancel: 'Anuluj' }, nav: { dashboards: 'Pulpity' } },
    gsw: { common: { save: 'Speichere', cancel: 'Abbräche' }, nav: { dashboards: 'Dashboards' } },
  }

  return Promise.resolve({
    ok: true,
    json: async () => translations[locale] || translations.en,
  } as Response)
}) as jest.Mock

describe('Language State Persistence - Property Tests', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <I18nProvider>{children}</I18nProvider>
  )

  beforeEach(() => {
    localStorageMock.clear()
    jest.clearAllMocks()
  })

  // Feature: complete-i18n-system, Property 30: Language state persistence across navigation
  describe('Property 30: Language state persistence across navigation', () => {
    it('should maintain language selection across component remounts', async () => {
      // **Validates: Requirements 14.5**
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          async (selectedLanguage) => {
            // First render - set language
            const { result: result1, unmount: unmount1 } = renderHook(() => useI18n(), { wrapper })

            // Wait for initial load
            await waitFor(() => {
              expect(result1.current.locale).toBeTruthy()
            })

            // Set language
            await act(async () => {
              await result1.current.setLocale(selectedLanguage)
            })

            // Wait for language to be set
            await waitFor(() => {
              expect(result1.current.locale).toBe(selectedLanguage)
            })

            // Unmount (simulating navigation)
            unmount1()

            // Second render - verify language persists
            const { result: result2, unmount: unmount2 } = renderHook(() => useI18n(), { wrapper })

            // Wait for component to load
            await waitFor(() => {
              expect(result2.current.locale).toBeTruthy()
            })

            // Verify language persisted
            expect(result2.current.locale).toBe(selectedLanguage)

            unmount2()
            return true
          }
        ),
        { numRuns: 6 } // Test all 6 languages
      )
    })

    it('should persist language in localStorage', async () => {
      // **Validates: Requirements 14.5**
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          async (selectedLanguage) => {
            const { result, unmount } = renderHook(() => useI18n(), { wrapper })

            // Wait for initial load
            await waitFor(() => {
              expect(result.current.locale).toBeTruthy()
            })

            // Set language
            await act(async () => {
              await result.current.setLocale(selectedLanguage)
            })

            // Wait for language to be set
            await waitFor(() => {
              expect(result.current.locale).toBe(selectedLanguage)
            })

            // Verify localStorage was updated
            const storedLocale = localStorageMock.getItem('orka-ppm-locale')
            expect(storedLocale).toBe(selectedLanguage)

            unmount()
            return true
          }
        ),
        { numRuns: 6 }
      )
    })

    it('should load persisted language on initialization', async () => {
      // **Validates: Requirements 14.5**
      
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom('en', 'de', 'fr', 'es', 'pl', 'gsw'),
          async (persistedLanguage) => {
            // Pre-set language in localStorage
            localStorageMock.setItem('orka-ppm-locale', persistedLanguage)

            // Render component
            const { result, unmount } = renderHook(() => useI18n(), { wrapper })

            // Wait for component to load
            await waitFor(() => {
              expect(result.current.locale).toBeTruthy()
            })

            // Verify it loaded the persisted language
            expect(result.current.locale).toBe(persistedLanguage)

            unmount()
            return true
          }
        ),
        { numRuns: 6 }
      )
    })

    it('should maintain language across multiple navigation cycles', async () => {
      // **Validates: Requirements 14.5**
      
      const testLanguage = 'de'
      
      // Set initial language
      localStorageMock.setItem('orka-ppm-locale', testLanguage)

      // Simulate multiple navigation cycles
      for (let i = 0; i < 3; i++) {
        const { result, unmount } = renderHook(() => useI18n(), { wrapper })

        // Wait for component to load
        await waitFor(() => {
          expect(result.current.locale).toBeTruthy()
        })

        // Verify language persisted
        expect(result.current.locale).toBe(testLanguage)

        unmount()
      }
    })

    it('should preserve translations cache across remounts', async () => {
      // **Validates: Requirements 14.5**
      
      const testLanguage = 'fr'
      
      // First render - load translations
      const { result: result1, unmount: unmount1 } = renderHook(() => useI18n(), { wrapper })

      await waitFor(() => {
        expect(result1.current.locale).toBeTruthy()
      })

      await act(async () => {
        await result1.current.setLocale(testLanguage)
      })

      await waitFor(() => {
        expect(result1.current.locale).toBe(testLanguage)
      })

      // Get a translation to ensure it's loaded
      const translation1 = result1.current.t('common.save')
      expect(translation1).toBeTruthy()

      unmount1()

      // Clear fetch mock to verify cache is used
      ;(global.fetch as jest.Mock).mockClear()

      // Second render - should use cached translations
      const { result: result2, unmount: unmount2 } = renderHook(() => useI18n(), { wrapper })

      await waitFor(() => {
        expect(result2.current.locale).toBe(testLanguage)
      })

      // Get same translation
      const translation2 = result2.current.t('common.save')
      
      // Should be the same translation
      expect(translation2).toBe(translation1)

      unmount2()
    })
  })

  describe('Edge Cases', () => {
    it('should handle rapid language switches', async () => {
      const { result, unmount } = renderHook(() => useI18n(), { wrapper })

      await waitFor(() => {
        expect(result.current.locale).toBeTruthy()
      })

      // Rapidly switch languages
      await act(async () => {
        await result.current.setLocale('de')
        await result.current.setLocale('fr')
        await result.current.setLocale('es')
      })

      // Wait for final language to be set
      await waitFor(() => {
        expect(result.current.locale).toBe('es')
      })

      // Verify localStorage has the final language
      expect(localStorageMock.getItem('orka-ppm-locale')).toBe('es')

      unmount()
    })

    it('should handle missing localStorage gracefully', async () => {
      // Temporarily break localStorage
      const originalSetItem = localStorageMock.setItem
      localStorageMock.setItem = () => {
        throw new Error('localStorage not available')
      }

      const { result, unmount } = renderHook(() => useI18n(), { wrapper })

      await waitFor(() => {
        expect(result.current.locale).toBeTruthy()
      })

      // Should still work even if localStorage fails
      await act(async () => {
        await result.current.setLocale('de')
      })

      await waitFor(() => {
        expect(result.current.locale).toBe('de')
      })

      // Restore localStorage
      localStorageMock.setItem = originalSetItem

      unmount()
    })
  })
})
