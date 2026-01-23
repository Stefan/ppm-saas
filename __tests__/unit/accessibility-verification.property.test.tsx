/**
 * Property-Based Tests for Accessibility Verification
 * Feature: ui-structure-tests
 * 
 * Property 12: Accessibility Verification
 * 
 * Validates: Requirements 2.4, 7.2
 */

import React from 'react';
import * as fc from 'fast-check';
import { render, cleanup } from '@testing-library/react';
import {
  checkAccessibility,
  verifyInteractiveAccessibility,
  verifyComponentStructure,
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
 * Generates valid accessibility requirements
 */
const accessibilityRequirementsArb = fc.record({
  role: fc.option(fc.constantFrom('button', 'link', 'heading', 'navigation', 'tab', 'menuitem'), { nil: undefined }),
  ariaLabel: fc.option(fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), { nil: undefined }),
  ariaDescribedBy: fc.option(fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), { nil: undefined }),
  ariaLabelledBy: fc.option(fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), { nil: undefined }),
  tabIndex: fc.option(fc.integer({ min: -1, max: 10 }), { nil: undefined }),
});

/**
 * Generates a subset of accessibility requirements (for partial matching tests)
 */
const partialAccessibilityArb = fc.record({
  role: fc.option(fc.constantFrom('button', 'link', 'heading'), { nil: undefined }),
  ariaLabel: fc.option(fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1), { nil: undefined }),
});

/**
 * Generates interactive element tag names
 */
const interactiveTagArb = fc.constantFrom('button', 'a', 'input', 'select', 'textarea');

/**
 * Generates test IDs
 */
const testIdArb = fc.integer({ min: 0, max: 100 }).map(n => `element-${n}`);

// ============================================================================
// Test Components
// ============================================================================

/**
 * Creates a component with specified accessibility attributes
 */
function createAccessibleComponent(
  testId: string,
  accessibility?: {
    role?: string;
    ariaLabel?: string;
    ariaDescribedBy?: string;
    ariaLabelledBy?: string;
    tabIndex?: number;
  }
) {
  return function AccessibleComponent() {
    return (
      <div
        data-testid={testId}
        role={accessibility?.role}
        aria-label={accessibility?.ariaLabel}
        aria-describedby={accessibility?.ariaDescribedBy}
        aria-labelledby={accessibility?.ariaLabelledBy}
        tabIndex={accessibility?.tabIndex}
      >
        Content
      </div>
    );
  };
}

/**
 * Creates an interactive element with accessibility attributes
 */
function createInteractiveElement(
  testId: string,
  tagName: string,
  hasAccessibility: boolean
) {
  return function InteractiveElement() {
    const props: any = {
      'data-testid': testId,
    };
    
    if (hasAccessibility) {
      if (tagName === 'button' || tagName === 'a') {
        props['aria-label'] = 'Accessible label';
      } else if (tagName === 'input' || tagName === 'select' || tagName === 'textarea') {
        props['aria-label'] = 'Input label';
      }
    }
    
    // Void elements (input, select, textarea) should not have children
    if (tagName === 'input') {
      props.type = 'text';
      return React.createElement(tagName, props);
    } else if (tagName === 'select') {
      return React.createElement(tagName, props, React.createElement('option', {}, 'Option'));
    } else if (tagName === 'textarea') {
      props.defaultValue = 'Content';
      return React.createElement(tagName, props);
    }
    
    return React.createElement(tagName, props, 'Content');
  };
}

// ============================================================================
// Property 12: Accessibility Verification
// ============================================================================

