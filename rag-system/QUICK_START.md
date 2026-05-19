# 🚀 TBN RAG System - Quick Start Guide

## What You Have Now
A **100% FREE** RAG (Retrieval-Augmented Generation) system that:
- Uses Ollama (local AI - no API costs)
- Ingests books, articles, PDFs, websites
- Answers questions using collected knowledge
- Runs on your existing server

## Cost: $0.00 per month 💰

---

## Step 1: Setup Ollama Models (5 minutes)

You already have Ollama installed! Just download the models:

```bash
cd rag-system

# Make setup script executable
chmod +x setup_ollama.sh

# Run setup (downloads models)
./setup_ollama.sh
```

This downloads:
- **llama3.2** - Main AI model for answering questions
- **nomic-embed-text** - For creating embeddings

---

## Step 2: Install Python Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

---

## Step 3: Test Ollama Connection (1 minute)

```bash
python ollama_client.py
```

You should see:
```
✅ Ollama is running!
📦 Installed models: llama3.2, nomic-embed-text
```

---

## Step 4: Ingest Your First Document (3 minutes)

### Option A: From a URL
```bash
python ingest_documents.py --url "https://en.wikipedia.org/wiki/Artificial_intelligence"
```

### Option B: From a local file
```bash
python ingest_documents.py --file "/path/to/book.txt"
```

### Option C: Scrape a website (multiple pages)
```bash
python ingest_documents.py --scrape "https://example.com" --max-pages 10
```

---

## Step 5: Query the System (1 minute)

### Command Line
```bash
python query_rag.py "What is artificial intelligence?"
```

### Web Interface
```bash
python rag_api.py
```

Then open: http://localhost:5005

---

## Real-World Examples

### Ingest a Programming Book
```bash
# Download a free programming book
wget https://eloquentjavascript.net/Eloquent_JavaScript.pdf

# Ingest it
python ingest_documents.py --file Eloquent_JavaScript.pdf

# Ask questions
python query_rag.py "How do closures work in JavaScript?"
```

### Ingest Medical Research
```bash
python ingest_documents.py --url "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC..."

python query_rag.py "What are the symptoms of LGMD?"
```

### Ingest Your Own Documentation
```bash
# Scrape your company docs
python ingest_documents.py --scrape "https://docs.yourcompany.com" --max-pages 50

# Now your bot knows your docs!
python query_rag.py "How do I deploy to production?"
```

---

## Integration with TBN Protocol

Add to your `api/routes.py`:

```python
from rag_system.rag_engine import RAGEngine

rag = RAGEngine()

@app.route('/api/tbn/ask', methods=['POST'])
def tbn_ask():
    question = request.json.get('question')
    result = rag.query(question)
    return jsonify(result)
```

---

## Troubleshooting

### "Ollama is not running"
```bash
ollama serve
```

### "No documents found"
You need to ingest documents first:
```bash
python ingest_documents.py --url "https://example.com"
```

### "Embedding failed"
Make sure you have the embedding model:
```bash
ollama pull nomic-embed-text
```

---

## Performance Tips

1. **Chunk size**: Adjust in `document_processor.py` (default: 1000 chars)
2. **Number of results**: Adjust `n_results` in queries (default: 5)
3. **Temperature**: Lower = more focused, Higher = more creative

---

## Cost Comparison

| Solution | Cost per 1M tokens |
|----------|-------------------|
| OpenAI GPT-4 | $30-60 |
| OpenAI GPT-3.5 | $2 |
| **Your Ollama RAG** | **$0** ✅ |

---

## Next Steps

1. ✅ Ingest more documents (books, articles, your docs)
2. ✅ Integrate with TBN dashboard
3. ✅ Create a bot that uses this knowledge
4. ✅ Deploy to production (already on your server!)

---

## Support

Questions? Check:
- Ollama docs: https://ollama.ai/docs
- ChromaDB docs: https://docs.trychroma.com
- LangChain docs: https://python.langchain.com

---

**You now have a FREE, production-ready RAG system! 🎉**

No API costs. No cloud fees. Just pure local AI power.
