// Debug script to check environment variables
console.log('🔍 Environment Variable Diagnostics')
console.log('===================================')

console.log('\n📋 Raw Environment Variables:')
console.log('NEXT_PUBLIC_SUPABASE_URL:', process.env.NEXT_PUBLIC_SUPABASE_URL || 'UNDEFINED')
console.log('NEXT_PUBLIC_SUPABASE_ANON_KEY length:', process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.length || 0)
console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL || 'UNDEFINED')

if (process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  console.log('\n🔑 API Key Analysis:')
  console.log('- Length:', key.length)
  console.log('- Starts with:', key.substring(0, 20))
  console.log('- Contains "NEXT_PUBLIC":', key.includes('NEXT_PUBLIC'))
  console.log('- Contains "=":', key.includes('='))
  console.log('- JWT format (3 parts):', key.split('.').length === 3)
  
  // Try to decode JWT payload
  try {
    const parts = key.split('.')
    if (parts.length === 3) {
      const payload = JSON.parse(atob(parts[1]))
      console.log('\n📄 JWT Payload:')
      console.log('- Issuer:', payload.iss)
      console.log('- Reference:', payload.ref)
      console.log('- Role:', payload.role)
      console.log('- Issued at:', new Date(payload.iat * 1000).toISOString())
      console.log('- Expires at:', new Date(payload.exp * 1000).toISOString())
      
      const now = Math.floor(Date.now() / 1000)
      console.log('- Current time:', new Date(now * 1000).toISOString())
      console.log('- Is expired:', payload.exp < now)
      console.log('- Time until expiry (days):', Math.floor((payload.exp - now) / 86400))
    }
  } catch (error) {
    console.log('❌ JWT decode error:', error.message)
  }
}

console.log('\n🌍 Environment Context:')
console.log('- NODE_ENV:', process.env.NODE_ENV)
console.log('- VERCEL:', process.env.VERCEL)
console.log('- VERCEL_ENV:', process.env.VERCEL_ENV)

// Check if we're in Vercel deployment
if (process.env.VERCEL) {
  console.log('\n⚠️ RUNNING IN VERCEL DEPLOYMENT')
  console.log('Environment variables are loaded from Vercel dashboard, not .env.local')
  console.log('To fix: Update environment variables in Vercel dashboard')
} else {
  console.log('\n🏠 RUNNING LOCALLY')
  console.log('Environment variables loaded from .env.local file')
}