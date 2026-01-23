/**
 * Structure Test Utilities
 * 
 * Provides reusable helpers for verifying page and component structure
 * in both E2E (Playwright) and unit (Jest/RTL) tests.
 */

import type { Page, Locator } from '@playwright/test';
import type { RenderResult } from '@testing-library/react';
import type {
  PageStructure,
  SectionDefinition,
  ElementDefinition,
  ComponentStructure,
} from './structure-manifest';

// ============================================================================
// Result Types
// ============================================================================

/**
 * Details about a single element verification
 */
export interface ElementDetail {
  /** Test ID of the element */
  testId: string;
  
  /** Whether the element was found in the DOM */
  found: boolean;
  
  /** Whether the element is visible (not hidden) */
  visible: boolean;
  
  /** Whether the element meets accessibility requirements */
  accessible: boolean;
  
  /** Accessibility issues found */
  accessibilityIssues?: string[];
  
  /** Expected accessibility attributes */
  expectedAccessibility?: {
    role?: string;
    ariaLabel?: string;
    ariaDescribedBy?: string;
    ariaLabelledBy?: string;
    tabIndex?: number;
  };
}

/**
 * Result of verifying a section
 */
export interface SectionVerificationResult {
  /** Section name */
  sectionName: string;
  
  /** Section test ID */
  sectionTestId: string;
  
  /** Whether the section passed verification */
  passed: boolean;
  
  /** Test IDs of missing required elements */
  missingElements: string[];
  
  /** Details for all elements checked */
  elementDetails: ElementDetail[];
  
  /** Suggested fixes for failures */
  suggestedFixes: string[];
}

/**
 * Result of verifying a page structure
 */
export interface StructureVerificationResult {
  /** Whether the page passed verification */
  passed: boolean;
  
  /** Test IDs of all missing required elements */
  missingElements: string[];
  
  /** Test IDs of unexpected elements found */
  unexpectedElements: string[];
  
  /** Details for all elements checked */
  details: ElementDetail[];
  
  /** Results for each section */
  sectionResults: SectionVerificationResult[];
  
  /** Suggested fixes for failures */
  suggestedFixes: string[];
  
  /** Whether this was a timeout failure */
  timeoutFailure?: boolean;
  
  /** Classification of timeout (partial/full) */
  timeoutClassification?: 'partial' | 'full';
  
  /** Number of elements found (for timeout classification) */
  elementsFound?: number;
}

/**
 * Result of verifying a component structure
 */
export interface ComponentVerificationResult {
  /** Component name */
  componentName: string;
  
  /** Whether the component passed verification */
  passed: boolean;
  
  /** Test IDs of missing required elements */
  missingElements: string[];
  
  /** Details for all elements checked */
  elementDetails: ElementDetail[];
  
  /** Suggested fixes for failures */
  suggestedFixes: string[];
}

/**
 * Result of verifying element existence
 */
export interface ElementVerificationResult {
  /** Whether all elements exist */
  passed: boolean;
  
  /** Test IDs of missing elements */
  missingElements: string[];
  
  /** Test IDs of found elements */
  foundElements: string[];
}

// ============================================================================
// E2E Utilities (Playwright)
// ============================================================================

/**
 * Waits for dynamic content to load before structure verification
 * 
 * @param page - Playwright page object
 * @param options - Configuration options
 */
export async function waitForDynamicContent(
  page: Page,
  options?: {
    /** Maximum time to wait in milliseconds */
    timeout?: number;
    
    /** Specific selector to wait for */
    selector?: string;
    
    /** Wait for network to be idle */
    waitForNetwork?: boolean;
  }
): Promise<void> {
  const timeout = options?.timeout ?? 30000;
  
  try {
    // Wait for network idle if requested
    if (options?.waitForNetwork) {
      await page.waitForLoadState('networkidle', { timeout });
    }
    
    // Wait for specific selector if provided
    if (options?.selector) {
      await page.waitForSelector(options.selector, { 
        timeout,
        state: 'visible'
      });
    }
    
    // Always wait for DOM content to be loaded
    await page.waitForLoadState('domcontentloaded', { timeout });
    
    // Small additional delay for React hydration
    await page.waitForTimeout(100);
  } catch (error) {
    // Log but don't throw - let verification handle missing elements
    console.warn('waitForDynamicContent timeout:', error);
  }
}

