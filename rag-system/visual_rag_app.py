#!/usr/bin/env python3
"""
Visual RAG System - Beautiful drag-and-drop interface
No command line needed - just click, drag, and upload!
"""

from flask import Flask, request, jsonify, render_template_string
from rag_engine import RAGEngine
from document_processor import DocumentProcessor
from vector_store import VectorStore
import os
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

rag = RAGEngine()
processor = DocumentProcessor()
store = VectorStore()

# Beautiful HTML interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TBN Knowledge Base - Visual Interface</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats-bar {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
            padding: 10px 20px;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9ff;
        }
        
        .upload-area:hover {
            background: #e8ebff;
            border-color: #764ba2;
        }
        
        .upload-area.dragover {
            background: #d0d7ff;
            border-color: #764ba2;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        .upload-text {
            font-size: 1.2em;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .upload-hint {
            color: #999;
            font-size: 0.9em;
        }
        
        .file-input {
            display: none;
        }
        
        .url-input-group {
            margin-top: 20px;
        }
        
        .url-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 1em;
            margin-bottom: 10px;
        }
        
        .url-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            font-weight: bold;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .query-area {
            margin-top: 20px;
        }
        
        .query-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 1em;
            resize: vertical;
            min-height: 100px;
            font-family: inherit;
        }
        
        .query-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .answer-box {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            display: none;
        }
        
        .answer-box h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .answer-text {
            color: #333;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .tts-controls {
            display: flex;
            gap: 10px;
            margin-top: 12px;
            align-items: center;
        }
        
        .btn-tts {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: opacity 0.2s;
        }
        
        .btn-tts:hover { opacity: 0.85; }
        .btn-tts:disabled { opacity: 0.4; cursor: not-allowed; }
        
        .tts-status {
            font-size: 13px;
            color: #667eea;
            font-style: italic;
        }
        
        .tts-lang-select {
            padding: 7px 12px;
            border-radius: 20px;
            border: 2px solid #667eea;
            background: white;
            color: #333;
            font-size: 14px;
            cursor: pointer;
            outline: none;
        }
        
        .tts-lang-select:focus {
            border-color: #764ba2;
        }
        
        .translation-box {
            margin-top: 15px;
            padding: 15px 20px;
            background: linear-gradient(135deg, #f0f4ff, #f8f0ff);
            border-radius: 10px;
            border-left: 4px solid #764ba2;
        }
        
        .translation-box h4 {
            color: #764ba2;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        .translated-text {
            color: #333;
            line-height: 1.7;
            font-size: 15px;
        }
        
        .sources {
            margin-top: 15px;
        }
        
        .source-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 3px solid #764ba2;
            font-size: 0.9em;
        }
        
        .source-label {
            font-weight: bold;
            color: #764ba2;
            margin-bottom: 5px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .success-message {
            background: #4caf50;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
            display: none;
        }
        
        .error-message {
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
            display: none;
        }
        
        .file-types {
            margin-top: 15px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        
        .file-types h4 {
            color: #856404;
            margin-bottom: 10px;
        }
        
        .file-types ul {
            list-style: none;
            color: #856404;
        }
        
        .file-types li {
            padding: 5px 0;
        }
        
        .file-types li:before {
            content: "✓ ";
            color: #4caf50;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 TBN Knowledge Base</h1>
            <p>Visual Interface - No Command Line Needed!</p>
        </div>
        
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-number" id="doc-count">0</div>
                <div class="stat-label">Documents</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="ollama-status">⚪</div>
                <div class="stat-label">Ollama Status</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">$0</div>
                <div class="stat-label">Cost (FREE!)</div>
            </div>
        </div>
        
        <div class="main-content">
            <!-- Upload Section -->
            <div class="card">
                <h2>📁 Add Knowledge</h2>
                
                <div class="upload-area" id="dropArea">
                    <div class="upload-icon">📤</div>
                    <div class="upload-text">Drag & Drop Files Here</div>
                    <div class="upload-hint">or click to browse</div>
                    <input type="file" id="fileInput" class="file-input" multiple 
                           accept=".txt,.pdf,.doc,.docx,.md">
                </div>
                
                <div class="file-types">
                    <h4>Supported Files:</h4>
                    <ul>
                        <li>Text files (.txt, .md)</li>
                        <li>PDF documents (.pdf)</li>
                        <li>Word documents (.doc, .docx)</li>
                        <li>Any text-based content</li>
                    </ul>
                </div>
                
                <div class="url-input-group">
                    <input type="text" id="urlInput" class="url-input" 
                           placeholder="Or paste a website URL here...">
                    <button class="btn" onclick="addFromURL()">📥 Add from URL</button>
                </div>
                
                <div class="success-message" id="uploadSuccess"></div>
                <div class="error-message" id="uploadError"></div>
                <div class="loading" id="uploadLoading">
                    <div class="spinner"></div>
                    <div>Processing document...</div>
                </div>
            </div>
            
            <!-- Query Section -->
            <div class="card">
                <h2>💬 Ask Questions</h2>
                
                <textarea id="queryInput" class="query-input" 
                          placeholder="Type your question here...&#10;&#10;Examples:&#10;• What is the TBN Protocol?&#10;• How do I register a bot?&#10;• Explain machine learning"></textarea>
                
                <div class="query-area">
                    <button class="btn" onclick="askQuestion()">🔍 Get Answer</button>
                </div>
                
                <div class="loading" id="queryLoading">
                    <div class="spinner"></div>
                    <div>Searching and generating answer...</div>
                </div>
                
                <div class="answer-box" id="answerBox">
                    <h3>💡 Answer:</h3>
                    <div class="answer-text" id="answerText"></div>
                    
                    <!-- Translated text box — shown when non-English language selected -->
                    <div class="translation-box" id="translationBox" style="display:none;">
                        <h4 id="translationLabel">🌐 Translation:</h4>
                        <div class="translated-text" id="translatedText"></div>
                    </div>
                    
                    <div class="tts-controls">
                        <select id="ttsLang" class="tts-lang-select">
                            <option value="">🌐 Loading voices...</option>
                        </select>
                        <select id="ttsVoice" class="tts-lang-select">
                            <option value="">🎙️ Default voice</option>
                        </select>
                        <button class="btn-tts" id="speakBtn" onclick="speakAnswer()">🔊 Listen</button>
                        <button class="btn-tts" id="stopBtn" onclick="stopSpeaking()" style="display:none; background: linear-gradient(135deg, #e74c3c, #c0392b);">⏹ Stop</button>
                        <span class="tts-status" id="ttsStatus"></span>
                    </div>
                    
                    <div class="sources" id="sourcesBox">
                        <h4>📚 Sources:</h4>
                        <div id="sourcesList"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Load stats on page load
        loadStats();
        
        function loadStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('doc-count').textContent = data.total_documents;
                    document.getElementById('ollama-status').textContent = 
                        data.ollama_available ? '✅' : '❌';
                });
        }
        
        // Drag and drop functionality
        const dropArea = document.getElementById('dropArea');
        const fileInput = document.getElementById('fileInput');
        
        dropArea.addEventListener('click', () => fileInput.click());
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.classList.remove('dragover');
            }, false);
        });
        
        dropArea.addEventListener('drop', handleDrop, false);
        fileInput.addEventListener('change', handleFiles, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles({target: {files: files}});
        }
        
        function handleFiles(e) {
            const files = e.target.files;
            if (files.length === 0) return;
            
            document.getElementById('uploadLoading').style.display = 'block';
            document.getElementById('uploadSuccess').style.display = 'none';
            document.getElementById('uploadError').style.display = 'none';
            
            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('uploadLoading').style.display = 'none';
                if (data.success) {
                    const msg = document.getElementById('uploadSuccess');
                    msg.textContent = `✅ Success! Added ${data.chunks_added} chunks from ${data.files_processed} file(s)`;
                    msg.style.display = 'block';
                    loadStats();
                    setTimeout(() => msg.style.display = 'none', 5000);
                } else {
                    const msg = document.getElementById('uploadError');
                    msg.textContent = `❌ Error: ${data.error}`;
                    msg.style.display = 'block';
                }
                fileInput.value = '';
            })
            .catch(err => {
                document.getElementById('uploadLoading').style.display = 'none';
                const msg = document.getElementById('uploadError');
                msg.textContent = `❌ Error: ${err}`;
                msg.style.display = 'block';
            });
        }
        
        function addFromURL() {
            const url = document.getElementById('urlInput').value.trim();
            if (!url) {
                alert('Please enter a URL');
                return;
            }
            
            document.getElementById('uploadLoading').style.display = 'block';
            document.getElementById('uploadSuccess').style.display = 'none';
            document.getElementById('uploadError').style.display = 'none';
            
            fetch('/api/ingest', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('uploadLoading').style.display = 'none';
                if (data.success) {
                    const msg = document.getElementById('uploadSuccess');
                    msg.textContent = `✅ Success! Added ${data.chunks_added} chunks from URL`;
                    msg.style.display = 'block';
                    document.getElementById('urlInput').value = '';
                    loadStats();
                    setTimeout(() => msg.style.display = 'none', 5000);
                } else {
                    const msg = document.getElementById('uploadError');
                    msg.textContent = `❌ Error: ${data.error}`;
                    msg.style.display = 'block';
                }
            })
            .catch(err => {
                document.getElementById('uploadLoading').style.display = 'none';
                const msg = document.getElementById('uploadError');
                msg.textContent = `❌ Error: ${err}`;
                msg.style.display = 'block';
            });
        }
        
        function askQuestion() {
            const question = document.getElementById('queryInput').value.trim();
            if (!question) {
                alert('Please enter a question');
                return;
            }
            
            document.getElementById('queryLoading').style.display = 'block';
            document.getElementById('answerBox').style.display = 'none';
            document.getElementById('translationBox').style.display = 'none';
            document.getElementById('translatedText').textContent = '';
            
            fetch('/api/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: question})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('queryLoading').style.display = 'none';
                document.getElementById('answerBox').style.display = 'block';
                document.getElementById('answerText').textContent = data.answer;
                
                const sourcesList = document.getElementById('sourcesList');
                sourcesList.innerHTML = '';
                
                if (data.sources && data.sources.length > 0) {
                    data.sources.forEach((source, i) => {
                        const div = document.createElement('div');
                        div.className = 'source-item';
                        div.innerHTML = `
                            <div class="source-label">Source ${i+1}:</div>
                            ${source.text.substring(0, 200)}...
                            ${source.metadata.source ? `<br><small>From: ${source.metadata.source}</small>` : ''}
                        `;
                        sourcesList.appendChild(div);
                    });
                } else {
                    document.getElementById('sourcesBox').style.display = 'none';
                }
            })
            .catch(err => {
                document.getElementById('queryLoading').style.display = 'none';
                alert('Error: ' + err);
            });
        }
        
        // Allow Enter to submit (Shift+Enter for new line)
        document.getElementById('queryInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
        
        // Allow Enter in URL input
        document.getElementById('urlInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addFromURL();
            }
        });
        
        // ── Text-to-Speech (free, browser built-in) ──────────────────────
        let ttsUtterance = null;
        let allVoices = [];
        
        function loadVoices() {
            allVoices = window.speechSynthesis.getVoices();
            if (allVoices.length === 0) return;
            
            const langSelect = document.getElementById('ttsLang');
            const voiceSelect = document.getElementById('ttsVoice');
            
            // Build unique language list
            const langMap = {};
            allVoices.forEach(v => {
                const lang = v.lang;
                const langName = new Intl.DisplayNames([navigator.language || 'en'], {type: 'language'});
                const baseLang = lang.split('-')[0];
                let label = '';
                try { label = langName.of(baseLang); } catch(e) { label = lang; }
                if (!langMap[lang]) langMap[lang] = label + ' (' + lang + ')';
            });
            
            // Sort languages alphabetically
            const sortedLangs = Object.entries(langMap).sort((a, b) => a[1].localeCompare(b[1]));
            
            langSelect.innerHTML = '<option value="">🌐 All languages</option>';
            sortedLangs.forEach(([code, name]) => {
                const opt = document.createElement('option');
                opt.value = code;
                opt.textContent = name;
                // Default to en-GB or en-US if available
                if (code === 'en-GB' || code === 'en-US') opt.selected = true;
                langSelect.appendChild(opt);
            });
            
            // Populate voices for default selected language
            updateVoiceList();
        }
        
        function updateVoiceList() {
            const langSelect = document.getElementById('ttsLang');
            const voiceSelect = document.getElementById('ttsVoice');
            const selectedLang = langSelect.value;
            
            const filtered = selectedLang
                ? allVoices.filter(v => v.lang === selectedLang)
                : allVoices;
            
            voiceSelect.innerHTML = '<option value="">🎙️ Default voice</option>';
            filtered.forEach((v, i) => {
                const opt = document.createElement('option');
                opt.value = v.name;
                opt.textContent = v.name + (v.localService ? ' (offline)' : ' (online)');
                voiceSelect.appendChild(opt);
            });
        }
        
        // Load voices — Chrome loads them async, Firefox sync
        if (window.speechSynthesis) {
            loadVoices();
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
        
        document.getElementById('ttsLang').addEventListener('change', updateVoiceList);
        
        function speakAnswer() {
            if (!window.speechSynthesis) {
                alert('Sorry, your browser does not support text-to-speech.');
                return;
            }
            
            const text = document.getElementById('answerText').textContent.trim();
            if (!text) return;
            
            const selectedLang = document.getElementById('ttsLang').value;
            const targetLang = selectedLang ? selectedLang.split('-')[0] : 'en';
            
            document.getElementById('ttsStatus').textContent = '⏳ Translating...';
            document.getElementById('speakBtn').disabled = true;
            
            // If English selected, skip translation
            if (!selectedLang || targetLang === 'en') {
                // Hide any previous translation
                document.getElementById('translationBox').style.display = 'none';
                document.getElementById('translatedText').textContent = '';
                speakText(text, selectedLang || 'en-GB');
                return;
            }
            
            // Translate via MyMemory free API (no key needed, 5000 chars/day free)
            const sourceLang = 'en';
            const apiUrl = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text.substring(0, 500))}&langpair=${sourceLang}|${targetLang}`;
            
            fetch(apiUrl)
                .then(r => r.json())
                .then(data => {
                    const translated = data.responseData && data.responseData.translatedText
                        ? data.responseData.translatedText
                        : text; // fallback to original if translation fails
                    
                    // Show translated text on screen
                    const langName = document.getElementById('ttsLang').options[document.getElementById('ttsLang').selectedIndex].text;
                    document.getElementById('translationLabel').textContent = `🌐 Translation (${langName}):`;
                    document.getElementById('translatedText').textContent = translated;
                    document.getElementById('translationBox').style.display = 'block';
                    
                    speakText(translated, selectedLang);
                })
                .catch(() => {
                    // Fallback: speak original text if translation fails
                    document.getElementById('translationBox').style.display = 'none';
                    document.getElementById('ttsStatus').textContent = '⚠️ Translation failed, speaking English';
                    speakText(text, 'en-GB');
                });
        }
        
        function speakText(text, lang) {
            // Stop anything already playing
            window.speechSynthesis.cancel();
            
            ttsUtterance = new SpeechSynthesisUtterance(text);
            ttsUtterance.rate = 0.95;
            ttsUtterance.pitch = 1;
            ttsUtterance.lang = lang;
            
            // Apply selected voice
            const selectedVoiceName = document.getElementById('ttsVoice').value;
            if (selectedVoiceName) {
                const voice = allVoices.find(v => v.name === selectedVoiceName);
                if (voice) ttsUtterance.voice = voice;
            }
            
            ttsUtterance.onstart = () => {
                document.getElementById('speakBtn').style.display = 'none';
                document.getElementById('speakBtn').disabled = false;
                document.getElementById('stopBtn').style.display = 'inline-flex';
                document.getElementById('ttsStatus').textContent = '🎙️ Speaking...';
            };
            
            ttsUtterance.onend = () => {
                document.getElementById('speakBtn').style.display = 'inline-flex';
                document.getElementById('stopBtn').style.display = 'none';
                document.getElementById('ttsStatus').textContent = '';
            };
            
            ttsUtterance.onerror = () => {
                document.getElementById('speakBtn').style.display = 'inline-flex';
                document.getElementById('speakBtn').disabled = false;
                document.getElementById('stopBtn').style.display = 'none';
                document.getElementById('ttsStatus').textContent = '';
            };
            
            window.speechSynthesis.speak(ttsUtterance);
        }
        
        function stopSpeaking() {
            window.speechSynthesis.cancel();
            document.getElementById('speakBtn').style.display = 'inline-flex';
            document.getElementById('stopBtn').style.display = 'none';
            document.getElementById('ttsStatus').textContent = '';
        }
        // ─────────────────────────────────────────────────────────────────
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        total_chunks = 0
        files_processed = 0
        
        for file in files:
            if file.filename == '':
                continue
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file
            text = processor.load_from_file(filepath)
            if text:
                chunks = processor.chunk_text(text, metadata={
                    'source': filename,
                    'type': 'upload'
                })
                added = store.add_documents(chunks)
                total_chunks += added
                files_processed += 1
            
            # Clean up
            os.remove(filepath)
        
        return jsonify({
            'success': True,
            'chunks_added': total_chunks,
            'files_processed': files_processed,
            'total_documents': store.count()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest():
    """Ingest from URL"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        text = processor.load_from_url(url)
        if not text:
            return jsonify({'success': False, 'error': 'Could not load content from URL'}), 400
        
        chunks = processor.chunk_text(text, metadata={'source': url, 'type': 'url'})
        added = store.add_documents(chunks)
        
        return jsonify({
            'success': True,
            'chunks_added': added,
            'total_documents': store.count()
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query():
    """Query endpoint"""
    try:
        data = request.json
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        result = rag.query(question)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get system statistics"""
    return jsonify(rag.get_stats())

if __name__ == '__main__':
    print("🚀 Starting Visual RAG Interface...")
    print("📊 System stats:", rag.get_stats())
    print("\n🌐 Open in your browser: http://localhost:5006")
    print("✨ Beautiful drag-and-drop interface ready!")
    print("💡 No command line needed - just drag files and ask questions!")
    
    app.run(host='0.0.0.0', port=5006, debug=True)
