/**
 * Property-Based Tests for Structure Verification
 * Feature: ui-structure-tests
 * 
 * Property 2: Page Structure Verification Correctness
 * Property 3: Component Structure Verification Correctness
 * Property 6: All Missing Elements Reported
 * 
 * Validates: Requirements 2.1, 3.1, 3.3, 8.3
 */

import React from 'react';
import * as fc from 'fast-check';
import { render, cleanup } from '@testing-library/react';
import {
  verifyComponentStructure,
  verifyElementsExist,
  checkAccessibility,
} from '@/lib/testing/structure-test-utils';
import type {
  ElementDefinition,
  ComponentStructure,
} from '@/lib/testing/structure-manifest';

// Cleanup after each test to prevent DOM accumulation
afterEach(() => {
  cleanup();
});

// ============================================================================
// Arbitraries (Generators)
// ============================================================================

/**
 * Generates a valid ElementDefinition with controlled test IDs
 */
const elementDefinitionArb = fc.record({
  testId: fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
  required: fc.boolean(),
  description: fc.string({ minLength: 5, maxLength: 50 }),
  accessibility: fc.option(
    fc.record({
      role: fc.option(fc.constantFrom('button', 'link', 'heading', 'navigation'), { nil: undefined }),
      ariaLabel: fc.option(fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), { nil: undefined }),
      ariaDescribedBy: fc.option(fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), { nil: undefined }),
    }),
    { nil: undefined }
  ),
});

/**
 * Generates a ComponentStructure with unique test IDs and at least 3 required elements
 */