/**
 * Captures a screenshot for structure verification failures
 * 
 * @param page - Playwright page object
 * @param name - Name for the screenshot file
 */
export async function captureStructureSnapshot(
  page: Page,
  name: string
): Promise<void> {
  try {
    const sanitizedName = name.replace(/[^a-z0-9-]/gi, '-').toLowerCase();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `structure-failure-${sanitizedName}-${timestamp}.png`;
    
    await page.screenshot({
      path: `test-results/structure-failures/${filename}`,
      fullPage: true,
    });
    
    console.log(`Screenshot saved: ${filename}`);
  } catch (error) {
    console.error('Failed to capture screenshot:', error);
  }
}

/**
 * Verifies a single element in E2E tests
 */
async function verifyElement(
  page: Page,
  element: ElementDefinition
): Promise<ElementDetail> {
  const locator = page.getByTestId(element.testId);
  const count = await locator.count();
  const found = count > 0;
  
  let visible = false;
  let accessible = true;
  const accessibilityIssues: string[] = [];
  
  if (found) {
    try {
      visible = await locator.first().isVisible();
    } catch {
      visible = false;
    }
    
    // Check accessibility requirements if specified
    if (element.accessibility) {
      const firstElement = locator.first();
      
      if (element.accessibility.role) {
        const role = await firstElement.getAttribute('role');
        if (role !== element.accessibility.role) {
          accessible = false;
          accessibilityIssues.push(
            `Expected role="${element.accessibility.role}", found "${role || 'none'}"`
          );
        }
      }
      
      if (element.accessibility.ariaLabel) {
        const ariaLabel = await firstElement.getAttribute('aria-label');
        if (!ariaLabel) {
          accessible = false;
          accessibilityIssues.push('Missing aria-label attribute');
        }
      }
      
      if (element.accessibility.ariaDescribedBy) {
        const ariaDescribedBy = await firstElement.getAttribute('aria-describedby');
        if (!ariaDescribedBy) {
          accessible = false;
          accessibilityIssues.push('Missing aria-describedby attribute');
        }
      }
      
      if (element.accessibility.ariaLabelledBy) {
        const ariaLabelledBy = await firstElement.getAttribute('aria-labelledby');
        if (!ariaLabelledBy) {
          accessible = false;
          accessibilityIssues.push('Missing aria-labelledby attribute');
        }
      }
      
      if (element.accessibility.tabIndex !== undefined) {
        const tabIndex = await firstElement.getAttribute('tabindex');
        const actualTabIndex = tabIndex ? parseInt(tabIndex, 10) : undefined;
        if (actualTabIndex !== element.accessibility.tabIndex) {
          accessible = false;
          accessibilityIssues.push(
            `Expected tabindex="${element.accessibility.tabIndex}", found "${actualTabIndex ?? 'none'}"`
          );
        }
      }
    }
  }
  
  return {
    testId: element.testId,
    found,
    visible,
    accessible,
    accessibilityIssues: accessibilityIssues.length > 0 ? accessibilityIssues : undefined,
    expectedAccessibility: element.accessibility,
  };
}

/**
 * Verifies a section structure in E2E tests
 * 
 * @param page - Playwright page object
 * @param section - Section definition to verify
 */
