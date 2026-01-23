/**
 * Property-Based Tests for Manifest Validation
 * Feature: ui-structure-tests
 * Property 7: Manifest Validation Correctness
 * 
 * Validates: Requirements 5.2, 5.3
 */

import * as fc from 'fast-check';
import {
  validatePageStructure,
  validateComponentStructure,
  ElementDefinition,
  SectionDefinition,
  PageStructure,
  ComponentStructure,
} from '@/lib/testing/structure-manifest';

describe('Manifest Validation - Property Tests', () => {
  describe('Property 7: Manifest Validation Correctness', () => {
    // Arbitraries for generating valid structures
    const elementArbitrary = fc.record({
      testId: fc.string({ minLength: 1, maxLength: 50 }),
      required: fc.boolean(),
      description: fc.string({ minLength: 1, maxLength: 100 }),
    }) as fc.Arbitrary<ElementDefinition>;

    const sectionArbitrary = fc.record({
      name: fc.string({ minLength: 1, maxLength: 50 }),
      testId: fc.string({ minLength: 1, maxLength: 50 }),
      required: fc.boolean(),
      elements: fc.array(elementArbitrary, { minLength: 1, maxLength: 5 }),
    }) as fc.Arbitrary<SectionDefinition>;

    const pageStructureArbitrary = fc.record({
      path: fc.constantFrom('/dashboard', '/projects', '/financials', '/reports'),
      name: fc.string({ minLength: 1, maxLength: 50 }),
      sections: fc.array(sectionArbitrary, { minLength: 1, maxLength: 5 }),
    }) as fc.Arbitrary<PageStructure>;

    const componentStructureArbitrary = fc.record({
      name: fc.string({ minLength: 1, maxLength: 50 }),
      testId: fc.string({ minLength: 1, maxLength: 50 }),
      requiredElements: fc.array(elementArbitrary, { minLength: 1, maxLength: 5 }),
      states: fc.record({
        loading: fc.option(fc.array(elementArbitrary, { maxLength: 3 }), { nil: undefined }),
        error: fc.option(fc.array(elementArbitrary, { maxLength: 3 }), { nil: undefined }),
        empty: fc.option(fc.array(elementArbitrary, { maxLength: 3 }), { nil: undefined }),
      }),
    }) as fc.Arbitrary<ComponentStructure>;

    describe('Valid Manifests', () => {
      it('accepts valid page structures', () => {
        fc.assert(
          fc.property(pageStructureArbitrary, (pageStructure) => {
            const result = validatePageStructure(pageStructure);
            
            // Valid structures should pass validation
            expect(result.valid).toBe(true);
            expect(result.errors).toHaveLength(0);
          }),
          { numRuns: 100 }
        );
      });

      it('accepts valid component structures', () => {
        fc.assert(
          fc.property(componentStructureArbitrary, (componentStructure) => {
            const result = validateComponentStructure(componentStructure);
            
            // Valid structures should pass validation
            expect(result.valid).toBe(true);
            expect(result.errors).toHaveLength(0);
          }),
          { numRuns: 100 }
        );
      });
    });

    describe('Invalid Manifests - Missing Required Fields', () => {
      it('rejects page structures without path', () => {
        fc.assert(
          fc.property(pageStructureArbitrary, (pageStructure) => {
            const invalid = { ...pageStructure, path: undefined };
            const result = validatePageStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'path')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects page structures without name', () => {
        fc.assert(
          fc.property(pageStructureArbitrary, (pageStructure) => {
            const invalid = { ...pageStructure, name: undefined };
            const result = validatePageStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'name')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects page structures without sections', () => {
        fc.assert(
          fc.property(pageStructureArbitrary, (pageStructure) => {
            const invalid = { ...pageStructure, sections: undefined };
            const result = validatePageStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'sections')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects component structures without name', () => {
        fc.assert(
          fc.property(componentStructureArbitrary, (componentStructure) => {
            const invalid = { ...componentStructure, name: undefined };
            const result = validateComponentStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'name')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects component structures without testId', () => {
        fc.assert(
          fc.property(componentStructureArbitrary, (componentStructure) => {
            const invalid = { ...componentStructure, testId: undefined };
            const result = validateComponentStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'testId')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects component structures without requiredElements', () => {
        fc.assert(
          fc.property(componentStructureArbitrary, (componentStructure) => {
            const invalid = { ...componentStructure, requiredElements: undefined };
            const result = validateComponentStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'requiredElements')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects component structures without states', () => {
        fc.assert(
          fc.property(componentStructureArbitrary, (componentStructure) => {
            const invalid = { ...componentStructure, states: undefined };
            const result = validateComponentStructure(invalid);
            
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
            expect(result.errors.some(e => e.path === 'states')).toBe(true);
          }),
          { numRuns: 50 }
        );
      });
    });

    describe('Invalid Manifests - Wrong Types', () => {
      it('rejects page structures with non-string path', () => {
        fc.assert(
          fc.property(
            pageStructureArbitrary,
            fc.oneof(fc.integer(), fc.boolean(), fc.constant(null)),
            (pageStructure, invalidPath) => {
              const invalid = { ...pageStructure, path: invalidPath };
              const result = validatePageStructure(invalid);
              
              expect(result.valid).toBe(false);
              expect(result.errors.some(e => e.path === 'path')).toBe(true);
            }
          ),
          { numRuns: 50 }
        );
      });

      it('rejects page structures with non-array sections', () => {
        fc.assert(
          fc.property(
            pageStructureArbitrary,
            fc.oneof(fc.string(), fc.integer(), fc.constant(null)),
            (pageStructure, invalidSections) => {
              const invalid = { ...pageStructure, sections: invalidSections };
              const result = validatePageStructure(invalid);
              
              expect(result.valid).toBe(false);
              expect(result.errors.some(e => e.path === 'sections')).toBe(true);
            }
          ),
          { numRuns: 50 }
        );
      });

      it('rejects component structures with non-array requiredElements', () => {
        fc.assert(
          fc.property(
            componentStructureArbitrary,
            fc.oneof(fc.string(), fc.integer(), fc.constant(null)),
            (componentStructure, invalidElements) => {
              const invalid = { ...componentStructure, requiredElements: invalidElements };
              const result = validateComponentStructure(invalid);
              
              expect(result.valid).toBe(false);
              expect(result.errors.some(e => e.path === 'requiredElements')).toBe(true);
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Invalid Element Definitions', () => {
      it('rejects sections with invalid elements', () => {
        fc.assert(
          fc.property(pageStructureArbitrary, (pageStructure) => {
            const invalidElement = {
              testId: '', // Empty testId is invalid
              required: true,
              description: 'test',
            };
            
            const invalidStructure = {
              ...pageStructure,
              sections: [
                {
                  ...pageStructure.sections[0],
                  elements: [invalidElement],
                },
              ],
            };
            
            const result = validatePageStructure(invalidStructure);
            
            // Should have validation errors for the invalid element
            expect(result.errors.length).toBeGreaterThan(0);
          }),
          { numRuns: 50 }
        );
      });

      it('rejects elements without required field', () => {
        const invalidElement = {
          testId: 'test-id',
          // missing required field
          description: 'test description',
        };
        
        const pageStructure = {
          path: '/test',
          name: 'Test',
          sections: [
            {
              name: 'Test Section',
              testId: 'test-section',
              required: true,
              elements: [invalidElement],
            },
          ],
        };
        
        const result = validatePageStructure(pageStructure);
        
        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.path.includes('required'))).toBe(true);
      });

      it('rejects elements without description', () => {
        const invalidElement = {
          testId: 'test-id',
          required: true,
          // missing description
        };
        
        const pageStructure = {
          path: '/test',
          name: 'Test',
          sections: [
            {
              name: 'Test Section',
              testId: 'test-section',
              required: true,
              elements: [invalidElement],
            },
          ],
        };
        
        const result = validatePageStructure(pageStructure);
        
        expect(result.valid).toBe(false);
        expect(result.errors.some(e => e.path.includes('description'))).toBe(true);
      });
    });

    describe('Error Reporting Specificity', () => {
      it('provides specific error paths for nested validation failures', () => {
        const pageStructure = {
          path: '/test',
          name: 'Test',
          sections: [
            {
              name: 'Section 1',
              testId: 'section-1',
              required: true,
              elements: [
                {
                  testId: '', // Invalid
                  required: true,
                  description: 'test',
                },
              ],
            },
          ],
        };
        
        const result = validatePageStructure(pageStructure);
        
        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
        // Error path should indicate the specific element
        expect(result.errors.some(e => e.path.includes('sections[0]'))).toBe(true);
        expect(result.errors.some(e => e.path.includes('elements[0]'))).toBe(true);
      });

      it('reports all validation errors, not just the first one', () => {
        const invalidStructure = {
          // Missing path
          // Missing name
          sections: 'not an array', // Wrong type
        };
        
        const result = validatePageStructure(invalidStructure);
        
        expect(result.valid).toBe(false);
        // Should have multiple errors
        expect(result.errors.length).toBeGreaterThanOrEqual(3);
      });
    });

    describe('Edge Cases', () => {
      it('handles null input gracefully', () => {
        const result = validatePageStructure(null);
        
        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      });

      it('handles undefined input gracefully', () => {
        const result = validateComponentStructure(undefined);
        
        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      });

      it('handles empty objects', () => {
        const result = validatePageStructure({});
        
        expect(result.valid).toBe(false);
        expect(result.errors.length).toBeGreaterThan(0);
      });

      it('handles structures with empty arrays', () => {
        const pageStructure = {
          path: '/test',
          name: 'Test',
          sections: [], // Empty sections array
        };
        
        const result = validatePageStructure(pageStructure);
        
        // Empty sections array is technically valid, just not useful
        expect(result.valid).toBe(true);
      });
    });
  });
});
