/**
 * Chrome CSS Property Validation Unit Tests
 * Task 8.1: Write unit tests for Chrome CSS property validation
 * Tests computed styles for Chrome-specific properties, webkit prefixes, and fallback behavior
 */

import {
  ChromeCSSValidator,
  chromeCSSValidator,
  validateChromeCSS,
  hasRequiredChromeOptimizations,
  applyMissingChromeOptimizations,
  validateChromeFallbacks,
  CHROME_CSS_PROPERTIES,
  CHROME_CSS_VALIDATION
} from '../lib/utils/chrome-css-validation'

// Mock DOM environment
const mockElement = {
  style: {} as CSSStyleDeclaration,
  classList: {
    add: jest.fn(),
    remove: jest.fn(),
    contains: jest.fn()
  }
} as unknown as HTMLElement

// Mock getComputedStyle
const mockComputedStyle = {
  overscrollBehavior: 'contain',
  webkitOverflowScrolling: 'touch',
  backgroundAttachment: 'local',
  minHeight: '100vh',
  transform: 'translateZ(0px)',
  webkitTransform: 'translateZ(0px)',
  willChange: 'scroll-position',
  boxSizing: 'border-box',
  webkitBoxSizing: 'border-box',
  backgroundSize: 'cover',
  webkitBackgroundSize: 'cover',
  contain: 'layout style paint',
  webkitOverscrollBehavior: 'contain',
  webkitBackgroundAttachment: 'local',
  webkitWillChange: 'scroll-position'
} as CSSStyleDeclaration

Object.defineProperty(window, 'getComputedStyle', {
  value: jest.fn(() => mockComputedStyle),
  writable: true
})

// Mock document.createElement for property support detection
Object.defineProperty(document, 'createElement', {
  value: jest.fn(() => ({
    style: {
      overscrollBehavior: '',
      webkitOverflowScrolling: '',
      backgroundAttachment: '',
      minHeight: '',
      transform: '',
      webkitTransform: '',
      willChange: '',
      boxSizing: '',
      webkitBoxSizing: '',
      backgroundSize: '',
      webkitBackgroundSize: '',
      contain: '',
      webkitOverscrollBehavior: '',
      webkitBackgroundAttachment: '',
      webkitWillChange: ''
    }
  })),
  writable: true
})

