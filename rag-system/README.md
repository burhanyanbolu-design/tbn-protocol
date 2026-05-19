# TBN RAG System - FREE Local AI
## No API costs - Uses Ollama (already installed)

## Quick Start

### 1. Install Ollama Models (One-time setup)
```bash
# Install a good model for embeddings and chat
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Ingest Documents (Books, Articles, etc.)
```bash
# Ingest from URLs
python ingest_documents.py --url "https://example.com/book.pdf"

# Ingest from local files
python ingest_documents.py --file "/path/to/book.txt"

# Ingest from web scraping
python ingest_documents.py --scrape "https://example.com/articles"
```

### 4. Start the RAG API
```bash
python rag_api.py
```

### 5. Query the System
```bash
# Via API
curl -X POST http://localhost:5005/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'

# Via Python
python query_rag.py "What is machine learning?"
```

## Architecture

```
Documents → Text Chunking → Embeddings (Ollama) → ChromaDB
                                                        ↓
User Question → Embedding → Search Similar → Retrieve Context
                                                        ↓
                                            Ollama LLM → Answer
```

## Cost: $0.00 (100% FREE)
- No OpenAI API costs
- No cloud costs
- Runs on your existing server