export async function verifySection(
  page: Page,
  section: SectionDefinition
): Promise<SectionVerificationResult> {
  const elementDetails: ElementDetail[] = [];
  const missingElements: string[] = [];
  const suggestedFixes: string[] = [];
  
  // Verify section container exists
  const sectionLocator = page.getByTestId(section.testId);
  const sectionExists = (await sectionLocator.count()) > 0;
  
  if (!sectionExists && section.required) {
    missingElements.push(section.testId);
    suggestedFixes.push(
      `Add data-testid="${section.testId}" to the ${section.name} section container`
    );
  }
  
  // Verify all elements in the section
  for (const element of section.elements) {
    const detail = await verifyElement(page, element);
    elementDetails.push(detail);
    
    if (!detail.found && element.required) {
      missingElements.push(element.testId);
      suggestedFixes.push(
        `Add data-testid="${element.testId}" to ${element.description}`
      );
    }
    
    if (detail.found && !detail.visible && element.required) {
      suggestedFixes.push(
        `Element "${element.testId}" exists but is not visible. Check CSS display/visibility.`
      );
    }
    
    if (detail.found && !detail.accessible && element.accessibility) {
      suggestedFixes.push(
        `Element "${element.testId}" has accessibility issues: ${detail.accessibilityIssues?.join(', ')}`
      );
    }
    
    // Recursively verify children
    if (element.children) {
      for (const child of element.children) {
        const childDetail = await verifyElement(page, child);
        elementDetails.push(childDetail);
        
        if (!childDetail.found && child.required) {
          missingElements.push(child.testId);
          suggestedFixes.push(
            `Add data-testid="${child.testId}" to ${child.description}`
          );
        }
      }
    }
  }
  
  return {
    sectionName: section.name,
    sectionTestId: section.testId,
    passed: missingElements.length === 0,
    missingElements,
    elementDetails,
    suggestedFixes,
  };
}

/**
 * Verifies a complete page structure in E2E tests
 * 
 * @param page - Playwright page object
 * @param pageStructure - Page structure definition to verify
 */
export async function verifyPageStructure(
  page: Page,
  pageStructure: PageStructure
): Promise<StructureVerificationResult> {
  const sectionResults: SectionVerificationResult[] = [];
  const allMissingElements: string[] = [];
  const allDetails: ElementDetail[] = [];
  const allSuggestedFixes: string[] = [];
  
  // Wait for dynamic content if specified
  if (pageStructure.waitForSelector) {
    await waitForDynamicContent(page, {
      selector: pageStructure.waitForSelector,
    });
  } else {
    await waitForDynamicContent(page);
  }
  
  // Verify all required sections
  for (const section of pageStructure.sections) {
    if (!section.required) continue;
    
    const result = await verifySection(page, section);
    sectionResults.push(result);
    
    allMissingElements.push(...result.missingElements);
    allDetails.push(...result.elementDetails);
    allSuggestedFixes.push(...result.suggestedFixes);
  }
  
  // Count how many elements were found for timeout classification
  const elementsFound = allDetails.filter(d => d.found).length;
  const totalElements = allDetails.length;
  
  return {
    passed: allMissingElements.length === 0,
    missingElements: allMissingElements,
    unexpectedElements: [], // Not implemented in this version
    details: allDetails,
    sectionResults,
    suggestedFixes: allSuggestedFixes,
    elementsFound,
  };
}

// ============================================================================
// Unit Test Utilities (Jest/RTL)
// ============================================================================

/**
 * Verifies a single element in unit tests
 */
