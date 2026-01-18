# Requirements Document

## Introduction

This specification defines a comprehensive internationalization (i18n) system for the ORKA PPM application. The system will replace the current inline translation approach with a scalable, maintainable solution that supports 6 languages across all application pages and components. The system must provide excellent developer experience, optimal performance through lazy loading, and seamless user experience with persistent language preferences.

## Glossary

- **I18n_System**: The internationalization system responsible for managing translations, language switching, and locale-specific formatting
- **Translation_File**: A JSON file containing key-value pairs of translation strings for a specific language
- **Translation_Key**: A dot-notation string identifier used to retrieve translated content (e.g., 'page.section.element')
- **Language_Code**: ISO 639-1 two-letter language code (en, de, fr, es, pl) or ISO 639-3 code (gsw for Swiss German)
- **Translation_Function**: The `t()` function used by developers to retrieve translated strings
- **Language_Loader**: The module responsible for fetching and caching translation files
- **Locale_Formatter**: Utilities for formatting dates, numbers, and currencies according to locale conventions
- **Translation_Cache**: In-memory storage of loaded translation files to avoid redundant network requests
- **Fallback_Language**: The default language (English) used when a translation is missing in the selected language
- **Browser_Language**: The user's preferred language as detected from browser settings
- **Language_Persistence**: Storage mechanism (localStorage) that maintains language selection across sessions
- **Translation_Coverage**: The completeness of translations across all application features
- **Server_Component**: React Server Component that renders on the server
- **Client_Component**: React Client Component that renders in the browser
- **Language_Context**: React Context providing language state and functions throughout the component tree

## Requirements

### Requirement 1: Separate Language Files

**User Story:** As a developer, I want each language to have its own JSON file, so that translations are organized, maintainable, and can be loaded independently.

#### Acceptance Criteria

1. THE I18n_System SHALL store each Language_Code's translations in a separate JSON file at `/public/locales/{lang}.json`
2. WHEN the application starts, THE I18n_System SHALL NOT load all Translation_Files simultaneously
3. THE Translation_File SHALL use a nested JSON structure with dot-notation keys for organization
4. WHEN a Translation_File is malformed, THE I18n_System SHALL log an error and fall back to Fallback_Language
5. THE Translation_File SHALL support Unicode characters for all languages including special characters in Swiss German

### Requirement 2: Lazy Loading and Caching

**User Story:** As a user, I want fast application performance, so that language files don't slow down the initial page load.

#### Acceptance Criteria

1. WHEN a user selects a language, THE Language_Loader SHALL fetch only that language's Translation_File
2. WHEN a Translation_File is loaded, THE Translation_Cache SHALL store it in memory
3. WHEN a previously loaded language is selected again, THE Language_Loader SHALL retrieve it from Translation_Cache without network requests
4. THE Language_Loader SHALL fetch Translation_Files asynchronously without blocking UI rendering
5. WHEN a Translation_File fetch fails, THE I18n_System SHALL retry once before falling back to Fallback_Language

### Requirement 3: Complete Application Coverage

**User Story:** As a user, I want the entire application in my preferred language, so that I can use all features without encountering untranslated text.

#### Acceptance Criteria

1. THE I18n_System SHALL provide translations for all navigation menu items
2. THE I18n_System SHALL provide translations for all page titles and headings
3. THE I18n_System SHALL provide translations for all form labels, placeholders, and validation messages
4. THE I18n_System SHALL provide translations for all buttons, links, and interactive elements
5. THE I18n_System SHALL provide translations for all error messages and notifications
6. THE I18n_System SHALL provide translations for all tooltips and help text
7. THE I18n_System SHALL provide translations for all table headers and data labels
8. THE I18n_System SHALL provide translations for all dashboard widgets and KPI labels
9. THE I18n_System SHALL provide translations for all modal dialogs and confirmation messages
10. THE I18n_System SHALL provide translations for all status indicators and badges

### Requirement 4: TypeScript Support

**User Story:** As a developer, I want TypeScript autocomplete for translation keys, so that I can avoid typos and discover available translations easily.

#### Acceptance Criteria

1. THE I18n_System SHALL generate TypeScript types from Translation_Keys
2. WHEN a developer types `t('`, THE IDE SHALL display autocomplete suggestions for valid Translation_Keys
3. WHEN a developer uses an invalid Translation_Key, THE TypeScript compiler SHALL produce a type error
4. THE I18n_System SHALL maintain type safety across Server_Components and Client_Components
5. THE TypeScript types SHALL update automatically when Translation_Files are modified

### Requirement 5: Simple Translation Function

**User Story:** As a developer, I want a simple `t('key')` function, so that I can add translations quickly without complex syntax.

#### Acceptance Criteria

