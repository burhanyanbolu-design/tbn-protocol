#!/bin/bash
# Deploy TBN RAG System to production

echo "🚀 Deploying TBN RAG System"
echo "============================"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Setup Ollama models
echo "📥 Setting up Ollama models..."
ollama pull llama3.2
ollama pull nomic-embed-text

# Test the system
echo "🧪 Testing RAG system..."
python3 ollama_client.py

# Copy systemd service
echo "📋 Installing systemd service..."
sudo cp rag.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rag
sudo systemctl restart rag

echo "✅ RAG system deployed!"
echo ""
echo "🌐 Access at: http://localhost:5005"
echo "📊 Check status: sudo systemctl status rag"
echo "📝 View logs: sudo journalctl -u rag -f"
