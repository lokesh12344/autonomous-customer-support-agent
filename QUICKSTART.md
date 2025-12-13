# 🚀 Quick Start Guide

## Prerequisites Check

```bash
# 1. Check Python version (need 3.8+)
python3 --version

# 2. Check if Ollama is installed
which ollama

# 3. Activate virtual environment (if using)
source venv/bin/activate
```

## Installation (Already Done ✅)

Dependencies are already installed from `requirements.txt`:
- FastAPI, Uvicorn
- LangChain ecosystem
- Ollama, Chroma, Stripe
- Pydantic, SQLAlchemy

## Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```

Required values:
- `STRIPE_API_KEY` - Get from https://dashboard.stripe.com/test/apikeys
- `MODEL_NAME` - Default: "llama3"
- Other values have sensible defaults

## Running Ollama

```bash
# Start Ollama server (in a separate terminal)
ollama serve

# Pull the model (first time only)
ollama pull llama3
# or
ollama pull mistral

# Verify it's running
curl http://localhost:11434/api/tags
```

## Start the Application

### Option 1: Using the start script
```bash
./start.sh
```

### Option 2: Manual start
```bash
# Initialize database
python3 -m app.services.database

# Start FastAPI
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Direct Python
```bash
python3 -m app.main
```

## Access the API

Once running:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root**: http://localhost:8000/

## Test the Chat Endpoint

### Using curl:
```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help with my order"}'
```

### Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/chat/",
    json={"message": "What is my order status for ORD123?"}
)
print(response.json())
```

### Using the Swagger UI:
1. Go to http://localhost:8000/docs
2. Click on `/chat/` endpoint
3. Click "Try it out"
4. Enter a message in the JSON:
   ```json
   {
     "message": "I need help with a refund"
   }
   ```
5. Click "Execute"

## Project Structure

```
app/
├── main.py              - FastAPI app entry point
├── agent.py             - Customer support agent
├── routes/
│   └── chat.py          - Chat API endpoints
├── tools/               - Agent tools (DB, RAG, Stripe)
├── services/            - Core services (DB, LLM, vectorstore)
└── utils/
    └── config.py        - Configuration management
```

## Testing Individual Components

```bash
# Test database
python3 -m app.services.database

# Test LLM engine
python3 -m app.services.llm_engine

# Test vector store
python3 -m app.services.vectorstore

# Test agent
python3 -m app.agent

# Run validation
python3 validate.py
```

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Check if port 11434 is open: `curl http://localhost:11434/`

### "Module not found" errors
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### "Database locked" errors
- Close any other connections to the database
- Delete `data/db.sqlite` and reinitialize

### Agent not working properly
- This is a simplified implementation
- Tools return placeholder data
- Full ReAct agent requires business logic implementation

## Development Workflow

1. **Make changes** to code files
2. **Save** (server auto-reloads with `--reload` flag)
3. **Test** at http://localhost:8000/docs
4. **Check logs** in the terminal

## Stop the Server

Press `Ctrl+C` in the terminal running the server

## Next Steps

See [SCAFFOLD_SUMMARY.md](SCAFFOLD_SUMMARY.md) for:
- What's implemented (50%)
- What's pending (50%)
- Implementation roadmap

---

**Need Help?** Check the main [README.md](README.md) for detailed documentation.
