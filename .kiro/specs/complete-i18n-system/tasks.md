# Implementation Plan: Complete I18n System

## Overview

This implementation plan breaks down the i18n system into incremental, testable steps. Each task builds on previous work, with checkpoints to ensure quality. The approach prioritizes core functionality first, then adds advanced features like pluralization and formatting.

## Tasks

- [x] 1. Set up translation file structure and types
  - Create `/public/locales/` directory
  - Create initial JSON files for all 6 languages (en, de, fr, es, pl, gsw)
  - Migrate existing translations from `lib/i18n/translations.ts` to JSON files
  - Create TypeScript type definitions in `lib/i18n/types.ts`
  - _Requirements: 1.1, 1.3, 1.5, 20.1-20.7_

- [x] 2. Implement translation loader with caching
  - [x] 2.1 Create translation loader in `lib/i18n/loader.ts`
    - Implement `loadTranslations()` function with fetch and caching
    - Implement `preloadTranslations()` for background loading
    - Implement `clearTranslationCache()` for cache management
    - Implement `isLanguageCached()` for cache checking
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.2 Write property test for lazy loading
    - **Property 8: Single language loaded on initialization**
    - **Validates: Requirements 1.2, 2.1**

  - [x] 2.3 Write property test for caching
    - **Property 5: Cache prevents redundant network requests**
    - **Validates: Requirements 2.3, 18.3**

  - [x] 2.4 Write property test for retry logic
    - **Property 7: Network error retry logic**
    - **Validates: Requirements 2.5, 19.3**

  - [x] 2.5 Write property test for malformed JSON handling
    - **Property 6: Malformed JSON fallback**
    - **Validates: Requirements 1.4, 19.2**

- [x] 3. Implement I18n Context Provider
  - [x] 3.1 Create I18nContext in `lib/i18n/context.tsx`
    - Implement I18nProvider component with state management
    - Implement language detection from localStorage and browser
    - Implement `setLocale()` function with persistence
    - Implement `t()` translation function with dot-notation key lookup
    - Implement `useI18n()` hook
    - Implement `useTranslations()` convenience hook
    - _Requirements: 5.2, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

  - [x] 3.2 Write property test for translation lookup
    - **Property 1: Translation lookup returns correct value**
    - **Validates: Requirements 5.2**

  - [x] 3.3 Write property test for fallback to English
    - **Property 2: Missing key fallback to English**
    - **Validates: Requirements 5.3, 10.1**

  - [x] 3.4 Write property test for missing key returns key
    - **Property 3: Missing key returns key itself**
    - **Validates: Requirements 5.4, 10.2**

  - [x] 3.5 Write property test for localStorage persistence
    - **Property 15: Language persistence in localStorage**
    - **Validates: Requirements 7.1, 7.2**

  - [x] 3.6 Write property test for browser language detection
    - **Property 16: Browser language detection on first visit**
    - **Validates: Requirements 8.1, 8.2**

  - [x] 3.7 Write property test for regional variant normalization
    - **Property 14: Regional variant normalization**
    - **Validates: Requirements 8.3**

  - [x] 3.8 Write property test for unsupported language fallback
    - **Property 13: Unsupported language fallback**
    - **Validates: Requirements 7.4, 8.4**

  - [x] 3.9 Write property test for stored preference precedence
    - **Property 17: Stored preference takes precedence**
    - **Validates: Requirements 8.5**

- [x] 4. Checkpoint - Ensure core translation system works
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Server Component support
  - [x] 5.1 Create server translation function in `lib/i18n/server.ts`
    - Implement `getServerLocale()` to read from cookies
    - Implement `getTranslations()` for Server Components
    - Add cookie synchronization when language changes
    - _Requirements: 14.2, 14.3_

  - [x] 5.2 Write property test for server-client fallback consistency
    - **Property 28: Fallback consistency across environments**
    - **Validates: Requirements 10.4**

  - [x] 5.3 Write unit test for Server Component translation
    - Test that getTranslations() works in Server Component context
    - _Requirements: 14.3_

