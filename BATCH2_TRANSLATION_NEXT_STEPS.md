# Batch 2 Translation - Next Steps

## Current Status ✅

**Infrastructure Complete:**
- ✅ English keys: 635 keys added to `en.json`
- ✅ Structure: All 5 language files have `changes` object with English placeholders
- ✅ Automation: All scripts created and tested
- ✅ Documentation: Complete guides available
- ✅ Workbook: `BATCH2_TRANSLATION_WORKBOOK.csv` ready (52KB, 635 rows)

**What's Pending:**
- ⏳ Translations: 3,175 strings need translation (635 keys × 5 languages)

## Your Options for Completing Translations

### Option 1: DeepL Web Interface (Recommended) ⭐

**Why This is Best:**
- ✅ Free (no API key needed)
- ✅ Highest quality translations
- ✅ Full control over formality
- ✅ Easy to review and adjust
- ✅ Works with the CSV workbook

**Steps:**
1. Open `BATCH2_TRANSLATION_WORKBOOK.csv` in Google Sheets or Excel
2. Copy Column B (English text) - all 635 rows
3. Go to https://www.deepl.com/translator
4. Paste and translate to German (select formal "Sie")
5. Copy translated text back to Column C
6. Repeat for French (formal "vous"), Spanish (informal "tú"), Polish (formal)
7. For Swiss German, use German translation as base
8. Save the CSV file
9. Run: `npx tsx scripts/import-translations.ts`
10. Run: `npm run generate-types`
11. Run: `npx tsx scripts/check-translation-progress.ts`

**Time Estimate:** 2-4 hours

**Quality:** Excellent (DeepL is industry-leading)

### Option 2: DeepL API (Fastest)

**Requirements:**
- DeepL API key (free tier: 500,000 chars/month)
- Sign up at: https://www.deepl.com/pro-api

**Steps:**
1. Get your DeepL API key
2. I can create an API integration script
3. Run the script (takes 5-10 minutes)
4. Review and adjust if needed

**Time Estimate:** 10-15 minutes (after setup)

**Quality:** Excellent

### Option 3: AI-Assisted (ChatGPT/Claude)

**Steps:**
1. Copy sections of English text from the CSV
2. Ask ChatGPT/Claude to translate with specific instructions:
   - German: Formal "Sie" form, business terminology
   - French: Formal "vous" form, business terminology
   - Spanish: Informal "tú" form, professional style
   - Polish: Formal business Polish
3. Paste translations back into CSV
4. Run import script

**Time Estimate:** 4-6 hours

**Quality:** Very Good (with proper prompting)

### Option 4: Professional Translation Service

**Steps:**
1. Export the English changes object
2. Send to professional translators
3. Import completed translations

**Time Estimate:** 1-2 weeks

**Quality:** Excellent (native speakers)

**Cost:** $200-500

## My Recommendation

**Use Option 1 (DeepL Web Interface)** because:

1. **Free** - No API keys or costs
2. **High Quality** - DeepL is the best free translation tool
3. **Control** - You can review and adjust each translation
4. **Proven** - The CSV workbook is designed for this workflow
5. **Manageable** - 2-4 hours is reasonable for 3,175 strings

## Critical Requirements

When translating, ensure:

### 1. Preserve Interpolation Variables
All variables MUST stay exactly as-is:
- `{count}` → `{count}` (NOT `{anzahl}` or `{nombre}`)
- `{projectName}` → `{projectName}`
- `{changeId}` → `{changeId}`
- `{date}` → `{date}`
- `{email}` → `{email}`

### 2. Maintain Formality Levels
- **German (de)**: Formal "Sie" form (NOT "du")
  - Example: "Sind Sie sicher?" ✅ NOT "Bist du sicher?" ❌
- **French (fr)**: Formal "vous" form (NOT "tu")
  - Example: "Êtes-vous sûr?" ✅ NOT "Es-tu sûr?" ❌
- **Spanish (es)**: Informal "tú" form (per project standards)
  - Example: "¿Estás seguro?" ✅ NOT "¿Está usted seguro?" ❌
- **Polish (pl)**: Formal business Polish
- **Swiss German (gsw)**: Based on German (Baseldytsch characteristics)

### 3. Use Consistent Technical Terms

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

## After Translation is Complete

1. **Import translations:**
   ```bash
   npx tsx scripts/import-translations.ts
   ```

2. **Regenerate TypeScript types:**
   ```bash
   npm run generate-types
   ```

3. **Check progress:**
   ```bash
   npx tsx scripts/check-translation-progress.ts
   ```
   
   Expected output:
   ```
   ✅ German (de): 100% (635/635 keys)
   ✅ French (fr): 100% (635/635 keys)
   ✅ Spanish (es): 100% (635/635 keys)
   ✅ Polish (pl): 100% (635/635 keys)
   ✅ Swiss German (gsw): 100% (635/635 keys)
   
   🎯 Overall Batch 2 Progress: 100%
   ```

4. **Test in application:**
   ```bash
   npm run dev
   ```
   - Switch language in app
   - Navigate to Change Management section
   - Verify translations display correctly
   - Check for layout issues

5. **Update components** (Week 4):
   - Modify 10 Change Management components
   - Add `useTranslations('changes')` hook
   - Replace hardcoded strings
   - Test in all languages

## Resources

- **Translation Workbook**: `BATCH2_TRANSLATION_WORKBOOK.csv`
- **Import Script**: `scripts/import-translations.ts`
- **Progress Checker**: `scripts/check-translation-progress.ts`
- **Complete Guide**: `BATCH2_CSV_TRANSLATION_GUIDE.md`
- **Workflow Guide**: `BATCH2_TRANSLATION_WORKFLOW.md`
- **Status Report**: `BATCH2_TRANSLATION_STATUS.md`

## Timeline

- **Option 1 (DeepL Web)**: 2-4 hours → 100% complete
- **Option 2 (DeepL API)**: 10-15 minutes → 100% complete
- **Option 3 (AI-Assisted)**: 4-6 hours → 100% complete
- **Option 4 (Professional)**: 1-2 weeks → 100% complete

## Success Criteria

- [ ] All 635 keys translated in all 5 languages
- [ ] All interpolation variables preserved
- [ ] Correct formality levels maintained
- [ ] Technical terms consistent
- [ ] Import script runs successfully
- [ ] Progress checker shows 100%
- [ ] TypeScript types regenerated
- [ ] No compilation errors
- [ ] Manual testing passed in all languages

---

**Ready to Start?**

Open `BATCH2_TRANSLATION_WORKBOOK.csv` and begin with German (Column C).

Use DeepL: https://www.deepl.com/translator

Good luck! 🚀
