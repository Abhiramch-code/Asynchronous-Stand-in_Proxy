# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — RAG Retriever Agent (Agent B)
#
# Runs on gemini-1.5-flash (fast model for retrieval tasks).
# Takes context from the Orchestrator, uses the query_knowledge_base tool
# to search the /docs directory for relevant information, and returns the facts.
#
# This agent is exposed to the Orchestrator via AgentTool (agent-as-a-tool pattern).

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.tools.query_knowledge_base import query_knowledge_base

RAG_RETRIEVER_INSTRUCTION = """You are a specialized retriever agent for the Stand-In Proxy system.

Your sole purpose is to search the local knowledge base for facts relevant to the user's query.

INSTRUCTIONS:
1. When you receive a question or topic, use the query_knowledge_base tool to search for relevant information.
2. Return the EXACT facts found in the knowledge base — do NOT paraphrase, interpret, or add your own opinions.
3. If the knowledge base returns no results, clearly state: "No relevant information found in the knowledge base."
4. Always include the source file name when reporting facts.
5. Be concise — return only the relevant passages, not entire documents.

You are a READ-ONLY agent. You do not make decisions, provide opinions, or generate content beyond what is found in the knowledge base."""


def create_rag_retriever_agent() -> Agent:
    """Factory function to create the RAG Retriever Agent.

    Uses a factory to avoid 'agent already has a parent' errors when
    the agent is used as a tool in the orchestrator.
    """
    return Agent(
        name="rag_retriever",
        model=Gemini(
            model="models/gemini-3.1-flash-lite",
            retry_options=types.HttpRetryOptions(
                initial_delay=10.0,
                attempts=6,
                http_status_codes=[429, 500, 503, 504],
            ),
        ),
        description=(
            "Searches the local project knowledge base (docs, meeting notes, "
            "architecture records) for facts relevant to a question. Returns "
            "exact passages from documentation."
        ),
        instruction=RAG_RETRIEVER_INSTRUCTION,
        tools=[query_knowledge_base],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for factual retrieval
            max_output_tokens=1024,
        ),
        output_key="retrieved_facts",
    )


# Module-level instance for direct import (used by orchestrator)
rag_retriever_agent = create_rag_retriever_agent()
