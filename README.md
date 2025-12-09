🧠 Autonomous Customer Support Agent (Agentic AI)

An end-to-end, autonomous customer support agent built with local LLMs, LangChain ReAct, FastAPI, SQLite, Chroma, and Stripe.
Designed to look up orders, trigger refunds, search FAQs, and provide instant customer resolutions — all without human intervention.

This repository contains the planned architecture, tech stack, and implementation roadmap.
(Code implementation will be added in upcoming commits.)

🚀 Features 

Local LLM reasoning using LLaMA 3 / Mistral via Ollama
LangChain ReAct agent for structured reasoning + safe tool execution
SQLite operational database (orders, customers, inventory)
Chroma vector store for semantic FAQ & policy retrieval
Stripe API integration (test mode refunds)
FastAPI backend to orchestrate the agent
Slack/Web Chat interface for live demo
Safe & verified workflows for refunds, replacements, order status
Local + low-cost architecture (no paid APIs required)

| Layer               | Technology                     |
| ------------------- | ------------------------------ |
| **Backend**         | FastAPI                        |
| **AI Engine**       | LLaMA 3 / Mistral (via Ollama) |
| **Agent Framework** | LangChain ReAct Agent          |
| **Database**        | SQLite                         |
| **Vector Store**    | Chroma                         |
| **Payments**        | Stripe (Test Mode)             |
| **Channels**        | Slack API / Web UI             |
| **Environment**     | Python 3.10+                   |

🎯 Core Capabilities
1. Autonomous Decision-Making
Understands customer intent
Chooses correct tools (DB, FAQ, Stripe)
Executes actions safely

2. Operational Actions
Order tracking
Refund initiation
Replacement eligibility
Policy explanations
FAQ + RAG-based answers

3. Safety
ReAct → step-wise reasoning
Policy checks before refunds
Validated Stripe workflows
Human fallback option (Slack)
