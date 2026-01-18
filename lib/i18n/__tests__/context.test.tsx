/**
 * Unit tests for I18n Context
 * 
 * Tests the I18nProvider, useI18n, and useTranslations hooks
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { ReactNode } from 'react';
import { I18nProvider, useI18n, useTranslations } from '../context';
import { loadTranslations, clearTranslationCache } from '../loader';

// Mock the loader module
jest.mock('../loader', () => ({
  loadTranslations: jest.fn(),
  isLanguageCached: jest.fn(),
  clearTranslationCache: jest.fn(),
}));

const mockLoadTranslations = loadTranslations as jest.MockedFunction<typeof loadTranslations>;
const mockIsLanguageCached = require('../loader').isLanguageCached as jest.Mock;

// Mock localStorage
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

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock navigator.language
Object.defineProperty(window.navigator, 'language', {
  writable: true,
  value: 'en-US',
});

describe('I18nContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear();
    
    // Default mock implementation
    mockLoadTranslations.mockResolvedValue({
      nav: {
        dashboards: 'Dashboards',
        scenarios: 'Scenarios',
      },
      common: {
        save: 'Save',
        cancel: 'Cancel',
      },
    });
    
    mockIsLanguageCached.mockReturnValue(false);
  });

  describe('I18nProvider', () => {
    it('should provide i18n context to children', async () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en');
      expect(result.current.translations).toBeDefined();
      expect(typeof result.current.t).toBe('function');
      expect(typeof result.current.setLocale).toBe('function');
    });

    it('should detect browser language on first load', async () => {
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        value: 'de-DE',
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('de');
      expect(mockLoadTranslations).toHaveBeenCalledWith('de');
    });

    it('should use saved locale from localStorage', async () => {
      localStorageMock.setItem('orka-ppm-locale', 'fr');

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('fr');
      expect(mockLoadTranslations).toHaveBeenCalledWith('fr');
    });

    it('should load translations on mount', async () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(mockLoadTranslations).toHaveBeenCalled();
      });
    });
  });

  describe('useI18n hook', () => {
    it('should throw error when used outside provider', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      expect(() => {
        renderHook(() => useI18n());
      }).toThrow('useI18n must be used within I18nProvider');

      consoleSpy.mockRestore();
    });

    it('should return i18n context value', async () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current).toHaveProperty('locale');
      expect(result.current).toHaveProperty('translations');
      expect(result.current).toHaveProperty('isLoading');
      expect(result.current).toHaveProperty('setLocale');
      expect(result.current).toHaveProperty('t');
    });
  });

  describe('useTranslations hook', () => {
    it('should return translation function and metadata', async () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useTranslations(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current).toHaveProperty('t');
      expect(result.current).toHaveProperty('locale');
      expect(result.current).toHaveProperty('isLoading');
      expect(typeof result.current.t).toBe('function');
    });
  });

  describe('setLocale function', () => {
    it('should change locale and save to localStorage', async () => {
      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.setLocale('de');
      });

      await waitFor(() => {
        expect(result.current.locale).toBe('de');
      });

      expect(localStorageMock.getItem('orka-ppm-locale')).toBe('de');
    });

    it('should warn for unsupported locale', async () => {
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.setLocale('invalid');
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Unsupported locale: invalid')
      );

      consoleSpy.mockRestore();
    });

    it('should load translations for new locale', async () => {
      mockLoadTranslations.mockResolvedValueOnce({
        nav: { dashboards: 'Dashboards' },
      });

      mockLoadTranslations.mockResolvedValueOnce({
        nav: { dashboards: 'Armaturenbretter' },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.setLocale('de');
      });

      await waitFor(() => {
        expect(mockLoadTranslations).toHaveBeenCalledWith('de');
      });
    });
  });

  describe('t function', () => {
    it('should translate simple keys', async () => {
      // Reset and set fresh mock
      mockLoadTranslations.mockReset();
      mockLoadTranslations.mockResolvedValue({
        nav: {
          dashboards: 'Dashboards',
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('nav.dashboards')).toBe('Dashboards');
    });

    it('should return key for missing translations', async () => {
      mockLoadTranslations.mockResolvedValue({
        nav: {
          dashboards: 'Dashboards',
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('nav.missing')).toBe('nav.missing');
    });

    it('should handle interpolation', async () => {
      mockLoadTranslations.mockResolvedValue({
        validation: {
          minLength: 'Minimum length is {min} characters',
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('validation.minLength', { min: 5 })).toBe(
        'Minimum length is 5 characters'
      );
    });

    it('should handle multiple interpolation parameters', async () => {
      mockLoadTranslations.mockResolvedValue({
        message: {
          greeting: 'Hello {name}, you have {count} messages',
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(
        result.current.t('message.greeting', { name: 'John', count: 5 })
      ).toBe('Hello John, you have 5 messages');
    });

    it('should handle nested keys', async () => {
      mockLoadTranslations.mockResolvedValue({
        dashboard: {
          stats: {
            total: 'Total Projects',
          },
        },
      });

      const wrapper = ({ children }: { children: ReactNode }) => (
        <I18nProvider>{children}</I18nProvider>
      );

      const { result } = renderHook(() => useI18n(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('dashboard.stats.total')).toBe('Total Projects');
    });
  });
});
