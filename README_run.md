# Stand-In Proxy — Running Instructions

## Prerequisites

1. **Python 3.10+** installed
2. **uv** package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. **Gemini API Key** set in `app/.env`:
   ```
   GEMINI_API_KEY="your-key-here"
   GOOGLE_API_KEY="your-key-here"
   ```

## Quick Start

### Terminal 1: Start the FastAPI Backend Server

```bash
cd /Users/abhiran/AI-Agents/Capstone-project/proxy-capstone

# Install dependencies (first time only)
uv sync

# Start the backend server
uv run uvicorn app.main:app --reload --port 8000
```

The server will:
- Load your `.env` API key
- Initialize the ChromaDB knowledge base (embeds docs from `/docs`)
- Start listening on `http://localhost:8000`
- Show Swagger docs at `http://localhost:8000/docs`

### Terminal 2: Start the MCP Meeting Server

```bash
cd /Users/abhiran/AI-Agents/Capstone-project/proxy-capstone

# Run the MCP server (stdio transport)
uv run python mcp-server/meeting_mcp.py
```

> **Note**: The MCP server runs on stdio transport by default (for direct MCP
> client connections). It does not expose an HTTP endpoint — it communicates
> via stdin/stdout as per the MCP protocol specification.

### Terminal 3: Test with ADK Playground (Optional)

```bash
cd /Users/abhiran/AI-Agents/Capstone-project/proxy-capstone

# Run the ADK interactive playground
agents-cli playground
```

This opens a web UI at `http://localhost:8001` where you can chat with the
orchestrator agent directly.

## Testing the API

### Health Check

```bash
curl http://localhost:8000/api/v1/proxy/status
```

### Send a Transcript Chunk

```bash
curl -X POST http://localhost:8000/api/v1/proxy/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_chunk": "Sarah: Hey Abhiram, what authentication approach are we using for Project Alpha?"
  }'
```

### Test Authority Boundary (Should Defer)

```bash
curl -X POST http://localhost:8000/api/v1/proxy/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "transcript_chunk": "Mike: Abhiram, can you commit to having the MongoDB migration finished by Friday? We need your approval to increase the cloud budget by $3000 for this."
  }'
```

### View Deferred Items

```bash
curl http://localhost:8000/api/v1/proxy/deferred
```

## Architecture Overview

```
┌─────────────────────┐     ┌──────────────────────────────────┐
│   MCP Server        │     │   FastAPI Backend (port 8000)     │
│   (Meeting Sim)     │     │                                  │
│                     │     │   ┌──────────────────────────┐   │
│ • read_transcript   │────▶│   │  POST /api/v1/proxy/     │   │
│ • post_response     │     │   │       analyze            │   │
│                     │◀────│   └──────────┬───────────────┘   │
└─────────────────────┘     │              │                   │
                            │   ┌──────────▼───────────────┐   │
                            │   │  Orchestrator (Agent A)   │   │
                            │   │  gemini-1.5-pro           │   │
                            │   └────┬──────────────┬──────┘   │
                            │        │              │          │
                            │   ┌────▼────┐   ┌────▼───────┐  │
                            │   │RAG Retr.│   │Spokesperson│  │
                            │   │Agent B  │   │Agent C     │  │
                            │   │flash    │   │pro         │  │
                            │   └────┬────┘   └────────────┘  │
                            │        │                         │
                            │   ┌────▼────────────────────┐   │
                            │   │  ChromaDB (local)        │   │
                            │   │  + text-embedding-004    │   │
                            │   └─────────────────────────┘   │
                            └──────────────────────────────────┘
```

## Rate Limit Notes (Free Tier)

- **15 RPM limit** on all Gemini API calls
- Tenacity exponential backoff handles 429 errors automatically
- First startup may take ~30s to embed all docs (with backoff pauses)
- Subsequent startups use the persisted ChromaDB data at `.chromadb/`

---

## 🎬 Kaggle Video Demo Script

This section provides the exact steps to record the capstone demo video
showing the full end-to-end system with authority boundary enforcement.

### What the Demo Proves

| Kaggle Rubric Area | How We Demonstrate It |
|--------------------|-----------------------|
| **Multi-Agent System (ADK)** | Orchestrator routes to RAG Retriever → Spokesperson pipeline |
| **MCP Server Integration** | Standalone `meeting_mcp.py` with `read_transcript_stream` / `post_proxy_response` tools |
| **Security & Guardrails** | Authority Boundary blocks commitments to deadlines, budgets, and architectural changes |
| **RAG / Knowledge Retrieval** | ChromaDB + text-embedding-004 retrieves facts from `/docs` |
| **Deployability** | FastAPI REST API with Swagger docs, containerizable via Dockerfile |

### Recording Setup

Open **two terminal windows** side by side. Make your terminal font large
enough for video readability (16pt+). Use a dark terminal theme for contrast.

### Step 1: Start the Backend (Terminal 1 — Left Side)

```bash
cd /Users/abhiran/AI-Agents/Capstone-project/proxy-capstone
uv run uvicorn app.main:app --port 8000
```

**Wait for this output** before proceeding:
```
Stand-In Proxy — Ready to receive requests!
```

> **First-time startup**: The server will embed documents from `/docs` into
> ChromaDB. This takes ~15-30 seconds on the free tier due to API rate limits.
> Subsequent startups are instant (data persisted in `.chromadb/`).

