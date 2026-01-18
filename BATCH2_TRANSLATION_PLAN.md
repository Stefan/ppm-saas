# Batch 2 Translation Completion Plan

## Overview

This document outlines the plan to complete Batch 2 translations before proceeding to Batches 3-8.

## Current Status

- ✅ **English**: 611 keys complete (100%)
- ⏳ **German**: 611 keys need translation (0%)
- ⏳ **French**: 611 keys need translation (0%)
- ⏳ **Spanish**: 611 keys need translation (0%)
- ⏳ **Polish**: 611 keys need translation (0%)
- ⏳ **Swiss German**: 611 keys need translation (0%)

**Total translation work needed**: 3,055 strings

## Translation Options

### Option A: Professional Translation Service
**Recommended for**: Production quality, consistency

**Process**:
1. Send `BATCH2_TRANSLATION_WORKBOOK.csv` to translation service
2. Specify formality levels for each language
3. Request glossary for technical terms
4. Review and import translations

**Estimated Cost**: $0.10-0.20 per word × ~15,000 words = $1,500-3,000
**Estimated Time**: 5-7 business days
**Quality**: High

### Option B: Native Speaker Team
**Recommended for**: Cost savings, internal control

**Process**:
1. Assign one native speaker per language
2. Provide translation guidelines and glossary
3. Use CSV workbook for consistency
4. Peer review translations

**Estimated Cost**: Internal resources
**Estimated Time**: 40-60 hours total (8-12 hours per language)
**Quality**: Medium-High (depends on reviewers)

### Option C: Hybrid Approach
**Recommended for**: Balance of cost and quality

**Process**:
1. Use machine translation for initial draft
2. Native speakers review and correct
3. Focus on high-priority sections first

**Estimated Cost**: Minimal + internal review time
**Estimated Time**: 20-30 hours total
**Quality**: Medium

## Recommended Approach: Phased Translation

### Phase 1: High-Priority Sections (Week 1)
**Focus**: User-facing interfaces
**Sections**: requestForm, pendingApprovals, requestDetail
**Keys**: ~170 per language (850 total)
**Effort**: 15-20 hours

**Deliverable**: Core functionality translated in all languages

### Phase 2: Medium-Priority Sections (Week 2)
**Focus**: Frequently used features
**Sections**: implementationTracker, approvalWorkflow, analytics
**Keys**: ~240 per language (1,200 total)
**Effort**: 20-25 hours

**Deliverable**: Main features fully translated

### Phase 3: Lower-Priority Sections (Week 3)
**Focus**: Admin and advanced features
**Sections**: Configuration, monitoring, analysis, estimation
**Keys**: ~201 per language (1,005 total)
**Effort**: 15-20 hours

**Deliverable**: Complete Batch 2 translation

## Translation Workflow

### Step 1: Prepare
```bash
# Ensure workbook is up to date
npx tsx scripts/export-for-translation.ts
```

### Step 2: Translate
- Open `BATCH2_TRANSLATION_WORKBOOK.csv`
- Fill in translations for assigned language(s)
- Follow language-specific guidelines
- Maintain consistent terminology

### Step 3: Review
- Check for completeness (no empty cells)
- Verify interpolation variables preserved
- Ensure proper formality level
- Test sample strings in context

### Step 4: Import
```bash
# Import completed translations
npx tsx scripts/import-translations.ts

# Regenerate types
npm run generate-types

# Verify
npm run type-check
```

### Step 5: Test
- Switch to translated language in app
- Navigate through Change Management module
- Verify all strings display correctly
- Check for layout issues with longer translations

## Quality Checklist

For each language, verify:

- [ ] All 611 keys translated (no English placeholders)
- [ ] Consistent terminology throughout
- [ ] Proper formality level (Sie/vous/tú/formal/dialect)
- [ ] Interpolation variables preserved: `{count}`, `{projectName}`, etc.
- [ ] Special characters properly handled
- [ ] JSON syntax valid
- [ ] No compilation errors
- [ ] Manual testing passed

