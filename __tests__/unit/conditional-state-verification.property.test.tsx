/**
 * Property 4: Conditional State Verification
 * 
 * For any component with defined states (loading, error, empty), when the component
 * is in a specific state, the verification function SHALL check for exactly the
 * elements defined for that state in the manifest.
 * 
 * Feature: ui-structure-tests, Property 4: Conditional State Verification
 * Validates: Requirements 3.4
 */

import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import * as fc from 'fast-check';
import { verifyComponentStructure } from '@/lib/testing/structure-test-utils';
import type { ComponentStructure, ElementDefinition } from '@/lib/testing/structure-manifest';

// Helper to create a test component that renders specific test IDs
function createTestComponent(testIds: string[]) {
  return function TestComponent() {
    return (
      <div data-testid="test-component">
        {testIds.map((testId) => (
          <div key={testId} data-testid={testId}>
            {testId}
          </div>
        ))}
      </div>
    );
  };
}

// Arbitrary for generating element definitions
const elementDefinitionArb = fc.record({
  testId: fc.string({ minLength: 1, maxLength: 20 }).map(s => s.replace(/[^a-z0-9-]/gi, '-').toLowerCase()),
  required: fc.boolean(),
  description: fc.string({ minLength: 5, maxLength: 50 }),
});

// Arbitrary for generating component structures with states
const componentStructureWithStatesArb = fc.record({
  name: fc.string({ minLength: 3, maxLength: 20 }),
  testId: fc.string({ minLength: 3, maxLength: 20 }).map(s => s.replace(/[^a-z0-9-]/gi, '-').toLowerCase()),
  requiredElements: fc.array(elementDefinitionArb, { minLength: 1, maxLength: 5 }),
  states: fc.record({
    loading: fc.array(elementDefinitionArb, { minLength: 1, maxLength: 3 }),
    error: fc.array(elementDefinitionArb, { minLength: 1, maxLength: 3 }),
    empty: fc.array(elementDefinitionArb, { minLength: 1, maxLength: 3 }),
  }),
});

