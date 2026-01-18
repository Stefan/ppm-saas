/**
 * Unit tests for CacheStatsCard component
 * 
 * Tests verify:
 * - Component renders without errors
 * - Displays cache statistics correctly
 * - Handles different cache types (redis vs memory)
 * - Returns null when no data provided
 * - Proper styling and layout
 * 
 * Requirements: 3.4, 8.2
 */

import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import CacheStatsCard from '@/components/admin/CacheStatsCard'

describe('CacheStatsCard', () => {
  const mockTranslations = {
    cacheStatistics: 'Cache Statistics',
    cacheType: 'Cache Type',
    hitRate: 'Hit Rate',
    memoryUsed: 'Memory Used',
    cacheEntries: 'Cache Entries',
    timestamps: 'Timestamps'
  }

  const mockRedisStats = {
    type: 'redis',
    hit_rate: 85,
    used_memory: '2.5MB',
    keyspace_hits: 1000,
    keyspace_misses: 150
  }

  const mockMemoryStats = {
    type: 'memory',
    entries: 42,
    timestamps: 15
  }

  it('renders without errors with redis cache data', () => {
    const { container } = render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    expect(container).toBeInTheDocument()
  })

  it('displays cache statistics title', () => {
    render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('Cache Statistics')).toBeInTheDocument()
  })

  it('displays redis cache type correctly', () => {
    render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('REDIS')).toBeInTheDocument()
    expect(screen.getByText('Cache Type')).toBeInTheDocument()
  })

  it('displays redis-specific metrics', () => {
    render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('Hit Rate')).toBeInTheDocument()
    expect(screen.getByText('2.5MB')).toBeInTheDocument()
    expect(screen.getByText('Memory Used')).toBeInTheDocument()
  })

  it('displays memory cache type correctly', () => {
    render(
      <CacheStatsCard 
        cacheStats={mockMemoryStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('MEMORY')).toBeInTheDocument()
  })

  it('displays memory-specific metrics', () => {
    render(
      <CacheStatsCard 
        cacheStats={mockMemoryStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('Cache Entries')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('Timestamps')).toBeInTheDocument()
  })

  it('returns null when cacheStats is null', () => {
    const { container } = render(
      <CacheStatsCard 
        cacheStats={null}
        translations={mockTranslations}
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it('has proper grid layout structure', () => {
    const { container } = render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    const gridElement = container.querySelector('.grid.grid-cols-1.md\\:grid-cols-3')
    expect(gridElement).toBeInTheDocument()
  })

  it('applies proper styling to container', () => {
    const { container } = render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    const cardElement = container.querySelector('.bg-white.p-6.rounded-lg.shadow-sm.border.border-gray-200')
    expect(cardElement).toBeInTheDocument()
  })

  it('displays cache type in blue color', () => {
    const { container } = render(
      <CacheStatsCard 
        cacheStats={mockRedisStats}
        translations={mockTranslations}
      />
    )
    const cacheTypeElement = container.querySelector('.text-blue-600')
    expect(cacheTypeElement).toHaveTextContent('REDIS')
  })

  it('handles missing optional fields gracefully', () => {
    const minimalStats = {
      type: 'redis'
    }
    render(
      <CacheStatsCard 
        cacheStats={minimalStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('REDIS')).toBeInTheDocument()
    expect(screen.getByText('0%')).toBeInTheDocument() // Default hit_rate
    expect(screen.getByText('N/A')).toBeInTheDocument() // Default used_memory
  })

  it('displays unknown cache type when type is missing', () => {
    const unknownStats = {
      type: ''
    }
    render(
      <CacheStatsCard 
        cacheStats={unknownStats}
        translations={mockTranslations}
      />
    )
    expect(screen.getByText('UNKNOWN')).toBeInTheDocument()
  })
})
