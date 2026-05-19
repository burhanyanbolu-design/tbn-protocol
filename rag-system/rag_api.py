#!/usr/bin/env python3
"""
RAG API - Flask REST API for the RAG system
Integrates with TBN Protocol
"""

from flask import Flask, request, jsonify, render_template_string
from rag_engine import RAGEngine
from document_processor import DocumentProcessor
from vector_store import VectorStore

app = Flask(__name__)
rag = RAGEngine()

# Simple web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TBN RAG System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .stats {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .query-box {
            margin: 20px 0;
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            resize: vertical;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #45a049;
        }
        .answer {
            background: #f9f9f9;
            padding: 20px;
            border-left: 4px solid #4CAF50;
            margin: 20px 0;
            display: none;
        }
        .sources {
            margin-top: 20px;
        }
        .source-item {
            background: #fff;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #2196F3;
            border-radius: 3px;
        }
        .loading {
            display: none;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 TBN RAG System</h1>
        <p>Ask questions and get answers from the knowledge base (powered by Ollama - FREE!)</p>
        
        <div class="stats">
            <strong>📊 System Status:</strong><br>
            Documents: <span id="doc-count">Loading...</span><br>
            Ollama: <span id="ollama-status">Loading...</span>
        </div>
        
        <div class="query-box">
            <textarea id="question" rows="3" placeholder="Ask a question..."></textarea>
            <button onclick="askQuestion()">Ask Question</button>
            <div class="loading" id="loading">🔍 Searching and generating answer...</div>
        </div>
        
        <div class="answer" id="answer-box">
            <h3>💬 Answer:</h3>
            <div id="answer-text"></div>
            
            <div class="sources" id="sources-box">
                <h4>📚 Sources:</h4>
                <div id="sources-list"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Load stats on page load
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('doc-count').textContent = data.total_documents;
                document.getElementById('ollama-status').textContent = 
                    data.ollama_available ? '✅ Running' : '❌ Not running';
            });
        
        function askQuestion() {
            const question = document.getElementById('question').value;
            if (!question.trim()) {
                alert('Please enter a question');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('answer-box').style.display = 'none';
            
            fetch('/api/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: question})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('answer-box').style.display = 'block';
                document.getElementById('answer-text').textContent = data.answer;
                
                const sourcesList = document.getElementById('sources-list');
                sourcesList.innerHTML = '';
                
                data.sources.forEach((source, i) => {
                    const div = document.createElement('div');
                    div.className = 'source-item';
                    div.innerHTML = `<strong>Source ${i+1}:</strong><br>${source.text.substring(0, 200)}...`;
                    sourcesList.appendChild(div);
                });
            })
            .catch(err => {
                document.getElementById('loading').style.display = 'none';
                alert('Error: ' + err);
            });
        }
        
        // Allow Enter to submit (Shift+Enter for new line)
        document.getElementById('question').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/query', methods=['POST'])
def query():
    """Query endpoint"""
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    result = rag.query(question)
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get system statistics"""
    return jsonify(rag.get_stats())

@app.route('/api/ingest', methods=['POST'])
def ingest():
    """Ingest new documents"""
    data = request.json
    url = data.get('url')
    text = data.get('text')
    
    if not url and not text:
        return jsonify({'error': 'Provide url or text'}), 400
    
    processor = DocumentProcessor()
    store = VectorStore()
    
    if url:
        content = processor.load_from_url(url)
        chunks = processor.chunk_text(content, metadata={'source': url})
    else:
        chunks = processor.chunk_text(text, metadata={'source': 'api'})
    
    added = store.add_documents(chunks)
    
    return jsonify({
        'success': True,
        'chunks_added': added,
        'total_documents': store.count()
    })

if __name__ == '__main__':
    print("🚀 Starting TBN RAG API...")
    print("📊 System stats:", rag.get_stats())
    print("\n🌐 Access the web interface at: http://localhost:5006")
    print("📡 API endpoint: http://localhost:5006/api/query")
    
    app.run(host='0.0.0.0', port=5006, debug=True)
