# Tor Service for Railway

This is the Tor proxy service for CyberNexus Dark Web Intelligence collection.

## Railway Deployment

**IMPORTANT:** When creating this service in Railway, you have two options:

### Option 1: Root Directory (Recommended)
1. Set the **Root Directory** to: `cybernexus/backend/tor-service`
2. Railway will automatically detect the Dockerfile in that directory
3. **Do NOT** generate a public domain - this is an internal-only service
4. The service name will be used by the backend (e.g., `tor-service`)

### Option 2: Environment Variable (Alternative)
If Railway still can't detect the Dockerfile:
1. Set the **Root Directory** to: `cybernexus` (or leave it at repo root)
2. Add environment variable: `RAILWAY_DOCKERFILE_PATH=cybernexus/backend/tor-service/Dockerfile`
3. Railway will use this path to find the Dockerfile
4. **Do NOT** generate a public domain - this is an internal-only service

## Configuration

The service uses the `dperson/torproxy:latest` image which provides:
- Tor SOCKS5 proxy on port 9050
- Tor control port on 9051
- Automatic Tor circuit management

## Health Check

The service includes a health check that verifies Tor is running and can connect to the Tor network.

## Logging

The service is configured with detailed logging enabled:

- **Log Level**: `notice` (moderately verbose, good for production monitoring)
- **Log Output**: stdout/stderr (visible in container logs)
- **Log Domains**: GENERAL, CIRC (circuits), STREAM (connections), CONN (connections), ORCONN (OR connections), HTTPCONN (HTTP connections)

You will see detailed logs for:
- New circuit establishment
- Connection requests through the proxy
- Stream creation and closure
- Circuit status changes
- Error messages and warnings

To view logs:
- **Docker Compose**: `docker-compose logs -f tor-proxy`
- **Railway**: Check the service logs in the Railway dashboard

## Backend Connection

The backend service connects to this Tor service using Railway's internal networking:
- Set `TOR_PROXY_HOST=tor-service` in backend environment variables
- Railway automatically resolves service names via internal DNS

