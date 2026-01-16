/**
 * Tests for CLS Prevention Utilities
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals'
import { 
  calculateAspectRatio, 
  getSkeletonDimensions,
  imageLoadingConfig
} from '../lib/performance/cls-fixes'

describe('CLS Prevention Utilities', () => {
  describe('calculateAspectRatio', () => {
    it('should calculate correct aspect ratio for common dimensions', () => {
      expect(calculateAspectRatio(1920, 1080)).toBe('16 / 9')
      expect(calculateAspectRatio(1280, 720)).toBe('16 / 9')
      expect(calculateAspectRatio(800, 600)).toBe('4 / 3')
      expect(calculateAspectRatio(1000, 1000)).toBe('1 / 1')
    })

    it('should handle non-standard dimensions', () => {
      expect(calculateAspectRatio(1366, 768)).toBe('683 / 384')
      expect(calculateAspectRatio(1024, 768)).toBe('4 / 3')
    })

    it('should handle portrait orientations', () => {
      expect(calculateAspectRatio(1080, 1920)).toBe('9 / 16')
      expect(calculateAspectRatio(600, 800)).toBe('3 / 4')
    })
  })

  describe('getSkeletonDimensions', () => {
    it('should return correct dimensions for stat variant', () => {
      const dimensions = getSkeletonDimensions('stat')
      expect(dimensions.height).toBe('120px')
      expect(dimensions.aspectRatio).toBeUndefined()
    })

    it('should return correct dimensions for chart variant', () => {
      const dimensions = getSkeletonDimensions('chart')
      expect(dimensions.height).toBe('320px')
      expect(dimensions.aspectRatio).toBe('16 / 9')
    })

    it('should return correct dimensions for project variant', () => {
      const dimensions = getSkeletonDimensions('project')
      expect(dimensions.height).toBe('180px')
    })

    it('should return default dimensions for unknown variant', () => {
      const dimensions = getSkeletonDimensions('unknown')
      expect(dimensions.height).toBe('120px')
    })
  })

  describe('imageLoadingConfig', () => {
    it('should have correct loading strategy', () => {
      expect(imageLoadingConfig.loading).toBe('lazy')
      expect(imageLoadingConfig.decoding).toBe('async')
    })

    it('should have placeholder for images without dimensions', () => {
      expect(imageLoadingConfig.placeholder).toContain('data:image/svg+xml')
    })

    it('should have predefined aspect ratios', () => {
      expect(imageLoadingConfig.aspectRatios.thumbnail).toBe('1 / 1')
      expect(imageLoadingConfig.aspectRatios.card).toBe('16 / 9')
      expect(imageLoadingConfig.aspectRatios.banner).toBe('21 / 9')
      expect(imageLoadingConfig.aspectRatios.portrait).toBe('3 / 4')
    })
  })
})

describe('CLS Prevention in Browser', () => {
  let originalDocument: Document
  let originalWindow: Window & typeof globalThis

  beforeEach(() => {
    originalDocument = global.document
    originalWindow = global.window as Window & typeof globalThis
  })

  afterEach(() => {
    global.document = originalDocument
    global.window = originalWindow
  })

  it('should not throw errors when document is undefined', () => {
    // @ts-ignore
    global.document = undefined
    // @ts-ignore  
    global.window = undefined

    expect(() => {
      const { reserveFixedElementSpace } = require('../lib/performance/cls-fixes')
      reserveFixedElementSpace()
    }).not.toThrow()
  })
})