describe('Property 4: Conditional State Verification', () => {
  describe('State-Specific Element Verification', () => {
    it('verifies exactly the elements defined for loading state', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          // Create component that renders loading state elements
          const loadingTestIds = structure.states.loading?.map(e => e.testId) || [];
          const TestComponent = createTestComponent(loadingTestIds);
          
          const result = render(<TestComponent />);
          const verification = verifyComponentStructure(result, structure, 'loading');
          
          // Should check for loading elements, not required elements
          const loadingElements = structure.states.loading || [];
          const requiredLoadingIds = loadingElements
            .filter(e => e.required)
            .map(e => e.testId);
          
          // All required loading elements should be found
          const missingRequired = requiredLoadingIds.filter(
            id => !loadingTestIds.includes(id)
          );
          
          // Verification should pass if all required loading elements are present
          if (missingRequired.length === 0) {
            expect(verification.passed).toBe(true);
          } else {
            expect(verification.passed).toBe(false);
            expect(verification.missingElements).toEqual(expect.arrayContaining(missingRequired));
          }
        }),
        { numRuns: 50 }
      );
    });

    it('verifies exactly the elements defined for error state', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          // Create component that renders error state elements
          const errorTestIds = structure.states.error?.map(e => e.testId) || [];
          const TestComponent = createTestComponent(errorTestIds);
          
          const result = render(<TestComponent />);
          const verification = verifyComponentStructure(result, structure, 'error');
          
          // Should check for error elements, not required elements
          const errorElements = structure.states.error || [];
          const requiredErrorIds = errorElements
            .filter(e => e.required)
            .map(e => e.testId);
          
          // All required error elements should be found
          const missingRequired = requiredErrorIds.filter(
            id => !errorTestIds.includes(id)
          );
          
          // Verification should pass if all required error elements are present
          if (missingRequired.length === 0) {
            expect(verification.passed).toBe(true);
          } else {
            expect(verification.passed).toBe(false);
            expect(verification.missingElements).toEqual(expect.arrayContaining(missingRequired));
          }
        }),
        { numRuns: 50 }
      );
    });

    it('verifies exactly the elements defined for empty state', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          // Create component that renders empty state elements
          const emptyTestIds = structure.states.empty?.map(e => e.testId) || [];
          const TestComponent = createTestComponent(emptyTestIds);
          
          const result = render(<TestComponent />);
          const verification = verifyComponentStructure(result, structure, 'empty');
          
          // Should check for empty elements, not required elements
          const emptyElements = structure.states.empty || [];
          const requiredEmptyIds = emptyElements
            .filter(e => e.required)
            .map(e => e.testId);
          
          // All required empty elements should be found
          const missingRequired = requiredEmptyIds.filter(
            id => !emptyTestIds.includes(id)
          );
          
          // Verification should pass if all required empty elements are present
          if (missingRequired.length === 0) {
            expect(verification.passed).toBe(true);
          } else {
            expect(verification.passed).toBe(false);
            expect(verification.missingElements).toEqual(expect.arrayContaining(missingRequired));
          }
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('State Isolation', () => {
    it('does not check required elements when verifying a specific state', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          // Create component that renders ONLY loading state elements (not required elements)
          const loadingTestIds = structure.states.loading?.map(e => e.testId) || [];
          const TestComponent = createTestComponent(loadingTestIds);
          
          const result = render(<TestComponent />);
          const verification = verifyComponentStructure(result, structure, 'loading');
          
          // Required elements should NOT be checked when verifying loading state
          const requiredIds = structure.requiredElements.map(e => e.testId);
          const missingRequiredInReport = verification.missingElements.filter(
            id => requiredIds.includes(id)
          );
          
          // No required elements should be in the missing list when checking loading state
          expect(missingRequiredInReport).toEqual([]);
        }),
        { numRuns: 50 }
      );
    });

    it('checks required elements when no state is specified', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          // Create component that renders required elements
          const requiredTestIds = structure.requiredElements.map(e => e.testId);
          const TestComponent = createTestComponent(requiredTestIds);
          
          const result = render(<TestComponent />);
          // No state specified - should check required elements
          const verification = verifyComponentStructure(result, structure);
          
          // All required elements are present, so verification should pass
          expect(verification.passed).toBe(true);
          expect(verification.missingElements).toEqual([]);
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Missing State Elements Detection', () => {
    it('detects when state-specific elements are missing', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          // Ensure we have at least one required loading element
          if (!structure.states.loading || structure.states.loading.length === 0) {
            return true; // Skip this case
          }
          
          // Create component that renders NO elements
          const TestComponent = createTestComponent([]);
          
          const result = render(<TestComponent />);
          const verification = verifyComponentStructure(result, structure, 'loading');
          
          // Get required loading elements
          const requiredLoadingIds = structure.states.loading
            .filter(e => e.required)
            .map(e => e.testId);
          
          if (requiredLoadingIds.length > 0) {
            // Should fail because required loading elements are missing
            expect(verification.passed).toBe(false);
            expect(verification.missingElements.length).toBeGreaterThan(0);
            
            // All required loading elements should be in missing list
            requiredLoadingIds.forEach(id => {
              expect(verification.missingElements).toContain(id);
            });
          }
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Element Detail Reporting', () => {
    it('reports details for all checked elements in the specified state', () => {
      fc.assert(
        fc.property(componentStructureWithStatesArb, (structure) => {
          const loadingTestIds = structure.states.loading?.map(e => e.testId) || [];
          const TestComponent = createTestComponent(loadingTestIds);
          
          const result = render(<TestComponent />);
          const verification = verifyComponentStructure(result, structure, 'loading');
          
          // Should have details for all loading elements
          const loadingElementCount = structure.states.loading?.length || 0;
          expect(verification.elementDetails.length).toBe(loadingElementCount);
          
          // Each loading element should have a detail entry
          structure.states.loading?.forEach(element => {
            const detail = verification.elementDetails.find(d => d.testId === element.testId);
            expect(detail).toBeDefined();
            expect(detail?.testId).toBe(element.testId);
          });
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Real-World Example: VarianceKPIs Component', () => {
    it('correctly verifies VarianceKPIs loading state', () => {
      const varianceKpisStructure: ComponentStructure = {
        name: 'VarianceKPIs',
        testId: 'variance-kpis',
        requiredElements: [
          { testId: 'variance-kpis-header', required: true, description: 'Header' },
          { testId: 'variance-kpis-grid', required: true, description: 'Grid' },
        ],
        states: {
          loading: [
            { testId: 'variance-kpis-skeleton', required: true, description: 'Loading skeleton' },
          ],
          error: [
            { testId: 'variance-kpis-error', required: true, description: 'Error message' },
          ],
        },
      };

      // Component in loading state - only skeleton present
      const LoadingComponent = createTestComponent(['variance-kpis-skeleton']);
      const loadingResult = render(<LoadingComponent />);
      const loadingVerification = verifyComponentStructure(
        loadingResult,
        varianceKpisStructure,
        'loading'
      );

      // Should pass - skeleton is present
      expect(loadingVerification.passed).toBe(true);
      expect(loadingVerification.missingElements).toEqual([]);

      // Component in error state - only error message present
      const ErrorComponent = createTestComponent(['variance-kpis-error']);
      const errorResult = render(<ErrorComponent />);
      const errorVerification = verifyComponentStructure(
        errorResult,
        varianceKpisStructure,
        'error'
      );

      // Should pass - error message is present
      expect(errorVerification.passed).toBe(true);
      expect(errorVerification.missingElements).toEqual([]);

      // Component in normal state - required elements present
      const NormalComponent = createTestComponent([
        'variance-kpis-header',
        'variance-kpis-grid',
      ]);
      const normalResult = render(<NormalComponent />);
      const normalVerification = verifyComponentStructure(
        normalResult,
        varianceKpisStructure
      );

      // Should pass - required elements are present
      expect(normalVerification.passed).toBe(true);
      expect(normalVerification.missingElements).toEqual([]);
    });
  });
});
