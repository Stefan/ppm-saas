# Dependency Optimization Summary
## Bundle Size Reduction - Phase 3

**Date:** January 18, 2026  
**Focus:** Identify and optimize dependencies

---

## Current Bundle Status

### Total Bundle Size: ~3441 KiB (3.36 MiB)

| Chunk | Size | % | Status |
|-------|------|---|--------|
| 4145 (TipTap Editor) | 962 KiB | 28.0% | ✅ Optimized (lazy loaded) |
| charts-vendor (Recharts) | 397 KiB | 11.5% | ⚠️ Shared across many pages |
| 9993 (Unknown) | 378 KiB | 11.0% | 🔍 Needs analysis |
| supabase-vendor | 157 KiB | 4.6% | ✅ Necessary |
| vendor | 152 KiB | 4.4% | 🔍 Can be optimized |
| 5923 (Unknown) | 147 KiB | 4.3% | 🔍 Needs analysis |
| react-vendor | 137 KiB | 4.0% | ✅ Necessary |
| markdown-vendor | 113 KiB | 3.3% | ✅ Necessary |
| polyfills | 110 KiB | 3.2% | ✅ Necessary |
| Other chunks | ~888 KiB | 25.8% | Various page bundles |

**Target:** 1500 KiB  
**Current:** 3441 KiB  
**Over Budget:** 1941 KiB (229%)

---

## Dependency Analysis

### 1. Unused Dependencies Removed ✅

**Removed:**
- `html2canvas` - Not used anywhere in codebase
- `react-dropzone` - Not used anywhere in codebase
- `@tiptap/extension-collaboration` - Not used (15 packages removed)
- `@tiptap/extension-collaboration-cursor` - Not used

**Impact:** Minimal (tree-shaking already excluded these)

### 2. Recharts Usage Analysis 🔍

**Size:** 397 KiB  
**Used In:** 16+ files across multiple pages

**Pages using Recharts:**
- `/dashboards` - DashboardCharts, VarianceTrends
- `/financials` - 5 different views (Overview, Analysis, Trends, Detailed, Commitments)
- `/risks` - RiskCharts
- `/changes` - 3 dashboards (Analytics, Impact Analysis, Performance Monitoring)
- `/audit` - Timeline
- `/admin` - ChartSection
- Components: InteractiveChart, MobileOptimizedChart, RealTimeChart

**Status:** ✅ Already optimized
- Properly split into separate vendor chunk
- Shared across many pages (good caching)
- Cannot be lazy loaded (used on initial page load)

**Recommendation:** Keep as-is

### 3. TipTap Editor Analysis ✅

**Size:** 962 KiB  
**Used In:** PMR pages only

**Status:** ✅ Already optimized
- Lazy loaded via ResponsivePMREditor
- Only loads when user accesses PMR pages
- StarterKit replaced with selective imports (no size change)

**Recommendation:** Accept current size

### 4. React-Datepicker Analysis 🎯

**Size:** Part of vendor chunk (~20-30 KiB estimated)  
**Used In:** 1 file only (`components/audit/AuditFilters.tsx`)

**Opportunity:** ⚠️ Low priority
- Only used in audit page
- Could be lazy loaded
- Relatively small size
- Would require refactoring AuditFilters

**Recommendation:** Low priority optimization

### 5. React-Markdown Analysis ✅

**Size:** 113 KiB (markdown-vendor chunk)  
**Used In:** Multiple places

**Status:** ✅ Already optimized
- Properly split into separate vendor chunk
- Includes: react-markdown, remark-gfm, rehype-highlight
- Used for rendering markdown content

**Recommendation:** Keep as-is

### 6. React-Window Analysis ✅

**Size:** Part of vendor chunk (~10-15 KiB estimated)  
**Used In:** 3 virtualized components

**Files:**
- `components/ui/VirtualizedProjectSelector.tsx`
- `components/ui/VirtualizedResourceTable.tsx`
- `components/ui/VirtualizedProjectList.tsx`

**Status:** ✅ Necessary for performance
- Enables virtual scrolling for large lists
- Critical for performance with large datasets
- Small size relative to benefit

**Recommendation:** Keep as-is

---

## Unknown Chunks Analysis

### Chunk 9993 (378 KiB) 🔍

**Shared By:**
- `/financials` page
- `/changes` page
- `/resources` page
- `/admin/navigation-stats` page

**Likely Contains:**
- Shared UI components
- Common utilities
- Possibly some Recharts components
- Lucide icons (if not fully split)

**Next Steps:**
1. Open `.next/analyze/client.html` in browser
2. Search for chunk "9993"
3. Identify exact contents
4. Determine if can be split further