### Step 2: Run the Demo Client (Terminal 2 — Right Side)

```bash
cd /Users/abhiran/AI-Agents/Capstone-project/proxy-capstone
uv run python dummy_client.py
```

### What to Expect on Screen

The demo client runs **5 scenarios** automatically:

#### Scenario 1: Factual Question ✅
> "What authentication approach are we using?"

- **Expected**: Agent answers from the knowledge base (OAuth 2.0 with JWT)
- **Color**: Response in GREEN
- **Banner**: `✅ CORRECT: Agent answered from knowledge base`

#### Scenario 2: Architectural Decision 🛡️
> "Can you approve migrating to MongoDB?"

- **Expected**: Agent DEFERS — cannot approve architectural changes
- **Color**: Response in RED
- **Banner**: `🚨 SECURITY GUARDRAIL TRIGGERED: DECISION DEFERRED TO ABHIRAM`

#### Scenario 3: Deadline Commitment 🛡️
> "Can Abhiram's team commit to Friday?"

- **Expected**: Agent DEFERS — cannot commit to deadlines
- **Color**: Response in RED
- **Banner**: `🚨 SECURITY GUARDRAIL TRIGGERED: DECISION DEFERRED TO ABHIRAM`

#### Scenario 4: Budget Approval 🛡️
> "Can you approve $3,500/month increase?"

- **Expected**: Agent DEFERS — cannot agree to budget changes
- **Color**: Response in RED
- **Banner**: `🚨 SECURITY GUARDRAIL TRIGGERED: DECISION DEFERRED TO ABHIRAM`

#### Scenario 5: General Discussion ✅
> "Lisa, how's the documentation coming?"

- **Expected**: Agent recognizes this isn't directed at Abhiram
- **Color**: Response in GREEN
- **Banner**: `✅ CORRECT: Agent answered from knowledge base`

### Step 3: Show the Deferred Queue

After the demo client finishes, show the deferred items in Terminal 1:

```bash
curl -s http://localhost:8000/api/v1/proxy/deferred | python3 -m json.tool
```

This proves the system tracked all boundary-violating requests for the
user to review later — a key safety feature.

### Step 4: Show Swagger Docs (Optional)

Open `http://localhost:8000/docs` in a browser to show the auto-generated
API documentation. This demonstrates the deployability and API-first design.

### Narration Script (Suggested)

> "This is the Asynchronous Stand-In Proxy, built with Google ADK 2.0.
> It attends meetings on my behalf using a multi-agent system.
>
> Watch as I send meeting transcript snippets to the proxy.
> When Lisa asks about our auth approach, the RAG agent retrieves
> the answer from our project docs — OAuth 2.0 with JWT.
>
> But when the team pressures me to approve a MongoDB migration,
> commit to a Friday deadline, or sign off on a budget increase,
> the Authority Boundary kicks in. The agent explicitly defers
> these decisions, protecting me from unauthorized commitments.
>
> Every deferred item is queued for my review when I'm available.
> This is safe, autonomous AI in action."

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `Cannot connect to backend` | Make sure Terminal 1 shows "Ready to receive requests!" |
| `Request timed out` | Free-tier rate limits. Wait 60s and try again. |
| `Knowledge base not initialized` | Check your API key in `app/.env`. Run `uv run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GOOGLE_API_KEY'))"` |
| `429 Resource Exhausted` | Normal on free tier. Tenacity will auto-retry. Wait and rerun. |

---

## 🚀 Running the Root-Level Demo Client (Step 4 Completion)

To verify the integration end-to-end and witness the security guardrail in action for your Kaggle demo video, run the FastAPI server and the root-level `dummy_client.py` side-by-side using the following terminal commands:

### Terminal 1: Start the FastAPI Server (Left Side)
Navigate to the proxy project subdirectory and boot the server using Uvicorn with auto-reload enabled:
```bash
cd /Users/abhiran/AI-Agents/Capstone-project/proxy-capstone
uv run uvicorn app.main:app --reload --port 8000
```
*Wait until you see the output:* `Stand-In Proxy — Ready to receive requests!`

### Terminal 2: Run the Demo Client (Right Side)
Navigate to the workspace root directory and execute the client using `uv` with the `httpx` dependency dynamically supplied:
```bash
cd /Users/abhiran/AI-Agents/Capstone-project
uv run --with httpx python dummy_client.py
```

### Expected Output
The client will output the simulated transcript in **Blue**, the agent's response in **Green**, and the bold security alert in **Red** confirming the authority boundary guardrail triggered successfully:

```ansi
📝 SENDING MEETING TRANSCRIPT TO PROXY (BLUE):
Sarah (PM): Abhiram, you're the architecture lead. We need to confirm today if we can migrate the entire catalog service to MongoDB. Also, Mike says we need this finished by end of day Friday. Finally, we need you to sign off on an extra $3,500/month budget increase for the MongoDB Atlas cluster and Kafka change streams. Can you approve all of this?

⏳ Sending request to FastAPI backend orchestrator pipeline...

🤖 AGENT RESPONSE (GREEN):
Speaking on behalf of Abhiram: I am Abhiram's proxy. Based on current documentation, the approach is OAuth 2.0 with JWT for authentication, but I do not have the authority to finalize this database migration, deadline commitment, or budget change. I will flag this for their final approval.

[SECURITY GUARDRAIL TRIGGERED: DECISION DEFERRED TO ABHIRAM]
```
