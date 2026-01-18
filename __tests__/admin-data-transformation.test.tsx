/**
 * Unit Tests: Data Transformation Edge Cases
 * Feature: admin-performance-optimization
 * Tests empty data handling, malformed data handling, and large dataset performance
 * 
 * Validates: Requirements 8.5
 */

describe('Admin Performance Data Transformation', () => {
  // Helper function to simulate the endpoint data transformation
  const transformEndpointData = (stats: any) => {
    if (!stats?.endpoint_stats) return []
    
    return Object.entries(stats.endpoint_stats).map(([endpoint, data]: [string, any]) => ({
      endpoint: endpoint.length > 30 ? endpoint.substring(0, 30) + '...' : endpoint,
      fullEndpoint: endpoint,
      avg_duration: Math.round(data.avg_duration * 1000),
      requests: data.total_requests,
      error_rate: data.error_rate,
      rpm: data.requests_per_minute
    })).slice(0, 10)
  }

  // Helper function to simulate slow queries transformation
  const transformSlowQueries = (stats: any) => {
    if (!stats?.recent_slow_queries) return []
    
    return stats.recent_slow_queries.map((query: any) => ({
      endpoint: query.endpoint,
      duration: Math.round(query.duration * 1000),
      time: new Date(query.timestamp).toLocaleTimeString()
    }))
  }

  describe('Empty Data Handling', () => {
    it('should handle empty endpoint_stats gracefully', () => {
      const mockEmptyStats = {
        endpoint_stats: {},
        total_requests: 0,
        total_errors: 0,
        slow_queries_count: 0,
        recent_slow_queries: []
      }

      const result = transformEndpointData(mockEmptyStats)
      expect(result).toEqual([])
    })

    it('should handle null stats gracefully', () => {
      const result = transformEndpointData(null)
      expect(result).toEqual([])
    })

    it('should handle undefined stats gracefully', () => {
      const result = transformEndpointData(undefined)
      expect(result).toEqual([])
    })

    it('should handle empty recent_slow_queries array', () => {
      const mockStats = {
        endpoint_stats: {
          '/api/test': {
            total_requests: 100,
            avg_duration: 0.5,
            min_duration: 0.1,
            max_duration: 1.0,
            error_rate: 0,
            requests_per_minute: 10
          }
        },
        total_requests: 100,
        total_errors: 0,
        slow_queries_count: 0,
        recent_slow_queries: []
      }

      const result = transformSlowQueries(mockStats)
      expect(result).toEqual([])
    })

    it('should handle missing recent_slow_queries field', () => {
      const mockStats = {
        endpoint_stats: {},
        total_requests: 0,
        total_errors: 0,
        slow_queries_count: 0
      }

      const result = transformSlowQueries(mockStats)
      expect(result).toEqual([])
    })
  })

  describe('Malformed Data Handling', () => {
    it('should handle malformed endpoint_stats structure', () => {
      const mockMalformedStats = {
        endpoint_stats: {
          '/api/test': {
            // Missing required fields
            total_requests: 100
          }
        },
        total_requests: 100,
        total_errors: 0,
        slow_queries_count: 0,
        recent_slow_queries: []
      }

      const result = transformEndpointData(mockMalformedStats)
      
      // Should not crash, but may have NaN values
      expect(result).toHaveLength(1)
      expect(result[0].endpoint).toBe('/api/test')
      expect(result[0].requests).toBe(100)
    })

    it('should handle invalid timestamp in slow queries', () => {
      const mockStats = {
        endpoint_stats: {},
        total_requests: 0,
        total_errors: 0,
        slow_queries_count: 1,
        recent_slow_queries: [
          {
            endpoint: '/api/test',
            duration: 2.5,
            timestamp: 'invalid-timestamp'
          }
        ]
      }

      const result = transformSlowQueries(mockStats)
      
      // Should not crash
      expect(result).toHaveLength(1)
      expect(result[0].endpoint).toBe('/api/test')
      expect(result[0].duration).toBe(2500)
    })

    it('should handle missing fields in slow queries', () => {
      const mockStats = {
        endpoint_stats: {},
        total_requests: 0,
        total_errors: 0,
        slow_queries_count: 1,
        recent_slow_queries: [
          {
            endpoint: '/api/test'
            // Missing duration and timestamp
          }
        ]
      }

      const result = transformSlowQueries(mockStats)
      
      // Should not crash
      expect(result).toHaveLength(1)
      expect(result[0].endpoint).toBe('/api/test')
    })
  })

  describe('Large Dataset Performance', () => {
    it('should handle large endpoint_stats efficiently', () => {
      // Generate 100 endpoints
      const largeEndpointStats: Record<string, any> = {}
      for (let i = 0; i < 100; i++) {
        largeEndpointStats[`/api/endpoint-${i}`] = {
          total_requests: Math.floor(Math.random() * 1000),
          avg_duration: Math.random() * 2,
          min_duration: Math.random() * 0.5,
          max_duration: Math.random() * 5,
          error_rate: Math.random() * 10,
          requests_per_minute: Math.random() * 50
        }
      }

      const mockLargeStats = {
        endpoint_stats: largeEndpointStats,
        total_requests: 10000,
        total_errors: 50,
        slow_queries_count: 10,
        recent_slow_queries: []
      }

      const startTime = performance.now()
      const result = transformEndpointData(mockLargeStats)
      const endTime = performance.now()
      const transformTime = endTime - startTime

      // Should transform within reasonable time (< 100ms)
      expect(transformTime).toBeLessThan(100)
      
      // Should limit to 10 items
      expect(result).toHaveLength(10)
    })

    it('should limit endpoint data to 10 items', () => {
      // Generate 50 endpoints
      const largeEndpointStats: Record<string, any> = {}
      for (let i = 0; i < 50; i++) {
        largeEndpointStats[`/api/endpoint-${i}`] = {
          total_requests: 100,
          avg_duration: 0.5,
          min_duration: 0.1,
          max_duration: 1.0,
          error_rate: 0,
          requests_per_minute: 10
        }
      }

      const mockStats = {
        endpoint_stats: largeEndpointStats,
        total_requests: 5000,
        total_errors: 0,
        slow_queries_count: 0,
        recent_slow_queries: []
      }

      const result = transformEndpointData(mockStats)
      
      // Should limit to 10 items
      expect(result).toHaveLength(10)
    })

    it('should handle very long endpoint names', () => {
      const veryLongEndpoint = '/api/' + 'a'.repeat(200)
      
      const mockStats = {
        endpoint_stats: {
          [veryLongEndpoint]: {
            total_requests: 100,
            avg_duration: 0.5,
            min_duration: 0.1,
            max_duration: 1.0,
            error_rate: 0,
            requests_per_minute: 10
          }
        },
        total_requests: 100,
        total_errors: 0,
        slow_queries_count: 0,
        recent_slow_queries: []
      }

      const result = transformEndpointData(mockStats)
      
      // Should truncate long endpoint names
      expect(result).toHaveLength(1)
      expect(result[0].endpoint.length).toBeLessThanOrEqual(33) // 30 chars + '...'
      expect(result[0].fullEndpoint).toBe(veryLongEndpoint)
    })

    it('should convert durations from seconds to milliseconds', () => {
      const mockStats = {
        endpoint_stats: {
          '/api/test': {
            total_requests: 100,
            avg_duration: 1.5, // 1.5 seconds
            min_duration: 0.1,
            max_duration: 3.0,
            error_rate: 0,
            requests_per_minute: 10
          }
        },
        total_requests: 100,
        total_errors: 0,
        slow_queries_count: 0,
        recent_slow_queries: []
      }

      const result = transformEndpointData(mockStats)
      
      expect(result[0].avg_duration).toBe(1500) // Converted to ms
    })

    it('should handle many slow queries efficiently', () => {
      const manySlowQueries = []
      for (let i = 0; i < 100; i++) {
        manySlowQueries.push({
          endpoint: `/api/endpoint-${i}`,
          duration: Math.random() * 5,
          timestamp: new Date().toISOString()
        })
      }

      const mockStats = {
        endpoint_stats: {},
        total_requests: 0,
        total_errors: 0,
        slow_queries_count: 100,
        recent_slow_queries: manySlowQueries
      }

      const startTime = performance.now()
      const result = transformSlowQueries(mockStats)
      const endTime = performance.now()
      const transformTime = endTime - startTime

      // Should transform within reasonable time (< 100ms)
      expect(transformTime).toBeLessThan(100)
      expect(result).toHaveLength(100)
    })
  })
})
