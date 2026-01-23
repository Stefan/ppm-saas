# Design System Component Audit

## Executive Summary

This audit identifies components using inconsistent styles that should be migrated to the new design system. The analysis focuses on:
- Buttons using non-standard colors and styles
- Input fields with inconsistent styling
- Cards and containers with varied styling approaches
- Components using non-design-token spacing and colors

## Priority Classification

### Priority 1: High-Traffic Components (Immediate Migration)
Components used frequently across the application that have the most visual impact.

### Priority 2: Medium-Traffic Components (Next Phase)
Components used in specific features but still important for consistency.

### Priority 3: Low-Traffic Components (Future Migration)
Test files, examples, and rarely-used components.

---

## 1. Button Components Requiring Migration

### Priority 1: High-Traffic Buttons

#### 1.1 Navigation Buttons
**File**: `components/navigation/TopBar.tsx`
- **Lines**: 97, 276, 287, 322
- **Current Style**: `p-2 rounded-lg hover:bg-gray-100`, `rounded-xl shadow-lg`
- **Issues**: Inconsistent padding, non-standard rounded values
- **Migration**: Replace with `<Button variant="secondary" size="sm">`
- **Usage Frequency**: Very High (appears on every page)

#### 1.2 Performance Optimizer Button
**File**: `components/performance/PerformanceOptimizer.tsx`
- **Line**: 323
- **Current Style**: `bg-blue-600 text-white px-3 py-2 rounded-lg shadow-lg hover:bg-blue-700`
- **Issues**: Using `blue-600` instead of `primary-600`, inconsistent spacing
- **Migration**: Replace with `<Button variant="primary" size="sm">`
- **Usage Frequency**: High

#### 1.3 Cache Management Buttons
**File**: `components/admin/CacheManagement.tsx`
- **Lines**: 83, 91
- **Current Style**: `px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700`
- **Issues**: Using `blue-600` instead of `primary-600`, `rounded-md` instead of design token
- **Migration**: Replace with `<Button variant="primary" size="md">`
- **Usage Frequency**: Medium

#### 1.4 Workflow Approval Buttons
**File**: `components/workflow/ApprovalButtons.tsx`
- **Lines**: 97, 105
- **Current Style**: `bg-green-600 text-white px-4 py-3 rounded-lg`, `bg-red-600 text-white px-4 py-3 rounded-lg`
- **Issues**: Using semantic colors directly, inconsistent spacing
- **Migration**: Create semantic button variants or use existing with custom classes
- **Usage Frequency**: High

### Priority 2: Medium-Traffic Buttons

#### 2.1 Session Restoration Buttons
**File**: `components/device-management/SessionRestoration.tsx`
- **Lines**: 151, 158, 174, 196, 253, 357
- **Current Style**: Various inline styles with `p-2`, `px-4 py-2`, `rounded-lg`
- **Issues**: Inconsistent sizing and spacing
- **Migration**: Replace with appropriate Button component variants
- **Usage Frequency**: Medium

#### 2.2 PO Breakdown Buttons
**File**: `components/sap-po/POBreakdownTreeView.tsx`
- **Lines**: 152, 243, 253, 263, 478, 485
- **Current Style**: Various inline styles, some with `text-blue-600 hover:text-blue-700`
- **Issues**: Inconsistent button styles, using blue instead of primary
- **Migration**: Replace with Button component
- **Usage Frequency**: Medium

#### 2.3 PO Financial Dashboard Buttons
**File**: `components/sap-po/POFinancialDashboard.tsx`
- **Lines**: 288, 321, 334, 508, 514, 592, 598
- **Current Style**: Mix of inline styles and Button component usage
- **Issues**: Some buttons already use Button component, others don't
- **Migration**: Ensure all use Button component consistently
- **Usage Frequency**: Medium

### Priority 3: Low-Traffic Buttons (Test Files & Examples)

#### 3.1 Test File Buttons
**Files**: Various `__tests__/*.tsx` files
- **Issues**: Test files using inline styles for mock components
- **Migration**: Update test mocks to use Button component
- **Usage Frequency**: Low (test-only)

