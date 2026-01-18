# Batch 2 Translation - Quick Reference

## 🚀 Quick Start

### For Translators
```bash
# 1. Export keys to CSV
npx tsx scripts/export-for-translation.ts

# 2. Open and fill in translations
open BATCH2_TRANSLATION_WORKBOOK.csv

# 3. Import completed translations
npx tsx scripts/import-translations.ts

# 4. Regenerate types
npm run generate-types
```

### For Developers
```typescript
// Use English keys immediately in components
import { useTranslations } from 'next-intl';

const t = useTranslations('changes');

// Example usage
<h1>{t('implementationTracker.title')}</h1>
<p>{t('pendingApprovals.subtitle')}</p>
```

## 📊 Current Status

| Language | Keys | Status | Progress |
|----------|------|--------|----------|
| English | 611 | ✅ Complete | 100% |
| German | 611 | ⏳ Structure only | 0% |
| French | 611 | ⏳ Structure only | 0% |
| Spanish | 611 | ⏳ Structure only | 0% |
| Polish | 611 | ⏳ Structure only | 0% |
| Swiss German | 611 | ⏳ Structure only | 0% |

## 📁 Key Files

### Scripts
- `scripts/export-for-translation.ts` - Export to CSV
- `scripts/import-translations.ts` - Import from CSV
- `scripts/integrate-batch2-translations.ts` - Add structure

### Data
- `BATCH2_TRANSLATION_WORKBOOK.csv` - Translation workbook
- `public/locales/en.json` - English (complete)
- `public/locales/de.json` - German (needs translation)
- `public/locales/fr.json` - French (needs translation)
- `public/locales/es.json` - Spanish (needs translation)
- `public/locales/pl.json` - Polish (needs translation)
- `public/locales/gsw.json` - Swiss German (needs translation)

### Documentation
- `BATCH2_COMPLETION_REPORT.md` - Full delivery report
- `BATCH2_TRANSLATION_WORKFLOW.md` - Detailed workflow
- `BATCH2_TRANSLATION_STATUS.md` - Current status

## 🎯 Translation Priorities

### High Priority (170 keys)
- requestForm - Change request creation
- pendingApprovals - Approval interface
- requestDetail - Request details

### Medium Priority (240 keys)
- implementationTracker - Implementation tracking
- approvalWorkflow - Workflow interface
- analytics - Analytics dashboard

### Lower Priority (201 keys)
- approvalWorkflowConfiguration - Configuration
- implementationMonitoring - Monitoring
- impactAnalysis - Analysis tools
- impactEstimation - Estimation tools

## 🌍 Translation Guidelines

| Language | Formality | Example |
|----------|-----------|---------|
| German (de) | Formal (Sie) | "Implementierungsverfolgung" |
| French (fr) | Formal (vous) | "Suivi de la mise en œuvre" |
| Spanish (es) | Informal (tú) | "Seguimiento de implementación" |
| Polish (pl) | Formal | "Śledzenie wdrożenia" |
| Swiss German (gsw) | Baseldytsch | "Implementierigsverfolgig" |

## ⚡ Common Commands

```bash
# Export keys
npx tsx scripts/export-for-translation.ts

# Import translations
npx tsx scripts/import-translations.ts

# Regenerate types
npm run generate-types

# Validate
npm run type-check

# Check translation count
grep -c '"changes"' public/locales/*.json
```

## 📈 Progress Tracking

**Overall Batch 2**: 45% complete
- ✅ English keys: 100%
- ✅ Structure: 100%
- ✅ Automation: 100%
- ⏳ Translations: 0%
- ⏳ Components: 0%

## 🎯 Next Steps

1. **Immediate**: Begin German translation
2. **This week**: Complete German, start French/Spanish
3. **Next week**: Complete all translations
4. **Following week**: Update components, test

## 📞 Support

- Full workflow: `BATCH2_TRANSLATION_WORKFLOW.md`
- Status details: `BATCH2_TRANSLATION_STATUS.md`
- Complete report: `BATCH2_COMPLETION_REPORT.md`

---

**Last Updated**: January 18, 2026
**Status**: Ready for Translation
