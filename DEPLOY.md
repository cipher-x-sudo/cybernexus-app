# CyberNexus Railway Deployment Guide

## Quick Deploy

CyberNexus requires **two separate Railway services**:
1. **Backend** (Python FastAPI)
2. **Frontend** (Next.js)

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

## Environment Variables

### Backend
No required environment variables. Optional:
- `ENVIRONMENT`: `production` or `development`
- `LOG_LEVEL`: `INFO`, `DEBUG`, etc.

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
│  Railway:3000   │                │  Railway:8000    │
└─────────────────┘                └──────────────────┘
        │                                  │
        │                                  │
   NEXT_PUBLIC_API_URL             Real-time scans
   points to backend               DNS lookups
                                   HTTP checks
```
