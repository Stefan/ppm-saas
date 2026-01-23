/**
 * Property-Based Tests for Test ID Generator
 * Feature: ui-structure-tests
 * Property 1: Test ID Generation Consistency
 * 
 * Validates: Requirements 1.1, 1.3
 */

import * as fc from 'fast-check';
import {
  generateTestId,
  createTestIdBuilder,
  generateTestIdFromOptions,
} from '@/lib/testing/test-id';

describe('Test ID Generator - Property Tests', () => {
  describe('Property 1: Test ID Generation Consistency', () => {
    it('generates consistent output for same inputs', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
          fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
          (component, element, variant) => {
            const id1 = generateTestId(component, element, variant);
            const id2 = generateTestId(component, element, variant);
            
            // Same inputs must produce same outputs
            expect(id1).toBe(id2);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('always produces valid kebab-case format', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
          fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
          (component, element, variant) => {
            const id = generateTestId(component, element, variant);
            
            // Must match kebab-case pattern: lowercase alphanumeric with hyphens
            // Allow empty string for edge cases where all chars are stripped
            if (id.length > 0) {
              expect(id).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('handles camelCase input correctly', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(
            'myComponent',
            'MyComponent',
            'myComponentName',
            'MyComponentName',
            'varianceKPIs',
            'VarianceKPIs'
          ),
          (component) => {
            const id = generateTestId(component);
            
            // Should convert to kebab-case
            expect(id).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
            expect(id).not.toContain('_');
            expect(id).not.toMatch(/[A-Z]/);
          }
        ),
        { numRuns: 50 }
      );
    });

    it('handles special characters by removing them', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          (component) => {
            const id = generateTestId(component);
            
            // Should only contain lowercase letters, numbers, and hyphens
            if (id.length > 0) {
              expect(id).toMatch(/^[a-z0-9-]*$/);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('produces deterministic output regardless of call order', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 30 }),
          fc.string({ minLength: 1, maxLength: 30 }),
          fc.string({ minLength: 1, maxLength: 30 }),
          (comp1, comp2, comp3) => {
            // Generate IDs in different orders
            const id1a = generateTestId(comp1);
            const id2a = generateTestId(comp2);
            const id3a = generateTestId(comp3);
            
            const id3b = generateTestId(comp3);
            const id1b = generateTestId(comp1);
            const id2b = generateTestId(comp2);
            
            // Order of calls should not affect output
            expect(id1a).toBe(id1b);
            expect(id2a).toBe(id2b);
            expect(id3a).toBe(id3b);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('createTestIdBuilder - Property Tests', () => {
    it('builder produces consistent IDs', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          (componentName) => {
            const builder1 = createTestIdBuilder(componentName);
            const builder2 = createTestIdBuilder(componentName);
            
            // Same component name should produce same root ID
            expect(builder1.root()).toBe(builder2.root());
          }
        ),
        { numRuns: 100 }
      );
    });

    it('builder element method produces valid kebab-case', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 1, maxLength: 50 }),
          (componentName, elementName) => {
            const builder = createTestIdBuilder(componentName);
            const elementId = builder.element(elementName);
            
            if (elementId.length > 0) {
              expect(elementId).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('builder variant method produces valid kebab-case', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 1, maxLength: 50 }),
          (componentName, elementName, variantName) => {
            const builder = createTestIdBuilder(componentName);
            const variantId = builder.variant(elementName, variantName);
            
            if (variantId.length > 0) {
              expect(variantId).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('builder methods are consistent with generateTestId', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 1, maxLength: 50 }),
          (componentName, elementName, variantName) => {
            const builder = createTestIdBuilder(componentName);
            
            // Builder root should match generateTestId with just component
            expect(builder.root()).toBe(generateTestId(componentName));
            
            // Builder element should match generateTestId with component and element
            expect(builder.element(elementName)).toBe(
              generateTestId(componentName, elementName)
            );
            
            // Builder variant should match generateTestId with all three
            expect(builder.variant(elementName, variantName)).toBe(
              generateTestId(componentName, elementName, variantName)
            );
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('generateTestIdFromOptions - Property Tests', () => {
    it('produces same output as generateTestId', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
          fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
          (component, element, variant) => {
            const directId = generateTestId(component, element, variant);
            const optionsId = generateTestIdFromOptions({
              component,
              element,
              variant,
            });
            
            expect(optionsId).toBe(directId);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Edge Cases - Property Tests', () => {
    it('handles empty strings gracefully', () => {
      const id = generateTestId('', '', '');
      expect(typeof id).toBe('string');
    });

    it('handles whitespace-only strings', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('   ', '\t\t', '\n\n', '  \t  \n  '),
          (whitespace) => {
            const id = generateTestId(whitespace);
            expect(typeof id).toBe('string');
            // Whitespace should be stripped
            expect(id).not.toMatch(/\s/);
          }
        ),
        { numRuns: 20 }
      );
    });

    it('handles strings with only special characters', () => {
      fc.assert(
        fc.property(
          fc.constantFrom('!!!', '@@@', '###', '$$$', '%%%'),
          (special) => {
            const id = generateTestId(special);
            expect(typeof id).toBe('string');
            // Special chars should be removed
            if (id.length > 0) {
              expect(id).toMatch(/^[a-z0-9-]*$/);
            }
          }
        ),
        { numRuns: 20 }
      );
    });

    it('handles very long strings', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 100, maxLength: 500 }),
          (longString) => {
            const id = generateTestId(longString);
            expect(typeof id).toBe('string');
            if (id.length > 0) {
              expect(id).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('handles mixed case and special characters', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(
            'My_Component-Name',
            'my Component Name',
            'MyComponent123',
            'component_name_123',
            'Component-Name-V2'
          ),
          (mixed) => {
            const id = generateTestId(mixed);
            if (id.length > 0) {
              expect(id).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/);
            }
          }
        ),
        { numRuns: 50 }
      );
    });
  });
});
