/**
 * Page Structures Validation Test
 * 
 * Validates that all defined page structures in the manifest are valid
 */

import { PAGE_STRUCTURES, validatePageStructure } from '@/lib/testing/structure-manifest';

describe('Page Structures Validation', () => {
  it('should have all expected pages defined', () => {
    const expectedPages = [
      'dashboard',
      'financials',
      'projects',
      'resources',
      'reports',
      'risks',
      'scenarios',
      'monte-carlo',
      'admin',
      'audit',
      'changes',
      'feedback',
      'import'
    ];

    expectedPages.forEach(pageName => {
      expect(PAGE_STRUCTURES[pageName]).toBeDefined();
    });
  });

  it('should have valid structure for all defined pages', () => {
    Object.entries(PAGE_STRUCTURES).forEach(([pageName, structure]) => {
      const result = validatePageStructure(structure);
      
      if (!result.valid) {
        console.error(`Validation errors for ${pageName}:`, result.errors);
      }
      
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
  });

  it('should have required fields for dashboard structure', () => {
    const dashboard = PAGE_STRUCTURES.dashboard;
    
    expect(dashboard.path).toBe('/dashboards');
    expect(dashboard.name).toBe('Dashboard');
    expect(dashboard.sections).toBeDefined();
    expect(dashboard.sections.length).toBeGreaterThan(0);
    
    // Check for key sections
    const sectionNames = dashboard.sections.map(s => s.name);
    expect(sectionNames).toContain('Header');
    expect(sectionNames).toContain('KPI Cards');
    expect(sectionNames).toContain('Variance Section');
    expect(sectionNames).toContain('Project Health');
    expect(sectionNames).toContain('Recent Projects');
    expect(sectionNames).toContain('Quick Actions');
  });

  it('should have required fields for financials structure', () => {
    const financials = PAGE_STRUCTURES.financials;
    
    expect(financials.path).toBe('/financials');
    expect(financials.name).toBe('Financials');
    expect(financials.sections).toBeDefined();
    expect(financials.sections.length).toBeGreaterThan(0);
    
    // Check for key sections
    const sectionNames = financials.sections.map(s => s.name);
    expect(sectionNames).toContain('Header');
    expect(sectionNames).toContain('Tab Navigation');
    expect(sectionNames).toContain('Financial Metrics');
    expect(sectionNames).toContain('Budget Variance Table');
    
    // Check conditional sections
    expect(financials.conditionalSections).toBeDefined();
    expect(financials.conditionalSections!.length).toBeGreaterThan(0);
  });

  it('should have all page structures with valid paths', () => {
    Object.entries(PAGE_STRUCTURES).forEach(([pageName, structure]) => {
      expect(structure.path).toBeTruthy();
      expect(structure.path).toMatch(/^\//);
    });
  });

  it('should have all sections with test IDs', () => {
    Object.entries(PAGE_STRUCTURES).forEach(([pageName, structure]) => {
      structure.sections.forEach(section => {
        expect(section.testId).toBeTruthy();
        expect(section.testId).toMatch(/^[a-z0-9-]+$/);
      });
    });
  });
});
