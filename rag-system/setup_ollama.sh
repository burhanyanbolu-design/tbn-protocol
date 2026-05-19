#!/bin/bash
# Setup Ollama models for RAG system

echo "🚀 Setting up Ollama for TBN RAG System"
echo "========================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed!"
    echo "Install it from: https://ollama.ai"
    exit 1
fi

echo "✅ Ollama is installed"

# Start Ollama service (if not running)
echo ""
echo "📡 Starting Ollama service..."
ollama serve &
sleep 3

# Pull required models
echo ""
echo "📥 Downloading Llama 3.2 (main model)..."
ollama pull llama3.2

echo ""
echo "📥 Downloading nomic-embed-text (embeddings)..."
ollama pull nomic-embed-text

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Installed models:"
ollama list

echo ""
echo "🧪 Testing Ollama..."
echo "Question: What is 2+2?"
ollama run llama3.2 "What is 2+2? Answer in one sentence."

echo ""
echo "✅ Ollama is ready for RAG system!"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip install -r requirements.txt"
echo "2. Ingest documents: python ingest_documents.py --url <url>"
echo "3. Start API: python rag_api.py"
