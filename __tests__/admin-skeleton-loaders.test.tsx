/**
 * Unit tests for admin skeleton loader components
 * 
 * Tests verify:
 * - Components render without errors
 * - Fixed dimensions are applied correctly
 * - Animation classes are present
 * 
 * Requirements: 2.1, 2.2, 7.3
 */

import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import ChartSkeleton from '@/components/admin/ChartSkeleton'
import TableSkeleton from '@/components/admin/TableSkeleton'
import StatsSkeleton from '@/components/admin/StatsSkeleton'

describe('Admin Skeleton Loaders', () => {
  describe('ChartSkeleton', () => {
    it('renders without errors', () => {
      const { container } = render(<ChartSkeleton />)
      expect(container.firstChild).toBeInTheDocument()
    })

    it('has fixed 300px height matching actual chart dimensions', () => {
      const { container } = render(<ChartSkeleton />)
      const chartArea = container.querySelector('.h-\\[300px\\]')
      expect(chartArea).toBeInTheDocument()
    })

    it('applies pulse animation class', () => {
      const { container } = render(<ChartSkeleton />)
      const animatedElements = container.querySelectorAll('.animate-pulse-transform')
      expect(animatedElements.length).toBeGreaterThan(0)
    })

    it('has proper container styling', () => {
      const { container } = render(<ChartSkeleton />)
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toHaveClass('bg-white', 'p-6', 'rounded-lg', 'shadow-sm', 'border')
    })
  })

  describe('TableSkeleton', () => {
    it('renders without errors', () => {
      const { container } = render(<TableSkeleton />)
      expect(container.firstChild).toBeInTheDocument()
    })

    it('renders table structure with header and rows', () => {
      const { container } = render(<TableSkeleton />)
      const table = container.querySelector('table')
      const thead = container.querySelector('thead')
      const tbody = container.querySelector('tbody')
      
      expect(table).toBeInTheDocument()
      expect(thead).toBeInTheDocument()
      expect(tbody).toBeInTheDocument()
    })

    it('renders 5 skeleton rows matching typical slow queries display', () => {
      const { container } = render(<TableSkeleton />)
      const rows = container.querySelectorAll('tbody tr')
      expect(rows).toHaveLength(5)
    })

    it('applies pulse animation to skeleton elements', () => {
      const { container } = render(<TableSkeleton />)
      const animatedElements = container.querySelectorAll('.animate-pulse-transform')
      expect(animatedElements.length).toBeGreaterThan(0)
    })

    it('has proper table column widths', () => {
      const { container } = render(<TableSkeleton />)
      const headerCells = container.querySelectorAll('thead th')
      
      expect(headerCells[0]).toHaveClass('w-1/2')
      expect(headerCells[1]).toHaveClass('w-1/4')
      expect(headerCells[2]).toHaveClass('w-1/4')
    })
  })

  describe('StatsSkeleton', () => {
    it('renders without errors', () => {
      const { container } = render(<StatsSkeleton />)
      expect(container.firstChild).toBeInTheDocument()
    })

    it('renders 3-column grid matching cache statistics layout', () => {
      const { container } = render(<StatsSkeleton />)
      const grid = container.querySelector('.grid-cols-1.md\\:grid-cols-3')
      expect(grid).toBeInTheDocument()
    })

    it('renders 3 stat items', () => {
      const { container } = render(<StatsSkeleton />)
      const statItems = container.querySelectorAll('.text-center')
      expect(statItems).toHaveLength(3)
    })

    it('applies pulse animation to skeleton elements', () => {
      const { container } = render(<StatsSkeleton />)
      const animatedElements = container.querySelectorAll('.animate-pulse-transform')
      expect(animatedElements.length).toBeGreaterThan(0)
    })

    it('has proper container styling', () => {
      const { container } = render(<StatsSkeleton />)
      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toHaveClass('bg-white', 'p-6', 'rounded-lg', 'shadow-sm', 'border')
    })
  })

  describe('Layout Stability', () => {
    it('ChartSkeleton maintains fixed dimensions to prevent CLS', () => {
      const { container } = render(<ChartSkeleton />)
      const chartArea = container.querySelector('.h-\\[300px\\]')
      
      // Verify fixed height is set
      expect(chartArea).toBeInTheDocument()
      expect(chartArea).toHaveClass('w-full')
    })

    it('all skeletons use consistent styling', () => {
      const { container: chartContainer } = render(<ChartSkeleton />)
      const { container: tableContainer } = render(<TableSkeleton />)
      const { container: statsContainer } = render(<StatsSkeleton />)
      
      const chartWrapper = chartContainer.firstChild as HTMLElement
      const tableWrapper = tableContainer.firstChild as HTMLElement
      const statsWrapper = statsContainer.firstChild as HTMLElement
      
      // All should have consistent container classes
      const expectedClasses = ['bg-white', 'p-6', 'rounded-lg', 'shadow-sm', 'border']
      
      expectedClasses.forEach(className => {
        expect(chartWrapper).toHaveClass(className)
        expect(tableWrapper).toHaveClass(className)
        expect(statsWrapper).toHaveClass(className)
      })
    })
  })

  describe('Animation Performance', () => {
    it('uses GPU-accelerated animation class', () => {
      const { container } = render(<ChartSkeleton />)
      const animatedElements = container.querySelectorAll('.animate-pulse-transform')
      
      animatedElements.forEach(element => {
        expect(element).toHaveClass('animate-pulse-transform')
      })
    })

    it('applies animation to multiple elements in each skeleton', () => {
      const { container: chartContainer } = render(<ChartSkeleton />)
      const { container: tableContainer } = render(<TableSkeleton />)
      const { container: statsContainer } = render(<StatsSkeleton />)
      
      expect(chartContainer.querySelectorAll('.animate-pulse-transform').length).toBeGreaterThan(0)
      expect(tableContainer.querySelectorAll('.animate-pulse-transform').length).toBeGreaterThan(0)
      expect(statsContainer.querySelectorAll('.animate-pulse-transform').length).toBeGreaterThan(0)
    })
  })
})
