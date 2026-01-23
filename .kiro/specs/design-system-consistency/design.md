# Design Document: Design System Consistency

## Overview

Dieses Design beschreibt die Implementierung eines konsistenten, wartbaren Designsystems für die ORKA PPM App. Das System basiert auf Design Tokens, die in Tailwind CSS konfiguriert werden, und bietet wiederverwendbare React-Komponenten, die diese Tokens verwenden.

### Architektur-Prinzipien

1. **Token-First Approach**: Alle visuellen Eigenschaften werden als Design Tokens definiert
2. **Component-Based**: Wiederverwendbare React-Komponenten kapseln Styles und Verhalten
3. **Accessibility-First**: WCAG AA Standards sind in alle Komponenten integriert
4. **Responsive by Default**: Alle Komponenten passen sich automatisch an verschiedene Bildschirmgrößen an
5. **Type-Safe**: TypeScript-Typen für alle Komponenten-Props und Varianten

### Technologie-Stack

- **Tailwind CSS**: Utility-First CSS Framework mit Custom Config
- **CSS Custom Properties**: Für dynamische Theming-Unterstützung
- **React + TypeScript**: Typsichere Komponenten
- **clsx/cn**: Utility für bedingte Klassennamen-Kombinationen

## Architecture

### System-Ebenen

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│    (Pages, Features, Layouts)           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Component Layer                   │
│  (Button, Input, Card, etc.)            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│       Design Token Layer                │
│  (Colors, Spacing, Typography)          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         CSS Layer                       │
│  (Tailwind, Custom Properties)          │
└─────────────────────────────────────────┘
```

### Dateistruktur

```
app/
├── design-system.css          # Design Token Definitionen
├── globals.css                # Globale Styles
lib/
├── design-system.ts           # Utility-Funktionen (cn, variants)
components/
└── ui/
    ├── button.tsx             # Button-Komponente
    ├── input.tsx              # Input-Komponente
    ├── card.tsx               # Card-Komponente
    └── ...                    # Weitere Komponenten
tailwind.config.ts             # Tailwind-Konfiguration mit Tokens
```

## Components and Interfaces

### Design Token System

#### Farb-Tokens

```typescript
// tailwind.config.ts
const colors = {
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',  // Haupt-Primary
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  neutral: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
  },
  semantic: {
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
  }
}
```

#### Spacing-Tokens

```typescript
// tailwind.config.ts
const spacing = {
  0: '0px',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
}
```

#### Typografie-Tokens

```typescript
// tailwind.config.ts
const fontSize = {
  xs: ['12px', { lineHeight: '16px' }],
  sm: ['14px', { lineHeight: '20px' }],
  base: ['16px', { lineHeight: '24px' }],
  lg: ['18px', { lineHeight: '28px' }],
  xl: ['20px', { lineHeight: '28px' }],
  '2xl': ['24px', { lineHeight: '32px' }],
  '3xl': ['30px', { lineHeight: '36px' }],
  '4xl': ['36px', { lineHeight: '40px' }],
  '5xl': ['48px', { lineHeight: '1' }],
  '6xl': ['60px', { lineHeight: '1' }],
}

const fontWeight = {
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
}
```

#### Shadow- und Border-Tokens

```typescript
// tailwind.config.ts
const boxShadow = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
}

const borderRadius = {
  none: '0',
  sm: '4px',
  DEFAULT: '6px',
  md: '8px',
  lg: '12px',
  full: '9999px',
}
```

### Button-Komponente

#### Interface

```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  children: React.ReactNode
}
```

#### Varianten-Definition

```typescript
const buttonVariants = {
  variant: {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800',
    secondary: 'bg-neutral-200 text-neutral-900 hover:bg-neutral-300 active:bg-neutral-400',
    outline: 'border-2 border-primary-600 text-primary-600 hover:bg-primary-50 active:bg-primary-100',
  },
  size: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  },
}