describe('Property 12: Accessibility Verification', () => {
  describe('Interactive elements have accessibility attributes', () => {
    it('detects missing accessibility attributes on form inputs', () => {
      fc.assert(
        fc.property(
          testIdArb,
          (testId) => {
            // Create form input WITHOUT accessibility attributes or label
            const Component = () => <input data-testid={testId} type="text" />;
            const result = render(<Component />);
            
            // Verify interactive accessibility
            const verification = verifyInteractiveAccessibility(result, [testId]);
            
            // Should fail and report violations for inputs without labels
            expect(verification.passed).toBe(false);
            expect(verification.violations.length).toBeGreaterThan(0);
            expect(verification.violations[0].testId).toBe(testId);
            expect(verification.violations[0].issues.length).toBeGreaterThan(0);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('passes when interactive elements have accessibility attributes', () => {
      fc.assert(
        fc.property(
          testIdArb,
          interactiveTagArb,
          (testId, tagName) => {
            // Clean up before each iteration
            cleanup();
            
            // Create interactive element WITH accessibility attributes
            const Component = createInteractiveElement(testId, tagName, true);
            const result = render(<Component />);
            
            // Verify interactive accessibility
            const verification = verifyInteractiveAccessibility(result, [testId]);
            
            // Should pass with no violations
            expect(verification.passed).toBe(true);
            expect(verification.violations).toEqual([]);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('reports violations for all interactive elements without accessibility', () => {
      fc.assert(
        fc.property(
          fc.array(testIdArb, { minLength: 2, maxLength: 5 }),
          (testIds) => {
            // Clean up before each iteration
            cleanup();
            
            // Ensure unique test IDs
            const uniqueIds = [...new Set(testIds)];
            if (uniqueIds.length < 2) return;
            
            // Create multiple form inputs WITHOUT accessibility
            const Component = () => (
              <div>
                {uniqueIds.map(id => (
                  <input key={id} data-testid={id} type="text" />
                ))}
              </div>
            );
            const result = render(<Component />);
            
            // Verify interactive accessibility
            const verification = verifyInteractiveAccessibility(result, uniqueIds);
            
            // Should report violations for ALL elements
            expect(verification.passed).toBe(false);
            expect(verification.violations.length).toBe(uniqueIds.length);
            
            // Each violation should have the correct test ID
            const violationIds = verification.violations.map(v => v.testId).sort();
            expect(violationIds).toEqual(uniqueIds.sort());
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Accessibility attribute checking', () => {
    it('correctly identifies when all required attributes are present', () => {
      fc.assert(
        fc.property(
          testIdArb,
          accessibilityRequirementsArb,
          (testId, requirements) => {
            // Clean up before each iteration
            cleanup();
            
            // Skip if no requirements specified
            if (!requirements.role && !requirements.ariaLabel && 
                !requirements.ariaDescribedBy && !requirements.ariaLabelledBy && 
                requirements.tabIndex === undefined) {
              return;
            }
            
            // Create component WITH all required attributes
            const Component = createAccessibleComponent(testId, requirements);
            const result = render(<Component />);
            
            // Check accessibility
            const check = checkAccessibility(result, testId, requirements);
            
            // Should pass with no issues
            expect(check.passed).toBe(true);
            expect(check.issues).toEqual([]);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('correctly identifies missing role attribute', () => {
      fc.assert(
        fc.property(
          testIdArb,
          fc.constantFrom('button', 'link', 'heading', 'navigation'),
          (testId, expectedRole) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component WITHOUT role attribute
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Check accessibility with role requirement
            const check = checkAccessibility(result, testId, { role: expectedRole });
            
            // Should fail and report missing role
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThan(0);
            expect(check.issues.some(issue => issue.includes('role'))).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('correctly identifies missing aria-label attribute', () => {
      fc.assert(
        fc.property(
          testIdArb,
          (testId) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component WITHOUT aria-label
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Check accessibility with aria-label requirement
            const check = checkAccessibility(result, testId, { ariaLabel: 'required' });
            
            // Should fail and report missing aria-label
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThan(0);
            expect(check.issues.some(issue => issue.includes('aria-label'))).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('correctly identifies missing aria-describedby attribute', () => {
      fc.assert(
        fc.property(
          testIdArb,
          (testId) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component WITHOUT aria-describedby
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Check accessibility with aria-describedby requirement
            const check = checkAccessibility(result, testId, { ariaDescribedBy: 'required' });
            
            // Should fail and report missing aria-describedby
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThan(0);
            expect(check.issues.some(issue => issue.includes('aria-describedby'))).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('correctly identifies missing aria-labelledby attribute', () => {
      fc.assert(
        fc.property(
          testIdArb,
          (testId) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component WITHOUT aria-labelledby
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Check accessibility with aria-labelledby requirement
            const check = checkAccessibility(result, testId, { ariaLabelledBy: 'required' });
            
            // Should fail and report missing aria-labelledby
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThan(0);
            expect(check.issues.some(issue => issue.includes('aria-labelledby'))).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('correctly identifies incorrect tabindex value', () => {
      fc.assert(
        fc.property(
          testIdArb,
          fc.integer({ min: -1, max: 10 }),
          fc.integer({ min: -1, max: 10 }),
          (testId, actualTabIndex, expectedTabIndex) => {
            // Clean up before each iteration
            cleanup();
            
            // Skip if values are the same
            if (actualTabIndex === expectedTabIndex) return;
            
            // Create component WITH wrong tabindex
            const Component = createAccessibleComponent(testId, { tabIndex: actualTabIndex });
            const result = render(<Component />);
            
            // Check accessibility with different tabindex requirement
            const check = checkAccessibility(result, testId, { tabIndex: expectedTabIndex });
            
            // Should fail and report incorrect tabindex
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThan(0);
            expect(check.issues.some(issue => issue.includes('tabindex'))).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('reports all missing attributes when multiple are required', () => {
      fc.assert(
        fc.property(
          testIdArb,
          fc.constantFrom('button', 'link', 'heading'),
          (testId, role) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component WITHOUT any accessibility attributes
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Check accessibility with multiple requirements
            const check = checkAccessibility(result, testId, {
              role,
              ariaLabel: 'required',
              ariaDescribedBy: 'required',
            });
            
            // Should fail and report ALL missing attributes
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThanOrEqual(3);
            expect(check.issues.some(issue => issue.includes('role'))).toBe(true);
            expect(check.issues.some(issue => issue.includes('aria-label'))).toBe(true);
            expect(check.issues.some(issue => issue.includes('aria-describedby'))).toBe(true);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Component structure accessibility verification', () => {
    it('verifies accessibility requirements in component structure', () => {
      fc.assert(
        fc.property(
          testIdArb,
          fc.constantFrom('button', 'link', 'heading'),
          fc.string({ minLength: 2, maxLength: 30 }).filter(s => s.trim().length > 1),
          (testId, role, ariaLabel) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component structure with accessibility requirements
            const structure: ComponentStructure = {
              name: 'TestComponent',
              testId: 'test-component',
              requiredElements: [
                {
                  testId,
                  required: true,
                  description: 'Test element',
                  accessibility: {
                    role,
                    ariaLabel,
                  },
                },
              ],
              states: {},
            };
            
            // Create component WITH accessibility attributes
            const Component = createAccessibleComponent(testId, { role, ariaLabel });
            const result = render(<Component />);
            
            // Verify component structure
            const verification = verifyComponentStructure(result, structure);
            
            // Should pass - element exists and has correct accessibility
            expect(verification.passed).toBe(true);
            expect(verification.missingElements).toEqual([]);
            
            // Check element details for accessibility
            const elementDetail = verification.elementDetails.find(d => d.testId === testId);
            expect(elementDetail).toBeDefined();
            expect(elementDetail?.accessible).toBe(true);
            expect(elementDetail?.accessibilityIssues).toBeUndefined();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('reports accessibility violations in component structure verification', () => {
      fc.assert(
        fc.property(
          testIdArb,
          fc.constantFrom('button', 'link', 'heading'),
          (testId, role) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component structure with accessibility requirements
            const structure: ComponentStructure = {
              name: 'TestComponent',
              testId: 'test-component',
              requiredElements: [
                {
                  testId,
                  required: true,
                  description: 'Test element',
                  accessibility: {
                    role,
                    ariaLabel: 'required',
                  },
                },
              ],
              states: {},
            };
            
            // Create component WITHOUT accessibility attributes
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Verify component structure
            const verification = verifyComponentStructure(result, structure);
            
            // Element exists but has accessibility issues
            expect(verification.passed).toBe(true); // Still passes because element exists
            
            // Check element details for accessibility violations
            const elementDetail = verification.elementDetails.find(d => d.testId === testId);
            expect(elementDetail).toBeDefined();
            expect(elementDetail?.found).toBe(true);
            expect(elementDetail?.accessible).toBe(false);
            expect(elementDetail?.accessibilityIssues).toBeDefined();
            expect(elementDetail?.accessibilityIssues!.length).toBeGreaterThan(0);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  describe('Edge cases', () => {
    it('handles element not found gracefully', () => {
      fc.assert(
        fc.property(
          testIdArb,
          (testId) => {
            // Clean up before each iteration
            cleanup();
            
            // Create empty component
            const Component = () => <div>Empty</div>;
            const result = render(<Component />);
            
            // Check accessibility for non-existent element
            const check = checkAccessibility(result, testId, { role: 'button' });
            
            // Should fail and report element not found
            expect(check.passed).toBe(false);
            expect(check.issues.length).toBeGreaterThan(0);
            expect(check.issues[0]).toContain('not found');
          }
        ),
        { numRuns: 50 }
      );
    });

    it('handles no accessibility requirements gracefully', () => {
      fc.assert(
        fc.property(
          testIdArb,
          (testId) => {
            // Clean up before each iteration
            cleanup();
            
            // Create component
            const Component = createAccessibleComponent(testId, {});
            const result = render(<Component />);
            
            // Check accessibility with no requirements
            const check = checkAccessibility(result, testId, {});
            
            // Should pass (no requirements to check)
            expect(check.passed).toBe(true);
            expect(check.issues).toEqual([]);
          }
        ),
        { numRuns: 50 }
      );
    });

    it('handles empty interactive elements list', () => {
      const Component = () => <div>Empty</div>;
      const result = render(<Component />);
      
      // Verify with empty list
      const verification = verifyInteractiveAccessibility(result, []);
      
      // Should pass (no elements to check)
      expect(verification.passed).toBe(true);
      expect(verification.violations).toEqual([]);
    });
  });
});
