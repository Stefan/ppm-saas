/**
 * Minimal Supabase Configuration
 * Provides basic Supabase client setup and environment configuration
 */

import { createClient } from '@supabase/supabase-js'
import type { SupabaseClient } from '@supabase/supabase-js'

// Environment configuration
export const ENV_CONFIG = {
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
} as const

// Validate required environment variables
const hasValidConfig = !!(ENV_CONFIG.supabaseUrl && ENV_CONFIG.supabaseAnonKey &&
  ENV_CONFIG.supabaseUrl !== 'https://placeholder.supabase.co' &&
  ENV_CONFIG.supabaseAnonKey !== 'placeholder-anon-key')

// Only warn in production or after initial module load to avoid false warnings during dev server startup
if (!hasValidConfig && typeof window !== 'undefined') {
  console.warn('⚠️ Missing or invalid Supabase environment variables. Authentication will not work.')
  console.warn('Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file')
}

// Create Supabase client with fallback for missing environment variables
export const supabase: SupabaseClient = hasValidConfig
  ? createClient(
      ENV_CONFIG.supabaseUrl,
      ENV_CONFIG.supabaseAnonKey,
      {
        auth: {
          autoRefreshToken: true,
          persistSession: true,
          detectSessionInUrl: true,
          storage: typeof window !== 'undefined' ? window.localStorage : undefined,
          storageKey: 'supabase.auth.token',
        },
        realtime: {
          params: {
            eventsPerSecond: 10
          }
        }
      }
    )
  : createClient(
      'https://placeholder.supabase.co', // Placeholder URL
      'placeholder-anon-key', // Placeholder key
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
          detectSessionInUrl: false
        }
      }
    )

// Database types (basic)
export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          email: string
          full_name: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          avatar_url?: string | null
          updated_at?: string
        }
      }
      projects: {
        Row: {
          id: string
          name: string
          description: string | null
          owner_id: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          owner_id: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          owner_id?: string
          updated_at?: string
        }
      }
    }
  }
}

// Utility functions
export const getUser = async () => {
  const { data: { user }, error } = await supabase.auth.getUser()
  if (error) {
    console.error('Error getting user:', error)
    return null
  }
  return user
}

export const getSession = async () => {
  const { data: { session }, error } = await supabase.auth.getSession()
  if (error) {
    console.error('Error getting session:', error)
    return null
  }
  return session
}

export const signOut = async () => {
  const { error } = await supabase.auth.signOut()
  if (error) {
    console.error('Error signing out:', error)
    throw error
  }
}

// Export default client
export default supabase