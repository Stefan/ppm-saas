/**
 * Unit Tests for Server Component I18n
 * 
 * These tests verify specific examples and edge cases for server-side
 * translation functionality.
 */

import { getTranslations } from '../server';
import { loadTranslations } from '../loader';

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

describe('Server Component Translations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getTranslations', () => {
    it('should return translation function and locale', async () => {
      // Setup
      const mockTranslations = {
        common: {
          save: 'Save',
          cancel: 'Cancel',
        },
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const result = await getTranslations();

      // Verify
      expect(result).toHaveProperty('t');
      expect(result).toHaveProperty('locale');
      expect(typeof result.t).toBe('function');
      expect(result.locale).toBe('en');
    });

    it('should translate simple keys correctly', async () => {
      // Setup
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
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify
      expect(t('common.save')).toBe('Save');
      expect(t('common.cancel')).toBe('Cancel');
      expect(t('nav.dashboards')).toBe('Dashboards');
    });

    it('should handle missing keys by returning the key itself', async () => {
      // Setup
      const mockTranslations = {
        common: {
          save: 'Save',
        },
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify
      expect(t('missing.key')).toBe('missing.key');
      expect(t('common.missing')).toBe('common.missing');
    });

    it('should handle interpolation correctly', async () => {
      // Setup
      const mockTranslations = {
        greeting: 'Hello {name}!',
        message: 'You have {count} new messages',
        complex: '{user} sent {count} files to {recipient}',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify
      expect(t('greeting', { name: 'John' })).toBe('Hello John!');
      expect(t('message', { count: 5 })).toBe('You have 5 new messages');
      expect(t('complex', { user: 'Alice', count: 3, recipient: 'Bob' }))
        .toBe('Alice sent 3 files to Bob');
    });

    it('should handle missing interpolation parameters', async () => {
      // Setup
      const mockTranslations = {
        greeting: 'Hello {name}!',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify - placeholder should remain unchanged
      expect(t('greeting', {})).toBe('Hello {name}!');
      expect(t('greeting')).toBe('Hello {name}!');
    });

    it('should use default locale when cookie is not set', async () => {
      // Setup
      const mockTranslations = {
        test: 'Test value',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue(undefined),
      });

      // Execute
      const { locale } = await getTranslations();

      // Verify
      expect(locale).toBe('en');
      expect(mockLoadTranslations).toHaveBeenCalledWith('en');
    });

    it('should use locale from cookie when set', async () => {
      // Setup
      const mockTranslations = {
        test: 'Testwert',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'de' }),
      });

      // Execute
      const { locale } = await getTranslations();

      // Verify
      expect(locale).toBe('de');
      expect(mockLoadTranslations).toHaveBeenCalledWith('de');
    });

    it('should handle deeply nested keys', async () => {
      // Setup
      const mockTranslations = {
        level1: {
          level2: {
            level3: {
              level4: 'Deep value',
            },
          },
        },
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify
      expect(t('level1.level2.level3.level4')).toBe('Deep value');
    });

    it('should handle non-string values by returning the key', async () => {
      // Setup
      const mockTranslations = {
        invalid: {
          object: { nested: 'value' },
        },
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify - should return key when value is not a string
      expect(t('invalid.object')).toBe('invalid.object');
    });

    it('should handle empty translation dictionary', async () => {
      // Setup
      mockLoadTranslations.mockResolvedValue({});
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify
      expect(t('any.key')).toBe('any.key');
    });

    it('should handle multiple interpolations of the same variable', async () => {
      // Setup
      const mockTranslations = {
        repeat: '{name} said hello to {name}',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify - both occurrences should be replaced
      expect(t('repeat', { name: 'Alice' })).toBe('Alice said hello to Alice');
    });

    it('should convert numeric interpolation values to strings', async () => {
      // Setup
      const mockTranslations = {
        count: 'Total: {value}',
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Execute
      const { t } = await getTranslations();

      // Verify
      expect(t('count', { value: 42 })).toBe('Total: 42');
      expect(t('count', { value: 0 })).toBe('Total: 0');
      expect(t('count', { value: -10 })).toBe('Total: -10');
    });
  });

  describe('Server Component Context', () => {
    it('should work in async server component context', async () => {
      // This test simulates usage in a Server Component
      const mockTranslations = {
        dashboard: {
          title: 'Dashboard',
          subtitle: 'Welcome back',
        },
      };

      mockLoadTranslations.mockResolvedValue(mockTranslations);
      cookies.mockResolvedValue({
        get: jest.fn().mockReturnValue({ value: 'en' }),
      });

      // Simulate Server Component usage
      const ServerComponent = async () => {
        const { t, locale } = await getTranslations();
        return {
          title: t('dashboard.title'),
          subtitle: t('dashboard.subtitle'),
          locale,
        };
      };

      // Execute
      const result = await ServerComponent();

      // Verify
      expect(result.title).toBe('Dashboard');
      expect(result.subtitle).toBe('Welcome back');
      expect(result.locale).toBe('en');
    });
  });
});
