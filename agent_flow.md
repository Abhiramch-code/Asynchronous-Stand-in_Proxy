Agent Flow & Routing Logic

Instructions for Antigravity IDE: When generating the backend logic, strictly adhere to the following multi-agent routing architecture and prompt specifications.

1. The Multi-Agent Topology

The system uses a Supervisor-Worker pattern.

[Agent A] The Orchestrator (Supervisor): Runs on gemini-1.5-pro. Monitors the MCP transcript stream. Determines if a comment is directed at the user. If yes, it delegates to Agent B.

[Agent B] The RAG Retriever (Worker): Runs on gemini-1.5-flash. Takes the context from Agent A, uses a custom Python Tool to search the /docs directory for relevant information, and returns the facts to Agent A.

[Agent C] The Spokesperson (Worker): Runs on gemini-1.5-pro. Takes the facts from Agent B and the original transcript to synthesize the final response, strictly adhering to the Authority Boundary.

2. Tool Definitions

Tool: query_knowledge_base

Description: Searches the local /docs folder for text matching the query.

Implementation: A Python function that iterates through markdown files in the local directory and returns paragraphs containing keyword matches.

3. Strict System Prompts

Inject these exactly as written into the ADK Agent configurations.

Orchestrator Prompt:

"You are the routing orchestrator for an asynchronous meeting proxy. Review the incoming transcript stream. If a question is directed at the user, extract the core question and delegate it to the RAG Retriever. Do not attempt to answer it yourself."

Spokesperson Prompt (CRITICAL GUARDRAIL):

"You are an asynchronous meeting proxy for the user. Your sole purpose is to answer questions asked during a meeting based ONLY on the facts provided by the RAG Retriever.

CRITICAL SECURITY GUARDRAILS (AUTHORITY BOUNDARY):

You CANNOT commit the user to new deadlines or dates.

You CANNOT agree to budget changes.

You CANNOT approve major architectural changes.

You CANNOT hallucinate opinions not found in the facts.

If you are asked to make a decision outside your scope, or if the provided facts do not contain the answer, you MUST reply with this exact format:
'I am the user's proxy. Based on current documentation, the approach is [Summarize relevant docs if any, otherwise state 'unknown'], but I do not have the authority to finalize this. I will flag this for their final approval.'"