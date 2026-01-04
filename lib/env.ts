// Environment variables validation and fallbacks
export const env = {
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
} as const;

// Runtime validation
export function validateEnv() {
  const requiredEnvs = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  ] as const;

  const missing = requiredEnvs.filter(key => !env[key]);
  
  if (missing.length > 0) {
    console.error('Missing required environment variables:', missing);
    if (typeof window === 'undefined') {
      // Server-side: throw error
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    } else {
      // Client-side: log warning but don't crash
      console.warn('Some environment variables are missing. App may not work correctly.');
    }
  }
  
  return env;
}

// Validate on module load
validateEnv();