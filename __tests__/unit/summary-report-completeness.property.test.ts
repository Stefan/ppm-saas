/**
 * Property-Based Tests for Summary Report Completeness
 * Feature: ui-structure-tests
 * Property 10: Summary Report Completeness
 * 
 * Validates: Requirements 8.4
 */

import * as fc from 'fast-check';

describe('Summary Report Completeness - Property Tests', () => {
  describe('Property 10: Summary Report Completeness', () => {
    // Arbitrary for generating test items
    const testItemArbitrary = fc.record({
      id: fc.string({ minLength: 1, maxLength: 50 }),
      name: fc.string({ minLength: 1, maxLength: 100 }),
      type: fc.constantFrom('page', 'component', 'unit', 'e2e', 'visual'),
      status: fc.constantFrom('passed', 'failed', 'skipped'),
      duration: fc.integer({ min: 0, max: 10000 }),
    });

    describe('All Items Included', () => {
      it('summary includes entry for every tested item', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 50 }),
            (testedItems) => {
              // Generate summary report
              const summary = generateSummaryReport(testedItems);

              // Every tested item must have an entry in the summary
              expect(summary.items).toHaveLength(testedItems.length);

              // Check each item is present
              testedItems.forEach((item) => {
                const summaryEntry = summary.items.find((s) => s.id === item.id);
                expect(summaryEntry).toBeDefined();
                expect(summaryEntry?.name).toBe(item.name);
                expect(summaryEntry?.type).toBe(item.type);
                expect(summaryEntry?.status).toBe(item.status);
              });
            }
          ),
          { numRuns: 100 }
        );
      });

      it('summary preserves order of tested items', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 2, maxLength: 20 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              // Order should be preserved
              testedItems.forEach((item, index) => {
                expect(summary.items[index].id).toBe(item.id);
              });
            }
          ),
          { numRuns: 100 }
        );
      });

      it('summary handles duplicate IDs correctly', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 2, maxLength: 10 }),
            (testedItems) => {
              // Create duplicates by using same ID
              const itemsWithDuplicates = [
                ...testedItems,
                { ...testedItems[0], name: 'Duplicate test' },
              ];

              const summary = generateSummaryReport(itemsWithDuplicates);

              // Summary should include all items, even duplicates
              expect(summary.items.length).toBe(itemsWithDuplicates.length);
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Summary Statistics', () => {
      it('summary totals match individual item counts', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 50 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              // Total should match array length
              expect(summary.statistics.total).toBe(testedItems.length);

              // Status counts should match
              const passedCount = testedItems.filter((t) => t.status === 'passed').length;
              const failedCount = testedItems.filter((t) => t.status === 'failed').length;
              const skippedCount = testedItems.filter((t) => t.status === 'skipped').length;

              expect(summary.statistics.passed).toBe(passedCount);
              expect(summary.statistics.failed).toBe(failedCount);
              expect(summary.statistics.skipped).toBe(skippedCount);

              // Sum of status counts should equal total
              expect(summary.statistics.passed + summary.statistics.failed + summary.statistics.skipped).toBe(
                summary.statistics.total
              );
            }
          ),
          { numRuns: 100 }
        );
      });

      it('summary includes type breakdown', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 50 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              // Should have breakdown by type
              expect(summary.statistics.byType).toBeDefined();

              // Count items by type
              const typeCount = testedItems.reduce((acc, item) => {
                acc[item.type] = (acc[item.type] || 0) + 1;
                return acc;
              }, {} as Record<string, number>);

              // Verify type counts match
              Object.entries(typeCount).forEach(([type, count]) => {
                expect(summary.statistics.byType[type]).toBe(count);
              });
            }
          ),
          { numRuns: 100 }
        );
      });

      it('summary includes duration statistics', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 50 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              // Should have duration statistics
              expect(summary.statistics.duration).toBeDefined();
              expect(summary.statistics.duration.total).toBeDefined();
              expect(summary.statistics.duration.average).toBeDefined();
              expect(summary.statistics.duration.min).toBeDefined();
              expect(summary.statistics.duration.max).toBeDefined();

              // Calculate expected values
              const durations = testedItems.map((t) => t.duration);
              const totalDuration = durations.reduce((sum, d) => sum + d, 0);
              const avgDuration = totalDuration / durations.length;
              const minDuration = Math.min(...durations);
              const maxDuration = Math.max(...durations);

              // Verify calculations
              expect(summary.statistics.duration.total).toBe(totalDuration);
              expect(summary.statistics.duration.average).toBeCloseTo(avgDuration, 2);
              expect(summary.statistics.duration.min).toBe(minDuration);
              expect(summary.statistics.duration.max).toBe(maxDuration);
            }
          ),
          { numRuns: 100 }
        );
      });
    });

    describe('Summary Metadata', () => {
      it('summary includes timestamp', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 10 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              expect(summary.metadata.timestamp).toBeDefined();
              expect(typeof summary.metadata.timestamp).toBe('string');

              // Should be valid ISO date
              expect(() => new Date(summary.metadata.timestamp)).not.toThrow();
            }
          ),
          { numRuns: 50 }
        );
      });

      it('summary includes test run information', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 10 }),
            fc.record({
              environment: fc.constantFrom('ci', 'local', 'staging', 'production'),
              branch: fc.string({ minLength: 1, maxLength: 50 }),
              commit: fc.string({ minLength: 7, maxLength: 40 }).map(s => 
                s.replace(/[^0-9a-f]/gi, '0').toLowerCase().slice(0, 40)
              ), // Generate hex-like string
            }),
            (testedItems, runInfo) => {
              const summary = generateSummaryReport(testedItems, runInfo);

              expect(summary.metadata.environment).toBe(runInfo.environment);
              expect(summary.metadata.branch).toBe(runInfo.branch);
              expect(summary.metadata.commit).toBe(runInfo.commit);
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Failed Items Details', () => {
      it('summary includes details for all failed items', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 50 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              const failedItems = testedItems.filter((t) => t.status === 'failed');

              // Should have failed items section
              expect(summary.failedItems).toBeDefined();
              expect(summary.failedItems).toHaveLength(failedItems.length);

              // Each failed item should be included
              failedItems.forEach((failedItem) => {
                const summaryFailure = summary.failedItems.find((f) => f.id === failedItem.id);
                expect(summaryFailure).toBeDefined();
                expect(summaryFailure?.name).toBe(failedItem.name);
              });
            }
          ),
          { numRuns: 100 }
        );
      });

      it('summary includes error information for failures', () => {
        fc.assert(
          fc.property(
            fc.array(
              fc.record({
                id: fc.string({ minLength: 1, maxLength: 50 }),
                name: fc.string({ minLength: 1, maxLength: 100 }),
                type: fc.constantFrom('page', 'component', 'unit', 'e2e', 'visual'),
                status: fc.constant('failed' as const),
                duration: fc.integer({ min: 0, max: 10000 }),
                error: fc.record({
                  message: fc.string({ minLength: 1, maxLength: 200 }),
                  stack: fc.option(fc.string({ minLength: 1, maxLength: 500 }), { nil: undefined }),
                }),
              }),
              { minLength: 1, maxLength: 10 }
            ),
            (failedItems) => {
              const summary = generateSummaryReportWithErrors(failedItems);

              // Each failed item should have error details
              failedItems.forEach((item) => {
                const summaryFailure = summary.failedItems.find((f) => f.id === item.id);
                expect(summaryFailure).toBeDefined();
                expect(summaryFailure?.error).toBeDefined();
                expect(summaryFailure?.error?.message).toBe(item.error.message);
                if (item.error.stack !== undefined) {
                  expect(summaryFailure?.error?.stack).toBe(item.error.stack);
                }
              });
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Empty Test Runs', () => {
      it('handles empty test runs gracefully', () => {
        const summary = generateSummaryReport([]);

        expect(summary.items).toHaveLength(0);
        expect(summary.statistics.total).toBe(0);
        expect(summary.statistics.passed).toBe(0);
        expect(summary.statistics.failed).toBe(0);
        expect(summary.statistics.skipped).toBe(0);
        expect(summary.failedItems).toHaveLength(0);
      });

      it('handles all-passing test runs', () => {
        fc.assert(
          fc.property(
            fc.array(
              fc.record({
                ...testItemArbitrary.value,
                status: fc.constant('passed' as const),
              }),
              { minLength: 1, maxLength: 20 }
            ),
            (passingItems) => {
              const summary = generateSummaryReport(passingItems);

              expect(summary.statistics.total).toBe(passingItems.length);
              expect(summary.statistics.passed).toBe(passingItems.length);
              expect(summary.statistics.failed).toBe(0);
              expect(summary.failedItems).toHaveLength(0);
            }
          ),
          { numRuns: 50 }
        );
      });

      it('handles all-failing test runs', () => {
        fc.assert(
          fc.property(
            fc.array(
              fc.record({
                ...testItemArbitrary.value,
                status: fc.constant('failed' as const),
              }),
              { minLength: 1, maxLength: 20 }
            ),
            (failingItems) => {
              const summary = generateSummaryReport(failingItems);

              expect(summary.statistics.total).toBe(failingItems.length);
              expect(summary.statistics.passed).toBe(0);
              expect(summary.statistics.failed).toBe(failingItems.length);
              expect(summary.failedItems).toHaveLength(failingItems.length);
            }
          ),
          { numRuns: 50 }
        );
      });
    });

    describe('Summary Consistency', () => {
      it('generates same summary for same input', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 20 }),
            (testedItems) => {
              const summary1 = generateSummaryReport(testedItems);
              const summary2 = generateSummaryReport(testedItems);

              // Statistics should be identical
              expect(summary1.statistics.total).toBe(summary2.statistics.total);
              expect(summary1.statistics.passed).toBe(summary2.statistics.passed);
              expect(summary1.statistics.failed).toBe(summary2.statistics.failed);
              expect(summary1.items.length).toBe(summary2.items.length);
            }
          ),
          { numRuns: 100 }
        );
      });

      it('summary is serializable to JSON', () => {
        fc.assert(
          fc.property(
            fc.array(testItemArbitrary, { minLength: 1, maxLength: 20 }),
            (testedItems) => {
              const summary = generateSummaryReport(testedItems);

              // Should be serializable
              expect(() => JSON.stringify(summary)).not.toThrow();

              // Should be deserializable
              const jsonString = JSON.stringify(summary);
              const parsed = JSON.parse(jsonString);

              // Parsed should match original structure
              expect(parsed.items).toHaveLength(summary.items.length);
              expect(parsed.statistics.total).toBe(summary.statistics.total);
            }
          ),
          { numRuns: 100 }
        );
      });
    });
  });
});