### Chunk 5923 (147 KiB) 🔍

**Needs Investigation:**
- Unknown contents
- Likely another shared component chunk

**Next Steps:**
1. Analyze in bundle analyzer
2. Identify contents
3. Determine optimization strategy

---

## Optimization Opportunities

### Priority 1: Analyze Unknown Chunks 🔴

**Action:** Open bundle analyzer and identify chunk contents

```bash
# Already generated, just open in browser
open .next/analyze/client.html
```

**Expected Outcome:**
- Identify what's in chunks 9993 and 5923
- Find opportunities for further splitting
- Identify any duplicate code

**Potential Savings:** 100-200 KiB

### Priority 2: Optimize Vendor Chunk 🟡

**Current Size:** 152 KiB  
**Target:** 100 KiB  
**Potential Savings:** 50 KiB

**Approach:**
1. Analyze vendor chunk contents in bundle analyzer
2. Identify any unused code
3. Check for duplicate dependencies
4. Consider splitting into more granular chunks

### Priority 3: Page-Level Optimization 🟡

**Target Pages:**
- `/resources` - Likely has large bundle
- `/reports/pmr` - Uses TipTap (already lazy loaded)
- `/financials` - Multiple views with Recharts

**Approach:**
1. Ensure all heavy components are lazy loaded
2. Check for unnecessary imports
3. Optimize component rendering

**Potential Savings:** 100-150 KiB

### Priority 4: Consider Revised Target 🟢

**Current Reality:**
- TipTap: 962 KiB (necessary for rich text editing)
- Recharts: 397 KiB (used across 16+ files)
- Core dependencies: ~600 KiB (React, Supabase, etc.)
- **Minimum realistic:** ~2000 KiB

**Revised Target Options:**

**Option A: Aggressive (1800 KiB)**
- Requires replacing TipTap with lighter editor
- Significant development effort
- May impact UX

**Option B: Moderate (2200 KiB)**
- Optimize unknown chunks (-200 KiB)
- Optimize vendor chunk (-50 KiB)
- Page-level optimizations (-100 KiB)
- **Achievable without major changes**

**Option C: Realistic (2500 KiB)**
- Optimize unknown chunks (-150 KiB)
- Minor vendor optimizations (-25 KiB)
- **Easiest to achieve**

---

## Recommendations

### Immediate Actions

1. **Open Bundle Analyzer** 📊
   ```bash
   open .next/analyze/client.html
   ```
   - Identify contents of chunks 9993 and 5923
   - Look for optimization opportunities
   - Document findings

2. **Set Realistic Target** 🎯
   - Recommend: **2200 KiB** (Option B)
   - 36% reduction from original 3441 KiB
   - Achievable without major architectural changes
   - Still significant performance improvement

3. **Focus on High-Impact Optimizations** 💪
   - Unknown chunks (378 KiB + 147 KiB = 525 KiB)
   - Vendor chunk optimization (152 KiB)
   - Page-level lazy loading

### What NOT to Do ❌

1. **Don't replace TipTap** - Already optimized, good UX
2. **Don't try to optimize Recharts** - Used everywhere, already split
3. **Don't remove react-window** - Critical for performance
4. **Don't sacrifice UX for marginal gains** - Focus on real wins

---

## Next Steps

### Phase 1: Analysis (30 minutes)
1. ✅ Remove unused dependencies
2. 🔄 Open bundle analyzer
3. 🔄 Identify chunk 9993 contents
4. 🔄 Identify chunk 5923 contents
5. 🔄 Document findings

### Phase 2: Optimization (2-3 hours)
1. Split large shared chunks if possible
2. Optimize vendor chunk
3. Implement page-level lazy loading
4. Test and validate

### Phase 3: Validation (30 minutes)
1. Run bundle size check
2. Run Lighthouse audit
3. Verify performance improvements
4. Update documentation

---

## Conclusion

### What We've Learned ✅

1. **Tree-shaking works well** - Unused deps weren't in bundle
2. **Recharts is necessary** - Used across 16+ files
3. **TipTap is already optimized** - Lazy loaded, reasonable size
4. **Unknown chunks need investigation** - 525 KiB to analyze

### Realistic Assessment 📊

**Original Target:** 1500 KiB  
**Current Size:** 3441 KiB  
**Realistic Target:** 2200 KiB  
**Achievable Reduction:** ~1200 KiB (35%)

### Next Command 🚀

```bash
open .next/analyze/client.html
```

This will show the exact contents of each chunk and help us make data-driven decisions about further optimization.

