# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Application Entry Point
#
# This is the main entry point for the Stand-In Proxy backend.
# It initializes the FastAPI app with CORS middleware, includes the
# API router, and initializes the ChromaDB knowledge base on startup.
#
# Run with: uvicorn app.main:app --reload --port 8000

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

# Load environment variables FIRST — before any other imports
# that might need GEMINI_API_KEY or GOOGLE_API_KEY
load_dotenv(override=True)

# Re-export GEMINI_API_KEY as GOOGLE_API_KEY if needed by ADK
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.server.api import router as proxy_router  # noqa: E402
from app.tools.query_knowledge_base import initialize_knowledge_base  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application Lifespan — startup/shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application startup and shutdown lifecycle.

    On startup:
      - Initialize the ChromaDB knowledge base with document embeddings
    On shutdown:
      - Clean up resources
    """
    # --- STARTUP ---
    logger.info("=" * 60)
    logger.info("Stand-In Proxy — Starting up...")
    logger.info("=" * 60)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    logger.info(f"API Key configured: {'Yes' if api_key else 'NO — set GEMINI_API_KEY in .env!'}")

    try:
        initialize_knowledge_base()
        logger.info("Knowledge base initialized successfully.")
    except Exception as e:
        logger.warning(
            f"Knowledge base initialization deferred: {e}. "
            "It will be initialized on first query."
        )

    logger.info("Stand-In Proxy — Ready to receive requests!")
    logger.info("=" * 60)

    yield  # Application is running

    # --- SHUTDOWN ---
    logger.info("Stand-In Proxy — Shutting down...")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Asynchronous Stand-In Proxy",
    description=(
        "An autonomous concierge agent that attends digital meetings on behalf "
        "of a busy professional. Uses a multi-agent ADK system with RAG-backed "
        "knowledge retrieval and strict authority boundary guardrails."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware — allow future React frontend to communicate
# ---------------------------------------------------------------------------
# In production, restrict origins to your actual frontend domain
_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include API Router
# ---------------------------------------------------------------------------
app.include_router(proxy_router)


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    """Root endpoint — basic service information."""
    return {
        "service": "Asynchronous Stand-In Proxy",
        "version": "0.1.0",
        "docs": "/docs",
        "api": "/api/v1/proxy/status",
    }


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
