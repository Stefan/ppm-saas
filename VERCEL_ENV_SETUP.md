# Vercel Environment Variables Setup Guide

## Problem
You can't log into the production app because environment variables are not configured in Vercel.

**Important:** The `.env.production` file is only used for local builds. Vercel needs environment variables to be set in its dashboard.

## Quick Fix (Automated)

Run the verification script:

```bash
./scripts/verify-vercel-env.sh
```

This script will:
1. Check if Vercel CLI is installed
2. Verify you're logged in
3. Read variables from `.env.production`
4. Let you set them in Vercel
5. Trigger a new deployment

## Manual Fix (Vercel Dashboard)

### Step 1: Go to Vercel Dashboard
Visit: https://vercel.com/orka/orka-ppm/settings/environment-variables

### Step 2: Add Environment Variables

Add these variables for **Production** environment:

#### Variable 1: NEXT_PUBLIC_SUPABASE_URL
- **Name:** `NEXT_PUBLIC_SUPABASE_URL`
- **Value:** `https://xceyrfvxooiplbmwavlb.supabase.co`
- **Environment:** Production ✓

#### Variable 2: NEXT_PUBLIC_SUPABASE_ANON_KEY
- **Name:** `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Value:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY4Mjg3ODEsImV4cCI6MjA4MjQwNDc4MX0.jIyJlwx2g9xn8OTSaLum6H8BKqknyxB8gYxgEKdfgqo`
- **Environment:** Production ✓

#### Variable 3: SUPABASE_SERVICE_ROLE_KEY
- **Name:** `SUPABASE_SERVICE_ROLE_KEY`
- **Value:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhjZXlyZnZ4b29pcGxibXdhdmxiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjgyODc4MSwiZXhwIjoyMDgyNDA0NzgxfQ.ak3-04l8Fp1CnAg-Rp1s_mHyMnmVNCS9fwH9QWBO4lY`
- **Environment:** Production ✓

#### Variable 4: NEXT_PUBLIC_API_URL
- **Name:** `NEXT_PUBLIC_API_URL`
- **Value:** `https://orka-ppm.onrender.com`
- **Environment:** Production ✓

### Step 3: Redeploy

After adding the variables, trigger a new deployment:

**Option A: Via Dashboard**
- Go to: https://vercel.com/orka/orka-ppm
- Click "Redeploy" on the latest deployment

**Option B: Via Git Push**
```bash
git commit --allow-empty -m "Trigger redeploy for env vars"
git push origin main
```

**Option C: Via Vercel CLI**
```bash
vercel --prod
```

### Step 4: Verify

1. Wait for deployment to complete (2-3 minutes)
2. Visit your production URL
3. Try logging in with your credentials
4. Check browser console for any errors

## Troubleshooting

### Issue: Still can't log in after setting variables

**Check 1: Verify variables are set**
```bash
vercel env ls
```

**Check 2: Check browser console**
Open DevTools (F12) and look for:
- ✅ "Auth initialization complete" - Good!
- ❌ "CONFIGURATION ERROR" - Variables not loaded
- ❌ "Invalid API key" - Wrong key value

**Check 3: Verify deployment used new variables**
- Go to Vercel dashboard
- Check deployment logs
- Look for "Environment Variables" section

### Issue: "Invalid API key" error

This means the ANON_KEY is incorrect or corrupted.

**Fix:**
1. Go to Supabase dashboard: https://supabase.com/dashboard/project/xceyrfvxooiplbmwavlb/settings/api
2. Copy the "anon public" key
3. Update in Vercel dashboard
4. Redeploy

### Issue: "CORS error" or "Network error"

This means the backend isn't configured to accept requests from your frontend.

**Fix:**
1. Check backend CORS configuration
2. Ensure Supabase project allows your domain
3. Check Supabase project settings

## Vercel CLI Setup

If you don't have Vercel CLI installed:

```bash
# Install globally
npm install -g vercel

# Login
vercel login

# Link project (run in project directory)
vercel link
```

## Security Notes

⚠️ **Never commit sensitive keys to Git**
- The `.env.production` file should be in `.gitignore`
- Use Vercel dashboard or CLI to set production secrets
- Rotate keys if accidentally committed

✅ **Best Practices**
- Use different keys for development and production
- Regularly rotate service role keys
- Monitor Supabase logs for suspicious activity
- Enable RLS (Row Level Security) in Supabase

## Additional Resources

- [Vercel Environment Variables Docs](https://vercel.com/docs/concepts/projects/environment-variables)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