#### 3.2 Example File Buttons
**File**: `hooks/usePermissions.example.tsx`
- **Issues**: Example code with inline styles
- **Migration**: Update examples to demonstrate Button component usage
- **Usage Frequency**: Low (documentation-only)

---

## 2. Input Components Requiring Migration

### Priority 1: High-Traffic Inputs

#### 2.1 Login Page Inputs
**File**: `app/page.tsx`
- **Lines**: 243, 261
- **Current Style**: Inline className with various styles
- **Issues**: Not using Input component
- **Migration**: Replace with `<Input size="md" label="Email">`
- **Usage Frequency**: Very High (login page)

#### 2.2 Import Page File Input
**File**: `app/import/page.tsx`
- **Line**: 190
- **Current Style**: Dropzone input with inline styles
- **Issues**: File input with custom styling
- **Migration**: May need custom styling, but should use design tokens
- **Usage Frequency**: High

#### 2.3 Monte Carlo Configuration Inputs
**File**: `app/monte-carlo/page.tsx`
- **Lines**: 360, 379
- **Current Style**: Number inputs with inline styles
- **Issues**: Not using Input component
- **Migration**: Replace with `<Input type="number" size="md">`
- **Usage Frequency**: High

### Priority 2: Medium-Traffic Inputs

#### 2.4 Semantic Search Input
**File**: `components/audit/SemanticSearch.tsx`
- **Line**: 186
- **Current Style**: Search input with custom styling
- **Issues**: Not using Input component
- **Migration**: Replace with `<Input type="search" size="md">`
- **Usage Frequency**: Medium

