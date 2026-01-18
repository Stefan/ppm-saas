# Complete Remaining Components - Batch Update Guide

## Status: 5 of 10 Complete (50%)

### ✅ Completed
1. ChangeRequestForm.tsx
2. ChangeRequestDetail.tsx
3. PendingApprovals.tsx
4. ApprovalWorkflow.tsx
5. ImplementationMonitoringDashboard.tsx ✅ JUST COMPLETED

### ⏳ Remaining (5 components)
6. ImpactAnalysisDashboard.tsx
7. ImpactEstimationTools.tsx
8. ChangeAnalyticsDashboard.tsx
9. ApprovalWorkflowConfiguration.tsx
10. ImplementationTracker.tsx

## Quick Update Pattern

For each remaining component:

### Step 1: Add Import
```typescript
import { useTranslations } from '@/lib/i18n/context'
```

### Step 2: Add Hook
```typescript
const t = useTranslations('changes');
```

### Step 3: Replace Common Strings
- Titles: `{t('componentName.title')}`
- Subtitles: `{t('componentName.subtitle')}`
- Buttons: `{t('componentName.buttonName')}`
- Labels: `{t('componentName.labelName')}`
- Empty states: `{t('componentName.noData')}`
- Loading: `{t('componentName.loading')}`

### Step 4: Verify
```bash
getDiagnostics(['path/to/component.tsx'])
```

## Translation Keys Available

All keys are in `public/locales/en.json` under `changes.*`:

- `changes.impactAnalysis.*` - 40+ keys
- `changes.impactEstimation.*` - 35+ keys
- `changes.analytics.*` - 30+ keys
- `changes.approvalWorkflowConfiguration.*` - 60+ keys
- `changes.implementationTracker.*` - 80+ keys

## Time Estimate
- Components 6-8: 30 min each = 1.5 hours
- Component 9: 1 hour
- Component 10: 1.5 hours
- **Total**: ~4 hours remaining

