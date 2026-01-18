# Complete Batch 2 Translations with DeepL - Step-by-Step Guide

## 📊 Current Status

- **Completed**: 16% (100 keys professionally translated)
- **Remaining**: 84% (535 keys need translation)
- **Time Needed**: 2-3 hours
- **Tool**: DeepL (free web interface)

## 🎯 Goal

Complete all 2,675 remaining strings (535 keys × 5 languages) using DeepL's free web interface.

## 📝 Step-by-Step Instructions

### Step 1: Open the CSV File (2 minutes)

```bash
open BATCH2_TRANSLATION_WORKBOOK.csv
```

**Or** import to Google Sheets:
1. Go to https://sheets.google.com
2. File → Import → Upload
3. Select `BATCH2_TRANSLATION_WORKBOOK.csv`
4. Import settings: Detect automatically

### Step 2: Identify Untranslated Rows (5 minutes)

The CSV has 635 rows. Rows 1-102 are already translated. You need to translate rows 103-635.

**In Google Sheets:**
1. Scroll to row 103
2. This is where untranslated content begins
3. You'll translate from row 103 to row 635 (533 rows)

### Step 3: Translate German (Column C) - 45 minutes

**Process:**

1. **Select English text** (Column B, rows 103-635):
   - Click cell B103
   - Scroll to B635
   - Hold Shift and click B635
   - Press Ctrl+C (or Cmd+C on Mac) to copy

2. **Go to DeepL**:
   - Open https://www.deepl.com/translator
   - Select: English → German
   - **Important**: Click the formality button and select "Sie" (formal)

3. **Paste and translate**:
   - Paste the English text (Ctrl+V)
   - Wait for translation (takes 10-20 seconds)
   - Click "Copy translation" button

4. **Paste back to CSV**:
   - Click cell C103 in your spreadsheet
   - Paste (Ctrl+V)
   - The translations will fill down automatically

5. **Verify**:
   - Scroll through Column C
   - Check that translations look reasonable
   - Verify interpolation variables are preserved: `{count}`, `{projectName}`, etc.

**DeepL Character Limit**: If you hit the limit (~5,000 chars), split into smaller batches:
- Rows 103-300 (first batch)
- Rows 301-500 (second batch)
- Rows 501-635 (third batch)

### Step 4: Translate French (Column D) - 45 minutes

**Repeat the same process:**

1. Copy English (B103:B635)
2. Go to DeepL: English → French
3. **Important**: Select "vous" (formal) formality
4. Paste, translate, copy
5. Paste to Column D starting at D103

### Step 5: Translate Spanish (Column E) - 45 minutes

**Repeat the same process:**

1. Copy English (B103:B635)
2. Go to DeepL: English → Spanish
3. **Important**: Select "tú" (informal) formality
4. Paste, translate, copy
5. Paste to Column E starting at E103

### Step 6: Translate Polish (Column F) - 45 minutes

**Repeat the same process:**

1. Copy English (B103:B635)
2. Go to DeepL: English → Polish
3. Use default formality (formal)
4. Paste, translate, copy
5. Paste to Column F starting at F103

### Step 7: Swiss German (Column G) - 30 minutes

**Option A** (Recommended): Use German as base
1. Copy German translations (C103:C635)
2. Paste to Column G (G103:G635)
3. Swiss German users will understand standard German

**Option B**: Skip for now
- Swiss German is rarely used
- Can be added later if needed

### Step 8: Fix Interpolation Variables (30 minutes)

**Critical**: Ensure all variables are preserved!

1. **In Google Sheets, use Find & Replace** (Ctrl+H):
   
   Search for patterns that might have been translated:
   - Find: `\{count\}` → Should stay as `{count}`
   - Find: `\{projectName\}` → Should stay as `{projectName}`
   - Find: `\{changeId\}` → Should stay as `{changeId}`

2. **Manual check**:
   - Search for `{` in the English column
   - For each occurrence, verify the same variable exists in all language columns
   - Common variables to check:
     - `{count}`
     - `{projectName}`
     - `{changeId}`
     - `{date}`
     - `{email}`
     - `{number}`
     - `{percent}`

3. **Fix if needed**:
   - If DeepL changed `{count}` to `{anzahl}` in German, change it back to `{count}`
   - Variables must be EXACTLY the same across all languages

### Step 9: Save the CSV (5 minutes)

**In Google Sheets:**
1. File → Download → Comma-separated values (.csv)
2. Save as `BATCH2_TRANSLATION_WORKBOOK.csv`
3. **Important**: Overwrite the original file

**In Excel:**
1. File → Save As
2. Format: CSV UTF-8 (Comma delimited)
3. Save and overwrite original

### Step 10: Import Translations (2 minutes)

```bash
# Import the completed translations
npx tsx scripts/import-translations.ts

# You should see:
# ✅ Updated de.json with 635 translations
# ✅ Updated fr.json with 635 translations
# ✅ Updated es.json with 635 translations
# ✅ Updated pl.json with 635 translations
# ✅ Updated gsw.json with 635 translations
```

### Step 11: Regenerate Types (1 minute)

```bash
npm run generate-types
```

### Step 12: Check Progress (1 minute)

```bash
npx tsx scripts/check-translation-progress.ts
```

**Expected output:**
```
✅ German (de): 100% (635/635 keys)
✅ French (fr): 100% (635/635 keys)
✅ Spanish (es): 100% (635/635 keys)
✅ Polish (pl): 100% (635/635 keys)
✅ Swiss German (gsw): 100% (635/635 keys)

🎯 Overall Batch 2 Progress: 100%
```

