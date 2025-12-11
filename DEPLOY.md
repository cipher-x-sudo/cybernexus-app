# CyberNexus Railway Deployment Guide

## Quick Deploy

CyberNexus requires **three separate Railway services**:
1. **Backend** (Python FastAPI)
2. **Frontend** (Next.js)
3. **Tor Service** (Tor Proxy for Dark Web Intelligence)

## Step 1: Deploy Backend

1. Go to [Railway](https://railway.app) and create a new project
2. Click "New Service" → "GitHub Repo"
3. Select your repository
4. **Important:** Set the root directory to `cybernexus/backend`
5. Railway will auto-detect Python and use `nixpacks.toml`
6. Wait for deployment to complete
7. Go to **Settings** → **Networking** → Generate a public domain
8. Copy the domain URL (e.g., `https://cybernexus-backend-xxxx.up.railway.app`)

## Step 2: Deploy Frontend

1. In the same Railway project, click "New Service" → "GitHub Repo"
2. Select the same repository
3. **Important:** Set the root directory to `cybernexus/frontend`
4. **Add Environment Variable:**
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://YOUR-BACKEND-URL/api/v1` (use the URL from Step 1)
5. Wait for deployment to complete
6. Generate a public domain for the frontend

## Step 3: Deploy Tor Service

The Tor service is required for Dark Web Intelligence collection. It runs as an **internal-only service** (no public port).

1. In the same Railway project, click "New Service" → "GitHub Repo"
2. Select the same repository
3. **Important:** Set the root directory to `cybernexus/tor-service`
4. Railway will auto-detect the Dockerfile and deploy
5. **Do NOT generate a public domain** - this service is internal only
6. **Important:** Note the service name (Railway will show it, e.g., `tor-service` or `tor-proxy`)

## Step 4: Configure Backend to Use Tor Service

1. Go to your **Backend** service settings
2. Navigate to **Variables** tab
3. Add the following environment variable:
   - Name: `TOR_PROXY_HOST`
   - Value: `tor-service` (or whatever Railway named your Tor service)
4. **Important:** The service name must match exactly what Railway shows
5. Redeploy the backend service for changes to take effect

## Environment Variables

### Backend
**Required for Dark Web Intelligence:**
- `TOR_PROXY_HOST`: Set to your Tor service name (e.g., `tor-service`)
  - Railway automatically resolves service names via internal DNS
  - Defaults to `localhost` for local development

**Optional:**
- `ENVIRONMENT`: `production` or `development`
- `LOG_LEVEL`: `INFO`, `DEBUG`, etc.
- `TOR_PROXY_PORT`: Defaults to `9050` (usually don't need to change)
- `TOR_PROXY_TYPE`: Defaults to `socks5h` (usually don't need to change)

### Frontend (Required!)
- `NEXT_PUBLIC_API_URL`: Full URL to your backend API
  - Example: `https://cybernexus-backend.up.railway.app/api/v1`

## Troubleshooting

### "Tools not working / No output"
**Cause:** Frontend can't reach backend API
**Fix:** Make sure `NEXT_PUBLIC_API_URL` is set correctly on the frontend service

### "CORS errors in browser console"
**Cause:** Backend not allowing frontend origin
**Fix:** Backend already allows all origins, but verify the URL is correct

### "Dark Web Intelligence not working / Tor connection failed"
**Cause:** Backend can't reach Tor service
**Fix:** 
1. Verify `TOR_PROXY_HOST` is set correctly in backend environment variables
2. Check that the Tor service name matches exactly (case-sensitive)
3. Ensure Tor service is deployed and running (check Railway dashboard)
4. Verify Tor service health check is passing

### Checking if Backend is Running
Visit: `https://YOUR-BACKEND-URL/health`
You should see:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Checking API Docs
Visit: `https://YOUR-BACKEND-URL/docs`
This shows the Swagger API documentation.

## Local Development

```bash
# Terminal 1 - Backend
cd cybernexus/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd cybernexus/frontend
npm install
npm run dev
```

## Architecture

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│    Frontend     │ ──────────────▶│     Backend      │
│   (Next.js)     │                │   (FastAPI)      │
│  Railway:3000   │                │  Railway:8000   │
└─────────────────┘                └────────┬─────────┘
        │                                     │
        │                                     │ SOCKS5
   NEXT_PUBLIC_API_URL                        │ (Internal)
   points to backend                          ▼
                                    ┌──────────────────┐
                                    │   Tor Service    │
                                    │  (Internal Only) │
                                    │   Port: 9050     │
                                    └──────────────────┘
```

### Service Communication

- **Frontend → Backend**: Public HTTPS connection
- **Backend → Tor Service**: Internal Railway networking (service name resolution)
- **Tor Service**: No public port exposed (internal only)

### Railway Internal Networking

Railway automatically creates internal DNS entries for each service. When you set `TOR_PROXY_HOST=tor-service`, Railway resolves `tor-service` to the internal IP of your Tor service container. This allows services to communicate without exposing ports publicly.