#### 2.5 Workflow Comment Textarea
**File**: `components/workflow/ApprovalButtons.tsx`
- **Line**: 146
- **Current Style**: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500`
- **Issues**: Similar to Input but textarea, not using component
- **Migration**: Create Textarea component based on Input design
- **Usage Frequency**: Medium

#### 2.6 Help Chat Textarea
**File**: `components/HelpChat.tsx`
- **Lines**: 286, 430
- **Current Style**: Custom textarea with inline styles
- **Issues**: Not using Input/Textarea component
- **Migration**: Replace with Textarea component
- **Usage Frequency**: High

### Priority 3: Low-Traffic Inputs (Test Files)

#### 3.1 Test File Inputs
**Files**: Various `__tests__/*.tsx` files
- **Issues**: Test files using inline styles for mock inputs
- **Migration**: Update test mocks to use Input component
- **Usage Frequency**: Low (test-only)

---

## 3. Card/Container Components Requiring Migration

### Priority 1: High-Traffic Cards

#### 3.1 Dashboard KPI Cards
**File**: `__tests__/schedule-dashboard-integration.test.tsx`
- **Lines**: 164, 192, 248, 308, 363
- **Current Style**: `bg-white rounded-lg border p-4`
- **Issues**: Not using Card component
- **Migration**: Replace with `<Card padding="md" shadow="sm" border>`
- **Usage Frequency**: Very High (dashboard)

#### 3.2 PO Financial Dashboard Cards
**File**: `components/sap-po/POFinancialDashboard.tsx`
- **Lines**: 213, 224, 235, 253, 275, 345, 363, 380
- **Current Style**: `bg-white rounded-lg border border-gray-200 p-4` or `p-6`
- **Issues**: Not using Card component, inconsistent padding
- **Migration**: Replace with `<Card padding="md" shadow="sm" border>`
- **Usage Frequency**: High

#### 3.3 Workflow Status Cards
**File**: `components/workflow/WorkflowStatus.tsx`
- **Lines**: 206, 251
- **Current Style**: `bg-white rounded-lg border border-gray-200 p-4`
- **Issues**: Not using Card component
- **Migration**: Replace with `<Card padding="md" shadow="sm" border>`
- **Usage Frequency**: High

### Priority 2: Medium-Traffic Cards

#### 3.4 AI Insights Widget Cards
**File**: `components/ai/PredictiveInsightsWidget.tsx`
- **Lines**: 110, 161, 218
- **Current Style**: Mix of card-like containers with various styles
- **Issues**: Not using Card component consistently
- **Migration**: Replace with Card component
- **Usage Frequency**: Medium

#### 3.5 Error Boundary Cards
**Files**: `components/error-boundaries/*.tsx`
- **Lines**: Various
- **Current Style**: Custom error display cards
- **Issues**: Not using Card component
- **Migration**: Replace with Card component for consistency
- **Usage Frequency**: Medium (error states)

### Priority 3: Low-Traffic Cards

#### 3.6 Test File Cards
**Files**: Various `__tests__/*.tsx` files
- **Issues**: Test files using inline styles for mock cards
- **Migration**: Update test mocks to use Card component
- **Usage Frequency**: Low (test-only)

---

## 4. Color Usage Issues

### Non-Standard Color Usage (Should use Design Tokens)

#### 4.1 Blue Color Variants
**Files**: Multiple files using `bg-blue-50`, `bg-blue-600`, `text-blue-600`, etc.
- **Should use**: `bg-primary-50`, `bg-primary-600`, `text-primary-600`
- **Affected Files**: 
  - `components/admin/SetupHelp.tsx`
  - `components/admin/CacheManagement.tsx`
  - `components/performance/PerformanceOptimizer.tsx`
  - Many test files

#### 4.2 Semantic Colors (Yellow, Red, Green)
**Files**: Multiple files using `bg-yellow-50`, `bg-red-50`, `bg-green-50`, etc.
- **Should use**: `bg-semantic-warning`, `bg-semantic-error`, `bg-semantic-success`
- **Affected Files**:
  - `components/resources/ResourceActionButtons.tsx`
  - `components/admin/SetupHelp.tsx`
  - `components/admin/AuditTrailViewer.tsx`
  - `components/offline/OfflineIndicator.tsx`

---

## 5. Spacing Issues

### Inconsistent Padding/Margin Values

#### 5.1 Non-Standard Padding
**Pattern**: `px-3 py-2`, `px-4 py-3`, `p-2`, `p-3`, `p-4`, `p-6`
- **Issue**: Using values outside design token scale (should use 0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16)
- **Affected**: Most components listed above
- **Migration**: Map to nearest design token value

---

## 6. Border Radius Issues

### Inconsistent Border Radius Values

#### 6.1 Various Rounded Values
**Pattern**: `rounded-lg`, `rounded-md`, `rounded-xl`, `rounded-full`
- **Issue**: Should use design token values (sm, DEFAULT, md, lg, full)
- **Affected**: Most components listed above
- **Migration**: Standardize to design token values

---

## Migration Priority Summary

### Immediate (Week 1)
1. Navigation buttons (TopBar.tsx) - Very High Impact
2. Login page inputs (app/page.tsx) - Very High Impact
3. Dashboard cards (schedule-dashboard-integration.test.tsx) - High Impact
4. Help Chat textarea (HelpChat.tsx) - High Impact

### Next Phase (Week 2)
1. Performance Optimizer button
2. Cache Management buttons
3. Workflow Approval buttons
4. PO Financial Dashboard cards
5. Monte Carlo inputs

### Future (Week 3+)
1. Test file components
2. Example file components
3. Error boundary cards
4. Lower-traffic feature components

---

## Estimated Impact

### Components to Migrate
- **Buttons**: ~50 instances across 20+ files
- **Inputs**: ~30 instances across 15+ files
- **Cards**: ~40 instances across 15+ files

### Files to Update
- **Priority 1**: 10 files
- **Priority 2**: 15 files
- **Priority 3**: 30+ files (mostly tests)

### Expected Benefits
- **Consistency**: 100% visual consistency across all components
- **Maintainability**: Single source of truth for component styles
- **Accessibility**: All components meet WCAG AA standards
- **Performance**: Reduced CSS bundle size through token reuse
- **Developer Experience**: Faster development with reusable components

---

## Next Steps

1. ✅ Complete this audit
2. ⏭️ Migrate Priority 1 components (High-traffic)
3. ⏭️ Migrate Priority 2 components (Medium-traffic)
4. ⏭️ Clean up globals.css
5. ⏭️ Update test files to use new components
6. ⏭️ Add ESLint rules to prevent regression
