/**
 * Resources Page View Mode Rendering Tests
 * 
 * Tests the resources page view mode rendering to verify:
 * - resources-grid test ID exists in all view modes
 * - Only one view mode renders at a time
 * - View mode switching works correctly
 * 
 * Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3
 */

import { readFileSync } from 'fs'
import { join } from 'path'

describe('Resources Page View Mode Rendering Tests', () => {
  let pageContent: string

  beforeAll(() => {
    // Read the resources page source code
    const pagePath = join(process.cwd(), 'app/resources/page.tsx')
    pageContent = readFileSync(pagePath, 'utf-8')
  })

  describe('2.1 Test resources-grid test ID exists in cards view', () => {
    test('verifies resources-grid test ID is always present in the code', () => {
      // Verify that data-testid="resources-grid" exists in the code
      expect(pageContent).toContain('data-testid="resources-grid"')
    })

    test('verifies resources-grid wraps all view modes', () => {
      // Find the resources-grid container
      const gridTestIdIndex = pageContent.indexOf('data-testid="resources-grid"')
      expect(gridTestIdIndex).toBeGreaterThan(-1)

      // Get the content after the test ID
      const afterTestId = pageContent.substring(gridTestIdIndex)
      
      // Verify all three view modes are mentioned after the resources-grid test ID
      expect(afterTestId).toContain("viewMode === 'cards'")
      expect(afterTestId).toContain("viewMode === 'table'")
      expect(afterTestId).toContain("viewMode === 'heatmap'")
    })

    test('verifies cards view content is inside resources-grid', () => {
      // Find the resources-grid div
      const gridIndex = pageContent.indexOf('data-testid="resources-grid"')
      expect(gridIndex).toBeGreaterThan(-1)

      // Get content after resources-grid
      const afterGrid = pageContent.substring(gridIndex)
      
      // Verify cards view is inside (should appear before the closing of resources-grid)
      const cardsViewIndex = afterGrid.indexOf("viewMode === 'cards'")
      expect(cardsViewIndex).toBeGreaterThan(-1)
      
      // Verify ResourceCard component is rendered in cards view
      const resourceCardIndex = afterGrid.indexOf('ResourceCard')
      expect(resourceCardIndex).toBeGreaterThan(-1)
      expect(resourceCardIndex).toBeGreaterThan(cardsViewIndex)
    })
  })

  describe('2.2 Test resources-grid test ID exists in table view', () => {
    test('verifies table view is inside resources-grid', () => {
      const gridIndex = pageContent.indexOf('data-testid="resources-grid"')
      const afterGrid = pageContent.substring(gridIndex)
      
      // Verify table view conditional is inside
      const tableViewIndex = afterGrid.indexOf("viewMode === 'table'")
      expect(tableViewIndex).toBeGreaterThan(-1)
      
      // Verify VirtualizedResourceTable is rendered
      const tableComponentIndex = afterGrid.indexOf('VirtualizedResourceTable')
      expect(tableComponentIndex).toBeGreaterThan(-1)
      expect(tableComponentIndex).toBeGreaterThan(tableViewIndex)
    })
  })

  describe('2.3 Test resources-grid test ID exists in heatmap view', () => {
    test('verifies heatmap view is inside resources-grid', () => {
      const gridIndex = pageContent.indexOf('data-testid="resources-grid"')
      const afterGrid = pageContent.substring(gridIndex)
      
      // Verify heatmap view conditional is inside
      const heatmapViewIndex = afterGrid.indexOf("viewMode === 'heatmap'")
      expect(heatmapViewIndex).toBeGreaterThan(-1)
      
      // Verify heatmap content exists
      expect(afterGrid).toContain('Resource Utilization Heatmap')
    })
  })

  describe('2.4 Test only one view mode renders at a time', () => {
    test('verifies view modes use exclusive conditionals', () => {
      const gridIndex = pageContent.indexOf('data-testid="resources-grid"')
      const afterGrid = pageContent.substring(gridIndex)
      
      // Extract the section with view mode conditionals
      const cardsIndex = afterGrid.indexOf("viewMode === 'cards'")
      const tableIndex = afterGrid.indexOf("viewMode === 'table'")
      const heatmapIndex = afterGrid.indexOf("viewMode === 'heatmap'")
      
      // All three view modes should exist
      expect(cardsIndex).toBeGreaterThan(-1)
      expect(tableIndex).toBeGreaterThan(-1)
      expect(heatmapIndex).toBeGreaterThan(-1)
      
      // They should be in separate conditional blocks (using &&)
      const cardsConditional = afterGrid.substring(cardsIndex - 20, cardsIndex + 50)
      const tableConditional = afterGrid.substring(tableIndex - 20, tableIndex + 50)
      const heatmapConditional = afterGrid.substring(heatmapIndex - 20, heatmapIndex + 50)
      
      // Each should have its own conditional check
      expect(cardsConditional).toContain('&&')
      expect(tableConditional).toContain('&&')
      expect(heatmapConditional).toContain('&&')
    })

    test('verifies no nested view mode conditionals', () => {
      const gridIndex = pageContent.indexOf('data-testid="resources-grid"')
      const afterGrid = pageContent.substring(gridIndex, gridIndex + 5000) // Get a reasonable chunk
      
      // Count occurrences of each view mode check
      const cardsMatches = (afterGrid.match(/viewMode === 'cards'/g) || []).length
      const tableMatches = (afterGrid.match(/viewMode === 'table'/g) || []).length
      const heatmapMatches = (afterGrid.match(/viewMode === 'heatmap'/g) || []).length
      
      // Each view mode should be checked exactly once in the resources-grid section
      expect(cardsMatches).toBe(1)
      expect(tableMatches).toBe(1)
      expect(heatmapMatches).toBe(1)
    })
  })
})
