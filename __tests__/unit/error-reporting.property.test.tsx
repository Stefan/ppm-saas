/**
 * Property-Based Tests for Error Reporting
 * Feature: ui-structure-tests
 * 
 * Property 5: Error Reporting Completeness
 * Property 13: Timeout Error Classification
 * 
 * Validates: Requirements 8.1, 2.3, 8.5
 */

import React from 'react';
import * as fc from 'fast-check';
import { render, cleanup } from '@testing-library/react';
import {
  verifyComponentStructure,
  verifyElementsExist,
  formatVerificationError,
  classifyTimeoutFailure,
} from '@/lib/testing/structure-test-utils';
import type {
  ComponentStructure,
  StructureVerificationResult,
} from '@/lib/testing/structure-manifest';

// Cleanup after each test to prevent DOM accumulation
afterEach(() => {
  cleanup();
});

// ============================================================================
// Test Components
// ============================================================================

/**
 * Creates a test component with specified test IDs
 */
function createTestComponent(testIds: string[]) {
  return function TestComponent() {
    return (
      <div>
        {testIds.map((testId, index) => (
          <div key={`${testId}-${index}`} data-testid={testId}>
            {testId}
          </div>
        ))}
      </div>
    );
  };
}

// ============================================================================
// Property 5: Error Reporting Completeness
// ============================================================================

