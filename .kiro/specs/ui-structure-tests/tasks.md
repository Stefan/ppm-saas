# Implementation Plan: UI Structure Tests

## Overview

This implementation plan breaks down the UI structure tests feature into discrete coding tasks. The approach prioritizes establishing the core infrastructure first, then adding tests incrementally for pages and components.

## Tasks

- [x] 1. Set up test infrastructure and utilities
  - [x] 1.1 Create test ID generator utility
    - Create `lib/testing/test-id.ts` with `generateTestId` and `createTestIdBuilder` functions
    - Implement kebab-case formatting and consistent output
    - Export TypeScript types for test ID generation
    - _Requirements: 1.1, 1.3_
  
  - [x] 1.2 Write property tests for test ID generator
    - **Property 1: Test ID Generation Consistency**
    - Create `__tests__/unit/test-id-generator.property.test.ts`
    - Test that same inputs always produce same outputs
    - Test kebab-case format validation
    - **Validates: Requirements 1.1, 1.3**
  
  - [x] 1.3 Create structure manifest types and schema
    - Create `lib/testing/structure-manifest.ts` with TypeScript interfaces
    - Define `PageStructure`, `ComponentStructure`, `ElementDefinition`, `SectionDefinition`
    - Add manifest validation function
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 1.4 Write property tests for manifest validation
    - **Property 7: Manifest Validation Correctness**
    - Create `__tests__/unit/manifest-validation.property.test.ts`
    - Test valid manifests are accepted
    - Test invalid manifests are rejected with specific errors
    - **Validates: Requirements 5.2, 5.3**

- [x] 2. Checkpoint - Ensure infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create structure verification utilities
  - [x] 3.1 Create E2E structure verification utilities
    - Create `lib/testing/structure-test-utils.ts`
    - Implement `verifyPageStructure`, `verifySection`, `waitForDynamicContent`
    - Implement `captureStructureSnapshot` for failure screenshots
    - _Requirements: 2.1, 7.1, 7.3_
  
  - [x] 3.2 Create unit test structure verification utilities
    - Add `verifyComponentStructure`, `verifyElementsExist` to structure-test-utils
    - Implement accessibility checking helpers
    - _Requirements: 3.1, 7.2_
  
  - [x] 3.3 Write property tests for structure verification
    - **Property 2: Page Structure Verification Correctness**
    - **Property 3: Component Structure Verification Correctness**
    - **Property 6: All Missing Elements Reported**
    - Create `__tests__/unit/structure-verification.property.test.ts`
    - Test verification correctly identifies missing elements
    - Test all missing elements are reported
    - **Validates: Requirements 2.1, 3.1, 3.3, 8.3**
  
  - [x] 3.4 Write property tests for error reporting
    - **Property 5: Error Reporting Completeness**
    - **Property 13: Timeout Error Classification**
    - Test error reports contain expected element, actual state, suggested fix
    - Test timeout errors classify partial vs full failure
    - **Validates: Requirements 8.1, 2.3, 8.5**

- [x] 4. Checkpoint - Ensure verification utilities work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Add data-testid attributes to key components
  - [x] 5.1 Add test IDs to dashboard page components
    - Add data-testid to `app/dashboards/page.tsx` sections
    - Add data-testid to `app/dashboards/components/VarianceKPIs.tsx`
    - Add data-testid to `app/dashboards/components/VarianceTrends.tsx`
    - Add data-testid to KPICard, ProjectCard, AlertChip components
    - _Requirements: 1.2, 1.4_
  
  - [x] 5.2 Add test IDs to shared layout components
    - Add data-testid to `components/shared/AppLayout.tsx`
    - Add data-testid to `components/navigation/TopBar.tsx`
    - Add data-testid to `components/navigation/MobileNav.tsx`
    - _Requirements: 1.2, 1.4_
  
  - [x] 5.3 Add test IDs to financials page components
    - Add data-testid to `app/financials/page.tsx` sections
    - Add data-testid to financial sub-components
    - _Requirements: 1.2, 1.4_
  
  - [x] 5.4 Add test IDs to remaining critical pages
    - Add data-testid to `/projects`, `/resources`, `/reports`, `/risks`
    - Add data-testid to `/scenarios`, `/monte-carlo`, `/admin`, `/audit`
    - Add data-testid to `/changes`, `/feedback`, `/import`
    - _Requirements: 1.2, 1.4_

- [x] 6. Create structure manifests for all pages
  - [x] 6.1 Create dashboard page structure manifest
    - Define all sections and required elements for `/dashboards`
    - Include KPI cards, variance section, health summary, quick actions
    - _Requirements: 5.1, 5.5_
  
  - [x] 6.2 Create financials page structure manifest
    - Define all sections and required elements for `/financials`
    - Include header, metrics, tabs, alerts, tables
    - _Requirements: 5.1, 5.5_
  
  - [x] 6.3 Create remaining page structure manifests
    - Define structures for all other main pages
    - Group by section for organization
    - _Requirements: 5.1, 5.5_

