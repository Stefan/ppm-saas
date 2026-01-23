# Visual Regression Testing - Baseline Screenshot Guide

## Overview

This guide explains how to generate and manage baseline screenshots for visual regression testing.

## Requirements

- Requirement 4.1: Baseline screenshots for all main pages
- Requirement 4.4: Support updating baseline screenshots when intentional changes are made

## Initial Setup

### 1. Install Playwright Browsers

Before generating baseline screenshots, ensure all Playwright browsers are installed:

```bash
npx playwright install --with-deps
```

### 2. Start Development Server

The tests require a running development server:

```bash
npm run dev
```

Or for production build:

```bash
npm run build
npm run start
```

## Generating Initial Baseline Screenshots

### Generate All Baselines

To generate baseline screenshots for all pages and viewports:

```bash
npm run test:visual:update
```

This will:
- Run all visual regression tests tagged with `@visual`
- Capture screenshots for all configured pages
- Test across desktop, tablet, and mobile viewports
- Save screenshots to `__tests__/e2e/visual-regression.spec.ts-snapshots/`

### Generate Baselines for Specific Project

To generate baselines for a specific browser/device:

```bash
npx playwright test --grep='@visual' --update-snapshots --project=chromium-desktop
```

Available projects:
- `chromium-desktop` - Desktop Chrome (1920x1080)
- `firefox-desktop` - Desktop Firefox (1920x1080)
- `webkit-desktop` - Desktop Safari (1920x1080)
- `tablet-chrome` - Tablet Chrome (1024x768)
- `mobile-safari-iphone-12` - iPhone 12
- `mobile-chrome-pixel-5` - Pixel 5

## Running Visual Regression Tests

### Run All Visual Tests

```bash
npm run test:visual
```

### Run Tests for Specific Page

```bash
npx playwright test --grep='dashboard page - desktop viewport'
```

### Run Tests with UI Mode

```bash
npx playwright test --grep='@visual' --ui
```

## Updating Baseline Screenshots

### When to Update Baselines

Update baseline screenshots when:
- Intentional UI changes are made
- Design system updates are implemented
- Layout improvements are deployed
- Component styling is modified

### How to Update Baselines

1. **Review the changes**: First, run the tests to see what changed:
   ```bash
   npm run test:visual
   ```

2. **View the diff report**:
   ```bash
   npm run test:e2e:report
   ```

3. **Update baselines** if changes are intentional:
   ```bash
   npm run test:visual:update
   ```

4. **Commit the updated screenshots**:
   ```bash
   git add __tests__/e2e/visual-regression.spec.ts-snapshots/
   git commit -m "Update visual regression baselines for [feature/change]"
   ```

### Update Specific Page Baselines

To update baselines for a specific page only:

```bash
npx playwright test --grep='dashboard page' --update-snapshots
```

## Screenshot Organization

Baseline screenshots are organized by test file and browser:

```
__tests__/e2e/
└── visual-regression.spec.ts-snapshots/
    ├── dashboard-desktop-chromium-desktop-darwin.png
    ├── dashboard-tablet-chromium-desktop-darwin.png
    ├── dashboard-mobile-chromium-desktop-darwin.png
    ├── projects-desktop-chromium-desktop-darwin.png
    └── ...
```

## Configuration

Visual regression configuration is defined in:
- `lib/testing/visual-regression-config.ts` - Pages, viewports, thresholds
- `playwright.config.ts` - Playwright settings and projects

### Key Configuration Values

```typescript
{
  threshold: 0.1,        // 10% pixel difference threshold
  maxDiffPixels: 500,    // Maximum allowed different pixels
  animations: 'disabled' // Disable animations for consistency
}
```

## Troubleshooting

### Screenshots Don't Match

1. **Check for dynamic content**: Ensure timestamps, random data, or animations are masked
2. **Verify viewport size**: Ensure the viewport matches the baseline
3. **Check for font rendering differences**: Different OS may render fonts differently
4. **Review animation settings**: Ensure animations are disabled

### Tests Timeout

1. **Increase timeout**: Modify `timeout` in `playwright.config.ts`
2. **Check network**: Ensure stable internet connection for loading resources
3. **Verify server**: Ensure development server is running and responsive

### Baseline Screenshots Missing

1. **Generate baselines**: Run `npm run test:visual:update`
2. **Check file permissions**: Ensure write permissions for snapshot directory
3. **Verify test tags**: Ensure tests are tagged with `@visual`

## CI/CD Integration

Visual regression tests run automatically in CI/CD:

```yaml
- name: Run visual regression tests
  run: npm run test:visual

- name: Upload visual diff artifacts
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: visual-diffs
    path: test-results/visual-diffs/
```

## Best Practices

1. **Commit baselines**: Always commit baseline screenshots to version control
2. **Review diffs**: Always review visual diffs before updating baselines
3. **Test locally**: Run visual tests locally before pushing changes
4. **Document changes**: Include visual changes in PR descriptions
5. **Mask dynamic content**: Use `maskSelectors` for timestamps, user data, etc.
6. **Disable animations**: Ensure animations are disabled for consistent screenshots
7. **Use consistent data**: Use the same test data for baseline generation

## Example Workflow

1. Make UI changes to a component
2. Run visual tests: `npm run test:visual`
3. Review failures in report: `npm run test:e2e:report`
4. If changes are intentional, update baselines: `npm run test:visual:update`
5. Verify updated baselines: `npm run test:visual`
6. Commit changes:
   ```bash
   git add __tests__/e2e/visual-regression.spec.ts-snapshots/
   git commit -m "Update visual baselines for dashboard redesign"
   ```

## Additional Resources

- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Visual Regression Testing Best Practices](https://playwright.dev/docs/best-practices#visual-comparisons)
- Project Design Document: `.kiro/specs/ui-structure-tests/design.md`
