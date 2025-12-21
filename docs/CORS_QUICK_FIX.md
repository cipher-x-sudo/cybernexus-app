# CORS Error Quick Fix for Railway

## The Problem
```
Access to fetch at 'https://backend.up.railway.app/api/v1/...' 
from origin 'https://cybernexus.up.railway.app' has been blocked by CORS policy
```

## Immediate Fix (2 minutes)

### Step 1: Set CORS_ORIGINS in Backend Service
1. Go to Railway Dashboard
2. Click on your **Backend** service
3. Go to **Settings** → **Variables**
4. Click **+ New Variable**
5. Add:
   - **Name**: `CORS_ORIGINS`
   - **Value**: `https://cybernexus.up.railway.app` (your frontend domain)
   - Click **Add**

### Step 2: Redeploy Backend
1. Go to **Deployments** tab
2. Click **Redeploy** (or push a new commit)
3. Wait for deployment to complete (~2-3 minutes)

### Step 3: Verify
1. Open your frontend: `https://cybernexus.up.railway.app`
2. Open DevTools (F12) → Console
3. Try to create a scan or use any feature
4. CORS errors should be gone!

## Alternative: Allow All Origins (Less Secure)

If you want to allow all origins (for testing):

1. Set `CORS_ORIGINS=*` in backend environment variables
2. Redeploy backend
3. Note: Credentials will be disabled with wildcard

## Multiple Frontend Domains

If you have multiple frontend domains, separate them with commas:

```
CORS_ORIGINS=https://cybernexus.up.railway.app,https://staging.up.railway.app,https://localhost:3000
```

## Troubleshooting

### Still getting CORS errors after redeploy?

1. **Check backend logs:**
   - Railway Dashboard → Backend Service → Logs
   - Look for: `CORS configuration: origins=...`
   - Should show your frontend domain

2. **Verify environment variable:**
   - Settings → Variables
   - Make sure `CORS_ORIGINS` is set correctly
   - No typos, includes `https://`

3. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Or clear browser cache

4. **Check Network tab:**
   - DevTools → Network
   - Look for OPTIONS request (preflight)
   - Should return 200 OK with CORS headers

### Preflight OPTIONS request failing?

The backend now properly handles OPTIONS requests. If still failing:
- Make sure backend is redeployed with latest code
- Check that `allow_methods` includes "OPTIONS" (it does by default)

## Expected CORS Headers

After fix, you should see these headers in OPTIONS response:
```
Access-Control-Allow-Origin: https://cybernexus.up.railway.app
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```

## Quick Test

Test CORS from browser console:
```javascript
fetch('https://backend.up.railway.app/api/v1/health', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

Should work without CORS errors!








