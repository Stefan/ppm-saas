# Fix: "Failed to execute 'fetch' on 'Window': Invalid value" Error

## Quick Diagnosis

The error occurs during authentication (sign-up/sign-in). I've added debugging tools to help identify the exact cause.

## Steps to Fix

### 1. Use the Debug Tools
1. Visit your application's login page
2. You'll see an "Authentication Debugger" section at the bottom
3. Click **"Run Diagnostics"** to check:
   - Environment variables are loaded
   - Supabase URL is valid
   - Supabase client is properly initialized
4. Click **"Test Auth"** to test the actual authentication

### 2. Check Environment Variables

**In Development (.env.local):**
```bash
NEXT_PUBLIC_SUPABASE_URL="https://xceyrfvxooiplbmwavlb.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo"
```

**In Production (Vercel Dashboard):**
- Go to Project Settings → Environment Variables
- Ensure the same variables are set for Production, Preview, and Development

### 3. Common Issues & Solutions

#### Issue: Environment Variables Not Loading
**Symptoms:** Debugger shows "MISSING" for environment variables
**Solution:** 
- Restart your development server
- In production: Redeploy after setting environment variables

#### Issue: Invalid URL Format
**Symptoms:** Debugger shows "Is valid URL: false"
**Solution:**
- Check for extra quotes, spaces, or characters in the URL
- Ensure URL starts with `https://` and ends with `.supabase.co`

#### Issue: Network/CORS Problems
**Symptoms:** Auth test fails with network errors
**Solution:**
- Check if Supabase project is active
- Verify the anon key is correct and not expired

### 4. Test the Fix

1. **Local Testing:**
   ```bash
   cd frontend
   npm run dev
   ```
   Visit http://localhost:3000 and test sign-up

2. **Production Testing:**
   Deploy to Vercel and test on your live URL

### 5. Remove Debug Tools (After Fix)

Once the issue is resolved, remove the debug component:

1. Remove `AuthDebugger` import from `frontend/app/page.tsx`
2. Remove `<AuthDebugger />` component from the login form
3. Delete `frontend/components/AuthDebugger.tsx`

## Enhanced Error Handling

I've also improved error handling in the authentication form to show more specific error messages, which will help identify issues in the future.

## Need More Help?

If the debugger reveals specific issues, share the diagnostic output and I can provide targeted solutions.