function verifyElementInRender(
  result: RenderResult,
  element: ElementDefinition
): ElementDetail {
  const { queryAllByTestId } = result;
  const domElements = queryAllByTestId(element.testId);
  const found = domElements.length > 0;
  const domElement = domElements[0]; // Use first element if multiple exist
  
  let visible = false;
  let accessible = true;
  const accessibilityIssues: string[] = [];
  
  if (found && domElement) {
    // Check if element is visible (not hidden by CSS)
    const style = window.getComputedStyle(domElement);
    visible = style.display !== 'none' && style.visibility !== 'hidden';
    
    // Check accessibility requirements if specified
    if (element.accessibility) {
      if (element.accessibility.role) {
        const role = domElement.getAttribute('role');
        if (role !== element.accessibility.role) {
          accessible = false;
          accessibilityIssues.push(
            `Expected role="${element.accessibility.role}", found "${role || 'none'}"`
          );
        }
      }
      
      if (element.accessibility.ariaLabel) {
        const ariaLabel = domElement.getAttribute('aria-label');
        if (!ariaLabel) {
          accessible = false;
          accessibilityIssues.push('Missing aria-label attribute');
        }
      }
      
      if (element.accessibility.ariaDescribedBy) {
        const ariaDescribedBy = domElement.getAttribute('aria-describedby');
        if (!ariaDescribedBy) {
          accessible = false;
          accessibilityIssues.push('Missing aria-describedby attribute');
        }
      }
      
      if (element.accessibility.ariaLabelledBy) {
        const ariaLabelledBy = domElement.getAttribute('aria-labelledby');
        if (!ariaLabelledBy) {
          accessible = false;
          accessibilityIssues.push('Missing aria-labelledby attribute');
        }
      }
      
      if (element.accessibility.tabIndex !== undefined) {
        const tabIndex = domElement.getAttribute('tabindex');
        const actualTabIndex = tabIndex ? parseInt(tabIndex, 10) : undefined;
        if (actualTabIndex !== element.accessibility.tabIndex) {
          accessible = false;
          accessibilityIssues.push(
            `Expected tabindex="${element.accessibility.tabIndex}", found "${actualTabIndex ?? 'none'}"`
          );
        }
      }
    }
  }
  
  return {
    testId: element.testId,
    found,
    visible,
    accessible,
    accessibilityIssues: accessibilityIssues.length > 0 ? accessibilityIssues : undefined,
    expectedAccessibility: element.accessibility,
  };
}

/**
 * Verifies a component structure in unit tests
 * 
 * @param result - React Testing Library render result
 * @param componentStructure - Component structure definition to verify
 * @param state - Optional state to verify (e.g., 'loading', 'error', 'empty')
 */
export function verifyComponentStructure(
  result: RenderResult,
  componentStructure: ComponentStructure,
  state?: string
): ComponentVerificationResult {
  const elementDetails: ElementDetail[] = [];
  const missingElements: string[] = [];
  const suggestedFixes: string[] = [];
  
  // Determine which elements to check based on state
  let elementsToCheck: ElementDefinition[] = [];
  
  if (state && componentStructure.states[state]) {
    // Check state-specific elements
    elementsToCheck = componentStructure.states[state] || [];
  } else {
    // Check required elements (default state)
    elementsToCheck = componentStructure.requiredElements;
  }
  
  // Verify all elements
  for (const element of elementsToCheck) {
    const detail = verifyElementInRender(result, element);
    elementDetails.push(detail);
    
    if (!detail.found && element.required) {
      missingElements.push(element.testId);
      suggestedFixes.push(
        `Add data-testid="${element.testId}" to ${element.description} in ${componentStructure.name}`
      );
    }
    
    if (detail.found && !detail.visible && element.required) {
      suggestedFixes.push(
        `Element "${element.testId}" exists but is not visible. Check CSS display/visibility.`
      );
    }
    
    if (detail.found && !detail.accessible && element.accessibility) {
      suggestedFixes.push(
        `Element "${element.testId}" has accessibility issues: ${detail.accessibilityIssues?.join(', ')}`
      );
    }
    
    // Recursively verify children
    if (element.children) {
      for (const child of element.children) {
        const childDetail = verifyElementInRender(result, child);
        elementDetails.push(childDetail);
        
        if (!childDetail.found && child.required) {
          missingElements.push(child.testId);
          suggestedFixes.push(
            `Add data-testid="${child.testId}" to ${child.description}`
          );
        }
      }
    }
  }
  
  return {
    componentName: componentStructure.name,
    passed: missingElements.length === 0,
    missingElements,
    elementDetails,
    suggestedFixes,
  };
}

/**
 * Verifies that specific elements exist in unit tests
 * 
 * @param result - React Testing Library render result
 * @param testIds - Array of test IDs to check
 */