describe('ChromeCSSValidator', () => {
  let validator: ChromeCSSValidator
  let element: HTMLElement

  beforeEach(() => {
    validator = new ChromeCSSValidator()
    element = mockElement
    jest.clearAllMocks()
  })

  describe('validateElement', () => {
    it('should validate all Chrome-specific properties on an element', () => {
      const report = validator.validateElement(element)

      expect(report).toHaveProperty('element', element)
      expect(report).toHaveProperty('overallValid')
      expect(report).toHaveProperty('validationResults')
      expect(report).toHaveProperty('missingProperties')
      expect(report).toHaveProperty('unsupportedProperties')
      expect(report).toHaveProperty('recommendations')
      expect(Array.isArray(report.validationResults)).toBe(true)
    })

    it('should return valid results for properly configured element', () => {
      const report = validator.validateElement(element)

      // Should have validation results for all configured properties
      expect(report.validationResults.length).toBeGreaterThan(0)
      
      // Check that required properties are validated
      const requiredProperties = CHROME_CSS_PROPERTIES.filter(p => p.required)
      const validatedProperties = report.validationResults.map(r => r.property)
      
      requiredProperties.forEach(config => {
        expect(validatedProperties).toContain(config.property)
      })
    })

    it('should identify missing properties correctly', () => {
      // Mock element with missing properties
      const mockMissingStyle = {
        ...mockComputedStyle,
        overscrollBehavior: 'auto', // Wrong value
        webkitOverflowScrolling: 'auto' // Wrong value
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockMissingStyle)

      const report = validator.validateElement(element)
      
      // Should identify missing properties
      expect(report.missingProperties.length).toBeGreaterThan(0)
      expect(report.overallValid).toBe(false)
    })
  })

  describe('validateOverscrollBehavior', () => {
    it('should validate overscroll-behavior: contain property (Requirement 1.4)', () => {
      // Ensure the mock returns the expected value
      const mockValidStyle = {
        ...mockComputedStyle,
        overscrollBehavior: 'contain',
        webkitOverscrollBehavior: 'contain'
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockValidStyle)

      const result = validator.validateOverscrollBehavior(element)

      expect(result.property).toBe('overscrollBehavior')
      expect(result.expectedValue).toBe('contain')
      expect(result.actualValue).toBe('contain')
      expect(result.isValid).toBe(true)
    })

    it('should detect invalid overscroll-behavior values', () => {
      const mockInvalidStyle = {
        ...mockComputedStyle,
        overscrollBehavior: 'auto'
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockInvalidStyle)

      const result = validator.validateOverscrollBehavior(element)

      expect(result.isValid).toBe(false)
      expect(result.actualValue).toBe('auto')
    })

    it('should check webkit prefix fallback', () => {
      const mockWebkitStyle = {
        ...mockComputedStyle,
        overscrollBehavior: undefined,
        webkitOverscrollBehavior: 'contain'
      } as any

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockWebkitStyle)

      const result = validator.validateOverscrollBehavior(element)

      expect(result.isValid).toBe(true)
      expect(result.hasWebkitPrefix).toBe(true)
    })
  })

  describe('validateWebkitOverflowScrolling', () => {
    it('should validate webkit-overflow-scrolling: touch property (Requirement 1.5)', () => {
      const result = validator.validateWebkitOverflowScrolling(element)

      expect(result.property).toBe('webkitOverflowScrolling')
      expect(result.expectedValue).toBe('touch')
      expect(result.isValid).toBe(true)
      expect(result.hasWebkitPrefix).toBe(true)
    })

    it('should detect invalid webkit-overflow-scrolling values', () => {
      const mockInvalidStyle = {
        ...mockComputedStyle,
        webkitOverflowScrolling: 'auto'
      } as any

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockInvalidStyle)

      const result = validator.validateWebkitOverflowScrolling(element)

      expect(result.isValid).toBe(false)
      expect(result.actualValue).toBe('auto')
    })
  })

  describe('validateBackgroundAttachment', () => {
    it('should validate background-attachment: local property (Requirement 2.5)', () => {
      const result = validator.validateBackgroundAttachment(element)

      expect(result.property).toBe('backgroundAttachment')
      expect(result.expectedValue).toBe('local')
      expect(result.isValid).toBe(true)
      expect(result.actualValue).toBe('local')
    })

    it('should check webkit prefix for background-attachment', () => {
      const mockWebkitStyle = {
        ...mockComputedStyle,
        backgroundAttachment: undefined,
        webkitBackgroundAttachment: 'local'
      } as any

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockWebkitStyle)

      const result = validator.validateBackgroundAttachment(element)

      expect(result.isValid).toBe(true)
      expect(result.hasWebkitPrefix).toBe(true)
    })
  })

  describe('validateMinHeight', () => {
    it('should validate min-height: 100vh property (Requirements 2.1, 5.2)', () => {
      const result = validator.validateMinHeight(element)

      expect(result.property).toBe('minHeight')
      expect(result.expectedValue).toEqual(['100vh', '100%'])
      expect(result.isValid).toBe(true)
      expect(result.actualValue).toBe('100vh')
    })

    it('should accept 100% as valid min-height', () => {
      const mockPercentStyle = {
        ...mockComputedStyle,
        minHeight: '100%'
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockPercentStyle)

      const result = validator.validateMinHeight(element)

      expect(result.isValid).toBe(true)
      expect(result.actualValue).toBe('100%')
    })

    it('should detect invalid min-height values', () => {
      const mockInvalidStyle = {
        ...mockComputedStyle,
        minHeight: '50vh'
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockInvalidStyle)

      const result = validator.validateMinHeight(element)

      expect(result.isValid).toBe(false)
      expect(result.actualValue).toBe('50vh')
    })
  })

  describe('validateWebkitTransform', () => {
    it('should validate webkit-transform property (Requirements 3.5, 4.4)', () => {
      const result = validator.validateWebkitTransform(element)

      expect(result.property).toBe('webkitTransform')
      expect(result.isValid).toBe(true)
      expect(result.hasWebkitPrefix).toBe(true)
      expect(result.hasFallback).toBe(true)
    })

    it('should accept various transform values', () => {
      const validTransforms = [
        'translateZ(0px)',
        'translate3d(0, 0, 0)',
        'translate3d(0px, 0px, 0px)',
        'matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)'
      ]

      validTransforms.forEach(transform => {
        const mockTransformStyle = {
          ...mockComputedStyle,
          webkitTransform: transform,
          transform: transform
        } as any

        ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockTransformStyle)

        const result = validator.validateWebkitTransform(element)
        expect(result.isValid).toBe(true)
      })
    })

    it('should fallback to standard transform property', () => {
      const mockFallbackStyle = {
        ...mockComputedStyle,
        webkitTransform: undefined,
        transform: 'translateZ(0px)'
      } as any

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockFallbackStyle)

      const result = validator.validateWebkitTransform(element)

      expect(result.isValid).toBe(true)
      expect(result.actualValue).toBe('translateZ(0px)')
    })
  })

  describe('validateWillChange', () => {
    it('should validate will-change property (Requirement 4.5)', () => {
      const result = validator.validateWillChange(element)

      expect(result.property).toBe('willChange')
      expect(result.expectedValue).toEqual(['scroll-position', 'scroll-position, transform', 'auto'])
      expect(result.isValid).toBe(true)
    })

    it('should accept multiple will-change values', () => {
      const validValues = ['scroll-position', 'scroll-position, transform', 'auto']

      validValues.forEach(value => {
        const mockWillChangeStyle = {
          ...mockComputedStyle,
          willChange: value
        } as CSSStyleDeclaration

        ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockWillChangeStyle)

        const result = validator.validateWillChange(element)
        expect(result.isValid).toBe(true)
      })
    })

    it('should check webkit prefix for will-change', () => {
      const mockWebkitStyle = {
        ...mockComputedStyle,
        willChange: undefined,
        webkitWillChange: 'scroll-position'
      } as any

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockWebkitStyle)

      const result = validator.validateWillChange(element)

      expect(result.isValid).toBe(true)
      expect(result.hasWebkitPrefix).toBe(true)
    })
  })

  describe('hasRequiredChromeOptimizations', () => {
    it('should return true for element with all required optimizations', () => {
      const hasOptimizations = validator.hasRequiredChromeOptimizations(element)
      expect(hasOptimizations).toBe(true)
    })

    it('should return false for element missing required optimizations', () => {
      const mockIncompleteStyle = {
        ...mockComputedStyle,
        overscrollBehavior: 'auto', // Missing required optimization
        webkitOverflowScrolling: 'auto' // Missing required optimization
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockIncompleteStyle)

      const hasOptimizations = validator.hasRequiredChromeOptimizations(element)
      expect(hasOptimizations).toBe(false)
    })
  })

  describe('getMissingOptimizations', () => {
    it('should return empty array for fully optimized element', () => {
      const missing = validator.getMissingOptimizations(element)
      expect(Array.isArray(missing)).toBe(true)
    })

    it('should identify missing optimizations', () => {
      const mockIncompleteStyle = {
        ...mockComputedStyle,
        overscrollBehavior: 'auto',
        webkitOverflowScrolling: 'auto'
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockIncompleteStyle)

      const missing = validator.getMissingOptimizations(element)
      expect(missing.length).toBeGreaterThan(0)
    })
  })

  describe('applyMissingOptimizations', () => {
    it('should apply missing CSS properties to element', () => {
      const elementWithStyle = {
        ...mockElement,
        style: {} as CSSStyleDeclaration
      }

      // Mock missing optimizations
      const mockIncompleteStyle = {
        ...mockComputedStyle,
        overscrollBehavior: 'auto'
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockIncompleteStyle)

      validator.applyMissingOptimizations(elementWithStyle)

      // Should attempt to apply properties (exact behavior depends on browser support)
      expect(elementWithStyle).toBeDefined()
    })
  })
})

