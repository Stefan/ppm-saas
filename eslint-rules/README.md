# Custom ESLint Rules for Design System Compliance

This directory contains custom ESLint rules that enforce the ORKA PPM design system standards.

## Rules

### `no-hardcoded-colors`

Prevents the use of Tailwind color classes that are not part of the design system.

**Approved colors:**
- `primary` - Primary brand colors (blue scale)
- `neutral` - Neutral/gray colors
- `semantic` - Semantic colors (success, warning, error, info)
- `secondary` - Secondary colors (green scale)
- `accent` - Accent colors (yellow scale)
- `success` - Success colors (green scale)
- `warning` - Warning colors (yellow/orange scale)
- `error` - Error colors (red scale)

**Examples:**

```tsx
// ❌ Bad - using hardcoded Tailwind colors
<button className="bg-blue-500 text-white">Click me</button>
<div className="text-gray-700 border-red-300">Content</div>

// ✅ Good - using design tokens
<button className="bg-primary-600 text-white">Click me</button>
<div className="text-neutral-700 border-error-300">Content</div>
```

**Auto-fix:** This rule can automatically fix common color replacements:
- `gray`, `slate`, `zinc`, `stone` → `neutral`
- `blue`, `indigo`, `sky` → `primary`
- `red`, `rose` → `error`
- `green`, `emerald` → `success`
- `yellow`, `amber`, `orange` → `warning`

### `no-hardcoded-spacing`

Prevents the use of spacing values that are not part of the design system spacing scale.

**Approved spacing values:**
- `0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16` - Standard spacing scale (4px increments)
- `touch-target`, `touch-target-comfortable`, `touch-target-large` - Touch-friendly sizes
- `px`, `auto`, `full`, `screen` - Special values

**Examples:**

```tsx
// ❌ Bad - using non-standard spacing
<div className="p-7 m-14 gap-9">Content</div>
<div className="p-[20px] m-[1.5rem]">Content</div>

// ✅ Good - using design token spacing
<div className="p-6 m-16 gap-8">Content</div>
<div className="p-5 m-6">Content</div>
```

**Auto-fix:** This rule can automatically fix common spacing values:
- `7` → `6` (28px → 24px)
- `9` → `8` (36px → 32px)
- `11` → `12` (44px → 48px)
- `14`, `15`, `20`, `24`, `32` → `16` (→ 64px)

## Usage

These rules are automatically loaded in the ESLint configuration. To run ESLint with these rules:

```bash
# Check for issues
npm run lint

# Auto-fix issues where possible
npm run lint:fix
```

## Configuration

The rules are configured in `eslint.config.mjs` with the following settings:

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

## Disabling Rules

If you need to disable a rule for a specific line or file, use ESLint comments:

```tsx
// Disable for a single line
// eslint-disable-next-line design-system/no-hardcoded-colors
<div className="bg-blue-500">Legacy component</div>

// Disable for a file
/* eslint-disable design-system/no-hardcoded-colors */
```

However, this should be used sparingly and only for legacy code that hasn't been migrated yet.

## Benefits

1. **Consistency**: Ensures all components use the same design tokens
2. **Maintainability**: Makes it easy to update the design system globally
3. **Developer Experience**: Auto-fix capabilities speed up migration
4. **Quality**: Catches design system violations during development

## Migration Strategy

When migrating existing code:

1. Run `npm run lint` to see all violations
2. Run `npm run lint:fix` to auto-fix what can be fixed
3. Manually review and fix remaining issues
4. Update component tests if needed
5. Verify visual appearance hasn't changed

## Related Documentation

- [Design System Requirements](.kiro/specs/design-system-consistency/requirements.md)
- [Design System Design](.kiro/specs/design-system-consistency/design.md)
- [Tailwind Config](../tailwind.config.ts)
