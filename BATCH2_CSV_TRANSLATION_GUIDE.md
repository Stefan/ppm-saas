# Batch 2 CSV Translation Guide - Option 1

## Overview

This guide shows you how to efficiently translate all 635 keys using the CSV workbook and bulk translation tools.

**Estimated Time**: 2-4 hours (including review)
**Tools Needed**: Google Sheets or Excel + DeepL/Google Translate
**Result**: Professional translations for all 5 languages

## Step-by-Step Process

### Step 1: Open the Workbook (5 minutes)

1. **Locate the file**:
   ```bash
   open BATCH2_TRANSLATION_WORKBOOK.csv
   ```

2. **Import to Google Sheets** (Recommended):
   - Go to [Google Sheets](https://sheets.google.com)
   - File → Import → Upload
   - Select `BATCH2_TRANSLATION_WORKBOOK.csv`
   - Import settings: Detect automatically

3. **Or use Excel**:
   - Open Excel
   - File → Open → Select CSV
   - Ensure UTF-8 encoding

### Step 2: Bulk Translate with DeepL (30-45 minutes)

**DeepL is recommended** for better quality than Google Translate.

#### For Each Language Column:

**German (Column C)**:
1. Select all cells in Column C (C2:C636)
2. Copy the English text from Column B
3. Go to [DeepL Translator](https://www.deepl.com/translator)
4. Paste English text
5. Select target language: German
6. Click "Translate"
7. Copy translated text
8. Paste into Column C
9. **Important**: Review formality - DeepL should use "Sie" form

**French (Column D)**:
1. Repeat process for French
2. Ensure "vous" formal form is used

**Spanish (Column E)**:
1. Repeat process for Spanish
2. Check for "tú" informal form (you may need to adjust)

**Polish (Column F)**:
1. Repeat process for Polish
2. Verify formal business Polish

**Swiss German (Column G)**:
1. This is tricky - DeepL doesn't have Swiss German
2. Options:
   - Use German translation as base
   - Manually adjust to Baseldytsch dialect
   - Or skip for now and add later

### Step 3: Fix Interpolation Variables (30 minutes)

**Critical**: Ensure all variables are preserved!

1. **Search for** `{` in the English column
2. **For each match**, verify the translation has the same variable
3. **Common variables**:
   - `{count}` - must stay exactly as `{count}`
   - `{projectName}` - must stay exactly as `{projectName}`
   - `{changeId}` - must stay exactly as `{changeId}`
   - `{date}` - must stay exactly as `{date}`
   - `{email}` - must stay exactly as `{email}`

**Example**:
- ✅ Correct: `"{count} Aufgaben"` (German)
- ❌ Wrong: `"{anzahl} Aufgaben"` (variable changed)

**Quick Fix in Google Sheets**:
```
Find: \{count\}
Replace: {count}
(Ensure it's preserved in all languages)
```

### Step 4: Review Formality Levels (20 minutes)

#### German (Column C)
- **Check for**: "Sie" (formal) not "du" (informal)
- **Example**: "Sind Sie sicher?" ✅ not "Bist du sicher?" ❌

#### French (Column D)
- **Check for**: "vous" (formal) not "tu" (informal)
- **Example**: "Êtes-vous sûr?" ✅ not "Es-tu sûr?" ❌

#### Spanish (Column E)
- **Check for**: "tú" (informal) - this is correct per project standards
- **Example**: "¿Estás seguro?" ✅ not "¿Está usted seguro?" ❌

#### Polish (Column F)
- **Check for**: Formal business Polish
- **Example**: Use formal verb forms

### Step 5: Review Technical Terms (15 minutes)

Ensure consistency for key terms:

| English | German | French | Spanish | Polish |
|---------|--------|--------|---------|--------|
| Implementation | Implementierung | Mise en œuvre | Implementación | Wdrożenie |
| Change Request | Änderungsantrag | Demande de modification | Solicitud de cambio | Wniosek o zmianę |
| Approval | Genehmigung | Approbation | Aprobación | Zatwierdzenie |
| Workflow | Arbeitsablauf | Flux de travail | Flujo de trabajo | Przepływ pracy |
| Schedule | Zeitplan | Calendrier | Cronograma | Harmonogram |
| Milestone | Meilenstein | Jalon | Hito | Kamień milowy |
| Progress | Fortschritt | Progrès | Progreso | Postęp |
| Task | Aufgabe | Tâche | Tarea | Zadanie |

### Step 6: Save and Export (5 minutes)

1. **In Google Sheets**:
   - File → Download → Comma-separated values (.csv)
   - Save as `BATCH2_TRANSLATION_WORKBOOK.csv` (overwrite original)

2. **In Excel**:
   - File → Save As
   - Format: CSV UTF-8
   - Overwrite original file

### Step 7: Import Translations (2 minutes)

```bash
# Import the completed translations
npx tsx scripts/import-translations.ts

# Regenerate TypeScript types
npm run generate-types

# Check progress
npx tsx scripts/check-translation-progress.ts
```

**Expected Output**:
```
✅ German (de): 100% (635/635 keys)
✅ French (fr): 100% (635/635 keys)
✅ Spanish (es): 100% (635/635 keys)
✅ Polish (pl): 100% (635/635 keys)
✅ Swiss German (gsw): 100% (635/635 keys)

🎯 Overall Batch 2 Progress: 100%
```

### Step 8: Verify in Application (10 minutes)

1. **Start dev server** (if not running):
   ```bash
   npm run dev
   ```

2. **Test each language**:
   - Switch language in app
   - Navigate to Change Management section
   - Verify translations display correctly
   - Check for layout issues with longer text

3. **Look for**:
   - Missing translations (English fallbacks)
   - Broken interpolations (showing `{count}` instead of numbers)
   - Layout breaks (text overflow, wrapping issues)

## Quality Checklist

Before marking as complete:

- [ ] All 635 keys translated in all 5 languages
- [ ] All interpolation variables preserved (`{count}`, `{projectName}`, etc.)
- [ ] Correct formality levels:
  - [ ] German: "Sie" form
  - [ ] French: "vous" form
  - [ ] Spanish: "tú" form
  - [ ] Polish: Formal
  - [ ] Swiss German: Baseldytsch (or German as fallback)
- [ ] Technical terms consistent
- [ ] No English text remaining
- [ ] Import script ran successfully
- [ ] Progress checker shows 100%
- [ ] TypeScript types regenerated
- [ ] No compilation errors
- [ ] Manual testing passed in all languages

## Tips for Efficiency

### Use DeepL Pro (Recommended)
- Better quality than free tools
- Handles context better
- Preserves formatting
- Cost: ~$10/month
- Worth it for 3,175 strings

### Batch Processing
- Translate 100-200 strings at a time
- DeepL has character limits
- Break into manageable chunks

### Use Find & Replace
- Fix common issues quickly
- Ensure variable preservation
- Standardize terminology

### Keyboard Shortcuts
- Google Sheets: Ctrl+H (Find & Replace)
- Excel: Ctrl+H (Find & Replace)
- DeepL: Ctrl+A (Select all), Ctrl+C (Copy)

## Common Issues and Solutions

### Issue: Variables Changed
**Problem**: `{count}` became `{anzahl}` in German
**Solution**: Find & Replace to restore original variables

### Issue: Wrong Formality
**Problem**: German uses "du" instead of "Sie"
**Solution**: Use DeepL's formality setting or manually adjust

### Issue: Inconsistent Terms
**Problem**: "Implementation" translated differently in different places
**Solution**: Use Find & Replace to standardize

### Issue: Layout Breaks
**Problem**: German text too long, breaks UI
**Solution**: Use shorter synonyms or abbreviations

### Issue: Special Characters
**Problem**: Umlauts (ä, ö, ü) not displaying
**Solution**: Ensure UTF-8 encoding when saving CSV

## Alternative Tools

### If DeepL Doesn't Work:

1. **Google Translate**:
   - Free
   - Good for bulk translation
   - Lower quality than DeepL
   - URL: https://translate.google.com

2. **Microsoft Translator**:
   - Good for business terminology
   - Free tier available
   - URL: https://www.bing.com/translator

3. **ChatGPT/Claude**:
   - Can translate with context
   - Good for maintaining formality
   - Paste chunks of text

## Time Estimates

| Task | Time | Notes |
|------|------|-------|
| Open workbook | 5 min | One-time setup |
| Translate German | 30 min | Using DeepL |
| Translate French | 30 min | Using DeepL |
| Translate Spanish | 30 min | Using DeepL |
| Translate Polish | 30 min | Using DeepL |
| Swiss German | 30 min | Manual adjustment |
| Fix variables | 30 min | Critical step |
| Review formality | 20 min | Quality check |
| Review terms | 15 min | Consistency |
| Import & test | 15 min | Final steps |
| **Total** | **3-4 hours** | Can be done in one session |

## Next Steps After Completion

Once translations are 100% complete:

1. **Update Components** (Week 4):
   - Modify 10 Change Management components
   - Add `useTranslations('changes')` hook
   - Replace hardcoded strings
   - Test in all languages

2. **Mark Batch 2 Complete**:
   - Update execution log
   - Document any issues
   - Celebrate 85% coverage! 🎉

3. **Proceed to Batch 3**:
   - Apply same workflow to Financial Module
   - Use lessons learned
   - Continue toward 100% coverage

## Support

If you encounter issues:
- Check `BATCH2_TRANSLATION_WORKFLOW.md` for detailed guidance
- Run `npx tsx scripts/check-translation-progress.ts` to verify progress
- Review `BATCH2_TRANSLATION_STATUS.md` for current status

---

**Created**: January 18, 2026
**Method**: Option 1 - CSV Workbook with Bulk Translation
**Estimated Time**: 2-4 hours
**Next Step**: Open BATCH2_TRANSLATION_WORKBOOK.csv and begin translation
