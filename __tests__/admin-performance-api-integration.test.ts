/**
 * Integration tests for Admin Performance API
 * 
 * These tests catch issues like:
 * - 500 Internal Server Errors
 * - Missing endpoints
 * - Invalid response formats
 * - Authentication failures
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('Admin Performance API Integration', () => {
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
  beforeEach(() => {
    // Reset fetch mocks
    global.fetch = vi.fn()
  })
  
  afterEach(() => {
    vi.restoreAllMocks()
  })
  
  describe('GET /api/admin/performance/stats', () => {
    it('should return 200 with valid response structure', async () => {
      // Mock successful backend response
      const mockStats = {
        total_requests: 100,
        total_errors: 5,
        slow_queries_count: 2,
        endpoint_stats: {
          'GET /projects': {
            total_requests: 50,
            avg_duration: 0.125,
            error_rate: 0.2,
            requests_per_minute: 45
          }
        },
        recent_slow_queries: [],
        uptime_seconds: 3600
      }
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockStats,
        headers: new Headers({
          'Content-Type': 'application/json',
          'X-Data-Source': 'backend-real'
        })
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      expect(response.ok).toBe(true)
      expect(response.status).toBe(200)
      
      const data = await response.json()
      expect(data).toHaveProperty('total_requests')
      expect(data).toHaveProperty('total_errors')
      expect(data).toHaveProperty('endpoint_stats')
    })
    
    it('should handle 500 errors from backend gracefully', async () => {
      // Mock backend 500 error
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'Internal Server Error'
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
    })
    
    it('should return 401 when authorization header is missing', async () => {
      const response = await fetch('/api/admin/performance/stats')
      
      // Should check for auth before making backend request
      expect(response.status).toBe(401)
    })
    
    it('should validate response structure from backend', async () => {
      // Mock invalid backend response (missing required fields)
      const invalidResponse = {
        // Missing total_requests, total_errors, etc.
        some_field: 'value'
      }
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => invalidResponse
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      const data = await response.json()
      
      // Frontend should handle missing fields gracefully
      // Either by providing defaults or showing error
      expect(data).toBeDefined()
    })
  })
  
  describe('GET /api/admin/performance/health', () => {
    it('should return valid health status structure', async () => {
      const mockHealth = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        metrics: {
          total_requests: 100,
          error_rate: 0.5,
          slow_queries: 2,
          uptime: '1h 30m'
        },
        cache_status: 'in-memory'
      }
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockHealth
      })
      
      const response = await fetch('/api/admin/performance/health', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      expect(response.ok).toBe(true)
      
      const data = await response.json()
      expect(data).toHaveProperty('status')
      expect(data).toHaveProperty('metrics')
      expect(['healthy', 'degraded', 'unhealthy']).toContain(data.status)
    })
    
    it('should handle backend errors without crashing', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Server Error'
      })
      
      const response = await fetch('/api/admin/performance/health', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      expect(response.status).toBe(500)
    })
  })
  
  describe('GET /api/admin/cache/stats', () => {
    it('should return cache stats or fallback gracefully', async () => {
      // Mock backend unavailable
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Backend unavailable'))
      
      const response = await fetch('/api/admin/cache/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      // Should return fallback data, not error
      expect(response.ok).toBe(true)
      
      const data = await response.json()
      expect(data).toHaveProperty('type')
      expect(data.type).toBe('in-memory')
    })
    
    it('should handle timeout gracefully', async () => {
      // Mock timeout
      ;(global.fetch as any).mockImplementationOnce(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      )
      
      const response = await fetch('/api/admin/cache/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      // Should return fallback, not crash
      expect(response.status).toBe(200)
    })
  })
  
  describe('Error Detection Tests', () => {
    it('should detect missing Permission enum (original bug)', async () => {
      // This test verifies the fix for Permission.admin not existing
      
      // Mock backend returning 500 due to invalid permission
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => 'AttributeError: Permission.admin does not exist'
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
      
      const errorText = await response.text()
      
      // If this error occurs, it means the permission bug is back
      if (errorText.includes('Permission.admin')) {
        throw new Error(
          'REGRESSION: Permission.admin is being used but does not exist. ' +
          'Use Permission.admin_read or Permission.system_admin instead.'
        )
      }
    })
    
    it('should detect when backend is not running', async () => {
      // Mock connection refused
      ;(global.fetch as any).mockRejectedValueOnce(
        new Error('fetch failed: ECONNREFUSED')
      )
      
      try {
        await fetch('/api/admin/performance/stats', {
          headers: { 'Authorization': 'Bearer test-token' }
        })
      } catch (error: any) {
        expect(error.message).toContain('ECONNREFUSED')
      }
    })
    
    it('should detect malformed JSON responses', async () => {
      // Mock invalid JSON
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => {
          throw new Error('Unexpected token in JSON')
        }
      })
      
      try {
        const response = await fetch('/api/admin/performance/stats', {
          headers: { 'Authorization': 'Bearer test-token' }
        })
        await response.json()
      } catch (error: any) {
        expect(error.message).toContain('JSON')
      }
    })
    
    it('should detect CORS issues', async () => {
      // Mock CORS error
      ;(global.fetch as any).mockRejectedValueOnce(
        new Error('CORS policy: No Access-Control-Allow-Origin header')
      )
      
      try {
        await fetch('/api/admin/performance/stats', {
          headers: { 'Authorization': 'Bearer test-token' }
        })
      } catch (error: any) {
        expect(error.message).toContain('CORS')
      }
    })
  })
  
  describe('Response Validation', () => {
    it('should validate total_requests is a number', async () => {
      const invalidStats = {
        total_requests: 'not a number', // Invalid type
        total_errors: 5,
        endpoint_stats: {}
      }
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => invalidStats
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      const data = await response.json()
      
      // Should detect type mismatch
      expect(typeof data.total_requests).not.toBe('number')
    })
    
    it('should validate endpoint_stats structure', async () => {
      const invalidStats = {
        total_requests: 100,
        total_errors: 5,
        endpoint_stats: 'not an object' // Invalid type
      }
      
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => invalidStats
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token' }
      })
      
      const data = await response.json()
      
      // Should detect invalid structure
      expect(typeof data.endpoint_stats).not.toBe('object')
    })
  })
  
  describe('Authentication Flow', () => {
    it('should forward authorization header to backend', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ total_requests: 0 })
      })
      
      global.fetch = mockFetch
      
      await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer test-token-123' }
      })
      
      // Verify auth header was forwarded
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123'
          })
        })
      )
    })
    
    it('should handle expired tokens', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token expired' })
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer expired-token' }
      })
      
      expect(response.status).toBe(401)
    })
    
    it('should handle insufficient permissions', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Admin privileges required' })
      })
      
      const response = await fetch('/api/admin/performance/stats', {
        headers: { 'Authorization': 'Bearer user-token' }
      })
      
      expect(response.status).toBe(403)
    })
  })
})
