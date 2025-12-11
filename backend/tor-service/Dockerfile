FROM dperson/torproxy:latest

# Install curl for healthcheck (dperson/torproxy may not have it)
# Check if curl exists, if not try to install with available package manager
RUN if ! command -v curl >/dev/null 2>&1; then \
        if command -v apt-get >/dev/null 2>&1; then \
            apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*; \
        elif command -v apk >/dev/null 2>&1; then \
            apk add --no-cache curl; \
        elif command -v yum >/dev/null 2>&1; then \
            yum install -y curl && yum clean all; \
        else \
            echo "No package manager found, curl may not be available"; \
        fi \
    fi

# Expose Tor SOCKS proxy port (9050) and control port (9051)
EXPOSE 9050 9051

# Configure Tor to listen on all interfaces for internal Railway networking
ENV TOR_NewCircuitPeriod=30
ENV TOR_MaxCircuitDirtiness=60

# Enable detailed logging to stdout/stderr for container visibility
# Log level: notice (moderately verbose, good for production monitoring)
# Log to stdout so it appears in container logs
ENV TOR_Log="notice stdout"
# Enable detailed logging for connections, circuits, and streams
ENV TOR_LogMessageDomains="GENERAL CIRC STREAM CONN ORCONN HTTPCONN"
# Use 1 second granularity for timestamps
ENV TOR_LogTimeGranularity=1

# Health check to verify Tor is running
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD curl --socks5 localhost:9050 -s https://check.torproject.org/api/ip || exit 1

# The dperson/torproxy image already has the entrypoint configured
# It will start Tor and listen on 0.0.0.0:9050 by default

