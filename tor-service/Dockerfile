FROM dperson/torproxy:latest

# Install curl for healthcheck (dperson/torproxy may not have it)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Expose Tor SOCKS proxy port (9050) and control port (9051)
EXPOSE 9050 9051

# Configure Tor to listen on all interfaces for internal Railway networking
ENV TOR_NewCircuitPeriod=30
ENV TOR_MaxCircuitDirtiness=60

# Health check to verify Tor is running
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD curl --socks5 localhost:9050 -s https://check.torproject.org/api/ip || exit 1

# The dperson/torproxy image already has the entrypoint configured
# It will start Tor and listen on 0.0.0.0:9050 by default