1. THE Translation_Function SHALL accept a Translation_Key as its first parameter
2. THE Translation_Function SHALL return the translated string for the current language
3. WHEN a Translation_Key is not found, THE Translation_Function SHALL return the Fallback_Language translation
4. WHEN neither current nor Fallback_Language translations exist, THE Translation_Function SHALL return the Translation_Key itself
5. THE Translation_Function SHALL support interpolation with a second parameter for variable substitution
6. THE Translation_Function SHALL support pluralization with count-based rules

### Requirement 6: Naming Convention

**User Story:** As a developer, I want a clear naming convention for translation keys, so that I can easily find and organize translations.

#### Acceptance Criteria

1. THE Translation_Key SHALL follow dot-notation format: `category.subcategory.element`
2. THE Translation_Key SHALL use camelCase for multi-word identifiers (e.g., `dashboard.budgetAlert`)
3. THE Translation_Key SHALL group related translations by feature or page (e.g., `scenarios.*`, `resources.*`)
4. THE Translation_Key SHALL use common prefixes for shared elements (e.g., `common.save`, `common.cancel`)
5. THE Translation_Key SHALL use descriptive names that indicate the element's purpose

### Requirement 7: Language Persistence

**User Story:** As a user, I want my language choice to persist across sessions, so that I don't have to select it every time I visit the application.

#### Acceptance Criteria

1. WHEN a user selects a language, THE I18n_System SHALL store the Language_Code in localStorage
2. WHEN a user returns to the application, THE I18n_System SHALL load the stored Language_Code from localStorage
3. WHEN no stored language exists, THE I18n_System SHALL detect the Browser_Language
4. WHEN the Browser_Language is not supported, THE I18n_System SHALL default to Fallback_Language
5. THE Language_Persistence SHALL survive browser restarts and cache clearing (unless localStorage is cleared)

### Requirement 8: Browser Language Detection

**User Story:** As a new user, I want the application to detect my browser language, so that I see content in my preferred language immediately.

#### Acceptance Criteria

1. WHEN a user visits the application for the first time, THE I18n_System SHALL read the Browser_Language from `navigator.language`
2. WHEN the Browser_Language matches a supported Language_Code, THE I18n_System SHALL set it as the current language
3. WHEN the Browser_Language is a regional variant (e.g., 'en-US'), THE I18n_System SHALL match it to the base Language_Code (e.g., 'en')
4. WHEN the Browser_Language is not supported, THE I18n_System SHALL use Fallback_Language
5. THE browser language detection SHALL only occur on first visit, not on subsequent visits with stored preferences

### Requirement 9: Smooth Language Switching

**User Story:** As a user, I want to switch languages instantly, so that I can compare content in different languages without waiting.

#### Acceptance Criteria

1. WHEN a user selects a new language, THE I18n_System SHALL update all visible translations within 200ms
2. WHEN switching to a cached language, THE I18n_System SHALL NOT trigger a page reload
3. WHEN switching to an uncached language, THE I18n_System SHALL load the Translation_File and update the UI without full page reload
4. THE language switch SHALL preserve the user's current page and scroll position
5. THE language switch SHALL update the Language_Context to trigger re-renders of translated components

### Requirement 10: Fallback Mechanism

**User Story:** As a user, I want to see English text when a translation is missing, so that I can still understand the application functionality.

#### Acceptance Criteria

1. WHEN a Translation_Key is missing in the selected language, THE Translation_Function SHALL return the Fallback_Language translation
2. WHEN a Translation_Key is missing in both selected and Fallback_Language, THE Translation_Function SHALL return the Translation_Key itself
3. THE I18n_System SHALL log a warning to the console when falling back to Fallback_Language
4. THE fallback mechanism SHALL work consistently across Server_Components and Client_Components
5. THE fallback SHALL be transparent to users (no error messages displayed)

### Requirement 11: Locale-Specific Formatting

**User Story:** As a user, I want dates and numbers formatted according to my language's conventions, so that information is presented in a familiar format.

#### Acceptance Criteria

1. THE Locale_Formatter SHALL format dates according to the current Language_Code's conventions
2. THE Locale_Formatter SHALL format numbers with appropriate thousand separators and decimal points
3. THE Locale_Formatter SHALL format currency values with correct symbols and positions
4. THE Locale_Formatter SHALL format relative times (e.g., "2 days ago") in the current language
5. THE Locale_Formatter SHALL handle timezone conversions consistently across languages

### Requirement 12: Interpolation Support

**User Story:** As a developer, I want to insert variables into translated strings, so that I can create dynamic messages with proper grammar.

#### Acceptance Criteria

1. THE Translation_Function SHALL support variable interpolation using `{variableName}` syntax
2. WHEN a translation contains `{variableName}`, THE Translation_Function SHALL replace it with the provided value
3. THE interpolation SHALL support multiple variables in a single translation
4. THE interpolation SHALL handle missing variables by leaving the placeholder unchanged
5. THE interpolation SHALL escape HTML by default to prevent XSS attacks