const componentStructureArb = fc.record({
  name: fc.string({ minLength: 1, maxLength: 30 }),
  testId: fc.integer({ min: 0, max: 100 }).map(n => `component-${n}`),
  requiredElements: fc.array(elementDefinitionArb, { minLength: 3, maxLength: 6 }).map(elements => {
    // Ensure unique test IDs and set required to true
    const seen = new Set<string>();
    return elements
      .map(el => ({ ...el, required: true })) // Force required to true
      .filter(el => {
        if (seen.has(el.testId)) return false;
        seen.add(el.testId);
        return true;
      });
  }).filter(arr => arr.length >= 3), // Ensure at least 3 elements remain
  optionalElements: fc.option(fc.array(elementDefinitionArb, { maxLength: 3 }), { nil: undefined }),
  states: fc.record({
    loading: fc.option(fc.array(elementDefinitionArb, { maxLength: 2 }), { nil: undefined }),
    error: fc.option(fc.array(elementDefinitionArb, { maxLength: 2 }), { nil: undefined }),
    empty: fc.option(fc.array(elementDefinitionArb, { maxLength: 2 }), { nil: undefined }),
  }),
  description: fc.option(fc.string({ minLength: 5, maxLength: 100 }), { nil: undefined }),
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

/**
 * Creates a test component with accessibility attributes
 */
function createAccessibleComponent(
  testId: string,
  accessibility?: {
    role?: string;
    ariaLabel?: string;
    ariaDescribedBy?: string;
  }
) {
  return function AccessibleComponent() {
    return (
      <div
        data-testid={testId}
        role={accessibility?.role}
        aria-label={accessibility?.ariaLabel}
        aria-describedby={accessibility?.ariaDescribedBy}
      >
        Content
      </div>
    );
  };
}

// ============================================================================
// Property 2: Page Structure Verification Correctness
// ============================================================================

describe('Property 2: Page Structure Verification Correctness', () => {
  it('correctly identifies missing elements from manifest', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
          { minLength: 3, maxLength: 10 }
        ),
        fc.array(
          fc.integer({ min: 0, max: 100 }).map(n => `missing-${n}`),
          { minLength: 1, maxLength: 5 }
        ),
        (allTestIds, missingTestIds) => {
          // Ensure test IDs are unique
          const uniqueAllIds = [...new Set(allTestIds)];
          const uniqueMissingIds = [...new Set(missingTestIds)];
          
          // Present IDs are all IDs minus missing IDs
          const presentIds = uniqueAllIds.filter(id => !uniqueMissingIds.includes(id));
          
          // Skip if no present IDs or no unique IDs
          if (presentIds.length === 0 || uniqueAllIds.length === 0) return;
          
          // Create component with only present IDs
          const TestComponent = createTestComponent(presentIds);
          const result = render(<TestComponent />);
          
          // Verify elements
          const verification = verifyElementsExist(result, uniqueAllIds);
          
          // All missing IDs should be reported as missing
          uniqueMissingIds.forEach(missingId => {
            if (uniqueAllIds.includes(missingId)) {
              expect(verification.missingElements).toContain(missingId);
            }
          });
          
          // All present IDs should be reported as found
          presentIds.forEach(presentId => {
            expect(verification.foundElements).toContain(presentId);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('does not report false positives for present elements', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
          { minLength: 1, maxLength: 10 }
        ),
        (testIds) => {
          // Ensure test IDs are unique
          const uniqueIds = [...new Set(testIds)];
          
          // Create component with all IDs
          const TestComponent = createTestComponent(uniqueIds);
          const result = render(<TestComponent />);
          
          // Verify elements
          const verification = verifyElementsExist(result, uniqueIds);
          
          // Should have no missing elements
          expect(verification.missingElements).toEqual([]);
          expect(verification.passed).toBe(true);
          
          // All IDs should be found
          expect(verification.foundElements.sort()).toEqual(uniqueIds.sort());
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ============================================================================
// Property 3: Component Structure Verification Correctness
// ============================================================================

describe('Property 3: Component Structure Verification Correctness', () => {
  it('correctly identifies all required elements are present', () => {
    fc.assert(
      fc.property(
        componentStructureArb,
        (structure) => {
          // Get all required element test IDs
          const requiredTestIds = structure.requiredElements.map(e => e.testId);
          
          // Create component with all required elements
          const TestComponent = createTestComponent(requiredTestIds);
          const result = render(<TestComponent />);
          
          // Verify component structure
          const verification = verifyComponentStructure(result, structure);
          
          // Should pass with no missing elements
          expect(verification.passed).toBe(true);
          expect(verification.missingElements).toEqual([]);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('reports exact set of missing required elements', () => {
    fc.assert(
      fc.property(
        componentStructureArb,
        fc.integer({ min: 1, max: 3 }),
        (structure, numToRemove) => {
          // Clean up before each iteration
          cleanup();
          
          // Skip if not enough required elements
          if (structure.requiredElements.length <= numToRemove) return;
          
          // Get all required element test IDs
          const requiredTestIds = structure.requiredElements.map(e => e.testId);
          
          // Remove some elements to simulate missing
          const presentIds = requiredTestIds.slice(0, -numToRemove);
          const expectedMissingIds = requiredTestIds.slice(-numToRemove);
          
          // Skip if no present IDs (edge case)
          if (presentIds.length === 0) return;
          
          // Create component with only some elements
          const TestComponent = createTestComponent(presentIds);
          const result = render(<TestComponent />);
          
          // Verify component structure
          const verification = verifyComponentStructure(result, structure);
          
          // Should fail
          expect(verification.passed).toBe(false);
          
          // Should report exactly the missing elements
          expect(verification.missingElements.sort()).toEqual(expectedMissingIds.sort());
        }
      ),
      { numRuns: 100 }
    );
  });

  it('verifies state-specific elements when state is provided', () => {
    fc.assert(
      fc.property(
        componentStructureArb,
        fc.constantFrom('loading', 'error', 'empty'),
        (structure, state) => {
          // Get state-specific elements
          const stateElements = structure.states[state];
          
          // Skip if no elements defined for this state
          if (!stateElements || stateElements.length === 0) return;
          
          const stateTestIds = stateElements.map(e => e.testId);
          
          // Create component with state elements
          const TestComponent = createTestComponent(stateTestIds);
          const result = render(<TestComponent />);
          
          // Verify component structure with state
          const verification = verifyComponentStructure(result, structure, state);
          
          // Should pass with no missing elements
          expect(verification.passed).toBe(true);
          expect(verification.missingElements).toEqual([]);
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ============================================================================
// Property 6: All Missing Elements Reported
// ============================================================================

describe('Property 6: All Missing Elements Reported', () => {
  it('reports all missing elements, not just the first one', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 3, maxLength: 10 }),
        (testIds) => {
          // Ensure test IDs are unique and valid
          const uniqueIds = [...new Set(testIds.map(id => 
            id.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '') || 'id'
          ))];
          
          // Skip if not enough IDs
          if (uniqueIds.length < 3) return;
          
          // Create component with NO elements
          const EmptyComponent = () => <div>Empty</div>;
          const result = render(<EmptyComponent />);
          
          // Verify elements - all should be missing
          const verification = verifyElementsExist(result, uniqueIds);
          
          // Should report ALL missing elements
          expect(verification.missingElements.length).toBe(uniqueIds.length);
          expect(verification.missingElements.sort()).toEqual(uniqueIds.sort());
          expect(verification.passed).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('reports all missing elements in component verification', () => {
    fc.assert(
      fc.property(
        componentStructureArb,
        (structure) => {
          // Skip if no required elements
          if (structure.requiredElements.length === 0) return;
          
          // Create component with NO elements
          const EmptyComponent = () => <div>Empty</div>;
          const result = render(<EmptyComponent />);
          
          // Verify component structure
          const verification = verifyComponentStructure(result, structure);
          
          // Should report ALL missing required elements
          const expectedMissing = structure.requiredElements.map(e => e.testId);
          expect(verification.missingElements.length).toBe(expectedMissing.length);
          expect(verification.missingElements.sort()).toEqual(expectedMissing.sort());
          expect(verification.passed).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('reports partial missing elements correctly', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
          { minLength: 4, maxLength: 10 }
        ),
        (testIds) => {
          // Clean up before each iteration
          cleanup();
          
          // Ensure test IDs are unique
          const uniqueIds = [...new Set(testIds)];
          
          // Skip if not enough unique IDs
          if (uniqueIds.length < 4) return;
          
          // Split into present and missing
          const midpoint = Math.floor(uniqueIds.length / 2);
          const presentIds = uniqueIds.slice(0, midpoint);
          const missingIds = uniqueIds.slice(midpoint);
          
          // Skip if either half is empty
          if (presentIds.length === 0 || missingIds.length === 0) return;
          
          // Create component with only half the elements
          const TestComponent = createTestComponent(presentIds);
          const result = render(<TestComponent />);
          
          // Verify elements
          const verification = verifyElementsExist(result, uniqueIds);
          
          // Should report exactly the missing half
          expect(verification.missingElements.sort()).toEqual(missingIds.sort());
          expect(verification.foundElements.sort()).toEqual(presentIds.sort());
          expect(verification.passed).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ============================================================================
// Accessibility Verification Property Tests
// ============================================================================

describe('Accessibility Verification Properties', () => {
  it('correctly identifies missing accessibility attributes', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
        fc.constantFrom('button', 'link', 'heading'),
        (testId, role) => {
          // Create component WITHOUT accessibility attributes
          const ComponentWithoutA11y = () => (
            <div data-testid={testId}>Content</div>
          );
          const result = render(<ComponentWithoutA11y />);
          
          // Check accessibility
          const check = checkAccessibility(result, testId, { role });
          
          // Should fail and report missing role
          expect(check.passed).toBe(false);
          expect(check.issues.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('passes when all accessibility attributes are present', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
        fc.constantFrom('button', 'link', 'heading'),
        fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), // Non-empty, non-whitespace
        (testId, role, ariaLabel) => {
          // Clean up before each iteration
          cleanup();
          
          // Create component WITH accessibility attributes
          const AccessibleComponent = createAccessibleComponent(testId, { role, ariaLabel });
          const result = render(<AccessibleComponent />);
          
          // Check accessibility
          const check = checkAccessibility(result, testId, { role, ariaLabel });
          
          // Should pass
          expect(check.passed).toBe(true);
          expect(check.issues).toEqual([]);
        }
      ),
      { numRuns: 100 }
    );
  });
});

// ============================================================================
// Edge Cases
// ============================================================================

describe('Edge Cases - Structure Verification', () => {
  it('handles empty element lists', () => {
    const result = render(<div>Empty</div>);
    const verification = verifyElementsExist(result, []);
    
    expect(verification.passed).toBe(true);
    expect(verification.missingElements).toEqual([]);
    expect(verification.foundElements).toEqual([]);
  });

  it('handles duplicate test IDs in verification list', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`),
        (testId) => {
          const TestComponent = createTestComponent([testId]);
          const result = render(<TestComponent />);
          
          // Verify with duplicate IDs
          const verification = verifyElementsExist(result, [testId, testId, testId]);
          
          // Should still work correctly
          expect(verification.passed).toBe(true);
          expect(verification.foundElements).toContain(testId);
        }
      ),
      { numRuns: 50 }
    );
  });

  it('handles components with no required elements', () => {
    const structure: ComponentStructure = {
      name: 'EmptyComponent',
      testId: 'empty',
      requiredElements: [],
      states: {},
    };
    
    const result = render(<div>Empty</div>);
    const verification = verifyComponentStructure(result, structure);
    
    expect(verification.passed).toBe(true);
    expect(verification.missingElements).toEqual([]);
  });
});