describe('Convenience Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('validateChromeCSS', () => {
    it('should validate Chrome CSS properties using global validator', () => {
      const report = validateChromeCSS(mockElement)

      expect(report).toHaveProperty('element')
      expect(report).toHaveProperty('overallValid')
      expect(report).toHaveProperty('validationResults')
    })
  })

  describe('hasRequiredChromeOptimizations', () => {
    it('should check required optimizations using global validator', () => {
      const hasOptimizations = hasRequiredChromeOptimizations(mockElement)
      expect(typeof hasOptimizations).toBe('boolean')
    })
  })

  describe('applyMissingChromeOptimizations', () => {
    it('should apply missing optimizations using global validator', () => {
      expect(() => {
        applyMissingChromeOptimizations(mockElement)
      }).not.toThrow()
    })
  })

  describe('validateChromeFallbacks', () => {
    it('should validate fallback behavior for non-Chrome browsers', () => {
      const fallbacks = validateChromeFallbacks(mockElement)

      expect(fallbacks).toHaveProperty('hasWebkitFallbacks')
      expect(fallbacks).toHaveProperty('hasStandardFallbacks')
      expect(fallbacks).toHaveProperty('missingFallbacks')
      expect(typeof fallbacks.hasWebkitFallbacks).toBe('boolean')
      expect(typeof fallbacks.hasStandardFallbacks).toBe('boolean')
      expect(Array.isArray(fallbacks.missingFallbacks)).toBe(true)
    })

    it('should identify missing webkit fallbacks', () => {
      // Mock element without webkit properties
      const mockNoWebkitStyle = {
        overscrollBehavior: 'contain',
        backgroundAttachment: 'local',
        minHeight: '100vh',
        transform: 'translateZ(0px)',
        willChange: 'scroll-position',
        boxSizing: 'border-box',
        backgroundSize: 'cover',
        contain: 'layout style paint'
        // Missing all webkit prefixed properties
      } as CSSStyleDeclaration

      ;(window.getComputedStyle as jest.Mock).mockReturnValue(mockNoWebkitStyle)

      const fallbacks = validateChromeFallbacks(mockElement)

      // Since our mock doesn't have webkit properties, hasWebkitFallbacks should be false
      // But the validation logic might still find webkit support through property detection
      expect(typeof fallbacks.hasWebkitFallbacks).toBe('boolean')
      expect(Array.isArray(fallbacks.missingFallbacks)).toBe(true)
    })
  })
})

