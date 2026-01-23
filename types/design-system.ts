/**
 * Design System Type Definitions
 * 
 * This file contains TypeScript types for the ORKA PPM design system tokens.
 * These types ensure type safety when working with design tokens throughout the application.
 */

/**
 * Color scale with 9 shades (50-900)
 * Used for primary, neutral, and other color palettes
 */
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

/**
 * Semantic colors for common UI states
 */
export type SemanticColors = {
  success: string
  warning: string
  error: string
  info: string
}

/**
 * Spacing scale from 0 to 16 in 4px increments
 * Keys are numeric strings representing the scale value
 */
export type SpacingScale = {
  0: string
  1: string
  2: string
  3: string
  4: string
  5: string
  6: string
  8: string
  10: string
  12: string
  16: string
  'touch-target': string
  'touch-target-comfortable': string
  'touch-target-large': string
}

/**
 * Typography configuration including font sizes, line heights, and weights
 */
export type TypographyConfig = {
  fontSize: {
    xs: [string, { lineHeight: string }]
    sm: [string, { lineHeight: string }]
    base: [string, { lineHeight: string }]
    lg: [string, { lineHeight: string }]
    xl: [string, { lineHeight: string }]
    '2xl': [string, { lineHeight: string }]
    '3xl': [string, { lineHeight: string }]
    '4xl': [string, { lineHeight: string }]
    '5xl': [string, { lineHeight: string }]
    '6xl': [string, { lineHeight: string }]
  }
  fontWeight: {
    normal: string
    medium: string
    semibold: string
    bold: string
  }
}

/**
 * Shadow sizes for elevation
 */
export type ShadowScale = {
  sm: string
  DEFAULT: string
  md: string
  lg: string
  touch: string
  'touch-active': string
  'focus-ring': string
  'error-ring': string
}

/**
 * Border radius scale
 */
export type BorderRadiusScale = {
  none: string
  sm: string
  DEFAULT: string
  md: string
  lg: string
  full: string
  touch: string
  'touch-large': string
}

/**
 * Responsive breakpoints
 */
export type Breakpoints = {
  mobile: string
  tablet: string
  desktop: string
}

/**
 * Complete design tokens interface
 * Contains all design system tokens organized by category
 */
export interface DesignTokens {
  colors: {
    primary: ColorScale
    neutral: ColorScale
    semantic: SemanticColors
  }
  spacing: SpacingScale
  typography: TypographyConfig
  shadows: ShadowScale
  borderRadius: BorderRadiusScale
  breakpoints: Breakpoints
}