describe('Property 5: Error Reporting Completeness', () => {
  it('error reports contain expected element test ID', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.constantFrom('button', 'input', 'header', 'footer', 'nav', 'main'),
          { minLength: 1, maxLength: 5 }
        ),
        (testIds) => {
          // Ensure unique test IDs
          const uniqueIds = [...new Set(testIds)];
          
          // Create empty component (no elements)
          const EmptyComponent = () => <div>Empty</div>;
          const result = render(<EmptyComponent />);
          
          // Verify elements - all should be missing
          const verification = verifyElementsExist(result, uniqueIds);
          
          // All missing elements should be in the result
          uniqueIds.forEach(testId => {
            expect(verification.missingElements).toContain(testId);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('error reports contain actual state (missing)', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('button-primary', 'input-email', 'header-title'),
        (testId) => {
          // Create empty component
          const EmptyComponent = () => <div>Empty</div>;
          const result = render(<EmptyComponent />);
          
          // Verify element
          const verification = verifyElementsExist(result, [testId]);
          
          // Should report as missing
          expect(verification.passed).toBe(false);
          expect(verification.missingElements).toContain(testId);
          expect(verification.foundElements).not.toContain(testId);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('error reports contain suggested fix for missing elements', () => {
    fc.assert(
      fc.property(
        fc.record({
          name: fc.constantFrom('Button', 'Input', 'Header'),
          testId: fc.constantFrom('button', 'input', 'header'),
          requiredElements: fc.constant([
            {
              testId: 'element-1',
              required: true,
              description: 'First element',
            },
          ]),
          states: fc.constant({}),
        }),
        (structure: ComponentStructure) => {
          // Create empty component
          const EmptyComponent = () => <div>Empty</div>;
          const result = render(<EmptyComponent />);
          
          // Verify component structure
          const verification = verifyComponentStructure(result, structure);
          
          // Should have suggested fixes
          expect(verification.suggestedFixes.length).toBeGreaterThan(0);
          
          // Suggested fix should mention the missing element
          const hasFix = verification.suggestedFixes.some(fix =>
            fix.includes('element-1')
          );
          expect(hasFix).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('formatted error message includes all required information', () => {
    fc.assert(
      fc.property(
        fc.record({
          name: fc.constantFrom('TestComponent'),
          testId: fc.constantFrom('test-component'),
          requiredElements: fc.constant([
            {
              testId: 'required-element',
              required: true,
              description: 'A required element',
            },
          ]),
          states: fc.constant({}),
        }),
        (structure: ComponentStructure) => {
          // Create empty component
          const EmptyComponent = () => <div>Empty</div>;
          const result = render(<EmptyComponent />);
          
          // Verify component structure
          const verification = verifyComponentStructure(result, structure);
          
          // Format error message
          const errorMessage = formatVerificationError(verification);
          
          // Error message should contain:
          // 1. Component name
          expect(errorMessage).toContain(structure.name);
          
          // 2. Missing element test ID
          expect(errorMessage).toContain('required-element');
          
          // 3. Suggested fix
          expect(errorMessage.toLowerCase()).toMatch(/add|missing/);
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ============================================================================
// Property 13: Timeout Error Classification
// ============================================================================

describe('Property 13: Timeout Error Classification', () => {
  it('classifies as "full" when no elements found', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 10 }),
        (totalElements) => {
          // Create a result with no elements found
          const result: StructureVerificationResult = {
            passed: false,
            missingElements: Array(totalElements).fill('missing'),
            unexpectedElements: [],
            details: Array(totalElements).fill(null).map((_, i) => ({
              testId: `element-${i}`,
              found: false,
              visible: false,
              accessible: true,
            })),
            sectionResults: [],
            suggestedFixes: [],
            elementsFound: 0,
          };
          
          const classification = classifyTimeoutFailure(result);
          
          expect(classification).toBe('full');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('classifies as "partial" when some elements found', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 10 }),
        fc.integer({ min: 1, max: 5 }),
        (totalElements, foundCount) => {
          // Ensure foundCount is less than totalElements
          const actualFoundCount = Math.min(foundCount, totalElements - 1);
          
          // Skip if no partial state possible
          if (actualFoundCount === 0 || actualFoundCount >= totalElements) return;
          
          // Create a result with some elements found
          const result: StructureVerificationResult = {
            passed: false,
            missingElements: [],
            unexpectedElements: [],
            details: Array(totalElements).fill(null).map((_, i) => ({
              testId: `element-${i}`,
              found: i < actualFoundCount,
              visible: i < actualFoundCount,
              accessible: true,
            })),
            sectionResults: [],
            suggestedFixes: [],
            elementsFound: actualFoundCount,
          };
          
          const classification = classifyTimeoutFailure(result);
          
          expect(classification).toBe('partial');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('timeout error includes elements found count', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 10 }),
        fc.integer({ min: 0, max: 10 }),
        (totalElements, foundCount) => {
          const actualFoundCount = Math.min(foundCount, totalElements);
          
          // Create a result
          const result: StructureVerificationResult = {
            passed: false,
            missingElements: [],
            unexpectedElements: [],
            details: Array(totalElements).fill(null).map((_, i) => ({
              testId: `element-${i}`,
              found: i < actualFoundCount,
              visible: i < actualFoundCount,
              accessible: true,
            })),
            sectionResults: [],
            suggestedFixes: [],
            elementsFound: actualFoundCount,
            timeoutFailure: true,
            timeoutClassification: actualFoundCount === 0 ? 'full' : 'partial',
          };
          
          // Format error message
          const errorMessage = formatVerificationError(result);
          
          // Should include timeout information
          expect(errorMessage.toLowerCase()).toContain('timeout');
          
          // Should include elements found count
          expect(errorMessage).toContain(actualFoundCount.toString());
          expect(errorMessage).toContain(totalElements.toString());
        }
      ),
      { numRuns: 100 }
    );
  });

  it('distinguishes between partial and full timeout failures', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 5, max: 10 }),
        (totalElements) => {
          // Create full failure (0 elements found)
          const fullFailure: StructureVerificationResult = {
            passed: false,
            missingElements: [],
            unexpectedElements: [],
            details: Array(totalElements).fill(null).map((_, i) => ({
              testId: `element-${i}`,
              found: false,
              visible: false,
              accessible: true,
            })),
            sectionResults: [],
            suggestedFixes: [],
            elementsFound: 0,
          };
          
          // Create partial failure (some elements found)
          const partialFailure: StructureVerificationResult = {
            passed: false,
            missingElements: [],
            unexpectedElements: [],
            details: Array(totalElements).fill(null).map((_, i) => ({
              testId: `element-${i}`,
              found: i < Math.floor(totalElements / 2),
              visible: i < Math.floor(totalElements / 2),
              accessible: true,
            })),
            sectionResults: [],
            suggestedFixes: [],
            elementsFound: Math.floor(totalElements / 2),
          };
          
          const fullClassification = classifyTimeoutFailure(fullFailure);
          const partialClassification = classifyTimeoutFailure(partialFailure);
          
          expect(fullClassification).toBe('full');
          expect(partialClassification).toBe('partial');
          expect(fullClassification).not.toBe(partialClassification);
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ============================================================================
// Edge Cases
// ============================================================================

describe('Edge Cases - Error Reporting', () => {
  it('handles empty missing elements list', () => {
    const result: StructureVerificationResult = {
      passed: true,
      missingElements: [],
      unexpectedElements: [],
      details: [],
      sectionResults: [],
      suggestedFixes: [],
      elementsFound: 0,
    };
    
    const errorMessage = formatVerificationError(result);
    expect(typeof errorMessage).toBe('string');
  });

  it('handles result with no suggested fixes', () => {
    const result: StructureVerificationResult = {
      passed: false,
      missingElements: ['element-1'],
      unexpectedElements: [],
      details: [{
        testId: 'element-1',
        found: false,
        visible: false,
        accessible: true,
      }],
      sectionResults: [],
      suggestedFixes: [],
      elementsFound: 0,
    };
    
    const errorMessage = formatVerificationError(result);
    expect(typeof errorMessage).toBe('string');
    expect(errorMessage).toContain('element-1');
  });

  it('classifies timeout with all elements found as partial', () => {
    const result: StructureVerificationResult = {
      passed: true,
      missingElements: [],
      unexpectedElements: [],
      details: [
        { testId: 'element-1', found: true, visible: true, accessible: true },
        { testId: 'element-2', found: true, visible: true, accessible: true },
      ],
      sectionResults: [],
      suggestedFixes: [],
      elementsFound: 2,
    };
    
    const classification = classifyTimeoutFailure(result);
    expect(classification).toBe('partial');
  });
});