### Step 13: Test in Application (10 minutes)

```bash
npm run dev
```

1. Open the app in your browser
2. Switch to German language
3. Navigate to Change Management section
4. Verify translations display correctly
5. Repeat for French, Spanish, Polish

**Look for:**
- ✅ Translations display correctly
- ✅ No English fallbacks
- ✅ Interpolation variables work (numbers, names show correctly)
- ✅ No layout breaks (text fits in UI)
- ❌ Any issues? Note them for refinement

## ⚠️ Common Issues & Solutions

### Issue 1: Variables Changed

**Problem**: `{count}` became `{anzahl}` in German

**Solution**:
1. In Google Sheets: Ctrl+H (Find & Replace)
2. Find: `{anzahl}`
3. Replace: `{count}`
4. Replace all

### Issue 2: Wrong Formality

**Problem**: German uses "du" instead of "Sie"

**Solution**:
- Re-translate that section in DeepL
- Make sure "Sie" formality is selected
- Common phrases to check:
  - "Sind Sie sicher?" ✅ (not "Bist du sicher?" ❌)
  - "Möchten Sie" ✅ (not "Möchtest du" ❌)

### Issue 3: Text Too Long

**Problem**: German text breaks UI layout

**Solution**:
- Use shorter synonyms
- Abbreviate where appropriate
- Example: "Implementierungsverfolgung" → "Impl.-Verfolgung"

### Issue 4: Inconsistent Terms

**Problem**: "Implementation" translated differently in different places

**Solution**:
1. Decide on standard term: "Implementierung"
2. Find & Replace to standardize
3. Use the terminology table below

## 📋 Standard Terminology Reference

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
| Resource | Ressource | Ressource | Recurso | Zasób |
| Budget | Budget | Budget | Presupuesto | Budżet |
| Cost | Kosten | Coût | Costo | Koszt |
| Risk | Risiko | Risque | Riesgo | Ryzyko |
| Issue | Problem | Problème | Problema | Problem |
| Status | Status | Statut | Estado | Status |
| Priority | Priorität | Priorité | Prioridad | Priorytet |

## ⏱️ Time Breakdown

| Task | Time | Notes |
|------|------|-------|
| Open CSV | 2 min | One-time |
| Identify rows | 5 min | Find where to start |
| German translation | 45 min | Rows 103-635 |
| French translation | 45 min | Rows 103-635 |
| Spanish translation | 45 min | Rows 103-635 |
| Polish translation | 45 min | Rows 103-635 |
| Swiss German | 30 min | Copy from German |
| Fix variables | 30 min | Critical step |
| Save CSV | 5 min | Export properly |
| Import & test | 15 min | Final steps |
| **Total** | **3-4 hours** | Can be done in one session |

## 💡 Pro Tips

### Tip 1: Work in Batches
- Don't try to do all 535 rows at once
- Split into 3-4 batches of ~150 rows each
- Take breaks between batches

### Tip 2: Use Keyboard Shortcuts
- Google Sheets: Ctrl+C (copy), Ctrl+V (paste), Ctrl+H (find & replace)
- DeepL: Ctrl+A (select all), Ctrl+C (copy)

### Tip 3: Save Frequently
- Save your Google Sheet every 15 minutes
- Don't lose your work!

### Tip 4: Test As You Go
- After completing each language, import and test
- Catch issues early
- Don't wait until all languages are done

### Tip 5: Use DeepL's Context Feature
- If a translation seems off, add context
- Example: "Change" could mean "Änderung" (modification) or "Wechselgeld" (money)
- Add context: "Change Request" → clearly "Änderungsantrag"

## ✅ Quality Checklist

Before marking as complete:

- [ ] All 635 keys translated in all 5 languages
- [ ] All interpolation variables preserved (`{count}`, `{projectName}`, etc.)
- [ ] Correct formality levels:
  - [ ] German: "Sie" form
  - [ ] French: "vous" form
  - [ ] Spanish: "tú" form
  - [ ] Polish: Formal
  - [ ] Swiss German: Based on German
- [ ] Technical terms consistent (use reference table)
- [ ] No English text remaining
- [ ] Import script ran successfully
- [ ] Progress checker shows 100%
- [ ] TypeScript types regenerated
- [ ] No compilation errors
- [ ] Manual testing passed in all languages

## 🎉 After Completion

Once you reach 100%:

1. **Celebrate!** 🎊 You've completed 3,175 translations!

2. **Update execution log**:
   - Document completion date
   - Note any issues encountered
   - Record time spent

3. **Move to Week 4**: Component Integration
   - Update 10 Change Management components
   - Add `useTranslations('changes')` hook
   - Replace hardcoded strings
   - Test in all languages

4. **Mark Batch 2 Complete**: 85% i18n coverage achieved!

5. **Plan Batch 3**: Financial Module (next ~500 strings)

## 🆘 Need Help?

- **DeepL Issues**: Try Google Translate as backup
- **CSV Format Issues**: Ensure UTF-8 encoding
- **Import Errors**: Check delimiter (should be semicolon `;`)
- **Variable Issues**: Use Find & Replace to fix
- **Layout Issues**: Use shorter translations or abbreviations

---

**Ready to Start?**

1. Open `BATCH2_TRANSLATION_WORKBOOK.csv`
2. Go to https://www.deepl.com/translator
3. Start with German (Column C, rows 103-635)
4. Follow the steps above

**Good luck! You've got this! 💪**

---

**Created**: January 18, 2026  
**Method**: DeepL Web Interface  
**Estimated Time**: 2-4 hours  
**Target**: 100% Batch 2 completion