- [x] 6. Implement interpolation support
  - [x] 6.1 Add interpolation to translation function
    - Update `t()` function to support params parameter
    - Implement variable substitution with {variableName} syntax
    - Add HTML escaping for XSS prevention
    - _Requirements: 5.5, 12.1, 12.2, 12.5_

  - [x] 6.2 Write property test for variable interpolation
    - **Property 9: Variable interpolation**
    - **Validates: Requirements 5.5, 12.1, 12.2**

  - [x] 6.3 Write property test for multiple variables
    - **Property 10: Multiple variable interpolation**
    - **Validates: Requirements 12.3**

  - [x] 6.4 Write property test for missing variable handling
    - **Property 11: Missing variable handling**
    - **Validates: Requirements 12.4**

  - [x] 6.5 Write property test for HTML escaping
    - **Property 12: HTML escaping for XSS prevention**
    - **Validates: Requirements 12.5**

- [x] 7. Implement locale formatters
  - [x] 7.1 Create formatters in `lib/i18n/formatters.ts`
    - Implement `formatDate()` with Intl.DateTimeFormat
    - Implement `formatNumber()` with Intl.NumberFormat
    - Implement `formatCurrency()` with currency options
    - Implement `formatRelativeTime()` with Intl.RelativeTimeFormat
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 7.2 Write property test for date formatting
    - **Property 21: Date formatting per locale**
    - **Validates: Requirements 11.1**

  - [x] 7.3 Write property test for number formatting
    - **Property 22: Number formatting per locale**
    - **Validates: Requirements 11.2**

  - [x] 7.4 Write property test for currency formatting
    - **Property 23: Currency formatting per locale**
    - **Validates: Requirements 11.3**

  - [x] 7.5 Write property test for relative time formatting
    - **Property 24: Relative time formatting per locale**
    - **Validates: Requirements 11.4**

- [x] 8. Implement pluralization support
  - [x] 8.1 Add pluralization to translation system
    - Create pluralization rules for each language
    - Update `t()` function to support plural forms
    - Implement count-based form selection
    - Add support for zero, one, few, many, other forms
    - _Requirements: 5.6, 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 8.2 Write property test for plural form selection
    - **Property 25: Plural form selection by count**
    - **Validates: Requirements 13.2**

  - [x] 8.3 Write property test for language-specific plural rules
    - **Property 26: Language-specific plural rules**
    - **Validates: Requirements 13.4**

  - [x] 8.4 Write property test for pluralization with interpolation
    - **Property 27: Pluralization with interpolation**
    - **Validates: Requirements 13.5**

- [x] 9. Checkpoint - Ensure advanced features work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Update existing useLanguage hook for backward compatibility
  - [x] 10.1 Modify `hooks/useLanguage.ts`
    - Wrap new i18n system to maintain existing API
    - Map locale codes for compatibility
    - Preserve existing method signatures
    - _Requirements: 15.1, 15.3_

  - [x] 10.2 Write unit test for backward compatibility
    - Test that existing useLanguage hook still works
    - Test that old and new systems coexist
    - _Requirements: 15.1, 15.3_

- [x] 11. Update GlobalLanguageSelector component
  - [x] 11.1 Modify `components/navigation/GlobalLanguageSelector.tsx`
    - Update to use new i18n context
    - Remove page reload for cached languages
    - Add loading state for uncached languages
    - Sync language to cookies for Server Components
    - _Requirements: 9.2, 9.3, 15.4_

  - [x] 11.2 Write property test for no page reload
    - **Property 18: No page reload for cached languages**
    - **Validates: Requirements 9.2**

  - [x] 11.3 Write property test for async load without reload
    - **Property 19: Async load without page reload**
    - **Validates: Requirements 9.3**

  - [x] 11.4 Write unit test for GlobalLanguageSelector
    - Test that component still renders correctly
    - Test that language switching works
    - _Requirements: 15.4_

