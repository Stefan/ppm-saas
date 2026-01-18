# Admin Performance E2E Tests

## Overview

Comprehensive end-to-end tests for the admin performance page (`/admin/performance`) using Playwright. These tests verify:

- **Page load performance**: TBT < 200ms, CLS < 0.1, FCP < 1.5s
- **Lazy loading behavior**: Charts load after initial render, skeleton loaders appear
- **User interactions**: Refresh and cache clear work without errors
- **Error boundaries**: Component failures are isolated
- **Progressive loading**: Critical content renders within 1 second

## Test File

`__tests__/e2e/admin-performance.spec.ts`

## Prerequisites

1. **Install Playwright browsers** (first time only):
   ```bash
   npx playwright install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

## Running Tests

### Run all admin performance tests
```bash
npx playwright test __tests__/e2e/admin-performance.spec.ts
```

### Run on specific browser
```bash
# Chrome
npx playwright test __tests__/e2e/admin-performance.spec.ts --project=chromium-desktop

# Firefox
npx playwright test __tests__/e2e/admin-performance.spec.ts --project=firefox-desktop

# Safari
npx playwright test __tests__/e2e/admin-performance.spec.ts --project=webkit-desktop
```

### Run specific test suite
```bash
# Load performance tests only
npx playwright test __tests__/e2e/admin-performance.spec.ts -g "Load Performance"

# Lazy loading tests only
npx playwright test __tests__/e2e/admin-performance.spec.ts -g "Lazy Loading"

# User interaction tests only
npx playwright test __tests__/e2e/admin-performance.spec.ts -g "User Interactions"
```

### Run with UI mode (interactive)
```bash
npx playwright test __tests__/e2e/admin-performance.spec.ts --ui
```

### Run in headed mode (see browser)
```bash
npx playwright test __tests__/e2e/admin-performance.spec.ts --headed
```

### Debug a specific test
```bash
npx playwright test __tests__/e2e/admin-performance.spec.ts --debug
```

## Test Suites

### 1. Load Performance Tests
- ✅ Loads within performance budgets (TBT, CLS, FCP)
- ✅ Measures Web Vitals accurately
- ✅ Has no layout shifts during chart loading

**Requirements validated**: 1.1, 2.6, 7.1

### 2. Lazy Loading Tests
- ✅ Displays skeleton loaders before content
- ✅ Loads charts after initial render
- ✅ Matches skeleton dimensions to final content
- ✅ Lazy loads Recharts library

**Requirements validated**: 7.2, 7.3, 2.1

### 3. User Interaction Tests
- ✅ Handles refresh button click without errors
- ✅ Handles cache clear functionality
- ✅ Maintains performance during interactions
- ✅ Has no console errors on page load

**Requirements validated**: 6.1

### 4. Error Boundary Tests
- ✅ Displays error boundary fallback on component failure
- ✅ Isolates chart errors from page crash

**Requirements validated**: 6.1, 6.2

### 5. Progressive Loading Tests
- ✅ Renders critical content within 1 second
- ✅ Prioritizes critical API calls

**Requirements validated**: 7.1, 7.4

## Performance Budgets

The tests enforce these performance budgets:

| Metric | Budget | Requirement |
|--------|--------|-------------|
| Total Blocking Time (TBT) | < 200ms | 1.1 |
| Cumulative Layout Shift (CLS) | < 0.1 | 2.6 |
| First Contentful Paint (FCP) | < 1.5s | 7.1 |
| Time to First Byte (TTFB) | < 800ms | - |
| Total Load Time | < 3s | - |
| Largest Contentful Paint (LCP) | < 2.5s | - |

## Viewing Test Results

### HTML Report
After running tests, view the HTML report:
```bash
npx playwright show-report
```

### JSON Results
Results are saved to `test-results/results.json`

### Screenshots and Videos
- Screenshots: Captured on test failure
- Videos: Recorded on test failure
- Location: `test-results/` directory

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Install Playwright Browsers
  run: npx playwright install --with-deps

- name: Run Admin Performance E2E Tests
  run: npx playwright test __tests__/e2e/admin-performance.spec.ts

- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Troubleshooting

### Server not ready
If tests fail with "Server not ready":
1. Ensure dev server is running: `npm run dev`
2. Check server is accessible at `http://localhost:3000`
3. Increase timeout in `playwright.config.ts`

### Browsers not installed
If you see "Executable doesn't exist":
```bash
npx playwright install
```

### Tests timing out
If tests timeout:
1. Check network connectivity
2. Ensure backend API is running
3. Increase timeout in test file or config

### Console errors in tests
If tests fail due to console errors:
1. Check browser console in headed mode: `--headed`
2. Review error messages in test output
3. Fix underlying issues in the application

## Performance Monitoring

The tests use the `PerformanceTestUtils` class from `__tests__/utils/performance-testing.ts` to:

- Measure Core Web Vitals (LCP, FID, CLS, FCP, TTFB)
- Track resource loading and sizes
- Monitor memory usage
- Detect layout shifts
- Measure interaction performance

## Best Practices

1. **Run tests locally** before committing
2. **Check test output** for performance metrics
3. **Review failures** in headed mode for debugging
4. **Update budgets** if requirements change
5. **Add new tests** when adding features

## Related Files

- Test file: `__tests__/e2e/admin-performance.spec.ts`
- Config: `playwright.config.ts`
- Utils: `__tests__/utils/performance-testing.ts`
- Global setup: `__tests__/e2e/global-setup.ts`
- Global teardown: `__tests__/e2e/global-teardown.ts`

## Next Steps

After running these tests:

1. Review performance metrics in console output
2. Check for any failing tests
3. Fix any issues found
4. Run full test suite: `npx playwright test`
5. Generate performance report