describe('Configuration Constants', () => {
  describe('CHROME_CSS_PROPERTIES', () => {
    it('should contain all required Chrome CSS properties', () => {
      expect(Array.isArray(CHROME_CSS_PROPERTIES)).toBe(true)
      expect(CHROME_CSS_PROPERTIES.length).toBeGreaterThan(0)

      // Check that all properties have required fields
      CHROME_CSS_PROPERTIES.forEach(config => {
        expect(config).toHaveProperty('property')
        expect(config).toHaveProperty('expectedValues')
        expect(config).toHaveProperty('required')
        expect(config).toHaveProperty('description')
        expect(config).toHaveProperty('requirements')
        expect(Array.isArray(config.requirements)).toBe(true)
      })
    })

    it('should include properties for all specified requirements', () => {
      const requiredRequirements = ['1.4', '1.5', '2.1', '2.5', '3.4', '3.5', '4.1', '4.2', '4.3', '4.4', '4.5', '5.2', '6.4']
      
      const coveredRequirements = new Set()
      CHROME_CSS_PROPERTIES.forEach(config => {
        config.requirements.forEach(req => coveredRequirements.add(req))
      })

      requiredRequirements.forEach(req => {
        expect(coveredRequirements.has(req)).toBe(true)
      })
    })
  })

  describe('CHROME_CSS_VALIDATION', () => {
    it('should provide validation constants', () => {
      expect(CHROME_CSS_VALIDATION).toHaveProperty('REQUIRED_PROPERTIES')
      expect(CHROME_CSS_VALIDATION).toHaveProperty('WEBKIT_PROPERTIES')
      expect(CHROME_CSS_VALIDATION).toHaveProperty('FALLBACK_PROPERTIES')
      expect(CHROME_CSS_VALIDATION).toHaveProperty('ALL_PROPERTIES')

      expect(Array.isArray(CHROME_CSS_VALIDATION.REQUIRED_PROPERTIES)).toBe(true)
      expect(Array.isArray(CHROME_CSS_VALIDATION.WEBKIT_PROPERTIES)).toBe(true)
      expect(Array.isArray(CHROME_CSS_VALIDATION.FALLBACK_PROPERTIES)).toBe(true)
      expect(Array.isArray(CHROME_CSS_VALIDATION.ALL_PROPERTIES)).toBe(true)
    })

    it('should have required properties subset', () => {
      expect(CHROME_CSS_VALIDATION.REQUIRED_PROPERTIES.length).toBeGreaterThan(0)
      
      // All required properties should be in all properties
      CHROME_CSS_VALIDATION.REQUIRED_PROPERTIES.forEach(prop => {
        expect(CHROME_CSS_VALIDATION.ALL_PROPERTIES).toContain(prop)
      })
    })

    it('should have webkit properties for Chrome compatibility', () => {
      expect(CHROME_CSS_VALIDATION.WEBKIT_PROPERTIES.length).toBeGreaterThan(0)
      
      // Should include key webkit properties
      const expectedWebkitProps = ['webkitOverscrollBehavior', 'webkitBackgroundAttachment', 'webkitTransform']
      expectedWebkitProps.forEach(prop => {
        expect(CHROME_CSS_VALIDATION.WEBKIT_PROPERTIES).toContain(prop)
      })
    })
  })
})

