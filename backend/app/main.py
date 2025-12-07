"""
CyberNexus - Main Application Entry Point

Enterprise Threat Intelligence Platform
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings, init_directories
from app.api.routes import auth, entities, graph, threats, timeline, reports, websocket, capabilities


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {
            "api": "operational",
            "graph_engine": "operational",
            "collectors": "operational",
            "websocket": "operational"
        }
    }


