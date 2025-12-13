#!/bin/bash

echo "🚀 Starting Autonomous Customer Support Agent System"
echo "======================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please configure it with your API keys."
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo "Please start it with: ollama serve"
    echo "And pull a model: ollama pull llama3"
    exit 1
fi

echo "✅ Ollama is running"

# Check if database needs seeding
if [ ! -s data/db.sqlite ] || [ ! -f data/db.sqlite ]; then
    echo "📊 Database not found. Running seeding script..."
    python3 -m scripts.seed_database
fi

# Check if vector store needs ingestion
if [ ! -d vectorstore/chroma.sqlite3 ]; then
    echo "📚 Vector store empty. Ingesting FAQs..."
    python3 -m scripts.ingest_faq
fi

echo ""
echo "======================================================"
echo "✅ All systems ready!"
echo "======================================================"
echo ""
echo "Starting services..."
echo ""

# Start FastAPI in background
echo "🌐 Starting FastAPI backend on http://localhost:8000..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!

# Wait for FastAPI to start
sleep 3

# Start Streamlit
echo "🎨 Starting Streamlit frontend on http://localhost:8501..."
streamlit run frontend/app.py --server.port 8501

# Cleanup on exit
trap "echo 'Shutting down...'; kill $FASTAPI_PID 2>/dev/null" EXIT
