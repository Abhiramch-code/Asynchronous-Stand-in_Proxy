# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Agent Definitions
#
# This package contains the multi-agent topology:
#   - Orchestrator (Agent A): Supervisor — monitors transcript, routes questions
#   - RAG Retriever (Agent B): Worker — searches /docs knowledge base
#   - Spokesperson (Agent C): Worker — synthesizes responses with authority boundary
#
# The Orchestrator uses Agent-as-a-Tool pattern (AgentTool) to invoke
# the sub-agents while staying in control of the conversation flow.

from .orchestrator import create_orchestrator_agent, orchestrator_agent
from .rag_retriever import create_rag_retriever_agent, rag_retriever_agent
from .spokesperson import create_spokesperson_agent, spokesperson_agent

__all__ = [
    "orchestrator_agent",
    "rag_retriever_agent",
    "spokesperson_agent",
    "create_orchestrator_agent",
    "create_rag_retriever_agent",
    "create_spokesperson_agent",
]