### Requirement 13: Pluralization Support

**User Story:** As a developer, I want to handle plural forms correctly, so that messages display grammatically correct text for different quantities.

#### Acceptance Criteria

1. THE Translation_Function SHALL support pluralization rules for each Language_Code
2. WHEN a translation requires pluralization, THE Translation_Function SHALL select the correct form based on count
3. THE pluralization SHALL support zero, one, and many forms as needed by each language
4. THE pluralization SHALL handle complex rules (e.g., Polish has different rules for 2-4 vs 5+)
5. THE pluralization SHALL work with interpolation to insert the count value

### Requirement 14: Next.js App Router Compatibility

**User Story:** As a developer, I want the i18n system to work with Next.js 16 App Router, so that I can use it in both server and client components.

#### Acceptance Criteria

1. THE I18n_System SHALL provide a hook for Client_Components to access translations
2. THE I18n_System SHALL provide a function for Server_Components to access translations
3. THE I18n_System SHALL work with React Server Components without requiring client-side JavaScript
4. THE I18n_System SHALL support streaming SSR without blocking on translation loading
5. THE I18n_System SHALL maintain language state across client-side navigation

### Requirement 15: Integration with Existing Code

**User Story:** As a developer, I want the new i18n system to integrate smoothly with existing code, so that already-translated pages continue working during migration.

#### Acceptance Criteria

1. THE I18n_System SHALL maintain compatibility with the existing useLanguage hook
2. WHEN migrating a component, THE I18n_System SHALL allow gradual replacement of old translation calls
3. THE I18n_System SHALL support both old and new translation formats during the transition period
4. THE I18n_System SHALL preserve existing language selection behavior in GlobalLanguageSelector
5. THE migration SHALL not break TopBar and Dashboard components that are already translated

### Requirement 16: Missing Translation Detection

**User Story:** As a developer, I want to easily identify missing translations, so that I can ensure complete Translation_Coverage.

#### Acceptance Criteria

1. THE I18n_System SHALL provide a development mode that highlights missing translations
2. WHEN a translation is missing, THE I18n_System SHALL log the Translation_Key and Language_Code to the console
3. THE I18n_System SHALL provide a utility to generate a report of missing translations per language
4. THE missing translation detection SHALL work in both Server_Components and Client_Components
5. THE missing translation warnings SHALL only appear in development mode, not production

### Requirement 17: Translation File Organization

**User Story:** As a developer, I want translation files organized by feature, so that I can find and update related translations easily.

#### Acceptance Criteria

1. THE Translation_File SHALL organize keys by feature area (e.g., `dashboard.*`, `scenarios.*`, `resources.*`)
2. THE Translation_File SHALL group common elements under a `common.*` namespace
3. THE Translation_File SHALL group navigation items under a `nav.*` namespace
4. THE Translation_File SHALL group form elements under feature-specific namespaces (e.g., `scenarios.form.*`)
5. THE Translation_File SHALL maintain consistent structure across all Language_Codes

### Requirement 18: Performance Optimization

**User Story:** As a user, I want minimal impact on application performance, so that the i18n system doesn't slow down my experience.

#### Acceptance Criteria

1. THE I18n_System SHALL add less than 50KB to the initial JavaScript bundle
2. THE Translation_File SHALL be loaded asynchronously and not block initial page render
3. THE Translation_Cache SHALL prevent redundant network requests for previously loaded languages
4. THE I18n_System SHALL use React Context efficiently to minimize unnecessary re-renders
5. THE language switching SHALL complete within 200ms for cached languages

### Requirement 19: Error Handling

**User Story:** As a user, I want the application to handle translation errors gracefully, so that I can continue using the application even if translations fail to load.

#### Acceptance Criteria

1. WHEN a Translation_File fails to load, THE I18n_System SHALL fall back to Fallback_Language
2. WHEN a Translation_File is corrupted, THE I18n_System SHALL log an error and use Fallback_Language
3. WHEN network errors occur, THE I18n_System SHALL retry the request once before falling back
4. THE error handling SHALL not display error messages to users
5. THE error handling SHALL log detailed information to the console for debugging

### Requirement 20: Six Language Support

**User Story:** As a user, I want to use the application in one of six supported languages, so that I can work in my preferred language.

#### Acceptance Criteria

1. THE I18n_System SHALL support English (en) as the Fallback_Language
2. THE I18n_System SHALL support German (de) with formal tone
3. THE I18n_System SHALL support French (fr) with formal tone
4. THE I18n_System SHALL support Spanish (es) with informal tone
5. THE I18n_System SHALL support Polish (pl) with formal tone
6. THE I18n_System SHALL support Swiss German/Baseldytsch (gsw) with regional dialect
7. THE I18n_System SHALL maintain consistent Translation_Coverage across all six languages
