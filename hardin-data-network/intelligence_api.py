import sys
sys.path.insert(0, '/opt/tbn-protocol/hardin-data-network')
from flask import Flask, request, jsonify, send_file
from intelligence_engine import lottery_intelligence, football_predictor, currency_predictor, commodity_predictor, economy_predictor, horse_racing_predictor
import os

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('/opt/tbn-protocol/hardin-data-network/intelligence.html')

@app.route('/predict/lottery', methods=['POST'])
def pred_lottery():
    d = request.get_json(force=True) or {}
    return jsonify(lottery_intelligence(d.get('lottery', 'EuroMillions')))

@app.route('/predict/football', methods=['POST'])
def pred_football():
    d = request.get_json(force=True) or {}
    return jsonify(football_predictor(d.get('home', 'Arsenal'), d.get('away', 'Chelsea')))

@app.route('/predict/currency', methods=['POST'])
def pred_currency():
    d = request.get_json(force=True) or {}
    return jsonify(currency_predictor(d.get('currency', 'USD')))

@app.route('/predict/commodity', methods=['POST'])
def pred_commodity():
    d = request.get_json(force=True) or {}
    return jsonify(commodity_predictor(d.get('commodity', 'Gold')))

@app.route('/predict/economy', methods=['POST'])
def pred_economy():
    return jsonify(economy_predictor())

@app.route('/predict/horse', methods=['POST'])
def pred_horse():
    d = request.get_json(force=True) or {}
    return jsonify(horse_racing_predictor(d.get('course', None)))

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'hardin-intelligence'})

if __name__ == '__main__':
    print("Hardin Intelligence Platform running on port 5009")
    app.run(host='0.0.0.0', port=5009, debug=False)
