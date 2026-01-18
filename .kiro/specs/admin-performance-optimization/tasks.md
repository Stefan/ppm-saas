# Implementation Plan: Admin Performance Optimization

## Overview

This implementation plan transforms the admin performance page from a monolithic, synchronously-loaded component into a progressively-enhanced, performance-optimized experience. The approach follows a phased strategy: first establishing the foundation with skeleton loaders and layout stability, then implementing code splitting and lazy loading, followed by bundle optimization, animation improvements, and finally performance monitoring. Each task builds incrementally, ensuring the page remains functional throughout the optimization process.

## Tasks

- [x] 1. Create skeleton loader components with fixed dimensions
  - Create ChartSkeleton component with 300px height matching final chart dimensions
  - Create TableSkeleton component matching slow queries table dimensions
  - Create StatsSkeleton component for cache statistics section
  - Add CSS animations using transform and opacity for pulse effect
  - _Requirements: 2.1, 2.2, 7.3_

- [x] 2. Extract chart section into separate component for lazy loading
  - [x] 2.1 Create new ChartSection component file
    - Move chart rendering logic from main page to components/admin/ChartSection.tsx
    - Accept endpointData and slowQueriesData as props
    - Use selective Recharts imports (BarChart, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer)
    - Wrap component in React.memo() to prevent unnecessary re-renders
    - _Requirements: 3.3, 3.4, 8.2_
  
  - [x] 2.2 Write property test for chart component memoization
    - **Property 16: State Updates Are Batched**
    - **Validates: Requirements 8.4**
  
  - [x] 2.3 Define explicit chart dimensions in ChartSection
    - Set ResponsiveContainer width="100%" height={300}
    - Ensure dimensions match ChartSkeleton exactly
    - _Requirements: 2.2_

- [x] 3. Implement lazy loading for chart section
  - [x] 3.1 Add React.lazy() import for ChartSection in main page
    - Replace direct import with React.lazy(() => import('./components/admin/ChartSection'))
    - Wrap lazy component in Suspense with ChartSkeleton fallback
    - _Requirements: 3.4, 7.2, 7.5_
  
  - [x] 3.2 Write property test for lazy loading timing
    - **Property 13: Charts Load After Initial Render**
    - **Validates: Requirements 7.2**
  
  - [x] 3.3 Write property test for dynamic imports
    - **Property 4: Third-Party Libraries Use Dynamic Imports**
    - **Validates: Requirements 1.5, 3.4**

- [x] 4. Extract and lazy load slow queries table
  - [x] 4.1 Create SlowQueriesTable component
    - Move table rendering logic to components/admin/SlowQueriesTable.tsx
    - Accept slowQueriesData as props
    - Wrap in React.memo()
    - _Requirements: 3.4, 8.2_
  
  - [x] 4.2 Implement lazy loading for table
    - Use React.lazy() for SlowQueriesTable
    - Wrap in Suspense with TableSkeleton fallback
    - _Requirements: 3.4, 7.5_

- [x] 5. Extract and lazy load cache statistics
  - [x] 5.1 Create CacheStatsCard component
    - Move cache statistics rendering to components/admin/CacheStatsCard.tsx
    - Accept cacheStats as props
    - Wrap in React.memo()
    - _Requirements: 3.4, 8.2_
  
  - [x] 5.2 Implement lazy loading for cache stats
    - Use React.lazy() for CacheStatsCard
    - Wrap in Suspense with StatsSkeleton fallback
    - _Requirements: 3.4, 7.5_

- [x] 6. Optimize data fetching and state management
  - [x] 6.1 Implement request cancellation with AbortController
    - Create AbortController for each fetch cycle
    - Cancel pending requests before starting new ones
    - Clean up AbortController on component unmount
    - _Requirements: 8.3_
  
  - [x] 6.2 Write property test for request cancellation
    - **Property 15: Pending Requests Cancelled on Refresh**
    - **Validates: Requirements 8.3**
  
  - [x] 6.3 Batch state updates using React.startTransition
    - Wrap related state updates (stats, health, cache) in startTransition
    - Ensure single render cycle for multiple state changes
    - _Requirements: 8.4_
  
  - [x] 6.4 Memoize data transformations
    - Wrap prepareEndpointData in useMemo with proper dependencies
    - Memoize slowQueriesData transformation
    - _Requirements: 8.5_
  
  - [x] 6.5 Write unit tests for data transformation edge cases
    - Test empty data handling
    - Test malformed data handling
    - Test large dataset performance
    - _Requirements: 8.5_

