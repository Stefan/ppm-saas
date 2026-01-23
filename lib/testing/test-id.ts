/**
 * Test ID Generator Utility
 * 
 * Provides consistent data-testid generation following kebab-case naming convention.
 * Used across the application to ensure reliable test element selection.
 */

/**
 * Converts a string to kebab-case format
 * @param str - Input string to convert
 * @returns Kebab-case formatted string
 */
function toKebabCase(str: string): string {
  return str
    .trim()
    .replace(/([a-z])([A-Z])/g, '$1-$2') // camelCase to kebab-case
    .replace(/[\s_]+/g, '-') // spaces and underscores to hyphens
    .replace(/[^a-z0-9-]/gi, '') // remove non-alphanumeric except hyphens
    .toLowerCase()
    .replace(/-+/g, '-') // collapse multiple hyphens
    .replace(/^-|-$/g, ''); // trim leading/trailing hyphens
}

/**
 * Generates a consistent data-testid value
 * @param component - Component name (e.g., 'variance-kpis')
 * @param element - Optional element within component (e.g., 'header', 'grid')
 * @param variant - Optional variant (e.g., 'loading', 'error')
 * @returns Kebab-case formatted test ID
 * 
 * @example
 * generateTestId('VarianceKPIs') // 'variance-kpis'
 * generateTestId('VarianceKPIs', 'header') // 'variance-kpis-header'
 * generateTestId('VarianceKPIs', 'grid', 'loading') // 'variance-kpis-grid-loading'
 */
export function generateTestId(
  component: string,
  element?: string,
  variant?: string
): string {
  const parts = [toKebabCase(component)];
  
  if (element) {
    parts.push(toKebabCase(element));
  }
  
  if (variant) {
    parts.push(toKebabCase(variant));
  }
  
  return parts.filter(Boolean).join('-');
}

/**
 * Test ID builder interface
 */
export interface TestIdBuilder {
  /**
   * Get the root component test ID
   */
  root: () => string;
  
  /**
   * Get a test ID for an element within the component
   * @param name - Element name
   */
  element: (name: string) => string;
  
  /**
   * Get a test ID for a variant of an element
   * @param element - Element name
   * @param variant - Variant name
   */
  variant: (element: string, variant: string) => string;
}

/**
 * Creates a test ID builder for a component
 * @param componentName - Base component name
 * @returns Test ID builder with helper methods
 * 
 * @example
 * const testId = createTestIdBuilder('variance-kpis');
 * testId.root() // 'variance-kpis'
 * testId.element('header') // 'variance-kpis-header'
 * testId.variant('grid', 'loading') // 'variance-kpis-grid-loading'
 */
export function createTestIdBuilder(componentName: string): TestIdBuilder {
  const baseId = toKebabCase(componentName);
  
  return {
    root: () => baseId,
    element: (name: string) => generateTestId(baseId, name),
    variant: (element: string, variant: string) => generateTestId(baseId, element, variant),
  };
}

/**
 * Type for test ID generation options
 */
export interface TestIdOptions {
  component: string;
  element?: string;
  variant?: string;
}

/**
 * Generates a test ID from options object
 * @param options - Test ID generation options
 * @returns Kebab-case formatted test ID
 */
export function generateTestIdFromOptions(options: TestIdOptions): string {
  return generateTestId(options.component, options.element, options.variant);
}