## Translation Guidelines

### German (de)
- **Formality**: Formal "Sie" form
- **Style**: Business/professional
- **Key Terms**:
  - Implementation → Implementierung
  - Change Request → Änderungsantrag
  - Approval → Genehmigung
  - Workflow → Arbeitsablauf

### French (fr)
- **Formality**: Formal "vous" form
- **Style**: Business/professional
- **Key Terms**:
  - Implementation → Mise en œuvre
  - Change Request → Demande de modification
  - Approval → Approbation
  - Workflow → Flux de travail

### Spanish (es)
- **Formality**: Informal "tú" form
- **Style**: Professional but approachable
- **Key Terms**:
  - Implementation → Implementación
  - Change Request → Solicitud de cambio
  - Approval → Aprobación
  - Workflow → Flujo de trabajo

### Polish (pl)
- **Formality**: Formal business Polish
- **Style**: Professional
- **Key Terms**:
  - Implementation → Wdrożenie
  - Change Request → Wniosek o zmianę
  - Approval → Zatwierdzenie
  - Workflow → Przepływ pracy

### Swiss German (gsw)
- **Dialect**: Baseldytsch
- **Style**: Keep technical terms recognizable
- **Key Terms**:
  - Implementation → Implementierig
  - Change Request → Änderigaatrag
  - Approval → Genehmigung
  - Workflow → Arbeitsablauf

## Progress Tracking

Update this section as translations are completed:

### Week 1 Progress
- [ ] German - Phase 1 (170 keys)
- [ ] French - Phase 1 (170 keys)
- [ ] Spanish - Phase 1 (170 keys)
- [ ] Polish - Phase 1 (170 keys)
- [ ] Swiss German - Phase 1 (170 keys)

### Week 2 Progress
- [ ] German - Phase 2 (240 keys)
- [ ] French - Phase 2 (240 keys)
- [ ] Spanish - Phase 2 (240 keys)
- [ ] Polish - Phase 2 (240 keys)
- [ ] Swiss German - Phase 2 (240 keys)

### Week 3 Progress
- [ ] German - Phase 3 (201 keys)
- [ ] French - Phase 3 (201 keys)
- [ ] Spanish - Phase 3 (201 keys)
- [ ] Polish - Phase 3 (201 keys)
- [ ] Swiss German - Phase 3 (201 keys)

## After Batch 2 Completion

Once all translations are complete:

1. **Update Components** (10 components)
   - Add `useTranslations('changes')` hook
   - Replace hardcoded strings
   - Test in all languages

2. **Comprehensive Testing**
   - Test all 10 components in all 6 languages
   - Verify layout with longer translations
   - Check interpolations work correctly

3. **Documentation Update**
   - Mark Batch 2 as complete in execution log
   - Update progress tracking
   - Document any issues or learnings

4. **Proceed to Batch 3**
   - Apply same workflow to Financial Module
   - Use lessons learned from Batch 2
   - Continue toward 100% coverage

## Success Criteria

Batch 2 is complete when:
- ✅ All 5 languages fully translated (3,055 strings)
- ✅ All 10 components updated to use translations
- ✅ Zero TypeScript compilation errors
- ✅ Manual testing passed in all 6 languages
- ✅ Documentation updated
- ✅ Ready to proceed to Batch 3

## Timeline

**Optimistic**: 2-3 weeks (with dedicated resources)
**Realistic**: 3-4 weeks (with part-time resources)
**Conservative**: 4-6 weeks (with limited resources)

## Next Actions

1. **Immediate**: Decide on translation approach (A, B, or C)
2. **This Week**: Complete Phase 1 translations (high-priority)
3. **Next Week**: Complete Phase 2 translations (medium-priority)
4. **Following Week**: Complete Phase 3 translations (lower-priority)
5. **Week 4**: Update components and comprehensive testing

---

**Created**: January 18, 2026
**Status**: Ready to Execute
**Next Step**: Choose translation approach and begin Phase 1
