/**
 * Property-Based Tests for Mock Data Generators
 * Feature: ui-structure-tests
 * Property 11: Mock Data Validity
 * 
 * Validates: Requirements 7.5
 */

import * as fc from 'fast-check';
import {
  generateMockSession,
  generateMockAdminSession,
  generateMockProject,
  generateMockProjects,
  generateMockFinancialProject,
  generateMockFinancialMetrics,
  generateMockBudgetVariance,
  generateMockFinancialAlert,
  generateMockUser,
  generateMockResource,
  generateMockRisk,
  generateMockFinancialAlerts,
  generateMockResources,
  generateMockRisks,
  isValidMockSession,
  isValidMockProject,
  isValidMockFinancialMetrics,
} from '@/lib/testing/mock-generators';

describe('Mock Data Generators - Property Tests', () => {
  describe('Property 11: Mock Data Validity', () => {
    describe('Session Mock Generators', () => {
      it('generates valid session data that satisfies type requirements', () => {
        fc.assert(
          fc.property(
            fc.record({
              email: fc.option(fc.emailAddress(), { nil: undefined }),
              role: fc.option(fc.constantFrom('admin', 'manager', 'user', 'viewer'), { nil: undefined }),
            }),
            (overrides) => {
              const session = generateMockSession({
                user: overrides.email || overrides.role ? {
                  email: overrides.email,
                  role: overrides.role,
                } : undefined,
              });
              
              // Validate structure
              expect(isValidMockSession(session)).toBe(true);
              
              // Validate required fields
              expect(session.access_token).toBeTruthy();
              expect(session.refresh_token).toBeTruthy();
              expect(session.expires_at).toBeGreaterThan(Date.now());
              expect(session.expires_in).toBeGreaterThan(0);
              expect(session.token_type).toBe('bearer');
              expect(session.user.id).toBeTruthy();
              expect(session.user.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
              expect(['admin', 'manager', 'user', 'viewer']).toContain(session.user.role);
            }
          ),
          { numRuns: 100 }
        );
      });

      it('generates admin sessions with admin role', () => {
        fc.assert(
          fc.property(
            fc.constant(undefined),
            () => {
              const session = generateMockAdminSession();
              
              expect(isValidMockSession(session)).toBe(true);
              expect(session.user.role).toBe('admin');
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Project Mock Generators', () => {
      it('generates valid project data that satisfies type requirements', () => {
        fc.assert(
          fc.property(
            fc.record({
              name: fc.option(fc.string({ minLength: 1, maxLength: 100 }), { nil: undefined }),
              status: fc.option(fc.constantFrom('planning', 'active', 'on_hold', 'completed', 'cancelled'), { nil: undefined }),
              priority: fc.option(fc.constantFrom('low', 'medium', 'high', 'critical'), { nil: undefined }),
              health: fc.option(fc.constantFrom('green', 'yellow', 'red'), { nil: undefined }),
              budget: fc.option(fc.integer({ min: 0, max: 10000000 }), { nil: undefined }),
              progress: fc.option(fc.integer({ min: 0, max: 100 }), { nil: undefined }),
            }),
            (overrides) => {
              const project = generateMockProject(overrides);
              
              // Validate structure
              expect(isValidMockProject(project)).toBe(true);
              
              // Validate required fields
              expect(project.id).toBeTruthy();
              expect(project.name).toBeTruthy();
              expect(['planning', 'active', 'on_hold', 'completed', 'cancelled']).toContain(project.status);
              expect(['low', 'medium', 'high', 'critical']).toContain(project.priority);
              expect(['green', 'yellow', 'red']).toContain(project.health);
              expect(project.progress).toBeGreaterThanOrEqual(0);
              expect(project.progress).toBeLessThanOrEqual(100);
              
              // Validate dates
              expect(new Date(project.start_date).getTime()).not.toBeNaN();
              expect(new Date(project.created_at).getTime()).not.toBeNaN();
              expect(new Date(project.updated_at).getTime()).not.toBeNaN();
            }
          ),
          { numRuns: 100 }
        );
      });

      it('generates multiple projects with consistent structure', () => {
        fc.assert(
          fc.property(
            fc.integer({ min: 1, max: 20 }),
            (count) => {
              const projects = generateMockProjects(count);
              
              expect(projects).toHaveLength(count);
              projects.forEach(project => {
                expect(isValidMockProject(project)).toBe(true);
              });
            }
          ),
          { numRuns: 50 }
        );
      });

      it('generates financial projects with valid budget data', () => {
        fc.assert(
          fc.property(
            fc.record({
              budget: fc.option(fc.integer({ min: 1000, max: 1000000 }), { nil: undefined }),
              actual_cost: fc.option(fc.integer({ min: 0, max: 1000000 }), { nil: undefined }),
            }),
            (overrides) => {
              const project = generateMockFinancialProject(overrides);
              
              expect(project.id).toBeTruthy();
              expect(project.name).toBeTruthy();
              expect(typeof project.budget).toBe('number');
              expect(typeof project.actual_cost).toBe('number');
              expect(['green', 'yellow', 'red']).toContain(project.health);
            }
          ),
          { numRuns: 100 }
        );
      });
    });

    describe('Financial Data Mock Generators', () => {
      it('generates valid financial metrics that satisfy type requirements', () => {
        fc.assert(
          fc.property(
            fc.record({
              total_budget: fc.option(fc.integer({ min: 100000, max: 10000000 }), { nil: undefined }),
              total_actual: fc.option(fc.integer({ min: 50000, max: 10000000 }), { nil: undefined }),
              projects_over_budget: fc.option(fc.integer({ min: 0, max: 50 }), { nil: undefined }),
              projects_under_budget: fc.option(fc.integer({ min: 0, max: 50 }), { nil: undefined }),
            }),
            (overrides) => {
              const metrics = generateMockFinancialMetrics(overrides);
              
              // Validate structure
              expect(isValidMockFinancialMetrics(metrics)).toBe(true);
              
              // Validate required fields
              expect(typeof metrics.total_budget).toBe('number');
              expect(typeof metrics.total_actual).toBe('number');
              expect(typeof metrics.total_variance).toBe('number');
              expect(typeof metrics.variance_percentage).toBe('number');
              expect(typeof metrics.projects_over_budget).toBe('number');
              expect(typeof metrics.projects_under_budget).toBe('number');
              expect(typeof metrics.average_budget_utilization).toBe('number');
              expect(typeof metrics.currency_distribution).toBe('object');
              
              // Validate calculations
              const expectedVariance = metrics.total_actual - metrics.total_budget;
              expect(metrics.total_variance).toBeCloseTo(expectedVariance, 2);
            }
          ),
          { numRuns: 100 }
        );
      });

      it('generates valid budget variance data', () => {
        fc.assert(
          fc.property(
            fc.record({
              total_planned: fc.option(fc.integer({ min: 10000, max: 1000000 }), { nil: undefined }),
              total_actual: fc.option(fc.integer({ min: 5000, max: 1000000 }), { nil: undefined }),
            }),
            (overrides) => {
              const variance = generateMockBudgetVariance(overrides);
              
              expect(variance.project_id).toBeTruthy();
              expect(typeof variance.total_planned).toBe('number');
              expect(typeof variance.total_actual).toBe('number');
              expect(typeof variance.variance_amount).toBe('number');
              expect(typeof variance.variance_percentage).toBe('number');
              expect(variance.currency).toBeTruthy();
              expect(Array.isArray(variance.categories)).toBe(true);
              expect(variance.categories.length).toBeGreaterThan(0);
              
              // Validate calculations
              const expectedVariance = variance.total_actual - variance.total_planned;
              expect(variance.variance_amount).toBeCloseTo(expectedVariance, 2);
            }
          ),
          { numRuns: 100 }
        );
      });

      it('generates valid financial alerts', () => {
        fc.assert(
          fc.property(
            fc.record({
              budget: fc.option(fc.integer({ min: 10000, max: 500000 }), { nil: undefined }),
              actual_cost: fc.option(fc.integer({ min: 5000, max: 600000 }), { nil: undefined }),
            }),
            (overrides) => {
              const alert = generateMockFinancialAlert(overrides);
              
              expect(alert.project_id).toBeTruthy();
              expect(alert.project_name).toBeTruthy();
              expect(typeof alert.budget).toBe('number');
              expect(typeof alert.actual_cost).toBe('number');
              expect(typeof alert.utilization_percentage).toBe('number');
              expect(typeof alert.variance_amount).toBe('number');
              expect(['warning', 'critical']).toContain(alert.alert_level);
              expect(alert.message).toBeTruthy();
            }
          ),
          { numRuns: 100 }
        );
      });
    });

    describe('User Mock Generators', () => {
      it('generates valid user data that satisfies type requirements', () => {
        fc.assert(
          fc.property(
            fc.record({
              email: fc.option(fc.emailAddress(), { nil: undefined }),
              role: fc.option(fc.constantFrom('admin', 'manager', 'user', 'viewer'), { nil: undefined }),
            }),
            (overrides) => {
              const user = generateMockUser(overrides);
              
              expect(user.id).toBeTruthy();
              expect(user.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
              expect(['admin', 'manager', 'user', 'viewer']).toContain(user.role);
              expect(user.preferences).toBeDefined();
              expect(user.preferences.theme).toBeDefined();
              expect(user.preferences.language).toBeDefined();
              expect(user.preferences.timezone).toBeDefined();
              expect(user.preferences.notifications).toBeDefined();
              expect(user.preferences.dashboard).toBeDefined();
              expect(user.preferences.accessibility).toBeDefined();
            }
          ),
          { numRuns: 100 }
        );
      });
    });

    describe('Resource Mock Generators', () => {
      it('generates valid resource data that satisfies type requirements', () => {
        fc.assert(
          fc.property(
            fc.record({
              capacity: fc.option(fc.integer({ min: 20, max: 60 }), { nil: undefined }),
              hourly_rate: fc.option(fc.integer({ min: 50, max: 300 }), { nil: undefined }),
            }),
            (overrides) => {
              const resource = generateMockResource(overrides);
              
              expect(resource.id).toBeTruthy();
              expect(resource.name).toBeTruthy();
              expect(resource.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
              expect(typeof resource.capacity).toBe('number');
              expect(typeof resource.availability).toBe('number');
              expect(typeof resource.utilization_percentage).toBe('number');
              expect(resource.utilization_percentage).toBeGreaterThanOrEqual(0);
              expect(resource.utilization_percentage).toBeLessThanOrEqual(100);
              expect(['available', 'partially_allocated', 'mostly_allocated', 'fully_allocated']).toContain(resource.availability_status);
              expect(typeof resource.can_take_more_work).toBe('boolean');
              expect(Array.isArray(resource.skills)).toBe(true);
              expect(Array.isArray(resource.current_projects)).toBe(true);
            }
          ),
          { numRuns: 100 }
        );
      });

      it('generates multiple resources with consistent structure', () => {
        fc.assert(
          fc.property(
            fc.integer({ min: 1, max: 20 }),
            (count) => {
              const resources = generateMockResources(count);
              
              expect(resources).toHaveLength(count);
              resources.forEach(resource => {
                expect(resource.id).toBeTruthy();
                expect(resource.name).toBeTruthy();
                expect(typeof resource.utilization_percentage).toBe('number');
              });
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Risk Mock Generators', () => {
      it('generates valid risk data that satisfies type requirements', () => {
        fc.assert(
          fc.property(
            fc.record({
              probability: fc.option(fc.integer({ min: 1, max: 10 }), { nil: undefined }),
              impact: fc.option(fc.integer({ min: 1, max: 10 }), { nil: undefined }),
              category: fc.option(fc.constantFrom('technical', 'financial', 'resource', 'schedule', 'external'), { nil: undefined }),
            }),
            (overrides) => {
              const risk = generateMockRisk(overrides);
              
              expect(risk.id).toBeTruthy();
              expect(risk.project_id).toBeTruthy();
              expect(risk.title).toBeTruthy();
              expect(risk.description).toBeTruthy();
              expect(['technical', 'financial', 'resource', 'schedule', 'external']).toContain(risk.category);
              expect(risk.probability).toBeGreaterThanOrEqual(1);
              expect(risk.probability).toBeLessThanOrEqual(10);
              expect(risk.impact).toBeGreaterThanOrEqual(1);
              expect(risk.impact).toBeLessThanOrEqual(10);
              expect(risk.risk_score).toBe(risk.probability * risk.impact);
              expect(['identified', 'analyzing', 'mitigating', 'closed']).toContain(risk.status);
              expect(risk.mitigation).toBeTruthy();
              expect(risk.owner).toBeTruthy();
            }
          ),
          { numRuns: 100 }
        );
      });

      it('generates multiple risks with consistent structure', () => {
        fc.assert(
          fc.property(
            fc.integer({ min: 1, max: 20 }),
            (count) => {
              const risks = generateMockRisks(count);
              
              expect(risks).toHaveLength(count);
              risks.forEach(risk => {
                expect(risk.id).toBeTruthy();
                expect(risk.title).toBeTruthy();
                expect(risk.risk_score).toBe(risk.probability * risk.impact);
              });
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Batch Generators', () => {
      it('generates multiple financial alerts with consistent structure', () => {
        fc.assert(
          fc.property(
            fc.integer({ min: 1, max: 20 }),
            (count) => {
              const alerts = generateMockFinancialAlerts(count);
              
              expect(alerts).toHaveLength(count);
              alerts.forEach(alert => {
                expect(alert.project_id).toBeTruthy();
                expect(alert.project_name).toBeTruthy();
                expect(['warning', 'critical']).toContain(alert.alert_level);
              });
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Validation Helpers', () => {
      it('correctly validates valid mock sessions', () => {
        fc.assert(
          fc.property(
            fc.constant(undefined),
            () => {
              const session = generateMockSession();
              expect(isValidMockSession(session)).toBe(true);
            }
          ),
          { numRuns: 50 }
        );
      });

      it('correctly rejects invalid mock sessions', () => {
        const invalidSessions = [
          null,
          undefined,
          {},
          { access_token: 'token' },
          { access_token: 'token', user: null },
          { access_token: 'token', user: { id: '123' } },
        ];
        
        invalidSessions.forEach(invalid => {
          expect(isValidMockSession(invalid)).toBe(false);
        });
      });

      it('correctly validates valid mock projects', () => {
        fc.assert(
          fc.property(
            fc.constant(undefined),
            () => {
              const project = generateMockProject();
              expect(isValidMockProject(project)).toBe(true);
            }
          ),
          { numRuns: 50 }
        );
      });

      it('correctly rejects invalid mock projects', () => {
        const invalidProjects = [
          null,
          undefined,
          {},
          { id: '123' },
          { id: '123', name: 'Test' },
          { id: '123', name: 'Test', status: 'active' },
        ];
        
        invalidProjects.forEach(invalid => {
          expect(isValidMockProject(invalid)).toBe(false);
        });
      });

      it('correctly validates valid mock financial metrics', () => {
        fc.assert(
          fc.property(
            fc.constant(undefined),
            () => {
              const metrics = generateMockFinancialMetrics();
              expect(isValidMockFinancialMetrics(metrics)).toBe(true);
            }
          ),
          { numRuns: 50 }
        );
      });

      it('correctly rejects invalid mock financial metrics', () => {
        const invalidMetrics = [
          null,
          undefined,
          {},
          { total_budget: 100000 },
          { total_budget: 100000, total_actual: 90000 },
        ];
        
        invalidMetrics.forEach(invalid => {
          expect(isValidMockFinancialMetrics(invalid)).toBe(false);
        });
      });
    });
  });
});
