# Tor Service for Railway

This is the Tor proxy service for CyberNexus Dark Web Intelligence collection.

## Railway Deployment

**IMPORTANT:** When creating this service in Railway:

1. Set the **Root Directory** to: `cybernexus/tor-service`
2. Railway will automatically detect the Dockerfile
3. **Do NOT** generate a public domain - this is an internal-only service
4. The service name will be used by the backend (e.g., `tor-service`)

## Configuration

The service uses the `dperson/torproxy:latest` image which provides:
- Tor SOCKS5 proxy on port 9050
- Tor control port on 9051
- Automatic Tor circuit management

## Health Check

The service includes a health check that verifies Tor is running and can connect to the Tor network.

## Backend Connection

The backend service connects to this Tor service using Railway's internal networking:
- Set `TOR_PROXY_HOST=tor-service` in backend environment variables
- Railway automatically resolves service names via internal DNS