- [x] 7. Checkpoint - Ensure test IDs are in place
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create E2E page structure tests
  - [x] 8.1 Create page structure test framework
    - Create `__tests__/e2e/page-structure.spec.ts`
    - Implement test loop over all page structures
    - Add authentication handling for protected pages
    - _Requirements: 2.1, 2.2, 2.4_
  
  - [x] 8.2 Create dashboard page structure test
    - Test all required sections exist on `/dashboards`
    - Test interactive elements are accessible
    - Capture screenshot on failure
    - _Requirements: 2.1, 2.3, 2.4, 8.2_
  
  - [x] 8.3 Create financials page structure test
    - Test all required sections exist on `/financials`
    - Test tab navigation structure
    - _Requirements: 2.1, 2.3, 2.4_
  
  - [x] 8.4 Create remaining page structure tests
    - Add tests for all other main pages
    - Ensure consistent test patterns
    - _Requirements: 2.2_

- [x] 9. Create component structure unit tests
  - [x] 9.1 Create VarianceKPIs component structure test
    - Create `__tests__/component-structure/variance-kpis.structure.test.tsx`
    - Test all required elements render with valid data
    - Test loading, error, and empty states
    - _Requirements: 3.1, 3.2, 3.4_
  
  - [x] 9.2 Write property test for conditional state verification
    - **Property 4: Conditional State Verification**
    - Test that each state renders exactly the expected elements
    - **Validates: Requirements 3.4**
  
  - [x] 9.3 Create KPI card component structure tests
    - Test dashboard KPI cards render all elements
    - Test different variants and states
    - _Requirements: 3.1, 3.2_
  
  - [x] 9.4 Create navigation component structure tests
    - Test TopBar, MobileNav, Sidebar structure
    - Test responsive behavior
    - _Requirements: 3.1, 3.2_

- [x] 10. Checkpoint - Ensure structure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Set up visual regression testing
  - [x] 11.1 Create visual regression test configuration
    - Create `lib/testing/visual-regression-config.ts`
    - Define pages, viewports, thresholds
    - Configure animation disabling
    - _Requirements: 4.1, 4.5, 4.6_
  
  - [x] 11.2 Create visual regression test suite
    - Create `__tests__/e2e/visual-regression.spec.ts`
    - Implement screenshot capture for all pages
    - Implement viewport iteration (desktop, tablet, mobile)
    - _Requirements: 4.1, 4.2, 4.6_
  
  - [x] 11.3 Write property test for visual diff threshold
    - **Property 8: Visual Diff Threshold Detection**
    - Test that differences above threshold are detected
    - Test that diff images are generated on failure
    - **Validates: Requirements 4.2, 4.3**
  
  - [x] 11.4 Generate initial baseline screenshots
    - Run visual regression tests to capture baselines
    - Commit baseline screenshots to repository
    - _Requirements: 4.1, 4.4_

- [x] 12. Create mock data generators
  - [x] 12.1 Create component mock data generators
    - Create `lib/testing/mock-generators.ts`
    - Implement generators for session, project, financial data
    - Ensure generated data satisfies component prop types
    - _Requirements: 7.5_
  
  - [x] 12.2 Write property test for mock data validity
    - **Property 11: Mock Data Validity**
    - Test generated data satisfies type requirements
    - Test components render without errors with generated data
    - **Validates: Requirements 7.5**

- [x] 13. Checkpoint - Ensure visual regression tests work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Set up CI/CD integration
  - [x] 14.1 Create GitHub Actions workflow
    - Create `.github/workflows/ui-structure-tests.yml`
    - Configure unit test, E2E test, and visual regression jobs
    - Set up artifact upload for failures
    - _Requirements: 6.1, 6.4, 6.5, 6.6_
  
  - [x] 14.2 Add npm scripts for test execution
    - Add `test:structure`, `test:structure:unit`, `test:structure:e2e` scripts
    - Add `test:visual`, `test:visual:update` scripts
    - Add `test:structure:ci` for CI-specific configuration
    - _Requirements: 6.1_
  
  - [x] 14.3 Write property test for report format validity
    - **Property 9: Test Report Format Validity**
    - Test generated reports are valid JSON/XML
    - Test failed tests result in non-zero exit code
    - **Validates: Requirements 6.2, 6.3**
  
  - [x] 14.4 Write property test for summary report completeness
    - **Property 10: Summary Report Completeness**
    - Test summary includes entry for every tested item
    - **Validates: Requirements 8.4**

- [x] 15. Create accessibility verification
  - [x] 15.1 Add accessibility checks to structure verification
    - Extend verification utilities with accessibility checks
    - Check for role, aria-label, aria-describedby attributes
    - _Requirements: 2.4, 7.2_
  
  - [x] 15.2 Write property test for accessibility verification
    - **Property 12: Accessibility Verification**
    - Test interactive elements have accessibility attributes
    - Test violations are reported correctly
    - **Validates: Requirements 2.4, 7.2**

- [x] 16. Final checkpoint - Full test suite validation
  - Ensure all tests pass, ask the user if questions arise.
  - Run full CI workflow locally to validate
  - Verify all property tests pass with 100+ iterations

## Notes

- All tasks are required for comprehensive testing coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Test IDs should be added incrementally to avoid large PRs
