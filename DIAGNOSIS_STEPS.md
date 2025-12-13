# Manual Diagnosis Steps - Why API Still Points to Localhost

## Step 1: Verify Railway Has Redeployed
1. Go to Railway dashboard → Your Frontend service
2. Check the latest deployment commit hash
3. **Verify it matches your latest commit** (`9792941` or later)
4. If it's older, Railway hasn't picked up the changes yet
   - **Fix**: Wait for auto-deploy or trigger a manual redeploy

## Step 2: Check Railway Environment Variables
1. In Railway dashboard → Frontend service → **Variables** tab
2. Verify `NEXT_PUBLIC_API_URL` exists
3. **Verify the value is exactly**: `https://cybernexus-backend.up.railway.app/api/v1`
   - No trailing slash
   - Correct protocol (https)
   - Full path including `/api/v1`

## Step 3: Check Railway Build Logs
1. In Railway dashboard → Frontend service → **Deploy Logs**
2. Look for this section during the BUILD phase:
   ```
   🔧 Railway Build - Environment Variables
   ✅ NEXT_PUBLIC_API_URL: SET
      Value: https://cybernexus-backend.up.railway.app/api/v1
   ```
3. **If it shows NOT SET or wrong value**, the env var isn't available during build
   - **Fix**: Set the variable BEFORE deploying (Railway → Settings → Variables)

## Step 4: Inspect the Built JavaScript Bundle
Since Next.js embeds env vars at build time, we need to check the actual built code:

### Option A: Browser DevTools (Easiest)
1. Open your deployed site
2. Open DevTools → **Sources** tab (or **Page** tab)
3. Navigate to `.next/static/chunks/` folder
4. Find files like `pages/_app.js` or look for `API_BASE_URL` or `localhost:8000`
5. **Search for "localhost:8000"** in all loaded files
6. If you find it, the env var wasn't embedded properly

### Option B: View Page Source
1. Right-click on your deployed page → **View Page Source**
2. Press `Ctrl+F` (or `Cmd+F`) and search for `localhost:8000`
3. If found in the HTML source, the build used localhost

### Option C: Check Network Tab (What you already did)
1. The request URL shows: `http://localhost:8000/api/v1/capabilities/jobs`
2. This confirms the JavaScript code is using localhost
3. This means either:
   - Build didn't happen after our fix
   - Env var wasn't available during build
   - Next.js didn't embed it correctly

## Step 5: Force a Fresh Build
If the build is old, force a new one:

1. In Railway dashboard → Frontend service
2. Click **"Redeploy"** button (or go to **Settings** → **Deploy** → **Manual Deploy**)
3. Watch the build logs to verify:
   - The build happens AFTER our commit
   - Environment variables are logged correctly

## Step 6: Clear Browser Cache
Sometimes old JavaScript is cached:

1. Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Or open DevTools → **Application** tab → **Clear storage** → **Clear site data**
3. Or use Incognito/Private window

## Step 7: Add Debug Logging (Temporary)
Add this to verify what value is actually being used:

In `frontend/src/lib/api.ts`, temporarily add:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// DEBUG: Log the actual value (remove after diagnosis)
console.log('🔍 DEBUG API_BASE_URL:', API_BASE_URL);
console.log('🔍 DEBUG process.env.NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
```

Then:
1. Commit and push
2. Wait for Railway to rebuild
3. Check browser console for these debug messages
4. This will show exactly what value the code is using

## Step 8: Verify Dockerfile Build Process
Check if Railway is passing env vars during build:

1. Look at Railway build logs
2. During `npm run build`, env vars should be available
3. If Railway uses Dockerfile, check if it needs `ARG`:

```dockerfile
# In Dockerfile, add before RUN npm run build:
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
```

## Common Issues & Solutions

### Issue 1: "Variable set but still using localhost"
**Cause**: Variable set at RUNTIME but not BUILD TIME
**Fix**: Railway must set it BEFORE the build starts (in Variables, not runtime env)

### Issue 2: "Build succeeds but client code has localhost"
**Cause**: Next.js env section not working, or variable not available during build
**Fix**: 
- Ensure variable is in Railway → Variables (not Runtime env)
- Verify `env` section in `next.config.js` is correct

### Issue 3: "Everything looks correct but still localhost"
**Cause**: Browser/Service Worker cache
**Fix**: 
- Clear all caches
- Try incognito mode
- Check if Service Worker is caching old code

## Quick Fix to Test Right Now

If you want to test immediately without waiting for rebuild:

1. In Railway → Frontend service → Variables
2. Add/Update: `NEXT_PUBLIC_API_URL` = `https://cybernexus-backend.up.railway.app/api/v1`
3. **Manually trigger a redeploy**
4. Watch the build logs - it should show the variable is SET
5. After deploy completes, hard refresh your browser

## What to Report Back

After following these steps, tell me:
1. What does Railway build log show for `NEXT_PUBLIC_API_URL`?
2. Did you find `localhost:8000` in the built JavaScript?
3. What commit hash is Railway currently deployed on?
4. Is the variable set in Railway → Variables (not Runtime)?

