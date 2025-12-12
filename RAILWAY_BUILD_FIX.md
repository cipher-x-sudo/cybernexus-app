# Railway Build-Time Environment Variable Fix

## The Problem
- **Build Logs Show**: `NEXT_PUBLIC_API_URL: NOT SET` ❌
- **Deploy Logs Show**: `NEXT_PUBLIC_API_URL: SET` ✅
- **Result**: Next.js builds without the variable, so it falls back to `localhost:8000`

## Root Cause
Railway was using **NIXPACKS** builder (from `railway.json`), which wasn't passing environment variables during the build phase. Next.js needs `NEXT_PUBLIC_*` variables at **BUILD TIME**, not runtime.

## The Fix

### 1. Changed Railway Builder (DONE)
- Updated `frontend/railway.json` to use `DOCKERFILE` instead of `NIXPACKS`
- This ensures Railway uses our Dockerfile which has `ARG NEXT_PUBLIC_API_URL`

### 2. Dockerfile Configuration (DONE)
- Added `ARG NEXT_PUBLIC_API_URL` at the top
- Set `ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL` before the build
- This makes the variable available during `npm run build`

### 3. Next.js Config (DONE)
- Added explicit `env` section in `next.config.js` to embed the variable

## Important: Railway Configuration

After pushing these changes, you MUST ensure:

1. **In Railway Dashboard → Frontend Service → Variables**:
   - `NEXT_PUBLIC_API_URL` must be set to: `https://cybernexus-backend.up.railway.app/api/v1`
   - This should already be set (you confirmed it is)

2. **Railway will now**:
   - Use Dockerfile for builds
   - Automatically pass `NEXT_PUBLIC_API_URL` as a build argument
   - Make it available during `npm run build`

## Verification After Deploy

After Railway rebuilds, check:

1. **Build Logs** should show:
   ```
   🔧 Railway Build - Environment Variables
   ✅ NEXT_PUBLIC_API_URL: SET
      Value: https://cybernexus-backend.up.railway.app/api/v1
   ```

2. **Browser Console** (after loading the site):
   - Look for debug messages:
   ```
   🔍 [DEBUG] API_BASE_URL: https://cybernexus-backend.up.railway.app/api/v1
   ```
   - Should NOT show `localhost:8000`

3. **Network Tab**:
   - API requests should go to `https://cybernexus-backend.up.railway.app/api/v1/...`
   - Should NOT go to `http://localhost:8000/...`

## If It Still Doesn't Work

1. **Check Railway Build Logs**:
   - Does it say "Using Dockerfile"?
   - Does it show the variable is SET during build?

2. **Verify Railway Settings**:
   - Go to Railway → Frontend Service → Settings
   - Check if there's a "Build" section
   - Ensure it's using Dockerfile, not Nixpacks

3. **Manual Redeploy**:
   - Railway → Frontend Service → Redeploy
   - Watch the build logs carefully

## Files Changed

1. `frontend/railway.json` - Changed builder to DOCKERFILE
2. `frontend/Dockerfile` - Added ARG and ENV for build-time variable
3. `frontend/next.config.js` - Added explicit env section
4. `frontend/src/lib/api.ts` - Added debug logging (temporary)
