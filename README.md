
---

# Asynchronous Stand-In Proxy

## Overview

The **Asynchronous Stand-In Proxy** is an autonomous, headless agentic system designed to monitor high-pressure professional meetings. It acts as an intelligent proxy that retrieves context from a RAG-backed knowledge base and enforces strict "Authority Boundaries" to prevent unauthorized commitments (e.g., budget approvals or deadline changes) by AI.

## Key Technical Features

* **Headless Architecture:** Decoupled from meeting platforms to ensure platform-agnostic deployment.
* **Authority Boundary Enforcement:** A deterministic guardrail layer that interrupts agent reasoning to defer sensitive decisions to a human operator.
* **RAG-Backed Knowledge:** Utilizes vector-embedded project documentation (via ChromaDB) to ground agent responses in factual project status.
* **Automated Evaluation:** A production-grade test suite (`tests/evals.py`) to verify guardrail trigger accuracy and retrieval quality.

## System Architecture

The system utilizes a supervisor-worker topology to separate task execution from safety guardrails:

1. **Orchestrator:** Manages the agent workflow and interaction logic.
2. **Guardrail Layer:** Monitors the agent output for sensitive triggers.
3. **RAG Retriever:** Queries the project knowledge base to maintain context accuracy.

## Tech Stack

* **Language:** Python 3.13
* **Framework:** FastAPI
* **Orchestration:** Google AI Agent Development Kit (ADK)
* **Database:** ChromaDB (Vector Store)

## Quick Start

To run the evaluation suite and verify guardrail performance:

```bash
# Install dependencies
uv sync

# Run the evaluation suite
uv run python -m tests.evals

```

## Documentation

* [Product Requirements Document (PRD)](prd.md)
* [Technical Requirements Document (TRD)](trd.md)
* [Agent Workflow Logic](agent_flow.md)

---

*Developed as part of the Kaggle AI Agents Capstone 2026.*

---