const buttonBaseStyles = 'rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
```

#### Implementierung

```typescript
export function Button({ 
  variant = 'primary', 
  size = 'md', 
  disabled = false,
  className,
  children,
  ...props 
}: ButtonProps) {
  return (
    <button
      className={cn(
        buttonBaseStyles,
        buttonVariants.variant[variant],
        buttonVariants.size[size],
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
```

### Input-Komponente

#### Interface

```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  size?: 'sm' | 'md' | 'lg'
  error?: boolean
  errorMessage?: string
  label?: string
}
```

#### Varianten-Definition

```typescript
const inputVariants = {
  size: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-5 py-3 text-lg',
  },
}

const inputBaseStyles = 'w-full rounded-md border border-neutral-300 bg-white text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors disabled:bg-neutral-100 disabled:cursor-not-allowed'

const inputErrorStyles = 'border-semantic-error focus:ring-semantic-error'
```

#### Implementierung

```typescript
export function Input({ 
  size = 'md', 
  error = false,
  errorMessage,
  label,
  className,
  ...props 
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          {label}
        </label>
      )}
      <input
        className={cn(
          inputBaseStyles,
          inputVariants.size[size],
          error && inputErrorStyles,
          className
        )}
        {...props}
      />
      {error && errorMessage && (
        <p className="mt-1 text-sm text-semantic-error">{errorMessage}</p>
      )}
    </div>
  )
}
```

### Card-Komponente

#### Interface

```typescript
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'sm' | 'md' | 'lg'
  shadow?: 'sm' | 'md' | 'lg'
  border?: boolean
  children: React.ReactNode
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}
```

#### Varianten-Definition

```typescript
const cardVariants = {
  padding: {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  },
  shadow: {
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  },
}

