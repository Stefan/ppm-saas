# Design Document

## Overview

This design addresses the resources page structure verification failure by ensuring the `resources-grid` test ID is always present regardless of view mode. The solution maintains backward compatibility with all three view modes (cards, table, heatmap) while satisfying structure test requirements.

The core approach is to always render a container element with `data-testid="resources-grid"` and conditionally render the appropriate view mode content inside it. This ensures structure tests pass while preserving all existing functionality.

## Architecture

### Current Implementation

The current implementation conditionally renders the entire container with the test ID:

```typescript
{viewMode === 'cards' && (
  <div data-testid="resources-grid" className="...">
    {/* Card view content */}
  </div>
)}

{viewMode === 'table' && (
  <VirtualizedResourceTable ... />
)}

{viewMode === 'heatmap' && (
  <div className="...">
    {/* Heatmap content */}
  </div>
)}
```

**Problem**: The `resources-grid` test ID only exists when `viewMode === 'cards'`, causing structure tests to fail in other modes.

### Proposed Solution

Always render a container with `data-testid="resources-grid"` and conditionally render content inside:

```typescript
<div data-testid="resources-grid">
  {viewMode === 'cards' && (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
      {filteredResources.map((resource) => (
        <ResourceCard key={resource.id} resource={resource} />
      ))}
    </div>
  )}

  {viewMode === 'table' && (
    <Suspense fallback={<SkeletonCard variant="resource" />}>
      <VirtualizedResourceTable 
        resources={filteredResources}
        height={600}
        itemHeight={80}
      />
    </Suspense>
  )}

  {viewMode === 'heatmap' && (
    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-sm border border-gray-200">
      {/* Heatmap content */}
    </div>
  )}
</div>
```

**Benefits**:
- Test ID always present for structure verification
- No functional changes to view modes
- Minimal code changes
- Maintains responsive design
- Preserves all existing styling

## Components and Interfaces

### Modified Component: Resources Page

**File**: `app/resources/page.tsx`

**Changes**:
1. Move `data-testid="resources-grid"` to a parent container
2. Keep all three view mode implementations inside this container
3. Maintain all existing className attributes for styling
4. No changes to component logic or state management

### Component Structure

```
<div data-testid="resources-page">
  <div data-testid="resources-header">
    {/* Header content - unchanged */}
  </div>
  
  {/* Analytics, filters, etc. - unchanged */}
  
  <div data-testid="resources-grid">  {/* Always rendered */}
    {viewMode === 'cards' && <CardsView />}
    {viewMode === 'table' && <TableView />}
    {viewMode === 'heatmap' && <HeatmapView />}
  </div>
</div>
```

## Data Models

No data model changes required. This is purely a structural/DOM change.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Test ID Always Present

*For any* view mode (cards, table, or heatmap), the resources page should always render an element with `data-testid="resources-grid"`.

**Validates: Requirements 1.1, 4.4**

### Property 2: View Mode Content Exclusivity

*For any* view mode, exactly one view mode's content should be rendered inside the resources-grid container (cards XOR table XOR heatmap).

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: View Mode Switching Preserves Structure

*For any* sequence of view mode changes, the resources-grid test ID should remain present throughout all transitions.

**Validates: Requirements 2.4, 4.5**

### Property 4: Required Elements Present

*For any* page load, all three required test IDs (resources-header, resources-title, resources-grid) should be present in the DOM.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

## Error Handling

No new error handling required. The change is structural only and doesn't introduce new error conditions.

Existing error handling remains:
- Loading states display skeleton components
- Error states display error messages
- Empty states are handled by existing logic

## Testing Strategy

### Unit Tests

1. **Test: resources-grid test ID exists in all view modes**
   - Render page with viewMode='cards', verify test ID present
   - Render page with viewMode='table', verify test ID present
   - Render page with viewMode='heatmap', verify test ID present

2. **Test: Only one view mode renders at a time**
   - Set viewMode='cards', verify only card content visible
   - Set viewMode='table', verify only table content visible
   - Set viewMode='heatmap', verify only heatmap content visible

3. **Test: View mode switching updates content**
   - Start with cards view
   - Switch to table view, verify table renders
   - Switch to heatmap view, verify heatmap renders
   - Switch back to cards, verify cards render

### Property-Based Tests

Each property test should run a minimum of 100 iterations.

1. **Property Test: Test ID Always Present (Property 1)**
   - **Tag**: Feature: resources-page-structure-fix, Property 1: Test ID Always Present
   - Generate random view modes
   - Render page with each view mode
   - Assert resources-grid test ID exists

2. **Property Test: View Mode Content Exclusivity (Property 2)**
   - **Tag**: Feature: resources-page-structure-fix, Property 2: View Mode Content Exclusivity
   - Generate random view modes
   - Render page with each view mode
   - Assert exactly one view mode content is visible

3. **Property Test: View Mode Switching Preserves Structure (Property 3)**
   - **Tag**: Feature: resources-page-structure-fix, Property 3: View Mode Switching Preserves Structure
   - Generate random sequences of view mode changes
   - Apply each change
   - Assert resources-grid test ID remains present after each change

4. **Property Test: Required Elements Present (Property 4)**
   - **Tag**: Feature: resources-page-structure-fix, Property 4: Required Elements Present
   - Generate random view modes and page states
   - Render page
   - Assert all three required test IDs present

### Integration Tests

1. **E2E Test: Structure verification passes**
   - Run existing structure verification test suite
   - Verify resources page passes all checks
   - Test with different view modes

2. **E2E Test: User can switch view modes**
   - Navigate to resources page
   - Click view mode toggle button
   - Verify each view mode displays correctly
   - Verify no console errors

### Testing Library

- **Unit/Property Tests**: React Testing Library with Jest
- **Property-Based Testing**: fast-check (JavaScript property testing library)
- **E2E Tests**: Playwright (already in use for structure tests)

### Test Configuration

- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tests should run in CI/CD pipeline
- Structure tests should run on every PR