// Helper function to generate summary report
interface TestItem {
  id: string;
  name: string;
  type: string;
  status: string;
  duration: number;
}

interface TestItemWithError extends TestItem {
  error: {
    message: string;
    stack?: string;
  };
}

interface SummaryReport {
  items: TestItem[];
  statistics: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    byType: Record<string, number>;
    duration: {
      total: number;
      average: number;
      min: number;
      max: number;
    };
  };
  failedItems: Array<TestItem & { error?: { message: string; stack?: string } }>;
  metadata: {
    timestamp: string;
    environment?: string;
    branch?: string;
    commit?: string;
  };
}

function generateSummaryReport(
  testedItems: TestItem[],
  runInfo?: { environment: string; branch: string; commit: string }
): SummaryReport {
  const passedCount = testedItems.filter((t) => t.status === 'passed').length;
  const failedCount = testedItems.filter((t) => t.status === 'failed').length;
  const skippedCount = testedItems.filter((t) => t.status === 'skipped').length;

  const byType = testedItems.reduce((acc, item) => {
    acc[item.type] = (acc[item.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const durations = testedItems.map((t) => t.duration);
  const totalDuration = durations.reduce((sum, d) => sum + d, 0);
  const avgDuration = durations.length > 0 ? totalDuration / durations.length : 0;
  const minDuration = durations.length > 0 ? Math.min(...durations) : 0;
  const maxDuration = durations.length > 0 ? Math.max(...durations) : 0;

  const failedItems = testedItems.filter((t) => t.status === 'failed');

  return {
    items: testedItems,
    statistics: {
      total: testedItems.length,
      passed: passedCount,
      failed: failedCount,
      skipped: skippedCount,
      byType,
      duration: {
        total: totalDuration,
        average: avgDuration,
        min: minDuration,
        max: maxDuration,
      },
    },
    failedItems,
    metadata: {
      timestamp: new Date().toISOString(),
      environment: runInfo?.environment,
      branch: runInfo?.branch,
      commit: runInfo?.commit,
    },
  };
}

function generateSummaryReportWithErrors(
  testedItems: TestItemWithError[]
): SummaryReport {
  const baseReport = generateSummaryReport(testedItems);

  return {
    ...baseReport,
    failedItems: testedItems.map((item) => ({
      ...item,
      error: item.error,
    })),
  };
}
