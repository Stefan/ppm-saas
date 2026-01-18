/**
 * TypeScript type definitions for the i18n system
 * 
 * This file defines the core types used throughout the internationalization system,
 * including translation dictionaries, supported locales, and function signatures.
 */

// Import auto-generated translation keys
import type { TranslationKey as GeneratedTranslationKey } from './translation-keys';

/**
 * Translation dictionary structure
 * Nested object with string leaf values
 */
export type TranslationDictionary = {
  [key: string]: string | TranslationDictionary;
};

/**
 * Supported language codes
 * ISO 639-1 two-letter codes (en, de, fr, es, pl) and ISO 639-3 code (gsw)
 */
export type SupportedLocale = 'en' | 'de' | 'fr' | 'es' | 'pl' | 'gsw';

/**
 * Translation key type
 * Auto-generated from translation files for type safety and autocomplete
 * 
 * This type is generated from public/locales/en.json
 * Run 'npm run generate-types' to regenerate after adding new translations
 */
export type TranslationKey = GeneratedTranslationKey;

/**
 * Interpolation parameters
 * Key-value pairs for variable substitution in translations
 * Example: { name: 'John', count: 5 } for "Hello {name}, you have {count} messages"
 */
export type InterpolationParams = Record<string, string | number>;

/**
 * Pluralization rules
 * Defines different forms for plural translations based on count
 * Different languages have different plural rules (e.g., Polish has special rules for 2-4)
 */
export interface PluralRules {
  zero?: string;
  one: string;
  two?: string;
  few?: string;
  many?: string;
  other: string;
}

/**
 * Translation function type
 * Function signature for the t() translation function
 */
export type TranslationFunction = (
  key: TranslationKey,
  params?: InterpolationParams
) => string;

/**
 * Language metadata
 * Information about each supported language
 */
export interface LanguageMetadata {
  code: SupportedLocale;
  name: string;
  nativeName: string;
  formalTone: boolean;
}

/**
 * Supported languages with metadata
 */
export const SUPPORTED_LANGUAGES: LanguageMetadata[] = [
  { code: 'en', name: 'English', nativeName: 'English', formalTone: false },
  { code: 'de', name: 'German', nativeName: 'Deutsch', formalTone: true },
  { code: 'fr', name: 'French', nativeName: 'Français', formalTone: true },
  { code: 'es', name: 'Spanish', nativeName: 'Español', formalTone: false },
  { code: 'pl', name: 'Polish', nativeName: 'Polski', formalTone: false },
  { code: 'gsw', name: 'Swiss German', nativeName: 'Baseldytsch', formalTone: false },
];

/**
 * Default locale (fallback language)
 */
export const DEFAULT_LOCALE: SupportedLocale = 'en';

/**
 * LocalStorage key for persisting language preference
 */
export const STORAGE_KEY = 'orka-ppm-locale';

/**
 * Cookie name for syncing language between client and server
 */
export const COOKIE_NAME = 'orka-ppm-locale';
