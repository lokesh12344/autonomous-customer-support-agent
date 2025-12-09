# 🧠 Next-Gen Autonomous Customer Support Agent

**Built with Agentic AI · LangChain ReAct · FastAPI · SQLite · ChromaDB · Local LLM · Stripe Test Mode**

A lightweight autonomous support agent capable of:

- Order lookups (SQLite)
- Refund execution (Stripe Test Mode)
- FAQ retrieval (Chroma vector search)
- Policy-aware reasoning & safety checks
- Real-time chat interface (Slack / Web UI)

---

## 🚀 Features

### Agentic ReAct Pipeline
Observe → Reason → Act → Verify → Reply

### Local LLM Inference
LLaMA/Mistral/Vicuna via Ollama

### Tool-Based Actions
- `order_tool` → fetch order status
- `faq_tool` → semantic FAQ retrieval
- `refund_tool` → process refunds securely

### Safety & Guardrails
- Refund confirmation
- ₹10,000 refund limit
- DB verification before actions
- Auto human-escalation on low confidence

### Infrastructure
- FastAPI backend hosting the agent and endpoints
- ChromaDB for policy/FAQ embeddings & long-term memory
- SQLite for orders, customers, inventory, returns
- Slack/Web UI for live conversation demo

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Agent Framework | LangChain (ReAct agent + tools) |
| Orchestration | Minimal LangGraph (optional) |
| LLM | Local LLaMA/Mistral via Ollama |
| Database | SQLite + SQLAlchemy |
| Vector Store | ChromaDB |
| Payments | Stripe API (Test Mode) |
| UI | Slack Bot / Streamlit Chat UI |

---

## 📂 Project Structure

```
/project-root
│
├── app/
│   ├── main.py              # FastAPI server
│   ├── agent.py             # LangChain ReAct agent
│   ├── tools/
│   │   ├── orders.py        # SQLite order lookup tool
│   │   ├── refund.py        # Stripe refund tool
│   │   └── faq.py           # Chroma retrieval tool
│   ├── db/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── seed.py          # Sample seed data
│   └── memory/
│       └── vectorstore.py   # Chroma embedding setup
│
├── ui/
│   └── slack_bot.py         # Slack event handler
│
├── requirements.txt
├── README.md
└── .env.example
```

---

## ⚙️ Setup Instructions

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 2️⃣ Start Ollama (Local LLM)

```bash
ollama pull llama3
ollama serve
```

### 3️⃣ Configure Environment

Copy `.env.example` → `.env` and fill:

```env
STRIPE_API_KEY=sk_test_****
LLM_MODEL=llama3
```

### 4️⃣ Initialize SQLite & Chroma

```bash
python app/db/seed.py
```

### 5️⃣ Run FastAPI Server

```bash
uvicorn app.main:app --reload
```

### 6️⃣ (Optional) Run Slack Bot

```bash
python ui/slack_bot.py
```

---

## 🧪 Example Queries

- "Where is my order #8912?"
- "Process refund ₹7000 for order 1234."
- "Show me your return policy."
- "My product was damaged, what can I do?"

---

## 🔐 Safety & Guardrails

- **Refund limit**: ₹10,000
- **Mandatory user confirmation**
- **DB-verified order + payment mapping**
- **No hallucinated financial actions**
- **Escalates to human on uncertainty**

---

## 📈 Roadmap

- [ ] Multi-channel (WhatsApp API)
- [ ] Postgres migration for scale
- [ ] Production LLaMA 3 70B hosting
- [ ] Auto-email receipts
- [ ] Multi-turn memory optimization

---
