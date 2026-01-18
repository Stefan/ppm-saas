# Batch 2 Translation Workflow Guide

## Overview

This guide explains how to complete the translation of Batch 2 (Change Management Module) keys across all 6 languages.

## Current Status

- ✅ **English (en.json)**: 611 keys - 100% complete
- ⏳ **German (de.json)**: 611 keys - Structure in place, needs translation
- ⏳ **French (fr.json)**: 611 keys - Structure in place, needs translation
- ⏳ **Spanish (es.json)**: 611 keys - Structure in place, needs translation
- ⏳ **Polish (pl.json)**: 611 keys - Structure in place, needs translation
- ⏳ **Swiss German (gsw.json)**: 611 keys - Structure in place, needs translation

## Automated Scripts Available

### 1. Export for Translation
Creates a CSV workbook with all keys that need translation:

```bash
npx tsx scripts/export-for-translation.ts
```

**Output**: `BATCH2_TRANSLATION_WORKBOOK.csv`

This CSV contains:
- Column 1: Key path (e.g., `changes.implementationTracker.title`)
- Column 2: English text
- Columns 3-7: Empty columns for each language (de, fr, es, pl, gsw)
- Column 8: Notes (optional)

### 2. Import Translations
Imports completed translations from CSV back into JSON files:

```bash
npx tsx scripts/import-translations.ts
```

**Input**: `BATCH2_TRANSLATION_WORKBOOK.csv` (with translations filled in)

### 3. Regenerate Types
After importing translations, regenerate TypeScript types:

```bash
npm run generate-types
```

### 4. Validate Translations
Check for missing or inconsistent translations:

```bash
npm run validate-translations
```

## Translation Workflow

### Option A: Using CSV Workbook (Recommended for Professional Translators)

1. **Export keys to CSV**:
   ```bash
   npx tsx scripts/export-for-translation.ts
   ```

2. **Open in spreadsheet software**:
   - Excel, Google Sheets, or LibreOffice Calc
   - File: `BATCH2_TRANSLATION_WORKBOOK.csv`

3. **Fill in translations**:
   - Column 3 (German): Formal business German with "Sie"
   - Column 4 (French): Formal business French with "vous"
   - Column 5 (Spanish): Informal professional Spanish with "tú"
   - Column 6 (Polish): Formal business Polish
   - Column 7 (Swiss German): Baseldytsch dialect

4. **Save the CSV** (keep the same filename)

5. **Import translations**:
   ```bash
   npx tsx scripts/import-translations.ts
   ```

6. **Regenerate types**:
   ```bash
   npm run generate-types
   ```

7. **Verify**:
   ```bash
   npm run type-check
   ```

### Option B: Direct JSON Editing (For Quick Updates)

1. **Open language file** (e.g., `public/locales/de.json`)

2. **Navigate to changes object**:
   ```json
   {
     "changes": {
       "implementationTracker": {
         "title": "Implementation Tracking",  // ← Replace with German
         ...
       }
     }
   }
   ```

3. **Replace English text** with proper translation

4. **Save file**

5. **Regenerate types**:
   ```bash
   npm run generate-types
   ```

## Translation Guidelines by Language

### German (de.json)
- **Formality**: Formal "Sie" form
- **Style**: Business/professional
- **Examples**:
  - "Implementation Tracking" → "Implementierungsverfolgung"
  - "Change Request" → "Änderungsantrag"
  - "Assigned to" → "Zugewiesen an"
  - "Overall Progress" → "Gesamtfortschritt"

### French (fr.json)
- **Formality**: Formal "vous" form
- **Style**: Business/professional
- **Examples**:
  - "Implementation Tracking" → "Suivi de la mise en œuvre"
  - "Change Request" → "Demande de modification"
  - "Assigned to" → "Assigné à"
  - "Overall Progress" → "Progression globale"

### Spanish (es.json)
- **Formality**: Informal "tú" form (per project standards)
- **Style**: Professional but approachable
- **Examples**:
  - "Implementation Tracking" → "Seguimiento de implementación"
  - "Change Request" → "Solicitud de cambio"
  - "Assigned to" → "Asignado a"
  - "Overall Progress" → "Progreso general"

