from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import sys
import time

from app.config import settings, init_directories
from app.api.routes import auth, entities, graph, threats, timeline, reports, websocket, capabilities, company, darkweb, dashboard, network, network_ws, notifications, scheduled_searches
from app.utils import check_tor_connectivity
from app.utils.tor_status_cache import get_tor_status_cache
from app.middleware.network_blocker import NetworkBlockerMiddleware
from app.middleware.network_logger import NetworkLoggerMiddleware
from app.services.tunnel_analyzer import get_tunnel_analyzer
from app.core.database.database import init_db, close_db
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks
import asyncio

_tor_check_executor: ThreadPoolExecutor = None


def get_tor_check_executor() -> ThreadPoolExecutor:
    global _tor_check_executor
    if _tor_check_executor is None:
        _tor_check_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tor-status-check")
    return _tor_check_executor


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    logger.remove()
    logger.add(
        sys.stderr,
        format=settings.LOG_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    init_directories()
    logger.info("Data directories initialized")
    
    logger.info("Initializing database connection...")
    init_db()
    logger.info("Database connection initialized")
    
    logger.info("Running database migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config("migrations/alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        logger.warning("Continuing startup despite migration errors")
    
    logger.info("Initializing Tor status cache...")
    tor_cache = get_tor_status_cache()
    
    logger.info("Checking Tor proxy connectivity...")
    tor_status = check_tor_connectivity()
    tor_cache.update_status(tor_status)
    
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
    
    async def update_tor_status_periodically():
        update_interval = 60
        while True:
            try:
                await asyncio.sleep(update_interval)
                if not tor_cache.is_checking():
                    logger.debug("Periodic Tor status cache update triggered")
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, tor_cache.update_status_async)
            except asyncio.CancelledError:
                logger.info("Tor status cache background task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Tor status cache background task: {e}", exc_info=True)
                await asyncio.sleep(update_interval)
    
    tor_status_task = asyncio.create_task(update_tor_status_periodically())
    logger.info("Tor status cache background update task started")
    
    logger.info("Initializing custom DSA structures...")
    
    logger.info("Initializing scheduler service...")
    try:
        from app.services.scheduler import get_scheduler_service
        scheduler = get_scheduler_service()
        await scheduler.initialize()
        logger.info("Scheduler service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler service: {e}", exc_info=True)
    
    logger.info(f"{settings.APP_NAME} is ready!")
    
    yield
    
    tor_status_task.cancel()
    try:
        await tor_status_task
    except asyncio.CancelledError:
        pass
    logger.info("Tor status cache background task stopped")
    
    try:
        from app.services.scheduler import get_scheduler_service
        scheduler = get_scheduler_service()
        await scheduler.shutdown()
        logger.info("Scheduler service shut down")
    except Exception as e:
        logger.warning(f"Error shutting down scheduler service: {e}")
    
    logger.info(f"Shutting down {settings.APP_NAME}...")
    
    try:
        from app.services.browser_capture import cleanup_all_browser_instances
        await cleanup_all_browser_instances()
        logger.info("Browser service instances cleaned up")
    except Exception as e:
        logger.warning(f"Error during browser service cleanup: {e}")
    
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    description="",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

def get_cors_origins():
    origins_str = settings.CORS_ORIGINS
    logger.debug(f"[CORS] Raw CORS_ORIGINS from settings: '{origins_str}'")
    
    if origins_str == "*":
        logger.info("[CORS DEBUG HYP-A] Using wildcard '*' - all origins allowed, credentials disabled")
        return ["*"], False
    
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    logger.info(f"[CORS DEBUG HYP-A] Parsed {len(origins)} origins from string: {origins}")
    
    validated_origins = []
    for origin in origins:
        if origin.startswith(("http://", "https://")):
            validated_origins.append(origin)
        else:
            logger.warning(f"[CORS DEBUG HYP-A] Invalid CORS origin format (must start with http:// or https://): {origin}")
    
    if not validated_origins:
        logger.warning("[CORS DEBUG HYP-A] No valid origins found, defaulting to '*' (all origins, no credentials)")
        return ["*"], False
    
    logger.info(f"[CORS DEBUG HYP-A] Using {len(validated_origins)} explicit origins with credentials enabled: {validated_origins}")
    return validated_origins, True


def is_origin_allowed(origin: str, allowed_origins: list) -> bool:
    if not origin:
        return False
    
    if ".railway.app" in origin or ".railway.xyz" in origin:
        return True
    
    if "*" in allowed_origins:
        return True
    
    if origin in allowed_origins:
        return True
    
    for allowed in allowed_origins:
        if allowed.startswith("*."):
            domain = allowed[2:]
            if origin.endswith(domain):
                return True
    
    return False

cors_origins, allow_creds = get_cors_origins()

logger.info(f"CORS configuration: origins={cors_origins}, allow_credentials={allow_creds}, environment={settings.ENVIRONMENT}, debug={settings.CORS_DEBUG}")



class CORSDebugMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            is_allowed_val = is_origin_allowed(origin, cors_origins) if origin else None
            logger.debug(f"[CORS] {method} {path} | Origin: '{origin}' | Allowed: {is_allowed_val}")
        
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            logger.debug(
                f"CORS Request: {method} {path} | "
                f"Origin: {origin} | "
                f"Allowed: {is_origin_allowed(origin, cors_origins) if origin else 'N/A'}"
            )
        
        response = await call_next(request)
        
        if settings.CORS_DEBUG and (method == "OPTIONS" or origin):
            cors_response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith("access-control-")
            }
            logger.debug(f"[CORS] Response: {method} {path} | Status: {response.status_code} | CORS Headers: {cors_response_headers}")
        
        if settings.CORS_DEBUG and origin:
            cors_headers = {
                k: v for k, v in response.headers.items()
                if k.lower().startswith("access-control-")
            }
            if cors_headers:
                logger.debug(f"CORS Response Headers: {cors_headers}")
        
        return response


class CORSEnforcementMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        response = await call_next(request)
        
        has_cors_headers = any(
            k.lower().startswith("access-control-") 
            for k in response.headers.keys()
        )
        
        if origin:
            if not has_cors_headers:
                logger.warning(
                    f"[CORS ENFORCE] Missing CORS headers on {method} {path}, "
                    f"adding explicitly. Origin: {origin}"
                )
            
            if is_origin_allowed(origin, cors_origins):
                response.headers["Access-Control-Allow-Origin"] = origin
                if allow_creds:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                if allow_creds:
                    response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
                else:
                    response.headers["Access-Control-Allow-Headers"] = "*"
                if not has_cors_headers:
                    logger.info(f"[CORS ENFORCE] Added CORS headers for {method} {path}")
            else:
                if ".railway.app" in origin or ".railway.xyz" in origin:
                    logger.info(f"[CORS ENFORCE] Allowing Railway domain as fallback: {origin}")
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                    response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
                else:
                    logger.warning(f"[CORS ENFORCE] Origin {origin} not allowed, not adding CORS headers")
        
        return response


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
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=allowed_headers,
    expose_headers=["*"],
    max_age=3600,
)
logger.info("[CORS] CORSMiddleware added - will attempt to set CORS headers")

app.add_middleware(CORSEnforcementMiddleware)
logger.info("[CORS] CORSEnforcementMiddleware added - will enforce CORS headers if missing")

app.add_middleware(CORSDebugMiddleware)
logger.info("[CORS] CORSDebugMiddleware added - will log CORS request/response details")

if settings.NETWORK_ENABLE_LOGGING or settings.NETWORK_ENABLE_BLOCKING:
    tunnel_analyzer = None
    if settings.NETWORK_ENABLE_TUNNEL_DETECTION:
        tunnel_analyzer = get_tunnel_analyzer()
    
    logger.info("[Network] NetworkLoggerMiddleware will be added")
    
    if settings.NETWORK_ENABLE_BLOCKING:
        app.add_middleware(NetworkBlockerMiddleware)
        logger.info("[Network] NetworkBlockerMiddleware added")
    
    app.add_middleware(NetworkLoggerMiddleware, tunnel_analyzer=tunnel_analyzer)
    logger.info("[Network] NetworkLoggerMiddleware added")

@app.options("/{full_path:path}")
async def options_handler(request: Request, full_path: str):
    origin = request.headers.get("origin")
    
    if origin and not is_origin_allowed(origin, cors_origins):
        logger.warning(f"CORS: Origin not allowed in OPTIONS handler - {origin}")
        return Response(
            status_code=403,
            content="Origin not allowed",
            headers={"Access-Control-Allow-Origin": "null"}
        )
    
    requested_headers = request.headers.get("access-control-request-headers", "")
    if allow_creds:
        allowed_headers_list = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
        if requested_headers:
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
    
    if "*" in cors_origins:
        cors_headers["Access-Control-Allow-Origin"] = "*"
        cors_headers["Access-Control-Allow-Credentials"] = "false"
    elif origin and is_origin_allowed(origin, cors_origins):
        cors_headers["Access-Control-Allow-Origin"] = origin
        if allow_creds:
            cors_headers["Access-Control-Allow-Credentials"] = "true"
    elif origin:
        cors_headers["Access-Control-Allow-Origin"] = origin
        if allow_creds:
            cors_headers["Access-Control-Allow-Credentials"] = "true"
    else:
        cors_headers["Access-Control-Allow-Origin"] = "*"
    
    logger.info(f"[CORS] OPTIONS handler: {full_path} | Origin: {origin} | Headers set")
    return Response(status_code=200, headers=cors_headers)

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
app.include_router(scheduled_searches.router, prefix="/api/v1/scheduled-searches", tags=["Scheduled Searches"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def health_check(background_tasks: BackgroundTasks):
    tor_cache = get_tor_status_cache()
    tor_status = tor_cache.get_status()
    
    if tor_cache.is_stale(max_age_seconds=60) and not tor_cache.is_checking():
        logger.debug("Tor status cache is stale, triggering background update")
        executor = get_tor_check_executor()
        executor.submit(tor_cache.update_status_async)
    
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
            "error": tor_status.get("error"),
            "cache_age_seconds": (
                None if tor_status.get("last_updated") is None
                else round(time.time() - tor_status["last_updated"], 1)
            )
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    
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
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "accept, accept-language, content-type, content-length, authorization, x-requested-with, x-csrf-token, x-api-key"
    
    return response


