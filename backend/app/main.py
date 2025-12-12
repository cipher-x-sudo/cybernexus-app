"""
CyberNexus - Main Application Entry Point

Enterprise Threat Intelligence Platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from loguru import logger
import sys
import json
from datetime import datetime

from app.config import settings, init_directories
from app.api.routes import auth, entities, graph, threats, timeline, reports, websocket, capabilities, company, darkweb
from app.utils import check_tor_connectivity


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # Initialize directories
    init_directories()
    logger.info("Data directories initialized")
    
    # Check Tor connectivity
    logger.info("Checking Tor proxy connectivity...")
    tor_status = check_tor_connectivity()
    
    if tor_status["status"] == "connected" and tor_status["is_tor"]:
        logger.info(
            f"Tor proxy connected successfully - Exit node: {tor_status.get('ip', 'unknown')}, "
            f"Response time: {tor_status.get('response_time_ms', 0)}ms"
        )
    elif settings.TOR_REQUIRED:
        error_msg = tor_status.get("error", "Unknown error")
        logger.error(f"Tor proxy is required but unavailable: {error_msg}")
        raise RuntimeError(f"Tor proxy connection failed: {error_msg}")
    else:
        logger.warning(
            f"Tor proxy unavailable but not required - Status: {tor_status['status']}, "
            f"Error: {tor_status.get('error', 'Unknown')}"
        )
    
    # Initialize DSA structures
    logger.info("Initializing custom DSA structures...")
    # TODO: Initialize graph, indices, etc.
    
    logger.info(f"{settings.APP_NAME} is ready!")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## CyberNexus - Enterprise Threat Intelligence Platform
    
    A unified security intelligence platform that:
    - **Discovers** external attack surface through automated reconnaissance
    - **Monitors** dark web for leaked credentials and brand abuse
    - **Correlates** threats using graph-based relationship engine
    - **Visualizes** attack paths through 3D graphs and geographic maps
    - **Prioritizes** threats with intelligent severity scoring
    - **Reports** findings through professional documentation
    
    Built with custom Data Structure and Algorithm (DSA) implementations.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
def get_cors_origins():
    """Get CORS origins from settings, handling wildcard and Railway domains."""
    origins_str = settings.CORS_ORIGINS
    
    # #region agent log - Hypothesis A: Check if CORS_ORIGINS env var is loaded
    logger.info(f"[CORS DEBUG HYP-A] Raw CORS_ORIGINS from settings: '{origins_str}' (type: {type(origins_str)})")
    # #endregion
    
    # If "*" is specified, return ["*"] but set allow_credentials=False
    if origins_str == "*":
        logger.info("[CORS DEBUG HYP-A] Using wildcard '*' - all origins allowed, credentials disabled")
        return ["*"], False
    
    # Parse comma-separated origins
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    logger.info(f"[CORS DEBUG HYP-A] Parsed {len(origins)} origins from string: {origins}")
    
    # Validate origin format (must be valid URL)
    validated_origins = []
    for origin in origins:
        if origin.startswith(("http://", "https://")):
            validated_origins.append(origin)
        else:
            logger.warning(f"[CORS DEBUG HYP-A] Invalid CORS origin format (must start with http:// or https://): {origin}")
    
    # If no valid origins, default to allowing all (but without credentials)
    if not validated_origins:
        logger.warning("[CORS DEBUG HYP-A] No valid origins found, defaulting to '*' (all origins, no credentials)")
        return ["*"], False
    
    # If we have explicit origins, we can use credentials
    logger.info(f"[CORS DEBUG HYP-A] Using {len(validated_origins)} explicit origins with credentials enabled: {validated_origins}")
    return validated_origins, True


def is_origin_allowed(origin: str, allowed_origins: list) -> bool:
    """Check if an origin is allowed, supporting wildcard patterns."""
    if not origin:
        return False
    
    # If wildcard is allowed
    if "*" in allowed_origins:
        return True
    
    # Exact match
    if origin in allowed_origins:
        return True
    
    # Check Railway domain patterns (e.g., *.railway.app)
    for allowed in allowed_origins:
        if allowed.startswith("*."):
            domain = allowed[2:]  # Remove "*."
            if origin.endswith(domain):
                return True
    
    return False

cors_origins, allow_creds = get_cors_origins()

# Log CORS configuration for debugging
logger.info(f"CORS configuration: origins={cors_origins}, allow_credentials={allow_creds}, environment={settings.ENVIRONMENT}, debug={settings.CORS_DEBUG}")

# #region agent log
# Instrumentation: Log CORS configuration at startup
try:
    with open("/home/cipher/REPO/DSA-Project/.cursor/debug.log", "a") as f:
        log_entry = {
            "id": "log_cors_config",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": "main.py:145",
            "message": "CORS configuration loaded",
            "data": {
                "CORS_ORIGINS_env": settings.CORS_ORIGINS,
                "cors_origins_parsed": cors_origins,
                "allow_credentials": allow_creds,
                "environment": settings.ENVIRONMENT,
                "CORS_DEBUG": settings.CORS_DEBUG
            },
            "sessionId": "debug-session",
            "runId": "startup",
            "hypothesisId": "A"
        }
        f.write(json.dumps(log_entry) + "\n")
except Exception:
    pass
# #endregion


# CORS Request Logging Middleware
class CORSDebugMiddleware(BaseHTTPMiddleware):
    """Middleware to log CORS-related requests for debugging."""
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        # #region agent log
        # Instrumentation: Log all CORS-related requests (especially OPTIONS)
        # Hypothesis B: Check if preflight OPTIONS requests are reaching the middleware
        # Hypothesis C: Check if origin validation is working correctly
        if method == "OPTIONS" or origin:
            is_allowed_val = is_origin_allowed(origin, cors_origins) if origin else None
            logger.info(f"[CORS DEBUG HYP-B/C] {method} {path} | Origin: '{origin}' | Allowed: {is_allowed_val} | Config: {cors_origins}")
            logger.info(f"[CORS DEBUG HYP-B/C] Request headers: {dict(request.headers)}")
            try:
                with open("/home/cipher/REPO/DSA-Project/.cursor/debug.log", "a") as f:
                    log_entry = {
                        "id": f"log_cors_req_{method}_{path.replace('/', '_')}",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "location": "main.py:154",
                        "message": "CORS request received",
                        "data": {
                            "method": method,
                            "path": path,
                            "origin": origin,
                            "is_allowed": is_allowed_val,
                            "request_headers": dict(request.headers),
                            "hypothesisId": "B"
                        },
                        "sessionId": "debug-session",
                        "runId": "runtime"
                    }
                    f.write(json.dumps(log_entry) + "\n")
            except Exception:
                pass
        # #endregion
        
        # Log OPTIONS requests and CORS-related requests
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            logger.debug(
                f"CORS Request: {method} {path} | "
                f"Origin: {origin} | "
                f"Allowed: {is_origin_allowed(origin, cors_origins) if origin else 'N/A'}"
            )
        
        response = await call_next(request)
        
        # #region agent log
        # Instrumentation: Log CORS response headers AFTER middleware chain
        # Hypothesis A/E: Check if CORSMiddleware set headers, or if explicit handler bypassed it
        if method == "OPTIONS" or origin:
            cors_response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith("access-control-")
            }
            logger.info(f"[CORS DEBUG HYP-A/E] Response AFTER middleware: {method} {path} | Status: {response.status_code} | CORS Headers: {cors_response_headers}")
            logger.info(f"[CORS DEBUG HYP-A/E] ALL response headers: {dict(response.headers)}")
            try:
                with open("/home/cipher/REPO/DSA-Project/.cursor/debug.log", "a") as f:
                    log_entry = {
                        "id": f"log_cors_resp_after_middleware_{method}_{path.replace('/', '_')}",
                        "timestamp": int(datetime.now().timestamp() * 1000),
                        "location": "main.py:233",
                        "message": "CORS response headers after middleware chain",
                        "data": {
                            "method": method,
                            "path": path,
                            "status_code": response.status_code,
                            "cors_headers": cors_response_headers,
                            "all_response_headers": dict(response.headers),
                            "has_access_control_origin": "access-control-allow-origin" in [k.lower() for k in response.headers.keys()],
                            "hypothesisId": "A",
                            "note": "This shows what headers CORSMiddleware/explicit handler set"
                        },
                        "sessionId": "debug-session",
                        "runId": "runtime"
                    }
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to log CORS response: {e}")
        # #endregion
        
        # Log CORS response headers
        if settings.CORS_DEBUG and origin:
            cors_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith("access-control-")
            }
            if cors_headers:
                logger.debug(f"CORS Response Headers: {cors_headers}")
        
        return response


# Add CORS debug middleware ALWAYS (for Railway debugging)
# This helps diagnose CORS issues in production
app.add_middleware(CORSDebugMiddleware)

# Add CORS middleware - must be added before routes
# #region agent log - Hypothesis A/E: Log CORSMiddleware configuration
try:
    with open("/home/cipher/REPO/DSA-Project/.cursor/debug.log", "a") as f:
        log_entry = {
            "id": "log_cors_middleware_config",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": "main.py:281",
            "message": "CORSMiddleware configuration",
            "data": {
                "allow_origins": cors_origins,
                "allow_credentials": allow_creds,
                "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
                "hypothesisId": "A"
            },
            "sessionId": "debug-session",
            "runId": "startup"
        }
        f.write(json.dumps(log_entry) + "\n")
except Exception:
    pass
# #endregion

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,  # Must be False if origins=["*"]
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["Entities"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])
app.include_router(threats.router, prefix="/api/v1/threats", tags=["Threats"])
app.include_router(timeline.router, prefix="/api/v1/timeline", tags=["Timeline"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(capabilities.router, prefix="/api/v1/capabilities", tags=["Capabilities"])
app.include_router(company.router, prefix="/api/v1/company", tags=["Company"])
app.include_router(darkweb.router, prefix="/api/v1/darkweb", tags=["Dark Web"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    # Check Tor connectivity
    tor_status = check_tor_connectivity()
    
    # Determine overall health status
    # If Tor is unavailable but not required, mark as "degraded" not "unhealthy"
    overall_status = "healthy"
    if tor_status["status"] != "connected" and settings.TOR_REQUIRED:
        overall_status = "unhealthy"
    elif tor_status["status"] != "connected":
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "version": settings.APP_VERSION,
        "services": {
            "api": "operational",
            "graph_engine": "operational",
            "collectors": "operational",
            "websocket": "operational"
        },
        "tor_proxy": {
            "status": tor_status["status"],
            "is_tor": tor_status["is_tor"],
            "host": tor_status["host"],
            "port": tor_status["port"],
            "response_time_ms": tor_status.get("response_time_ms"),
            "ip": tor_status.get("ip"),
            "error": tor_status.get("error")
        }
    }


