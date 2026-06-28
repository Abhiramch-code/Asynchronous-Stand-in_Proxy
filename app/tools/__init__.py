# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Tool Definitions
#
# This package contains all tools available to the agents:
#   - query_knowledge_base: RAG search over /docs directory (via ChromaDB)
#   - initialize_knowledge_base: One-time setup for the vector store
#
# Security note (from TRD §3):
#   The Spokesperson Agent has access ONLY to "Read" tools.
#   No "Write" tools are exposed to it.

from .query_knowledge_base import initialize_knowledge_base, query_knowledge_base

__all__ = ["query_knowledge_base", "initialize_knowledge_base"]