- [x] 12. Add I18nProvider to app layout
  - [x] 12.1 Update `app/layout.tsx`
    - Wrap application with I18nProvider
    - Ensure provider is above all components
    - _Requirements: 14.1, 14.5_

  - [x] 12.2 Write property test for language state persistence
    - **Property 30: Language state persistence across navigation**
    - **Validates: Requirements 14.5**

- [x] 13. Implement development mode features
  - [x] 13.1 Add missing translation detection
    - Add console warnings for missing keys in development
    - Implement environment check (dev vs production)
    - Add translation coverage report utility
    - _Requirements: 16.1, 16.2, 16.3, 16.5_

  - [x] 13.2 Write property test for console warnings
    - **Property 4: Console warning for missing translations**
    - **Validates: Requirements 10.3, 16.2**

  - [x] 13.3 Write property test for production mode suppression
    - **Property 32: Production mode suppresses warnings**
    - **Validates: Requirements 16.5**

  - [x] 13.4 Write property test for missing translation detection in both environments
    - **Property 29: Missing translation detection in both environments**
    - **Validates: Requirements 16.4**

  - [x] 13.5 Write unit test for translation coverage report
    - Test that report utility generates correct output
    - _Requirements: 16.3_

- [x] 14. Migrate existing translated components
  - [x] 14.1 Update TopBar component to use new i18n system
    - Replace old translation calls with new `t()` function
    - Test that all translations still work
    - _Requirements: 15.5_

  - [x] 14.2 Update Dashboard component to use new i18n system
    - Replace old translation calls with new `t()` function
    - Test that all translations still work
    - _Requirements: 15.5_

  - [x] 14.3 Write unit tests for migrated components
    - Test TopBar renders with translations
    - Test Dashboard renders with translations
    - _Requirements: 15.5_

- [x] 15. Add translations for remaining pages
  - [x] 15.1 Add translations for Scenarios page
    - Add all scenario-related keys to translation files
    - Update Scenarios components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.2 Add translations for Resources page
    - Add all resource-related keys to translation files
    - Update Resources components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.3 Add translations for Financials page
    - Add all financial-related keys to translation files
    - Update Financials components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.4 Add translations for Risks page
    - Add all risk-related keys to translation files
    - Update Risks components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.5 Add translations for Reports page
    - Add all report-related keys to translation files
    - Update Reports components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.6 Add translations for Monte Carlo page
    - Add all monte-carlo-related keys to translation files
    - Update Monte Carlo components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.7 Add translations for Changes page
    - Add all change-related keys to translation files
    - Update Changes components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.8 Add translations for Feedback page
    - Add all feedback-related keys to translation files
    - Update Feedback components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.9 Add translations for Performance page
    - Add all performance-related keys to translation files
    - Update Performance components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.10 Add translations for Users page
    - Add all user-related keys to translation files
    - Update Users components to use `t()` function
    - _Requirements: 3.1-3.10_

  - [x] 15.11 Add translations for Audit page
    - Add all audit-related keys to translation files
    - Update Audit components to use `t()` function
    - _Requirements: 3.1-3.10_

- [x] 16. Checkpoint - Ensure all pages are translated
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Add Unicode character support tests
  - [x] 17.1 Write property test for Unicode preservation
    - **Property 31: Unicode character preservation**
    - **Validates: Requirements 1.5**

- [x] 18. Add context update re-render tests
  - [x] 18.1 Write property test for context re-renders
    - **Property 20: Context update triggers re-renders**
    - **Validates: Requirements 9.5**

- [x] 19. Create migration guide documentation
  - Document how to migrate components from old to new system
  - Document naming conventions for translation keys
  - Document how to add new translations
  - Document how to use interpolation and pluralization
  - _Requirements: 6.1-6.5, 17.1-17.5_

- [x] 20. Final checkpoint - Complete system verification
  - Run all tests (unit and property tests)
  - Test language switching in browser
  - Verify all pages are translated
  - Verify no console errors in production mode
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Migration is gradual - old and new systems coexist during transition
- TypeScript types provide compile-time safety for translation keys