const cardBaseStyles = 'bg-white rounded-lg'
const cardBorderStyles = 'border border-neutral-200'
const cardHeaderStyles = 'border-b border-neutral-200 pb-4 mb-4'
```

#### Implementierung

```typescript
export function Card({ 
  padding = 'md', 
  shadow = 'md',
  border = false,
  className,
  children,
  ...props 
}: CardProps) {
  return (
    <div
      className={cn(
        cardBaseStyles,
        cardVariants.padding[padding],
        cardVariants.shadow[shadow],
        border && cardBorderStyles,
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children, ...props }: CardHeaderProps) {
  return (
    <div className={cn(cardHeaderStyles, className)} {...props}>
      {children}
    </div>
  )
}

export function CardContent({ className, children, ...props }: CardContentProps) {
  return (
    <div className={cn(className)} {...props}>
      {children}
    </div>
  )
}
```

### Utility-Funktionen

#### cn (classnames) Funktion

```typescript
// lib/design-system.ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

Diese Funktion kombiniert `clsx` für bedingte Klassennamen mit `tailwind-merge`, um Tailwind-Klassen-Konflikte intelligent aufzulösen.

## Data Models

### Design Token Configuration

```typescript
// types/design-system.ts

export type ColorScale = {
  50: string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  800: string
  900: string
}

export type SemanticColors = {
  success: string
  warning: string
  error: string
  info: string
}

export type SpacingScale = {
  [key: string]: string
}

export type TypographyConfig = {
  fontSize: Record<string, [string, { lineHeight: string }]>
  fontWeight: Record<string, string>
}

export interface DesignTokens {
  colors: {
    primary: ColorScale
    neutral: ColorScale
    semantic: SemanticColors
  }
  spacing: SpacingScale
  typography: TypographyConfig
  shadows: Record<string, string>
  borderRadius: Record<string, string>
}
```

### Component Variant Types

```typescript
// types/components.ts

export type ButtonVariant = 'primary' | 'secondary' | 'outline'
export type ComponentSize = 'sm' | 'md' | 'lg'
export type ShadowSize = 'sm' | 'md' | 'lg'

export interface VariantConfig<T extends string> {
  [key: string]: Record<T, string>
}
```

## Correctness Properties

*Eine Property ist eine Eigenschaft oder ein Verhalten, das über alle gültigen Ausführungen eines Systems hinweg wahr sein sollte - im Wesentlichen eine formale Aussage darüber, was das System tun soll. Properties dienen als Brücke zwischen menschenlesbaren Spezifikationen und maschinell verifizierbaren Korrektheitsgarantien.*


### Property 1: Button-Varianten sind auf definierte Werte beschränkt

*For any* Button-Komponente, die Varianten-Prop sollte nur die Werte 'primary', 'secondary' oder 'outline' akzeptieren, und alle anderen Werte sollten abgelehnt werden oder auf einen Default zurückfallen.

**Validates: Requirements 1.1**

### Property 2: Button-Größen sind auf definierte Werte beschränkt

*For any* Button-Komponente, die Size-Prop sollte nur die Werte 'sm', 'md' oder 'lg' akzeptieren, und alle anderen Werte sollten abgelehnt werden oder auf einen Default zurückfallen.

**Validates: Requirements 1.7**

### Property 3: Alle Komponenten verwenden Spacing aus Design Tokens

*For any* Komponente (Button, Input, Card), alle verwendeten Padding- und Margin-Klassen sollten ausschließlich aus dem definierten Spacing-Scale stammen (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16).

**Validates: Requirements 1.2, 2.1, 3.1, 4.2**

### Property 4: Button-Farben stammen aus Design Tokens

*For any* Button-Variante, alle verwendeten Farbklassen sollten ausschließlich aus den definierten Design Tokens (primary, neutral, semantic) stammen.

**Validates: Requirements 1.3**

### Property 5: Buttons haben Hover-States

*For any* Button-Variante, die gerenderten Klassen sollten Hover-State-Klassen enthalten (hover:*).

**Validates: Requirements 1.4**

### Property 6: Alle Komponenten verwenden Border-Radius aus Design Tokens

*For any* Komponente (Button, Card, Input), alle verwendeten Border-Radius-Klassen sollten ausschließlich aus dem definierten Border-Radius-Scale stammen.

**Validates: Requirements 1.5, 3.3**

### Property 7: Interaktive Elemente haben Focus-Rings

*For any* interaktive Komponente (Button, Input), die gerenderten Klassen sollten Focus-Ring-Klassen mit mindestens 2px Breite enthalten (focus:ring-2 oder größer).

**Validates: Requirements 1.6, 2.3**

### Property 8: Input-Größen sind auf definierte Werte beschränkt

*For any* Input-Komponente, die Size-Prop sollte nur die Werte 'sm', 'md' oder 'lg' akzeptieren, und alle anderen Werte sollten abgelehnt werden oder auf einen Default zurückfallen.

**Validates: Requirements 2.6**

### Property 9: Input hat einheitlichen Border-Style

*For any* Input-Komponente, die gerenderten Klassen sollten einen Border mit 1px Breite enthalten (border oder border-1).

**Validates: Requirements 2.2**

### Property 10: Placeholder-Farbe erfüllt Kontrast-Anforderungen

*For any* Input-Komponente, die Placeholder-Farbe (placeholder:text-*) sollte einen Kontrast von mindestens 4.5:1 zum weißen Hintergrund haben.

**Validates: Requirements 2.4**

### Property 11: Input im Error-State zeigt visuelles Feedback

*For any* Input-Komponente mit error=true, die gerenderten Klassen sollten Error-Border-Klassen enthalten und eine Fehlermeldung sollte gerendert werden.

**Validates: Requirements 2.5**

### Property 12: Card verwendet Shadow aus Design Tokens

*For any* Card-Komponente, die verwendeten Shadow-Klassen sollten ausschließlich aus dem definierten Shadow-Scale stammen (shadow-sm, shadow-md, shadow-lg).

**Validates: Requirements 3.2**

### Property 13: CardHeader hat konsistente Styles

*For any* CardHeader-Komponente, die gerenderten Klassen sollten einen Bottom-Border und konsistente Paddings enthalten.

**Validates: Requirements 3.4**

### Property 14: Card mit Border verwendet konsistente Border-Styles

*For any* Card-Komponente mit border=true, die gerenderten Klassen sollten Border-Klassen mit konsistenter Farbe und Breite enthalten.

**Validates: Requirements 3.5**

### Property 15: Textfarben erfüllen WCAG AA Kontrast-Anforderungen

*For any* definierte Textfarbe im Design System, der Kontrast zum Hintergrund sollte mindestens 4.5:1 für normalen Text und 3:1 für großen Text betragen.

**Validates: Requirements 5.4, 6.3, 7.2**

### Property 16: Disabled Buttons haben visuell erkennbaren State

*For any* Button-Komponente mit disabled=true, die gerenderten Klassen sollten Opacity-Reduktion und Cursor-Änderung enthalten.

**Validates: Requirements 7.3**

### Property 17: Interaktive Elemente haben Mindestgröße

*For any* interaktive Komponente (Button, Input), die kleinste Größenvariante sollte mindestens 44x44px ergeben.

**Validates: Requirements 7.4, 8.3**

### Property 18: Komponenten verwenden keine inline Tailwind-Styles

*For any* Komponente im Design System, der Quellcode sollte keine hartcodierten className-Strings enthalten, sondern nur Varianten-Funktionen verwenden.

**Validates: Requirements 10.2**

## Error Handling

### Ungültige Prop-Werte

Wenn eine Komponente mit ungültigen Prop-Werten aufgerufen wird:
- **Strategie**: Fallback auf sichere Default-Werte
- **Beispiel**: `variant="invalid"` → fällt zurück auf `variant="primary"`
- **Logging**: In Development-Mode wird eine Console-Warnung ausgegeben

### Fehlende Design Tokens

Wenn ein Design Token nicht gefunden wird:
- **Strategie**: Fallback auf Tailwind-Default-Werte
- **Beispiel**: Wenn `primary-600` nicht definiert ist, verwendet Tailwind `blue-600`
- **Prevention**: TypeScript-Typen verhindern Verwendung undefinierter Tokens

### Kontrast-Verletzungen

Wenn Farbkombinationen unzureichenden Kontrast haben:
- **Detection**: Automatisierte Tests prüfen alle Farbkombinationen
- **Prevention**: Design Tokens werden so definiert, dass sie WCAG AA erfüllen
- **Fallback**: Bei Problemen wird auf höheren Kontrast zurückgefallen

### Responsive Breakpoint-Probleme

Wenn Komponenten bei bestimmten Breakpoints nicht korrekt rendern:
- **Testing**: Visuelle Regression-Tests für alle Breakpoints
- **Fallback**: Mobile-First Approach stellt sicher, dass Basis-Styles immer funktionieren

## Testing Strategy

### Dual Testing Approach

Wir verwenden eine Kombination aus Unit-Tests und Property-Based Tests:

**Unit Tests** fokussieren auf:
- Spezifische Beispiele für jede Komponenten-Variante
- Edge Cases (z.B. sehr lange Button-Texte)
- Error-States und Fehlermeldungen
- Integration zwischen Komponenten (z.B. Card mit CardHeader)

**Property-Based Tests** fokussieren auf:
- Universelle Properties über alle Komponenten-Varianten
- Automatische Generierung von Test-Inputs
- Verifikation von Design Token Konsistenz
- Kontrast-Berechnungen für alle Farbkombinationen

### Testing Framework

- **Framework**: Vitest für Unit- und Property-Tests
- **Property Testing Library**: fast-check
- **Component Testing**: React Testing Library
- **Visual Testing**: Storybook mit Chromatic (optional)

### Property Test Configuration

Jeder Property-Test:
- Läuft mit **mindestens 100 Iterationen**
- Ist mit einem Kommentar annotiert: `// Feature: design-system-consistency, Property {N}: {property_text}`
- Referenziert die entsprechende Property aus diesem Design-Dokument
- Generiert zufällige, aber gültige Inputs

### Test Coverage Ziele

- **Komponenten**: 100% Coverage für alle UI-Komponenten
- **Design Tokens**: Alle Tokens werden in mindestens einem Test verwendet
- **Accessibility**: Alle WCAG AA Anforderungen werden getestet
- **Responsive**: Alle Breakpoints werden getestet

### Beispiel Property Test

```typescript
import { describe, it, expect } from 'vitest'
import { fc } from 'fast-check'
import { Button } from '@/components/ui/button'
import { render } from '@testing-library/react'

describe('Button Component Properties', () => {
  // Feature: design-system-consistency, Property 1: Button-Varianten sind auf definierte Werte beschränkt
  it('should only accept defined variant values', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('primary', 'secondary', 'outline'),
        (variant) => {
          const { container } = render(<Button variant={variant}>Test</Button>)
          const button = container.querySelector('button')
          expect(button).toBeTruthy()
          // Verify button has correct variant classes
        }
      ),
      { numRuns: 100 }
    )
  })
})
```

### Unit Test Balance

- Schreibe nicht zu viele Unit-Tests - Property-Tests decken viele Inputs ab
- Fokussiere Unit-Tests auf:
  - Konkrete Beispiele, die das erwartete Verhalten demonstrieren
  - Spezifische Edge Cases, die schwer zu generieren sind
  - Integration zwischen Komponenten
- Property-Tests übernehmen die umfassende Input-Abdeckung

### Continuous Integration

- Alle Tests laufen bei jedem Pull Request
- Property-Tests mit festen Seeds für reproduzierbare Ergebnisse
- Visual Regression Tests für UI-Änderungen
- Accessibility-Tests mit axe-core

## Implementation Notes

### Migration Strategy

1. **Phase 1**: Design Tokens in Tailwind Config definieren
2. **Phase 2**: Basis-Komponenten (Button, Input, Card) implementieren
3. **Phase 3**: Bestehende Komponenten migrieren
4. **Phase 4**: Globale Styles aufräumen und konsolidieren

### Backwards Compatibility

- Alte Komponenten bleiben während der Migration funktionsfähig
- Neue Komponenten werden parallel eingeführt
- Schrittweise Migration pro Feature/Page
- Deprecation-Warnings für alte Patterns

### Performance Considerations

- Tailwind JIT Mode für optimale Bundle-Größe
- CSS Custom Properties für dynamisches Theming
- Komponenten sind tree-shakeable
- Keine Runtime-Overhead durch Design Tokens

### Developer Experience

- TypeScript-Typen für alle Props und Varianten
- Storybook für Komponenten-Dokumentation
- ESLint-Rules für Design System Compliance
- VS Code Snippets für schnelle Komponenten-Erstellung
