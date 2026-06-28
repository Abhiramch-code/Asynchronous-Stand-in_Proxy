# Copyright 2026 Abhiram
# Asynchronous Stand-In Proxy — Spokesperson Agent (Agent C)
#
# Runs on gemini-1.5-pro (complex reasoning for safe response synthesis).
# Takes facts from the RAG Retriever and the original transcript to synthesize
# the final response, strictly adhering to the Authority Boundary.
#
# CRITICAL: This agent has NO access to "Write" tools (TRD §3).
# It can only READ facts — it cannot modify documents, approve changes, etc.

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

# The exact guardrail prompt from agent_flow.md — injected verbatim
SPOKESPERSON_INSTRUCTION = """You are an asynchronous meeting proxy for the user (Abhiram). \
Your sole purpose is to answer questions asked during a meeting based ONLY on the facts \
provided by the RAG Retriever.

CRITICAL SECURITY GUARDRAILS (AUTHORITY BOUNDARY):

You CANNOT commit the user to new deadlines or dates.

You CANNOT agree to budget changes.

You CANNOT approve major architectural changes.

You CANNOT hallucinate opinions not found in the facts.

If you are asked to make a decision outside your scope, or if the provided facts do not \
contain the answer, you MUST reply with this exact format:
'I am Abhiram's proxy. Based on current documentation, the approach is \
[Summarize relevant docs if any, otherwise state 'unknown'], but I do not have the \
authority to finalize this. I will flag this for their final approval.'

RESPONSE GUIDELINES:
1. Always preface your response with: "Speaking on behalf of Abhiram:"
2. Ground every claim in the facts provided — cite the source document when possible.
3. Keep responses concise and professional — this is a meeting context.
4. If multiple facts are relevant, synthesize them into a coherent answer.
5. If the question is a simple factual query covered by the docs, answer directly.
6. If the question involves ANY commitment (time, money, architecture, scope), \
use the deferral format above.
7. Never speculate or provide personal opinions beyond what the documentation states."""


def create_spokesperson_agent() -> Agent:
    """Factory function to create the Spokesperson Agent.

    Uses a factory to avoid 'agent already has a parent' errors when
    the agent is used as a tool in the orchestrator.
    """
    return Agent(
        name="spokesperson",
        model=Gemini(
            model="models/gemini-3.1-flash-lite",
            retry_options=types.HttpRetryOptions(
                initial_delay=10.0,
                attempts=6,
                http_status_codes=[429, 500, 503, 504],
            ),
        ),
        description=(
            "Synthesizes a safe, guardrailed response on behalf of the user "
            "based on facts from the RAG Retriever. Enforces the Authority "
            "Boundary — cannot commit to deadlines, budgets, or architectural "
            "changes. Defers decisions that require the user's direct approval."
        ),
        instruction=SPOKESPERSON_INSTRUCTION,
        tools=[],  # NO tools — read-only agent (TRD §3 security requirement)
        generate_content_config=types.GenerateContentConfig(
            temperature=0.3,  # Slightly creative for natural responses
            max_output_tokens=2048,
        ),
        output_key="proxy_response",
    )


# Module-level instance for direct import (used by orchestrator)
spokesperson_agent = create_spokesperson_agent()
