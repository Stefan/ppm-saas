# 🚨 VERCEL ENVIRONMENT VARIABLE FIX GUIDE

## Problem Diagnosis
The error "Invalid API key detected" indicates that Vercel is still using corrupted environment variables from the dashboard, which override the local `.env.local` file.

## 🎯 **IMMEDIATE FIX REQUIRED**

### Step 1: Clean Vercel Environment Variables

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Select your project**: `orka-ppm` 
3. **Navigate to**: Settings → Environment Variables
4. **DELETE ALL existing environment variables**:
   - Delete `NEXT_PUBLIC_SUPABASE_URL`
   - Delete `NEXT_PUBLIC_SUPABASE_ANON_KEY` 
   - Delete `NEXT_PUBLIC_API_URL`

### Step 2: Add Clean Environment Variables

**Add these EXACT values** (copy-paste carefully):

```
NEXT_PUBLIC_SUPABASE_URL=https://xceyrfvxooiplbmwavlb.supabase.co
```

```
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo
```

```
NEXT_PUBLIC_API_URL=https://orka-ppm.onrender.com
```

### Step 3: Redeploy

1. **Trigger redeploy** in Vercel dashboard
2. **OR** push any small change to GitHub to trigger auto-deploy

## 🔍 **Validation Steps**

After redeployment:

1. **Visit**: https://orka-ppm.vercel.app
2. **Open browser console** (F12)
3. **Look for**: "✅ Environment variables processed successfully"
4. **Should NOT see**: "❌ CONFIGURATION ERROR" or "Invalid API key"

## 🚨 **Common Mistakes to Avoid**

❌ **DON'T**: Copy variable names (NEXT_PUBLIC_SUPABASE_URL=...)
✅ **DO**: Copy only the values

❌ **DON'T**: Add quotes around values
✅ **DO**: Paste raw values without quotes

❌ **DON'T**: Add spaces before/after values
✅ **DO**: Ensure clean, trimmed values

## 🔧 **Alternative: Force Override Method**

If Vercel environment variables are still problematic, we can force override them in the code:

```typescript
// In frontend/lib/supabase.ts - add at the top
const FORCE_OVERRIDE = true;

if (FORCE_OVERRIDE) {
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://xceyrfvxooiplbmwavlb.supabase.co';
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo';
  process.env.NEXT_PUBLIC_API_URL = 'https://orka-ppm.onrender.com';
}
```

## 📊 **Expected Results**

After fix:
- ✅ No "Invalid API key" errors
- ✅ Authentication works properly
- ✅ Dashboard loads without "Failed to fetch"
- ✅ Console shows successful environment variable processing

## 🆘 **If Still Failing**

1. Check browser console for specific error messages
2. Run the debug script: `node debug_env_vars.js`
3. Verify JWT token is not expired
4. Check CORS headers in Network tab

---

**Priority**: 🔥 **CRITICAL** - Must fix before authentication will work
**Estimated Time**: 5-10 minutes
**Difficulty**: Easy (just copy-paste values correctly)