export function verifyElementsExist(
  result: RenderResult,
  testIds: string[]
): ElementVerificationResult {
  const { queryAllByTestId } = result;
  const missingElements: string[] = [];
  const foundElements: string[] = [];
  
  for (const testId of testIds) {
    const elements = queryAllByTestId(testId);
    if (elements.length > 0) {
      foundElements.push(testId);
    } else {
      missingElements.push(testId);
    }
  }
  
  return {
    passed: missingElements.length === 0,
    missingElements,
    foundElements,
  };
}

/**
 * Checks accessibility attributes for an element
 * 
 * @param result - React Testing Library render result
 * @param testId - Test ID of the element to check
 * @param requirements - Expected accessibility attributes
 */
export function checkAccessibility(
  result: RenderResult,
  testId: string,
  requirements: {
    role?: string;
    ariaLabel?: string;
    ariaDescribedBy?: string;
    ariaLabelledBy?: string;
    tabIndex?: number;
  }
): {
  passed: boolean;
  issues: string[];
} {
  const { queryAllByTestId } = result;
  const elements = queryAllByTestId(testId);
  const issues: string[] = [];
  
  if (elements.length === 0) {
    issues.push(`Element with testId="${testId}" not found`);
    return { passed: false, issues };
  }
  
  const element = elements[0]; // Use first element if multiple exist
  
  if (requirements.role) {
    const role = element.getAttribute('role');
    if (role !== requirements.role) {
      issues.push(
        `Expected role="${requirements.role}", found "${role || 'none'}"`
      );
    }
  }
  
  if (requirements.ariaLabel) {
    const ariaLabel = element.getAttribute('aria-label');
    if (!ariaLabel) {
      issues.push('Missing aria-label attribute');
    }
  }
  
  if (requirements.ariaDescribedBy) {
    const ariaDescribedBy = element.getAttribute('aria-describedby');
    if (!ariaDescribedBy) {
      issues.push('Missing aria-describedby attribute');
    }
  }
  
  if (requirements.ariaLabelledBy) {
    const ariaLabelledBy = element.getAttribute('aria-labelledby');
    if (!ariaLabelledBy) {
      issues.push('Missing aria-labelledby attribute');
    }
  }
  
  if (requirements.tabIndex !== undefined) {
    const tabIndex = element.getAttribute('tabindex');
    const actualTabIndex = tabIndex ? parseInt(tabIndex, 10) : undefined;
    if (actualTabIndex !== requirements.tabIndex) {
      issues.push(
        `Expected tabindex="${requirements.tabIndex}", found "${actualTabIndex ?? 'none'}"`
      );
    }
  }
  
  return {
    passed: issues.length === 0,
    issues,
  };
}

/**
 * Verifies that interactive elements have required accessibility attributes
 * 
 * @param result - React Testing Library render result
 * @param testIds - Array of test IDs for interactive elements
 */