- [x] 7. Checkpoint - Verify lazy loading and layout stability
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Optimize CSS animations for GPU compositing
  - [x] 8.1 Update refresh button animation
    - Replace any layout-triggering properties with transform
    - Use transform: rotate() for spin animation
    - Add will-change: transform only during animation
    - Remove will-change after animation completes
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 8.2 Write property test for animation properties
    - **Property 9: Animations Use Only Compositable Properties**
    - **Validates: Requirements 5.1, 5.3, 5.5**
  
  - [x] 8.3 Write property test for will-change usage
    - **Property 10: Will-Change Only on Active Animations**
    - **Validates: Requirements 5.4**
  
  - [x] 8.4 Optimize skeleton loader animations
    - Ensure pulse animation uses only transform and opacity
    - Verify no layout recalculations during animation
    - _Requirements: 5.1, 5.3, 5.5_

- [x] 9. Implement Web Vitals monitoring
  - [x] 9.1 Create usePerformanceMonitoring hook
    - Use web-vitals library to measure LCP, FID, CLS, TTFB, INP, FCP
    - Send metrics to analytics endpoint
    - Track component render times using React Profiler
    - Monitor long tasks using PerformanceObserver
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 9.2 Write property test for Web Vitals tracking
    - **Property 17: Web Vitals Measured and Reported**
    - **Validates: Requirements 9.1, 9.2**
  
  - [x] 9.3 Write property test for long task monitoring
    - **Property 2: No Long Tasks Exceed Threshold**
    - **Validates: Requirements 1.2, 9.4**
  
  - [x] 9.4 Integrate monitoring hook into PerformanceDashboard
    - Call usePerformanceMonitoring in main component
    - Log metrics to console in development
    - Send to analytics in production
    - _Requirements: 9.1, 9.2_

- [x] 10. Add error boundaries for lazy-loaded components
  - [x] 10.1 Create ChartErrorBoundary component
    - Implement getDerivedStateFromError and componentDidCatch
    - Display user-friendly error message on failure
    - Log errors for debugging
    - _Requirements: 6.1, 6.2_
  
  - [x] 10.2 Wrap lazy components in error boundaries
    - Wrap ChartSection in ChartErrorBoundary
    - Wrap SlowQueriesTable in error boundary
    - Wrap CacheStatsCard in error boundary
    - _Requirements: 6.1_
  
  - [x] 10.3 Write unit tests for error boundary behavior
    - Test error boundary catches and displays fallback
    - Test error logging functionality
    - Test recovery after error
    - _Requirements: 6.1_

- [x] 11. Optimize bundle configuration in next.config.ts
  - [x] 11.1 Verify code splitting configuration
    - Ensure webpack splitChunks separates vendor, charts, and page code
    - Verify Recharts is in separate chunk
    - Confirm React/React-DOM in separate vendor chunk
    - _Requirements: 3.1_
  
  - [x] 11.2 Enable production source maps with hidden-source-map
    - Set productionBrowserSourceMaps to true in next.config.ts
    - Configure devtool: 'hidden-source-map' for production
    - Verify source maps are generated but not referenced in bundle
    - _Requirements: 6.3, 6.4_
  
  - [x] 11.3 Verify tree-shaking configuration
    - Ensure usedExports: true in webpack config
    - Confirm sideEffects: false for optimization
    - _Requirements: 3.2, 4.1_

- [x] 12. Create bundle size monitoring script
  - [x] 12.1 Create scripts/check-bundle-size.js
    - Calculate total JavaScript bundle size from .next/static/chunks
    - Fail build if total exceeds 1,500 KiB
    - Log bundle size breakdown by chunk
    - _Requirements: 3.6, 9.5_
  
  - [x] 12.2 Add bundle size test to package.json
    - Add "test:bundle": "node scripts/check-bundle-size.js" script
    - Integrate into CI/CD pipeline
    - _Requirements: 9.5_
  
  - [x] 12.3 Write property test for bundle size limit
    - **Property 7: Total JavaScript Bundle Under Size Limit**
    - **Validates: Requirements 3.6**

- [x] 13. Checkpoint - Verify performance improvements
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Configure Lighthouse CI for automated testing
  - [x] 14.1 Update lighthouserc.js with admin performance page
    - Add /admin/performance to URL list
    - Set assertions for TBT < 200ms, CLS < 0.1
    - Configure FCP < 1500ms, LCP < 2500ms, TTI < 3500ms
    - _Requirements: 1.1, 2.6, 7.1_
  
  - [x] 14.2 Add Lighthouse test script to package.json
    - Ensure "lighthouse:ci": "lhci autorun --assert" exists
    - Test locally before committing
    - _Requirements: 9.5_

