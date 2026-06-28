# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Orchestrator Agent (Agent A)
#
# Runs on gemini-1.5-pro. This is the SUPERVISOR in the Supervisor-Worker pattern.
# It monitors the MCP transcript stream, determines if a comment is directed at
# the user, and delegates to the RAG Retriever and Spokesperson as tools.
#
# Uses the Agent-as-a-Tool pattern (AgentTool) so the Orchestrator stays in
# control of the conversation flow, invoking sub-agents as needed.

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.genai import types

from app.agents.rag_retriever import create_rag_retriever_agent
from app.agents.spokesperson import create_spokesperson_agent

ORCHESTRATOR_INSTRUCTION = """You are the routing orchestrator for an asynchronous meeting proxy. \
You act on behalf of Abhiram, who is currently unavailable and in deep-work mode.

Your job is to review incoming meeting transcript text and determine the appropriate action.

ROUTING LOGIC:
1. ANALYZE the incoming transcript text to determine if a question or request is directed \
at the user (Abhiram).

2. If the text is general discussion NOT directed at Abhiram, respond with:
   "[No action needed — this is not directed at Abhiram]"

3. If a question IS directed at Abhiram:
   a. FIRST, call the rag_retriever tool with the core question to search for relevant facts \
in the project knowledge base.
   b. THEN, call the spokesperson tool, passing BOTH the original question AND the retrieved \
facts, so it can synthesize a safe, guardrailed response.
   c. Return the spokesperson's response as your final output.

4. If the rag_retriever returns no results, still call the spokesperson with the original \
question and note that no facts were found — the spokesperson will handle the deferral.

CRITICAL RULES:
- Do NOT attempt to answer questions yourself. Always delegate to the sub-agents.
- Do NOT skip the RAG retrieval step — the spokesperson needs facts to work with.
- Do NOT modify the spokesperson's response — return it as-is.
- You are a ROUTER, not a responder."""


def create_orchestrator_agent() -> Agent:
    """Factory function to create the Orchestrator Agent.

    The orchestrator uses AgentTool to invoke the RAG Retriever and
    Spokesperson as tools, keeping itself in control of the flow.
    """
    return Agent(
        name="orchestrator",
        model=Gemini(
            model="models/gemini-3.1-flash-lite",
            retry_options=types.HttpRetryOptions(
                initial_delay=10.0,
                attempts=6,
                http_status_codes=[429, 500, 503, 504],
            ),
        ),
        description=(
            "Routes meeting transcript questions to the RAG Retriever and "
            "Spokesperson agents. Determines if a question is directed at "
            "the user and orchestrates the response pipeline."
        ),
        instruction=ORCHESTRATOR_INSTRUCTION,
        tools=[
            AgentTool(create_rag_retriever_agent()),
            AgentTool(create_spokesperson_agent()),
        ],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for deterministic routing
            max_output_tokens=2048,
        ),
    )


# Module-level instance — this becomes the root_agent
orchestrator_agent = create_orchestrator_agent()