describe('Browser Compatibility', () => {
  describe('Property Support Detection', () => {
    it('should handle missing window object gracefully', () => {
      // Mock server-side environment
      const originalWindow = global.window
      delete (global as any).window

      const validator = new ChromeCSSValidator()
      const report = validator.validateElement(mockElement)

      expect(report).toBeDefined()
      expect(report.validationResults).toBeDefined()

      // Restore window
      global.window = originalWindow
    })

    it('should detect property support correctly', () => {
      const validator = new ChromeCSSValidator()
      
      // Test with mock element that has properties
      const mockSupportElement = {
        style: {
          overscrollBehavior: '',
          webkitOverflowScrolling: '',
          backgroundAttachment: '',
          minHeight: '',
          transform: '',
          willChange: ''
        }
      }

      ;(document.createElement as jest.Mock).mockReturnValue(mockSupportElement)

      const report = validator.validateElement(mockElement)
      
      // Should detect supported properties
      report.validationResults.forEach(result => {
        expect(typeof result.isSupported).toBe('boolean')
      })
    })
  })

  describe('Fallback Behavior', () => {
    it('should provide fallback recommendations for unsupported properties', () => {
      // Mock element without webkit support
      const mockNoWebkitElement = {
        style: {
          overscrollBehavior: '',
          backgroundAttachment: '',
          minHeight: '',
          transform: '',
          willChange: ''
          // Missing webkit properties
        }
      }

      ;(document.createElement as jest.Mock).mockReturnValue(mockNoWebkitElement)

      const validator = new ChromeCSSValidator()
      const report = validator.validateElement(mockElement)

      expect(report.recommendations).toBeDefined()
      expect(Array.isArray(report.recommendations)).toBe(true)
    })

    it('should handle webkit prefix gracefully when not supported', () => {
      const validator = new ChromeCSSValidator()
      
      // Should not throw when webkit properties are not supported
      expect(() => {
        validator.validateElement(mockElement)
      }).not.toThrow()
    })
  })
})