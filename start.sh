#!/bin/bash

# Quick start script for the Autonomous Customer Support Agent

echo "🚀 Starting Autonomous Customer Support Agent..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your actual values."
    echo ""
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo "Please start it with: ollama serve"
    echo ""
    echo "And ensure you have a model pulled:"
    echo "  ollama pull llama3"
    echo ""
    exit 1
fi

echo "✅ Ollama is running"

# Initialize database
echo "📊 Initializing database..."
python3 -m app.services.database

echo ""
echo "🌐 Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""

# Start the server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
