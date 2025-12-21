# Railway Deployment Setup Guide

## Frontend API URL Configuration

The frontend needs to know where your backend API is located. This is configured via the `NEXT_PUBLIC_API_URL` environment variable.

### ⚠️ Important: Build-Time Variable

`NEXT_PUBLIC_API_URL` is a **build-time** variable in Next.js. This means:
- It must be set **BEFORE** the frontend is built
- If you set it after deployment, you must **redeploy** the frontend for it to take effect
- The value is embedded into the JavaScript bundle during build

### Setup Steps

1. **Find Your Backend Service URL**
   - Go to your Railway dashboard
   - Click on your **Backend** service
   - Copy the public domain URL (e.g., `https://cybernexus-backend.up.railway.app`)
   - Add `/api/v1` to the end: `https://cybernexus-backend.up.railway.app/api/v1`

2. **Set Environment Variable in Frontend Service**
   - Go to your **Frontend** service in Railway
   - Navigate to **Settings** → **Variables**
   - Click **+ New Variable**
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://your-backend-service.up.railway.app/api/v1`
   - Click **Add**

3. **Redeploy Frontend**
   - After setting the variable, Railway should automatically redeploy
   - If not, go to **Deployments** → **Redeploy** or trigger a new deployment
   - Wait for the build to complete

4. **Verify**
   - Open your frontend URL in a browser
   - Open browser DevTools (F12) → Console
   - You should NOT see errors about `localhost:8000` or connection refused
   - Try using a feature that calls the API (e.g., create a scan job)

### Troubleshooting

#### Error: `ERR_CONNECTION_REFUSED` to `localhost:8000`

**Cause:** `NEXT_PUBLIC_API_URL` is not set or the frontend wasn't rebuilt after setting it.

**Fix:**
1. Verify the variable is set in Railway (Frontend service → Settings → Variables)
2. Check the value is correct (should be `https://...` not `http://localhost:8000`)
3. **Redeploy the frontend** (this is critical!)
4. Wait for the build to complete

#### Error: `API URL not configured`

**Cause:** The frontend detected it's on Railway but `NEXT_PUBLIC_API_URL` is missing.

**Fix:**
1. Set `NEXT_PUBLIC_API_URL` in Railway (see steps above)
2. Redeploy the frontend service
3. The build process will embed the URL into the bundle

#### Backend URL Format

Make sure your backend URL:
- ✅ Starts with `https://` (not `http://`)
- ✅ Ends with `/api/v1` (the API base path)
- ✅ Is publicly accessible (not `localhost`)

**Correct examples:**
- `https://cybernexus-backend.up.railway.app/api/v1`
- `https://api-cybernexus-production.up.railway.app/api/v1`

**Incorrect examples:**
- `http://localhost:8000/api/v1` ❌ (won't work on Railway)
- `https://cybernexus-backend.up.railway.app` ❌ (missing `/api/v1`)
- `cybernexus-backend.up.railway.app/api/v1` ❌ (missing `https://`)

### Automatic Backend URL Inference

If `NEXT_PUBLIC_API_URL` is not set, the frontend will try to infer the backend URL based on common naming patterns:
- `backend.up.railway.app`
- `api.up.railway.app`
- `cybernexus-backend.up.railway.app`
- `cybernexus-api.up.railway.app`

However, **this is not reliable** and you should always set `NEXT_PUBLIC_API_URL` explicitly.

### Environment Variables Summary

#### Frontend Service
- `NEXT_PUBLIC_API_URL` (required) - Backend API URL

#### Backend Service
- `TOR_PROXY_HOST` (optional) - Tor service name for dark web features
- `REDIS_URL` (optional) - Redis connection string
- `ENVIRONMENT` (optional) - `production` or `development`
- `CORS_ORIGINS` (optional) - Comma-separated list of allowed origins
  - Default: `*` (allows all origins, but credentials disabled)
  - Recommended for Railway: `https://cybernexus.up.railway.app,https://your-frontend-domain.up.railway.app`
  - Example: `https://cybernexus.up.railway.app,https://localhost:3000`

### Quick Checklist

- [ ] Backend service is deployed and has a public domain
- [ ] Backend URL is accessible (test in browser: `https://your-backend.up.railway.app/health`)
- [ ] `NEXT_PUBLIC_API_URL` is set in Frontend service variables
- [ ] Frontend service has been redeployed after setting the variable
- [ ] Frontend build completed successfully
- [ ] Test API connection in browser console (should not show `localhost:8000`)

### Testing the Connection

1. Open your frontend in a browser
2. Open DevTools (F12) → Network tab
3. Try to create a scan or use any feature
4. Check the Network tab - requests should go to your Railway backend URL, not `localhost:8000`
5. If you see `localhost:8000`, the variable wasn't set or the frontend wasn't rebuilt

## CORS Configuration

### Error: `Access-Control-Allow-Origin header is present on the requested resource`

**Cause:** The backend is not allowing requests from your frontend domain.

**Fix:**

1. **Option 1: Set explicit CORS origins (Recommended)**
   - Go to your **Backend** service in Railway
   - Navigate to **Settings** → **Variables**
   - Add variable:
     - Name: `CORS_ORIGINS`
     - Value: `https://cybernexus.up.railway.app` (your frontend domain)
     - For multiple domains: `https://cybernexus.up.railway.app,https://localhost:3000`
   - Redeploy the backend service

2. **Option 2: Use wildcard (Less secure, but works)**
   - The backend defaults to `CORS_ORIGINS=*` which allows all origins
   - However, credentials are disabled when using wildcard
   - This should work for most cases

**Verify CORS is working:**
1. Open your frontend in a browser
2. Open DevTools (F12) → Console
3. Try to make an API request
4. You should NOT see CORS errors
5. Check the Network tab - the OPTIONS preflight request should return 200 OK

**Common CORS Issues:**
- ❌ `allow_origins=["*"]` with `allow_credentials=True` → Browsers block this
- ✅ `allow_origins=["*"]` with `allow_credentials=False` → Works (default)
- ✅ `allow_origins=["https://your-frontend.up.railway.app"]` with `allow_credentials=True` → Best practice