### Polish (pl.json)
- **Formality**: Formal business Polish
- **Style**: Professional
- **Examples**:
  - "Implementation Tracking" → "Śledzenie wdrożenia"
  - "Change Request" → "Wniosek o zmianę"
  - "Assigned to" → "Przypisane do"
  - "Overall Progress" → "Ogólny postęp"

### Swiss German (gsw.json)
- **Dialect**: Baseldytsch
- **Style**: Keep technical terms recognizable
- **Examples**:
  - "Implementation Tracking" → "Implementierigsverfolgig"
  - "Change Request" → "Änderigaatrag"
  - "Assigned to" → "Zuegwise aa"
  - "Overall Progress" → "Gsamtfortschritt"

## Key Sections to Translate

The `changes` object contains 10 major sections (in order of priority):

### High Priority (User-Facing)
1. **requestForm** (~60 keys) - Change request creation form
2. **pendingApprovals** (~60 keys) - Approval review interface
3. **requestDetail** (~50 keys) - Change request details view

### Medium Priority (Frequent Use)
4. **implementationTracker** (~150 keys) - Implementation tracking
5. **approvalWorkflow** (~40 keys) - Approval workflow interface
6. **analytics** (~50 keys) - Analytics dashboard

### Lower Priority (Admin/Advanced)
7. **approvalWorkflowConfiguration** (~80 keys) - Workflow configuration
8. **implementationMonitoring** (~70 keys) - Monitoring dashboard
9. **impactAnalysis** (~80 keys) - Impact analysis
10. **impactEstimation** (~70 keys) - Estimation tools

## Quality Checklist

Before marking a language as complete:

- [ ] All 611 keys translated (no English placeholders)
- [ ] Consistent terminology throughout
- [ ] Proper formality level maintained
- [ ] Interpolation variables preserved (e.g., `{count}`, `{projectName}`)
- [ ] Special characters properly escaped
- [ ] JSON syntax valid (no trailing commas, proper quotes)
- [ ] TypeScript types regenerated
- [ ] No compilation errors
- [ ] Manual testing in the application

## Testing Translations

After completing translations:

1. **Switch language in app**:
   - Use language selector in UI
   - Or set `NEXT_PUBLIC_DEFAULT_LOCALE` in `.env.local`

2. **Navigate to Change Management**:
   - Go to `/changes` route
   - Test all 10 components

3. **Verify**:
   - All text displays in correct language
   - No English fallbacks
   - Interpolations work correctly
   - UI layout not broken by longer translations

## Troubleshooting

### Issue: Import script fails
**Solution**: Check CSV format, ensure no extra commas or quotes

### Issue: JSON syntax error after editing
**Solution**: Use a JSON validator (jsonlint.com) to find the error

### Issue: Translations not showing in app
**Solution**: 
1. Clear browser cache
2. Restart dev server
3. Check browser console for errors
4. Verify language file was saved

### Issue: TypeScript errors after translation
**Solution**: Run `npm run generate-types` again

## Progress Tracking

Update `I18N_100_PERCENT_EXECUTION_LOG.md` after completing each language:

```markdown
**Progress**:
- ✅ English (en.json): 611 keys complete
- ✅ German (de.json): 611 keys complete
- ⏳ French (fr.json): In progress
- ⏳ Spanish (es.json): Pending
- ⏳ Polish (pl.json): Pending
- ⏳ Swiss German (gsw.json): Pending
```

## Estimated Time

- **Per language**: 8-12 hours (professional translator)
- **All 5 languages**: 40-60 hours total
- **With automation**: Can be parallelized

## Support

For questions or issues:
1. Check `BATCH2_TRANSLATION_STATUS.md` for current status
2. Review `I18N_DEVELOPER_GUIDE.md` for technical details
3. Consult translation memory for consistent terminology

---

**Last Updated**: January 18, 2026
**Version**: 1.0
**Status**: Ready for translation
