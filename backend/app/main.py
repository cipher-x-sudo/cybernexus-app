"""
CyberNexus - Main Application Entry Point

Enterprise Threat Intelligence Platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import sys

from app.config import settings, init_directories
from app.api.routes import auth, entities, graph, threats, timeline, reports, websocket, capabilities, company, darkweb, dashboard, network, network_ws, notifications
from app.utils import check_tor_connectivity
from app.middleware.network_blocker import NetworkBlockerMiddleware
from app.middleware.network_logger import NetworkLoggerMiddleware
from app.services.tunnel_analyzer import get_tunnel_analyzer
from app.core.database.database import init_db, close_db


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
    
    # Initialize database
    logger.info("Initializing database connection...")
    init_db()
    logger.info("Database connection initialized")
    
    # Run database migrations automatically
    logger.info("Running database migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("migrations/alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        # Don't fail startup if migrations fail - might be first run or connection issue
        logger.warning("Continuing startup despite migration errors")
    
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
    
    # Close database connections
    await close_db()
    logger.info("Database connections closed")


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
    logger.debug(f"[CORS] Raw CORS_ORIGINS from settings: '{origins_str}'")
    
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
    
    # Always allow Railway domains (for Railway deployments)
    if ".railway.app" in origin or ".railway.xyz" in origin:
        return True
    
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



# CORS Request Logging Middleware
class CORSDebugMiddleware(BaseHTTPMiddleware):
    """Middleware to log CORS-related requests for debugging."""
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        # Log CORS requests for debugging (only if CORS_DEBUG is enabled)
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            is_allowed_val = is_origin_allowed(origin, cors_origins) if origin else None
            logger.debug(f"[CORS] {method} {path} | Origin: '{origin}' | Allowed: {is_allowed_val}")
        
        # Log OPTIONS requests and CORS-related requests
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            logger.debug(
                f"CORS Request: {method} {path} | "
                f"Origin: {origin} | "
                f"Allowed: {is_origin_allowed(origin, cors_origins) if origin else 'N/A'}"
            )
        
        response = await call_next(request)
        
        # Log CORS response headers for debugging (only if CORS_DEBUG is enabled)
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            cors_response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith("access-control-")
            }
            logger.debug(f"[CORS] Response: {method} {path} | Status: {response.status_code} | CORS Headers: {cors_response_headers}")
        
        # Log CORS response headers
        if settings.CORS_DEBUG and origin:
            cors_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith("access-control-")
            }
            if cors_headers:
                logger.debug(f"CORS Response Headers: {cors_headers}")
        
        return response


# CORS Header Enforcement Middleware
# Ensures CORS headers are ALWAYS set if CORSMiddleware fails to set them
class CORSEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce CORS headers on all responses with Origin."""
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        response = await call_next(request)
        
        # Check if CORS headers are missing
        has_cors_headers = any(
            k.lower().startswith("access-control-") 
            for k in response.headers.keys()
        )
        
        # Always add CORS headers if request has Origin header and headers are missing
        if origin:
            if not has_cors_headers:
                logger.warning(
                    f"[CORS ENFORCE] Missing CORS headers on {method} {path}, "
                    f"adding explicitly. Origin: {origin}"
                )
            
            # Always set CORS headers if origin is allowed
            if is_origin_allowed(origin, cors_origins):
                response.headers["Access-Control-Allow-Origin"] = origin
                if allow_creds:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                # When credentials are enabled, must explicitly list headers (cannot use "*")
                if allow_creds:
                    response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
                else:
                    response.headers["Access-Control-Allow-Headers"] = "*"
                if not has_cors_headers:
                    logger.info(f"[CORS ENFORCE] Added CORS headers for {method} {path}")
            else:
                # Even if not explicitly allowed, allow Railway domains as fallback
                if ".railway.app" in origin or ".railway.xyz" in origin:
                    logger.info(f"[CORS ENFORCE] Allowing Railway domain as fallback: {origin}")
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                    response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
                else:
                    logger.warning(f"[CORS ENFORCE] Origin {origin} not allowed, not adding CORS headers")
        
        return response


# Add CORS middleware - must be added before routes
# IMPORTANT: FastAPI middleware order - LAST added runs FIRST on response
# We want execution order on RESPONSE:
# 1. CORSDebugMiddleware (runs last, logs final headers)
# 2. CORSEnforcementMiddleware (runs middle, ensures headers are set)
# 3. CORSMiddleware (runs first, tries to set headers)
#
# So we need to add in REVERSE order:
# - CORSDebugMiddleware added LAST (runs last on response)
# - CORSEnforcementMiddleware added MIDDLE (runs middle on response)
# - CORSMiddleware added FIRST (runs first on response)

# Add middleware in REVERSE order of desired execution
# (Last added = first executed on response)

# 1. CORSMiddleware - tries to set CORS headers (runs FIRST on response)
# When allow_credentials=True, we cannot use allow_headers=["*"], must be explicit
allowed_headers = [
    "accept",
    "accept-language",
    "content-type",
    "content-length",
    "authorization",
    "x-requested-with",
    "x-csrf-token",
    "x-api-key",
] if allow_creds else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,  # Must be False if origins=["*"]
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=allowed_headers,
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)
logger.info("[CORS] CORSMiddleware added - will attempt to set CORS headers")