export function verifyInteractiveAccessibility(
  result: RenderResult,
  testIds: string[]
): {
  passed: boolean;
  violations: Array<{
    testId: string;
    issues: string[];
  }>;
} {
  const violations: Array<{ testId: string; issues: string[] }> = [];
  
  for (const testId of testIds) {
    const { queryAllByTestId } = result;
    const elements = queryAllByTestId(testId);
    
    if (elements.length === 0) {
      violations.push({
        testId,
        issues: ['Element not found'],
      });
      continue;
    }
    
    const element = elements[0];
    const issues: string[] = [];
    const tagName = element.tagName.toLowerCase();
    
    // Check if element is interactive
    const interactiveTags = ['button', 'a', 'input', 'select', 'textarea'];
    const hasRole = element.getAttribute('role');
    const isInteractive = interactiveTags.includes(tagName) || 
                         hasRole === 'button' || 
                         hasRole === 'link' ||
                         hasRole === 'tab' ||
                         hasRole === 'menuitem';
    
    if (isInteractive) {
      // Buttons should have accessible names
      if (tagName === 'button' || hasRole === 'button') {
        const ariaLabel = element.getAttribute('aria-label');
        const ariaLabelledBy = element.getAttribute('aria-labelledby');
        const textContent = element.textContent?.trim();
        
        if (!ariaLabel && !ariaLabelledBy && !textContent) {
          issues.push('Interactive button missing accessible name (aria-label, aria-labelledby, or text content)');
        }
      }
      
      // Links should have accessible names
      if (tagName === 'a' || hasRole === 'link') {
        const ariaLabel = element.getAttribute('aria-label');
        const ariaLabelledBy = element.getAttribute('aria-labelledby');
        const textContent = element.textContent?.trim();
        
        if (!ariaLabel && !ariaLabelledBy && !textContent) {
          issues.push('Interactive link missing accessible name (aria-label, aria-labelledby, or text content)');
        }
      }
      
      // Form inputs should have labels
      if (['input', 'select', 'textarea'].includes(tagName)) {
        const ariaLabel = element.getAttribute('aria-label');
        const ariaLabelledBy = element.getAttribute('aria-labelledby');
        const id = element.getAttribute('id');
        const hasLabel = id && result.container.querySelector(`label[for="${id}"]`);
        
        if (!ariaLabel && !ariaLabelledBy && !hasLabel) {
          issues.push('Form input missing label (aria-label, aria-labelledby, or associated label element)');
        }
      }
    }
    
    if (issues.length > 0) {
      violations.push({ testId, issues });
    }
  }
  
  return {
    passed: violations.length === 0,
    violations,
  };
}

// ============================================================================
// Error Reporting Utilities
// ============================================================================

/**
 * Formats a structure verification result into a readable error message
 */
export function formatVerificationError(
  result: StructureVerificationResult | ComponentVerificationResult
): string {
  const lines: string[] = [];
  
  if ('sectionResults' in result) {
    // Page structure result
    lines.push('Page Structure Verification Failed');
    lines.push('=====================================');
    lines.push('');
    
    if (result.timeoutFailure) {
      lines.push(`⚠️  Timeout Failure: ${result.timeoutClassification}`);
      lines.push(`   Elements found: ${result.elementsFound} / ${result.details.length}`);
      lines.push('');
    }
    
    lines.push(`Missing Elements (${result.missingElements.length}):`);
    result.missingElements.forEach(testId => {
      const detail = result.details.find(d => d.testId === testId);
      if (detail) {
        lines.push(`  ❌ ${testId}`);
        const fix = result.suggestedFixes.find(f => f.includes(testId));
        if (fix) {
          lines.push(`     → ${fix}`);
        }
      }
    });
    
    lines.push('');
    lines.push('Section Results:');
    result.sectionResults.forEach(section => {
      const status = section.passed ? '✅' : '❌';
      lines.push(`  ${status} ${section.sectionName} (${section.sectionTestId})`);
      if (!section.passed) {
        section.missingElements.forEach(testId => {
          lines.push(`      - Missing: ${testId}`);
        });
      }
    });
  } else {
    // Component structure result
    lines.push(`Component Structure Verification Failed: ${result.componentName}`);
    lines.push('='.repeat(50 + result.componentName.length));
    lines.push('');
    
    lines.push(`Missing Elements (${result.missingElements.length}):`);
    result.missingElements.forEach(testId => {
      lines.push(`  ❌ ${testId}`);
      const fix = result.suggestedFixes.find(f => f.includes(testId));
      if (fix) {
        lines.push(`     → ${fix}`);
      }
    });
  }
  
  return lines.join('\n');
}

/**
 * Classifies a timeout failure as partial or full
 */
export function classifyTimeoutFailure(
  result: StructureVerificationResult
): 'partial' | 'full' {
  const elementsFound = result.elementsFound ?? 0;
  const totalElements = result.details.length;
  
  if (elementsFound === 0) {
    return 'full';
  } else if (elementsFound < totalElements) {
    return 'partial';
  }
  
  return 'partial';
}