- [x] 15. Implement critical CSS inlining
  - [x] 15.1 Identify critical CSS for above-the-fold content
    - Extract CSS for header, metric cards, and skeleton loaders
    - Create critical.css file with minimal styles
    - _Requirements: 10.1_
  
  - [x] 15.2 Configure Next.js to inline critical CSS
    - Use _document.tsx to inline critical styles
    - Defer non-critical CSS loading
    - _Requirements: 10.1, 10.2_
  
  - [x] 15.3 Write property test for CSS blocking
    - **Property 19: CSS Does Not Block First Contentful Paint**
    - **Validates: Requirements 10.5**

- [x] 16. Add comprehensive property-based tests
  - [x] 16.1 Write property test for Total Blocking Time
    - **Property 1: Total Blocking Time Under Threshold**
    - **Validates: Requirements 1.1**
  
  - [x] 16.2 Write property test for critical content timing
    - **Property 3: Critical Content Renders Before Non-Critical Scripts**
    - **Validates: Requirements 1.3**
  
  - [x] 16.3 Write property test for Cumulative Layout Shift
    - **Property 5: Cumulative Layout Shift Below Threshold**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6**
  
  - [x] 16.4 Write property test for skeleton dimensions
    - **Property 6: Skeleton Dimensions Match Final Content**
    - **Validates: Requirements 2.1, 7.3**
  
  - [x] 16.5 Write property test for critical content render time
    - **Property 12: Critical Content Renders Within Time Budget**
    - **Validates: Requirements 7.1**
  
  - [x] 16.6 Write property test for API call prioritization
    - **Property 14: Critical API Calls Start Before Non-Critical**
    - **Validates: Requirements 7.4**
  
  - [x] 16.7 Write property test for console errors
    - **Property 11: No Console Errors on Page Load**
    - **Validates: Requirements 6.1**
  
  - [x] 16.8 Write property test for component render tracking
    - **Property 18: Component Render Times Tracked**
    - **Validates: Requirements 9.3**

- [x] 17. Add integration tests with Playwright
  - [x] 17.1 Create E2E test for page load performance
    - Test page loads within performance budgets
    - Measure Web Vitals (LCP, CLS, FCP)
    - Verify no layout shifts during chart loading
    - _Requirements: 1.1, 2.6, 7.1_
  
  - [x] 17.2 Create E2E test for lazy loading behavior
    - Verify charts load after initial render
    - Verify skeleton loaders appear before content
    - Test error boundary fallback on component failure
    - _Requirements: 7.2, 7.3_
  
  - [x] 17.3 Create E2E test for user interactions
    - Test refresh button functionality
    - Test cache clear functionality
    - Verify no console errors during interactions
    - _Requirements: 6.1_

- [x] 18. Optimize unused JavaScript removal
  - [x] 18.1 Analyze bundle with webpack-bundle-analyzer
    - Run "npm run build:analyze" to generate report
    - Identify unused code in Recharts and other libraries
    - Document findings for optimization
    - _Requirements: 4.1, 4.4_
  
  - [x] 18.2 Implement selective Recharts imports throughout codebase
    - Replace any namespace imports with selective imports
    - Import only BarChart, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer
    - Verify tree-shaking removes unused components
    - _Requirements: 4.2, 4.3_
  
  - [x] 18.3 Remove unused utility library code
    - Audit all utility imports (lodash, date-fns, etc.)
    - Replace namespace imports with selective imports
    - Remove any unused utility functions
    - _Requirements: 4.3_
  
  - [x] 18.4 Write property test for unused JavaScript limit
    - **Property 8: Unused JavaScript Under Size Limit**
    - **Validates: Requirements 4.5**

- [x] 19. Final performance validation
  - [x] 19.1 Run full Lighthouse audit
    - Execute "npm run lighthouse:ci"
    - Verify TBT < 200ms
    - Verify CLS < 0.1
    - Verify bundle size < 1,500 KiB
    - Verify unused JS < 500 KiB
    - _Requirements: 1.1, 2.6, 3.6, 4.5_
  
  - [x] 19.2 Run all property-based tests
    - Execute "npm test" with all property tests
    - Verify all 19 properties pass with 100 iterations
    - Fix any failing properties
    - _Requirements: All_
  
  - [x] 19.3 Run bundle size analysis
    - Execute "npm run test:bundle"
    - Verify total bundle < 1,500 KiB
    - Verify unused JS < 500 KiB
    - _Requirements: 3.6, 4.5_
  
  - [x] 19.4 Document performance improvements
    - Record before/after metrics for TBT, CLS, bundle size
    - Create performance comparison report
    - Update README with optimization details
    - _Requirements: All_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive performance optimization
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties with 100 iterations each
- Unit tests validate specific examples and edge cases
- The implementation follows a progressive enhancement strategy: layout stability → code splitting → bundle optimization → monitoring
- All optimizations maintain full functionality while improving performance metrics
