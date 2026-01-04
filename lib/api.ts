import { env } from './env'

// API configuration with fallbacks
export const API_CONFIG = {
  baseURL: env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
} as const

// API URL builder with validation
export function getApiUrl(endpoint: string): string {
  const baseUrl = API_CONFIG.baseURL
  
  if (!baseUrl) {
    console.warn('API_URL not configured, using localhost fallback')
    return `http://localhost:8000${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
  }
  
  // Ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  
  // Remove trailing slash from baseUrl and combine
  const cleanBaseUrl = baseUrl.replace(/\/$/, '')
  
  return `${cleanBaseUrl}${normalizedEndpoint}`
}

// Fetch wrapper with error handling
export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = getApiUrl(endpoint)
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...API_CONFIG.headers,
        ...options.headers,
      },
    })
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }
    
    const data = await response.json()
    return data as T
  } catch (error: unknown) {
    console.error('API request error:', error)
    throw error instanceof Error ? error : new Error('Unknown API error')
  }
}