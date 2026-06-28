Technical Requirements Document (TRD)

1. Technology Stack

Agent Framework: Google Agent Development Kit (ADK 2.0)

Agent CLI: google-agents-cli for scaffolding and local evaluation.

Backend Runtime: Python 3.10+ (Aligning with Kaggle's ADK standard)

API / Server: FastAPI (to serve the ADK orchestration endpoints)

Integration: Model Context Protocol (MCP) Server using Python SDK

LLM Models: gemini-1.5-pro (for complex orchestration and guardrails), gemini-1.5-flash (for fast data retrieval/RAG).

2. System Architecture

The repository will be structured using agents-cli scaffold to maintain enterprise-grade organization.

2.1 Project Directory Structure

/proxy-capstone
│
├── /backend (FastAPI + ADK 2.0)
│   ├── /app
│   │   ├── /agents       # Defines LlmAgent configurations
│   │   ├── /tools        # Defines RAG and File-System tools
│   │   ├── /server       # FastAPI endpoints
│   │   └── main.py       # Application entry point
│   └── pyproject.toml    # Dependencies (google-adk, fastapi, uvicorn)
│
├── /mcp-server
│   ├── meeting_mcp.py    # MCP Server simulating transcript streams
│   └── mcp_config.json
│
└── /docs                 # Local knowledge base for the RAG agent


3. Security Implementation (The "Authority Boundary")

To secure the 70 Implementation points, the system employs Prompt-Level Sandboxing.

The Spokesperson Agent will not have access to any "Write" tools.

It will only have access to "Read" tools (the RAG query).

A pre-commit hook will be installed to scan for hardcoded API keys (shifting security left).

4. MCP Server Specification

The MCP Server (meeting_mcp.py) will expose two core capabilities to the ADK orchestrator:

read_transcript_stream: Returns the last 5 lines of the simulated meeting.

post_proxy_response: Accepts a string and logs it to the simulated meeting chat.