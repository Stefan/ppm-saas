import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization')
    
    if (!authHeader) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      )
    }
    
    // Try to fetch from backend, but provide fallback
    try {
      const response = await fetch(`${BACKEND_URL}/admin/cache/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': authHeader,
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      })
      
      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data, {
          status: 200,
          headers: {
            'X-Data-Source': 'backend-real'
          }
        })
      }
    } catch (fetchError) {
      console.log('Backend cache stats not available, using fallback')
    }
    
    // Fallback: Return in-memory cache info
    return NextResponse.json({
      type: 'in-memory',
      entries: 0,
      note: 'Using in-memory performance tracking'
    }, {
      status: 200,
      headers: {
        'X-Data-Source': 'fallback'
      }
    })
    
  } catch (error) {
    console.error('Cache stats API error:', error)
    return NextResponse.json(
      { 
        type: 'in-memory',
        error: 'Cache stats unavailable'
      },
      { status: 200 }
    )
  }
}
