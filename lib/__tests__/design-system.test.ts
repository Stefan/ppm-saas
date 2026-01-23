/**
 * Unit Tests for Design System Utilities
 * Tests the cn function for class name composition
 */

import { describe, it, expect } from '@jest/globals'
import { cn } from '../design-system'

describe('cn function', () => {
  it('should combine multiple classes correctly', () => {
    const result = cn('text-red-500', 'bg-blue-500', 'p-4')
    expect(result).toContain('text-red-500')
    expect(result).toContain('bg-blue-500')
    expect(result).toContain('p-4')
  })

  it('should resolve Tailwind conflicts with later classes overriding earlier ones', () => {
    // px-4 should override px-2
    const result1 = cn('px-2', 'px-4')
    expect(result1).toBe('px-4')
    expect(result1).not.toContain('px-2')

    // py-8 should override py-4
    const result2 = cn('py-4', 'py-8')
    expect(result2).toBe('py-8')
    expect(result2).not.toContain('py-4')

    // text-lg should override text-sm
    const result3 = cn('text-sm', 'text-lg')
    expect(result3).toBe('text-lg')
    expect(result3).not.toContain('text-sm')

    // bg-red-500 should override bg-blue-500
    const result4 = cn('bg-blue-500', 'bg-red-500')
    expect(result4).toBe('bg-red-500')
    expect(result4).not.toContain('bg-blue-500')
  })

  it('should handle conditional classes correctly', () => {
    const isActive = true
    const isDisabled = false

    const result = cn(
      'base-class',
      isActive && 'active-class',
      isDisabled && 'disabled-class',
      !isDisabled && 'enabled-class'
    )

    expect(result).toContain('base-class')
    expect(result).toContain('active-class')
    expect(result).toContain('enabled-class')
    expect(result).not.toContain('disabled-class')
  })

  it('should handle undefined and null values', () => {
    const result = cn('text-red-500', undefined, null, 'bg-blue-500')
    expect(result).toContain('text-red-500')
    expect(result).toContain('bg-blue-500')
  })

  it('should handle empty strings', () => {
    const result = cn('text-red-500', '', 'bg-blue-500')
    expect(result).toContain('text-red-500')
    expect(result).toContain('bg-blue-500')
  })

  it('should handle arrays of classes', () => {
    const result = cn(['text-red-500', 'bg-blue-500'], 'p-4')
    expect(result).toContain('text-red-500')
    expect(result).toContain('bg-blue-500')
    expect(result).toContain('p-4')
  })

  it('should handle objects with boolean values', () => {
    const result = cn({
      'text-red-500': true,
      'bg-blue-500': false,
      'p-4': true
    })
    expect(result).toContain('text-red-500')
    expect(result).toContain('p-4')
    expect(result).not.toContain('bg-blue-500')
  })

  it('should combine multiple types of inputs', () => {
    const isActive = true
    const result = cn(
      'base-class',
      ['array-class-1', 'array-class-2'],
      { 'object-class': true, 'hidden-class': false },
      isActive && 'conditional-class',
      'final-class'
    )

    expect(result).toContain('base-class')
    expect(result).toContain('array-class-1')
    expect(result).toContain('array-class-2')
    expect(result).toContain('object-class')
    expect(result).toContain('conditional-class')
    expect(result).toContain('final-class')
    expect(result).not.toContain('hidden-class')
  })

  it('should resolve complex Tailwind conflicts with multiple properties', () => {
    const result = cn(
      'px-2 py-4 text-sm bg-blue-500',
      'px-4 text-lg'
    )
    
    // px-4 should override px-2
    expect(result).toContain('px-4')
    expect(result).not.toContain('px-2')
    
    // text-lg should override text-sm
    expect(result).toContain('text-lg')
    expect(result).not.toContain('text-sm')
    
    // py-4 and bg-blue-500 should remain
    expect(result).toContain('py-4')
    expect(result).toContain('bg-blue-500')
  })

  it('should handle responsive variants correctly', () => {
    const result = cn('text-sm md:text-lg lg:text-xl')
    expect(result).toContain('text-sm')
    expect(result).toContain('md:text-lg')
    expect(result).toContain('lg:text-xl')
  })

  it('should resolve conflicts in responsive variants', () => {
    const result = cn('md:px-2', 'md:px-4')
    expect(result).toBe('md:px-4')
    expect(result).not.toContain('md:px-2')
  })
})