# 2. CORSEnforcementMiddleware - ensures headers are set if CORSMiddleware fails (runs MIDDLE on response)
app.add_middleware(CORSEnforcementMiddleware)
logger.info("[CORS] CORSEnforcementMiddleware added - will enforce CORS headers if missing")

# 3. CORSDebugMiddleware - logs final result (runs LAST on response, sees final headers)
app.add_middleware(CORSDebugMiddleware)
logger.info("[CORS] CORSDebugMiddleware added - will log CORS request/response details")

# Network Monitoring Middleware
# IMPORTANT: Middleware order - LAST added runs FIRST on request
# We want: Blocker -> Logger (blocker checks first, then logger captures)
# So we add in REVERSE order: Logger first, then Blocker

if settings.NETWORK_ENABLE_LOGGING or settings.NETWORK_ENABLE_BLOCKING:
    # Initialize tunnel analyzer if tunnel detection is enabled
    tunnel_analyzer = None
    if settings.NETWORK_ENABLE_TUNNEL_DETECTION:
        tunnel_analyzer = get_tunnel_analyzer()
    
    # Network Logger (added first, runs second on request)
    # We'll create instance after app is created to set WebSocket reference
    logger.info("[Network] NetworkLoggerMiddleware will be added")
    
    # Network Blocker (added second, runs first on request - checks blocks before logging)
    if settings.NETWORK_ENABLE_BLOCKING:
        app.add_middleware(NetworkBlockerMiddleware)
        logger.info("[Network] NetworkBlockerMiddleware added")
    
    # Network Logger (added after blocker, so it runs after blocker checks)
    app.add_middleware(NetworkLoggerMiddleware, tunnel_analyzer=tunnel_analyzer)
    logger.info("[Network] NetworkLoggerMiddleware added")

# Explicit OPTIONS handler as fallback for Railway/proxy issues
# This ensures preflight requests always get proper CORS headers
@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    """
    Explicit OPTIONS handler as fallback for CORS preflight requests.
    CORSMiddleware should handle this, but this ensures it works on Railway.
    """
    origin = request.headers.get("origin")
    
    # Check if origin is allowed
    if origin and not is_origin_allowed(origin, cors_origins):
        logger.warning(f"CORS: Origin not allowed in OPTIONS handler - {origin}")
        return Response(
            status_code=403,
            content="Origin not allowed",
            headers={"Access-Control-Allow-Origin": "null"}
        )
    
    # Build CORS headers
    # When credentials are enabled, must explicitly list headers (cannot use "*")
    requested_headers = request.headers.get("access-control-request-headers", "")
    if allow_creds:
        # Explicitly allow common headers when credentials are enabled
        allowed_headers_list = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
        # If specific headers were requested, include them if they're safe
        if requested_headers:
            # Add requested headers that aren't already in the list
            requested_list = [h.strip().lower() for h in requested_headers.split(",")]
            existing_list = [h.strip().lower() for h in allowed_headers_list.split(",")]
            for req_header in requested_list:
                if req_header not in existing_list:
                    allowed_headers_list += f", {req_header}"
        cors_allow_headers = allowed_headers_list
    else:
        cors_allow_headers = requested_headers if requested_headers else "*"
    
    cors_headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD",
        "Access-Control-Allow-Headers": cors_allow_headers,
        "Access-Control-Max-Age": "3600",
    }
    
    # Set origin header
    if "*" in cors_origins:
        cors_headers["Access-Control-Allow-Origin"] = "*"
        cors_headers["Access-Control-Allow-Credentials"] = "false"
    elif origin and is_origin_allowed(origin, cors_origins):
        cors_headers["Access-Control-Allow-Origin"] = origin
        if allow_creds:
            cors_headers["Access-Control-Allow-Credentials"] = "true"
    elif origin:
        # Fallback: allow the origin if it's a valid URL
        cors_headers["Access-Control-Allow-Origin"] = origin
        if allow_creds:
            cors_headers["Access-Control-Allow-Credentials"] = "true"
    else:
        cors_headers["Access-Control-Allow-Origin"] = "*"
    
    logger.info(f"[CORS] OPTIONS handler: {full_path} | Origin: {origin} | Headers set")
    return Response(status_code=200, headers=cors_headers)

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
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])
app.include_router(network.router, prefix="/api/v1/network", tags=["Network Monitoring"])
app.include_router(network_ws.router, prefix="/api/v1/network", tags=["Network WebSocket"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])


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


# Global exception handler to ensure CORS headers are set even on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures CORS headers are set."""
    origin = request.headers.get("origin")
    
    # Build error response
    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = 500
        detail = "Internal server error"
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    response = JSONResponse(
        status_code=status_code,
        content={"detail": detail}
    )
    
    # Add CORS headers if origin is present
    if origin:
        if is_origin_allowed(origin, cors_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            if allow_creds:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
            if allow_creds:
                response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
            else:
                response.headers["Access-Control-Allow-Headers"] = "*"
        elif ".railway.app" in origin or ".railway.xyz" in origin:
            # Fallback for Railway domains
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
    
    return response


