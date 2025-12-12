# Railway Frontend Service Setup - CRITICAL

## The Issue You're Seeing
Railway is trying to use the **root Dockerfile** (which builds both frontend and backend) instead of the **frontend Dockerfile**.

## Root Cause
Railway's **Root Directory** setting for the Frontend service is not set correctly.

## Fix in Railway Dashboard

1. Go to Railway Dashboard
2. Select your **Frontend** service
3. Go to **Settings** → **Source** (or **Settings** → **General**)
4. Look for **Root Directory** field
5. **CRITICAL**: Set it to exactly: `cybernexus/frontend`
   - No leading slash
   - No trailing slash
   - Exactly: `cybernexus/frontend`
6. Save the changes
7. Railway will automatically redeploy

## Verification

After setting the root directory correctly:

1. Railway should auto-detect the Dockerfile at `cybernexus/frontend/Dockerfile`
2. Build logs should show: "Using Detected Dockerfile" and it should be the frontend one
3. Build should succeed
4. Build logs should show: `✅ NEXT_PUBLIC_API_URL: SET` during the BUILD phase

## Why This Matters

- **Wrong root directory** = Railway uses root Dockerfile (fails because it expects `frontend/` directory)
- **Correct root directory** (`cybernexus/frontend`) = Railway uses `frontend/Dockerfile` (works correctly)

## Current Status

- `frontend/Dockerfile` exists and is configured correctly
- `frontend/railway.json` has been removed (Railway will auto-detect Dockerfile)
- Environment variable `NEXT_PUBLIC_API_URL` is set in Railway Variables
- **YOU MUST VERIFY** Railway service Root Directory is set to `cybernexus/frontend`
