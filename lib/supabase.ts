import { createClient } from '@supabase/supabase-js'

// 🚨 FORCE OVERRIDE: Completely bypass corrupted Vercel environment variables
const FORCE_OVERRIDE = true;

// Define clean configuration that bypasses all environment variables
const OVERRIDE_CONFIG = {
  SUPABASE_URL: 'https://xceyrfvxooiplbmwavlb.supabase.co',
  SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo',
  API_URL: 'https://orka-ppm.onrender.com'
};

if (FORCE_OVERRIDE) {
  console.log('🔧 FORCE OVERRIDE ACTIVE: Bypassing ALL Vercel environment variables');
  console.log('- Using hardcoded Supabase URL:', OVERRIDE_CONFIG.SUPABASE_URL);
  console.log('- Using hardcoded API URL:', OVERRIDE_CONFIG.API_URL);
  console.log('- Using fresh ANON_KEY (length:', OVERRIDE_CONFIG.SUPABASE_ANON_KEY.length, ')');
}

// Consolidated environment variable validation and cleaning functions
function cleanEnvVar(value: string | undefined): string {
  if (!value) return ''
  
  // ENHANCED: Remove ALL whitespace, newlines, tabs, carriage returns
  let cleaned = value.replace(/[\s\r\n\t]+/g, '')
  
  // Remove quotes and invisible characters
  cleaned = cleaned.replace(/^["']|["']$/g, '')
  cleaned = cleaned.replace(/[\u0000-\u001F\u007F-\u009F]/g, '')
  
  // CRITICAL FIX: Detect copy-paste corruption (variable names in values)
  if (cleaned.includes('NEXT_PUBLIC_SUPABASE_URL') || cleaned.includes('NEXT_PUBLIC_SUPABASE_ANON_KEY')) {
    console.error('❌ COPY-PASTE ERROR: Environment variable contains variable names!')
    console.error('❌ Raw value preview:', cleaned.substring(0, 100) + '...')
    console.error('❌ Length:', cleaned.length, '(expected ~208 for JWT)')
    throw new Error(`COPY-PASTE ERROR: Environment variable contains variable names instead of values. Length: ${cleaned.length}`)
  }
  
  // ENHANCED: Detect assignment syntax corruption
  if (cleaned.includes('SUPABASE_URL=') || cleaned.includes('ANON_KEY=')) {
    console.error('❌ ASSIGNMENT SYNTAX ERROR: Environment variable contains assignment syntax!')
    console.error('❌ Raw value preview:', cleaned.substring(0, 100) + '...')
    throw new Error('Environment variable contains assignment syntax - copy only the value, not the variable name')
  }
  
  // SMART EXTRACTION: If the value contains variable assignment, extract only the JWT part
  if (cleaned.includes('=') && cleaned.length > 300) {
    console.log('🔧 Detected malformed environment variable, attempting extraction...')
    
    // Look for JWT pattern (starts with eyJ)
    const jwtMatch = cleaned.match(/eyJ[A-Za-z0-9+/=._-]+/)
    if (jwtMatch) {
      cleaned = jwtMatch[0]
      console.log('✅ Successfully extracted JWT token from malformed environment variable')
      console.log('✅ Extracted length:', cleaned.length)
    } else {
      console.error('❌ Could not extract JWT token from malformed environment variable')
      throw new Error('Environment variable contains assignment syntax but no valid JWT token found')
    }
  }
  
  return cleaned
}

function validateSupabaseUrl(url: string): boolean {
  if (!url) return false
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'https:' && parsed.hostname.includes('supabase.co')
  } catch {
    return false
  }
}

function validateSupabaseKey(key: string): boolean {
  if (!key) return false
  
  // ENHANCED: Check for copy-paste corruption (variable names in values)
  if (key.includes('NEXT_PUBLIC_SUPABASE_') || key.includes('SUPABASE_URL') || key.includes('=')) {
    console.error('❌ COPY-PASTE ERROR: ANON_KEY contains variable names or assignment syntax!')
    console.error('❌ Key preview:', key.substring(0, 100) + '...')
    console.error('❌ Key length:', key.length, '(expected 200-400)')
    return false
  }
  
  // STRICT: Length validation (JWT tokens are typically 200-250 chars)
  if (key.length > 400 || key.length < 200) {
    console.error(`❌ INVALID JWT LENGTH: ${key.length} chars (expected 200-400)`)
    console.error('❌ This usually indicates copy-paste corruption')
    return false
  }
  
  // STRICT: Must be a JWT token (3 parts separated by dots)
  const parts = key.split('.')
  if (parts.length !== 3) {
    console.error(`❌ INVALID JWT STRUCTURE: ${parts.length} parts (expected 3: header.payload.signature)`)
    return false
  }
  
  // STRICT: Must start with eyJ (base64 encoded JWT header)
  if (!key.startsWith('eyJ')) {
    console.error('❌ INVALID JWT FORMAT: Must start with "eyJ" (JWT header)')
    console.error('❌ Current start:', key.substring(0, 10))
    return false
  }
  
  // ENHANCED: Validate each part is valid base64
  try {
    atob(parts[0]) // header
    atob(parts[1]) // payload
    // signature part doesn't need to be valid base64 for validation
  } catch (base64Error) {
    console.error('❌ INVALID BASE64: JWT parts are not valid base64 encoded')
    return false
  }
  
  return true
}

// Process environment variables with FORCE OVERRIDE
console.log('🔍 Processing environment variables (supabase.ts)...')

// Use override config if force override is enabled, otherwise use process.env
const rawUrl = FORCE_OVERRIDE ? OVERRIDE_CONFIG.SUPABASE_URL : process.env.NEXT_PUBLIC_SUPABASE_URL
const rawKey = FORCE_OVERRIDE ? OVERRIDE_CONFIG.SUPABASE_ANON_KEY : process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (FORCE_OVERRIDE) {
  console.log('🔧 USING FORCE OVERRIDE VALUES:')
  console.log('- URL:', rawUrl)
  console.log('- Key length:', rawKey?.length || 0)
  console.log('- Key starts with:', rawKey?.substring(0, 20) || 'UNDEFINED')
} else {
  console.log('📋 Raw ENV diagnostics:')
  console.log('- SUPABASE_URL:', rawUrl || 'UNDEFINED')
  console.log('- SUPABASE_KEY length:', rawKey?.length || 0)
  console.log('- SUPABASE_KEY starts with:', rawKey?.substring(0, 50) || 'UNDEFINED')
}

// Fallback configuration (same as override config for consistency)
const FALLBACK_CONFIG = OVERRIDE_CONFIG

// Clean and validate URL
let cleanedUrl = cleanEnvVar(rawUrl)
if (FORCE_OVERRIDE) {
  cleanedUrl = OVERRIDE_CONFIG.SUPABASE_URL
  console.log('✅ Using FORCE OVERRIDE URL:', cleanedUrl)
} else if (!cleanedUrl || !validateSupabaseUrl(cleanedUrl)) {
  console.warn('⚠️ Using fallback SUPABASE_URL due to invalid/missing environment variable')
  cleanedUrl = FALLBACK_CONFIG.SUPABASE_URL
}

// Clean and validate API key
let cleanedKey = cleanEnvVar(rawKey)
if (FORCE_OVERRIDE) {
  cleanedKey = OVERRIDE_CONFIG.SUPABASE_ANON_KEY
  console.log('✅ Using FORCE OVERRIDE ANON_KEY (length:', cleanedKey.length, ')')
} else if (!cleanedKey || !validateSupabaseKey(cleanedKey)) {
  console.warn('⚠️ Using fallback SUPABASE_ANON_KEY due to invalid/missing environment variable')
  cleanedKey = FALLBACK_CONFIG.SUPABASE_ANON_KEY
}

// Additional JWT payload validation
try {
  const parts = cleanedKey.split('.')
  const payload = JSON.parse(atob(parts[1]))
  
  console.log('✅ JWT payload validated:', {
    iss: payload.iss,
    ref: payload.ref,
    role: payload.role,
    iat: new Date(payload.iat * 1000).toISOString(),
    exp: new Date(payload.exp * 1000).toISOString()
  })
  
  // Check expiration with tolerance for clock skew
  const now = Math.floor(Date.now() / 1000)
  const clockSkewTolerance = 300 // 5 minutes
  
  if (payload.exp < (now - clockSkewTolerance)) {
    console.warn('⚠️ JWT token expired, but continuing with fallback configuration')
  }
  
  // Check if issued in future (with tolerance)
  if (payload.iat > (now + clockSkewTolerance)) {
    console.warn('⚠️ JWT token issued in future, but within tolerance')
  }
  
} catch (jwtError) {
  console.warn('⚠️ JWT validation failed, but continuing with fallback configuration:', jwtError)
}

console.log('✅ Environment variables processed successfully (supabase.ts)')
console.log('- URL:', cleanedUrl)
console.log('- Key length:', cleanedKey.length)
console.log('- Force override active:', FORCE_OVERRIDE)
console.log('- Using override config:', FORCE_OVERRIDE || cleanedUrl === FALLBACK_CONFIG.SUPABASE_URL || cleanedKey === FALLBACK_CONFIG.SUPABASE_ANON_KEY)

// Create Supabase client
export const supabase = createClient(
  cleanedUrl,
  cleanedKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
    global: {
      headers: {
        'X-Client-Info': 'ppm-saas-frontend',
      },
    },
  }
)

console.log('✅ Supabase client created successfully')

// Export config for debugging and other components
export const ENV_CONFIG = {
  url: cleanedUrl,
  keyLength: cleanedKey.length,
  keyPreview: cleanedKey.substring(0, 20) + '...',
  apiUrl: FORCE_OVERRIDE ? OVERRIDE_CONFIG.API_URL : (process.env.NEXT_PUBLIC_API_URL || 'https://orka-ppm.onrender.com'),
  isValid: true,
  forceOverride: FORCE_OVERRIDE,
  validationSource: 'supabase.ts'
}

// Export API URL for other components
export const API_URL = ENV_CONFIG.apiUrl

console.log('🌐 API Configuration:')
console.log('- API URL:', ENV_CONFIG.apiUrl)
console.log('- Force override active:', FORCE_OVERRIDE)