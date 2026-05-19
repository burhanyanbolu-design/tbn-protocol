"""
Hardin Data Network — Search API
Serves the search panel on port 5007
"""

import sys
sys.path.insert(0, '/opt/tbn-protocol/hardin-data-network')

from flask import Flask, request, jsonify, render_template_string
from search_engine import search

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hardin Data Network — Search</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
    min-height: 100vh;
  }

  /* Header */
  .header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border-bottom: 1px solid #30363d;
    padding: 20px 40px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .logo { font-size: 22px; font-weight: 700; color: #fff; }
  .logo span { color: #00d4ff; }
  .badge {
    background: rgba(0,212,255,0.1);
    border: 1px solid rgba(0,212,255,0.3);
    color: #00d4ff;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 1px;
  }

  /* Search box */
  .search-section {
    max-width: 800px;
    margin: 60px auto 40px;
    padding: 0 20px;
    text-align: center;
  }
  .search-title {
    font-size: 32px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
  }
  .search-subtitle {
    color: #8b949e;
    font-size: 15px;
    margin-bottom: 32px;
  }
  .search-box {
    display: flex;
    gap: 12px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 8px 8px 8px 20px;
    transition: border-color 0.2s;
  }
  .search-box:focus-within { border-color: #00d4ff; }
  .search-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: #fff;
    font-size: 16px;
    padding: 8px 0;
  }
  .search-input::placeholder { color: #484f58; }
  .search-btn {
    background: #00d4ff;
    color: #000;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }
  .search-btn:hover { background: #00b8d9; }
  .search-btn:disabled { background: #30363d; color: #8b949e; cursor: not-allowed; }

  /* Example queries */
  .examples {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-top: 16px;
  }
  .example-chip {
    background: #161b22;
    border: 1px solid #30363d;
    color: #8b949e;
    font-size: 12px;
    padding: 5px 12px;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .example-chip:hover { border-color: #00d4ff; color: #00d4ff; }

  /* Results */
  .results-section {
    max-width: 800px;
    margin: 0 auto 60px;
    padding: 0 20px;
  }
  .result-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 24px;
    margin-top: 20px;
    display: none;
  }
  .result-card.visible { display: block; }
  .result-query {
    color: #8b949e;
    font-size: 13px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #21262d;
  }
  .result-query span { color: #00d4ff; }
  .result-text {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.8;
    color: #e0e0e0;
    white-space: pre-wrap;
  }

  /* Loading */
  .loading {
    text-align: center;
    padding: 40px;
    color: #8b949e;
    display: none;
  }
  .loading.visible { display: block; }
  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #30363d;
    border-top-color: #00d4ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Stats bar */
  .stats-bar {
    background: #161b22;
    border-bottom: 1px solid #21262d;
    padding: 8px 40px;
    display: flex;
    gap: 24px;
    font-size: 12px;
    color: #8b949e;
  }
  .stats-bar span { color: #00d4ff; }

  /* Quality check button */
  .quality-bar {
    max-width: 800px;
    margin: 0 auto 0;
    padding: 0 20px;
    display: flex;
    justify-content: flex-end;
    margin-top: 12px;
  }
  .quality-btn {
    background: none;
    border: 1px solid #30363d;
    color: #8b949e;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .quality-btn:hover { border-color: #00ff88; color: #00ff88; }
  .quality-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Quality result card */
  .quality-card {
    max-width: 800px;
    margin: 12px auto 0;
    padding: 0 20px;
    display: none;
  }
  .quality-card.visible { display: block; }
  .quality-inner {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
  }
  .quality-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #21262d;
  }
  .quality-title { font-size: 13px; font-weight: 600; color: #fff; letter-spacing: 1px; }
  .quality-close { background: none; border: none; color: #8b949e; cursor: pointer; font-size: 18px; }
  .quality-close:hover { color: #fff; }
  .quality-text {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.7;
    color: #e0e0e0;
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
  }
  .quality-text .pass { color: #00ff88; }
  .quality-text .fail { color: #ff4444; }
  .quality-text .info { color: #00d4ff; }
  .quality-spinner {
    width: 20px; height: 20px;
    border: 2px solid #30363d;
    border-top-color: #00ff88;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    display: inline-block;
    vertical-align: middle;
    margin-right: 8px;
  }
    max-width: 800px;
    margin: 0 auto;
    padding: 0 20px;
  }
  .history-title {
    color: #8b949e;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 12px;
  }
  .history-item {
    color: #8b949e;
    font-size: 13px;
    padding: 6px 0;
    cursor: pointer;
    border-bottom: 1px solid #21262d;
    transition: color 0.2s;
  }
  .history-item:hover { color: #00d4ff; }
  .history-item::before { content: "🔍 "; }
</style>
</head>
<body>

<div class="header">
  <div class="logo">HARDIN <span>DATA</span></div>
  <div class="badge">TBN CERTIFIED</div>
  <div class="badge">31,803 DATA POINTS</div>
</div>

<div class="stats-bar">
  <div>🤖 <span>31</span> TBN Bots</div>
  <div>📊 <span>31,803</span> Data Points</div>
  <div>🗄️ <span>33</span> Categories</div>
  <div>🔒 All data TBN certified</div>
  <div style="margin-left:auto">
    <button class="quality-btn" id="qualityBtn" onclick="runQualityCheck()">
      🔬 Data Quality Check
    </button>
  </div>
</div>

<!-- Quality Check Result -->
<div class="quality-card" id="qualityCard">
  <div class="quality-inner">
    <div class="quality-header">
      <div class="quality-title">🔬 DATA QUALITY AUDIT</div>
      <button class="quality-close" onclick="document.getElementById('qualityCard').classList.remove('visible')">✕</button>
    </div>
    <div class="quality-text" id="qualityText"></div>
  </div>
</div>

<div class="search-section">
  <div class="search-title">Search Our Data Network</div>
  <div class="search-subtitle">Ask anything in plain English — football predictions, restaurants, finance, education and more</div>

  <div class="search-box">
    <input type="text" class="search-input" id="searchInput"
      placeholder="e.g. Chelsea vs Man United who will win? or Best Indian restaurants in Birmingham"
      onkeydown="if(event.key==='Enter') doSearch()">
    <button class="search-btn" id="searchBtn" onclick="doSearch()">Search</button>
  </div>

  <div class="examples">
    <div class="example-chip" onclick="setQuery('Chelsea vs Man United who will win?')">⚽ Chelsea vs Man United</div>
    <div class="example-chip" onclick="setQuery('Best Indian restaurants in Birmingham')">🍽️ Indian restaurants Birmingham</div>
    <div class="example-chip" onclick="setQuery('Should I buy gold now?')">🥇 Buy gold?</div>
    <div class="example-chip" onclick="setQuery('GBP to USD exchange rate')">💱 GBP/USD rate</div>
    <div class="example-chip" onclick="setQuery('Top selling cars in 2026')">🚗 Top cars 2026</div>
    <div class="example-chip" onclick="setQuery('Best universities in UK')">🎓 UK universities</div>
    <div class="example-chip" onclick="setQuery('Latest EuroMillions numbers')">🎰 EuroMillions</div>
    <div class="example-chip" onclick="setQuery('Arsenal recent form')">⚽ Arsenal form</div>
    <div class="example-chip" onclick="setQuery('Latest horse racing results')">🏇 Horse racing</div>
    <div class="example-chip" onclick="setQuery('UK unemployment rate')">📊 UK economy</div>
  </div>
</div>

<div class="results-section">
  <div class="loading" id="loading">
    <div class="spinner"></div>
    Searching 31,803 data points...
  </div>
  <div class="result-card" id="resultCard">
    <div class="result-query">Results for: <span id="resultQuery"></span></div>
    <div class="result-text" id="resultText"></div>
  </div>
</div>

<div class="history" id="historySection" style="display:none">
  <div class="history-title">Recent Searches</div>
  <div id="historyList"></div>
</div>

<script>
  const history = [];

  function setQuery(q) {
    document.getElementById('searchInput').value = q;
    doSearch();
  }

  async function doSearch() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) return;

    const btn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const card = document.getElementById('resultCard');

    btn.disabled = true;
    btn.textContent = 'Searching...';
    loading.classList.add('visible');
    card.classList.remove('visible');

    try {
      const r = await fetch('/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: q})
      });
      const d = await r.json();

      document.getElementById('resultQuery').textContent = q;
      document.getElementById('resultText').textContent = d.answer || d.error || 'No results found';
      card.classList.add('visible');

      // Add to history
      if (!history.includes(q)) {
        history.unshift(q);
        if (history.length > 10) history.pop();
        updateHistory();
      }
    } catch(e) {
      document.getElementById('resultText').textContent = 'Error: ' + e.message;
      card.classList.add('visible');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Search';
      loading.classList.remove('visible');
    }
  }

  function updateHistory() {
    const section = document.getElementById('historySection');
    const list = document.getElementById('historyList');
    if (history.length === 0) { section.style.display = 'none'; return; }
    section.style.display = 'block';
    list.innerHTML = history.map(q =>
      `<div class="history-item" onclick="setQuery('${q.replace(/'/g, "\\'")}')">${q}</div>`
    ).join('');
  }

  async function runQualityCheck() {
    const btn  = document.getElementById('qualityBtn');
    const card = document.getElementById('qualityCard');
    const text = document.getElementById('qualityText');

    btn.disabled = true;
    btn.innerHTML = '<span class="quality-spinner"></span> Running...';
    card.classList.add('visible');
    text.innerHTML = 'Running data quality audit across all 11 categories... This may take 10-15 seconds.';

    try {
      const r = await fetch('/quality-check');
      const d = await r.json();

      // Colour-code the output
      let html = d.result
        .replace(/✅/g, '<span class="pass">✅</span>')
        .replace(/❌/g, '<span class="fail">❌</span>')
        .replace(/ℹ️/g, '<span class="info">ℹ️</span>')
        .replace(/🎉/g, '<span class="pass">🎉</span>')
        .replace(/\[(\d+)\]/g, '<span class="info">[$1]</span>');

      text.innerHTML = html;
    } catch(e) {
      text.textContent = 'Error running quality check: ' + e.message;
    } finally {
      btn.disabled = false;
      btn.innerHTML = '🔬 Data Quality Check';
    }
  }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/search', methods=['POST'])
def do_search():
    data  = request.get_json(force=True) or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    try:
        answer = search(query)
        return jsonify({'query': query, 'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'hardin-search'})


@app.route('/quality-check')
def quality_check():
    """Run the data quality audit and return results"""
    import subprocess
    try:
        result = subprocess.run(
            ['python3', '/opt/tbn-protocol/hardin-data-network/verify_all_data.py'],
            capture_output=True, text=True, timeout=60
        )
        output = result.stdout + (result.stderr if result.stderr else '')
        return jsonify({'result': output, 'status': 'ok'})
    except subprocess.TimeoutExpired:
        return jsonify({'result': 'Timeout — audit took too long', 'status': 'error'})
    except Exception as e:
        return jsonify({'result': f'Error: {str(e)}', 'status': 'error'})

if __name__ == '__main__':
    print("=" * 55)
    print("  HARDIN DATA NETWORK — SEARCH ENGINE")
    print("  http://localhost:5007")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5008, debug=False)
