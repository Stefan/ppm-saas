# ESLint Design System Rules - Usage Guide

## Overview

Custom ESLint rules have been implemented to enforce design system compliance in the ORKA PPM codebase. These rules automatically detect and can auto-fix violations of the design system standards.

## Implemented Rules

### 1. `design-system/no-hardcoded-colors`

**Purpose:** Prevents the use of Tailwind color classes that are not part of the design system.

**Approved Colors:**
- `primary` - Primary brand colors (blue scale)
- `neutral` - Neutral/gray colors  
- `semantic` - Semantic colors (success, warning, error, info)
- `secondary` - Secondary colors (green scale)
- `accent` - Accent colors (yellow scale)
- `success` - Success colors (green scale)
- `warning` - Warning colors (yellow/orange scale)
- `error` - Error colors (red scale)

**Auto-fix Mappings:**
- `gray`, `slate`, `zinc`, `stone` → `neutral`
- `blue`, `indigo`, `sky` → `primary`
- `red`, `rose` → `error`
- `green`, `emerald` → `success`
- `yellow`, `amber`, `orange` → `warning`

**Example:**
```tsx
// ❌ Bad - triggers warning
<button className="bg-blue-500 text-white">Click me</button>

// ✅ Good - uses design token
<button className="bg-primary-500 text-white">Click me</button>
```

### 2. `design-system/no-hardcoded-spacing`

**Purpose:** Prevents the use of spacing values that are not part of the design system spacing scale.

**Approved Spacing Values:**
- Standard scale: `0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16` (4px increments)
- Touch targets: `touch-target`, `touch-target-comfortable`, `touch-target-large`
- Special values: `px`, `auto`, `full`, `screen`

**Auto-fix Mappings:**
- `7` → `6` (28px → 24px)
- `9` → `8` (36px → 32px)
- `11` → `12` (44px → 48px)
- `14`, `15`, `20`, `24`, `32` → `16` (→ 64px)

**Example:**
```tsx
// ❌ Bad - triggers warning
<div className="p-7 m-14 gap-9">Content</div>

// ✅ Good - uses design token spacing
<div className="p-6 m-16 gap-8">Content</div>
```

## Usage

### Running ESLint

```bash
# Check for design system violations
npm run lint

# Auto-fix violations where possible
npm run lint:fix

# Check specific file
npx eslint path/to/file.tsx

# Auto-fix specific file
npx eslint path/to/file.tsx --fix
```

### Configuration

The rules are configured in `eslint.config.mjs`:

```javascript
{
  plugins: {
    'design-system': require('./eslint-rules'),
  },
  rules: {
    'design-system/no-hardcoded-colors': 'warn',
    'design-system/no-hardcoded-spacing': 'warn',
  },
}
```

### Disabling Rules

If you need to disable a rule temporarily (e.g., for legacy code):

```tsx
// Disable for a single line
// eslint-disable-next-line design-system/no-hardcoded-colors
<div className="bg-blue-500">Legacy component</div>

// Disable for a block
/* eslint-disable design-system/no-hardcoded-colors */
<div className="bg-blue-500">Legacy component 1</div>
<div className="bg-red-500">Legacy component 2</div>
/* eslint-enable design-system/no-hardcoded-colors */

// Disable for entire file
/* eslint-disable design-system/no-hardcoded-colors */
```

**Note:** Use sparingly and only for legacy code that hasn't been migrated yet.

## Testing the Rules

To verify the rules are working:

1. Create a test file with violations:
```tsx
// test.tsx
export function Test() {
  return <button className="bg-blue-500 p-7">Test</button>;
}
```

2. Run ESLint:
```bash
npx eslint test.tsx
```

3. Expected output:
```
test.tsx
  3:31  warning  Avoid using "bg-blue-500" directly. Consider using "bg-primary-500"  design-system/no-hardcoded-colors
  3:31  warning  Avoid using "p-7" directly. Consider using "p-6"                     design-system/no-hardcoded-spacing
```

4. Auto-fix:
```bash
npx eslint test.tsx --fix
```

5. Result:
```tsx
export function Test() {
  return <button className="bg-primary-500 p-6">Test</button>;
}
```

## Migration Strategy

When migrating existing code to use design tokens:

1. **Identify violations:**
   ```bash
   npm run lint > violations.txt
   ```

2. **Auto-fix what can be fixed:**
   ```bash
   npm run lint:fix
   ```

3. **Review changes:**
   - Check git diff to ensure changes are correct
   - Verify visual appearance hasn't changed
   - Test functionality

4. **Manual fixes:**
   - Fix remaining violations that couldn't be auto-fixed
   - Update arbitrary values (e.g., `p-[20px]`) to use design tokens

5. **Update tests:**
   - Update component tests if needed
   - Verify all tests still pass

## Benefits

1. **Consistency:** Ensures all components use the same design tokens
2. **Maintainability:** Makes it easy to update the design system globally
3. **Developer Experience:** Auto-fix capabilities speed up migration
4. **Quality:** Catches design system violations during development
5. **Documentation:** Rules serve as living documentation of design standards

## Troubleshooting

### Rule not detecting violations

- Ensure ESLint cache is cleared: `rm -rf .eslintcache`
- Verify the file extension is included in ESLint config
- Check that the rule is enabled in `eslint.config.mjs`

### Auto-fix not working

- Some violations cannot be auto-fixed (e.g., arbitrary values)
- Ensure you're using the `--fix` flag
- Check that the violation has a suggested replacement

### False positives

- If a rule incorrectly flags valid code, please report it
- Use `eslint-disable` comments as a temporary workaround

## Related Documentation

- [Design System Requirements](./requirements.md)
- [Design System Design](./design.md)
- [ESLint Rules README](../../eslint-rules/README.md)
- [Tailwind Config](../../tailwind.config.ts)

## Validation

The rules have been tested and verified to:
- ✅ Detect hardcoded color violations
- ✅ Detect hardcoded spacing violations
- ✅ Provide auto-fix for common violations
- ✅ Not flag design token usage
- ✅ Work with JSX className attributes
- ✅ Work with template literals
- ✅ Work with object properties

Example validation output:
```
/Users/stefan/Projects/orka-ppm/hooks/usePermissions.example.tsx
  404:24  warning  Avoid using "border-gray-900" directly. Consider using "border-neutral-900"
  412:22  warning  Avoid using "bg-red-50" directly. Consider using "bg-error-50"
  412:22  warning  Avoid using "border-red-200" directly. Consider using "border-error-200"
  413:23  warning  Avoid using "text-red-800" directly. Consider using "text-error-800"
```
