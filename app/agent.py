# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Root Agent Definition
#
# This file is the ADK entry point. It defines the root_agent that the
# ADK framework uses as the primary execution entry point.
#
# The root_agent is the Orchestrator, which delegates to:
#   - RAG Retriever (Agent B) via AgentTool
#   - Spokesperson (Agent C) via AgentTool

import logging
import os

from dotenv import load_dotenv
from google.adk.apps import App

# Load environment variables FIRST — before any agent imports that
# might need GOOGLE_API_KEY for model initialization
load_dotenv(override=True)

# Re-export GEMINI_API_KEY as GOOGLE_API_KEY if needed by ADK
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

from app.agents.orchestrator import orchestrator_agent  # noqa: E402
from app.tools.query_knowledge_base import initialize_knowledge_base  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the knowledge base (ChromaDB + embeddings) on module load
# This indexes documents from /docs into the vector store
try:
    initialize_knowledge_base()
    logger.info("Knowledge base initialized successfully.")
except Exception as e:
    logger.warning(
        f"Knowledge base initialization deferred: {e}. "
        "It will be initialized on first query."
    )

# The root agent is the Orchestrator — ADK framework uses this as the entry point
root_agent = orchestrator_agent

# ADK App registration — name MUST match the agent directory name ("app")
app = App(
    root_agent=root_agent,
    name="app",
)
