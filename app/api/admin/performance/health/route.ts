import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// Fallback mock data
function getMockHealth() {
  return {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    metrics: {
      total_requests: 0,
      error_rate: 0,
      slow_queries: 0,
      uptime: '0h 0m'
    },
    cache_status: 'in-memory'
  }
}

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }
    
    // Try to forward request to backend with timeout
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000) // 3 second timeout
      
      const response = await fetch(`${BACKEND_URL}/admin/performance/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
        },
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data, {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'X-Data-Source': 'backend-real'
          },
        })
      }
      
      console.error('Backend performance health API error:', response.status, response.statusText)
      
    } catch (fetchError: any) {
      console.log('Backend not available, using fallback data:', fetchError.message)
    }
    
    // Return fallback mock data
    return NextResponse.json(getMockHealth(), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Data-Source': 'fallback-mock',
        'X-Backend-Status': 'unavailable'
      },
    })
    
  } catch (error) {
    console.error('Performance health API error:', error)
    
    // Return fallback data even on error
    return NextResponse.json(getMockHealth(), {
      status: 200,
      headers: {
        'X-Data-Source': 'fallback-error'
      }
    })
  }
}
