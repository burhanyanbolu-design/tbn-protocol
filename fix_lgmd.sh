#!/bin/bash
# Fix LGMD to use Groq (free) instead of OpenAI

cd /home/ubuntu/lgmd-research-agent

# Fix analyser.py
sed -i 's/client = OpenAI(api_key=_api_key)/client = OpenAI(api_key=_api_key, base_url=os.getenv("OPENAI_BASE_URL", "https:\/\/api.groq.com\/openai\/v1"))/' agent/analyser.py
sed -i 's/model="gpt-3.5-turbo"/model="llama-3.1-8b-instant"/' agent/analyser.py

# Fix hypothesis.py
sed -i 's/client = OpenAI(api_key=_api_key)/client = OpenAI(api_key=_api_key, base_url=os.getenv("OPENAI_BASE_URL", "https:\/\/api.groq.com\/openai\/v1"))/' agent/hypothesis.py
sed -i 's/model="gpt-3.5-turbo"/model="llama-3.1-8b-instant"/' agent/hypothesis.py

# Fix progress_score.py
sed -i 's/client = OpenAI(api_key=_api_key)/client = OpenAI(api_key=_api_key, base_url=os.getenv("OPENAI_BASE_URL", "https:\/\/api.groq.com\/openai\/v1"))/' agent/progress_score.py
sed -i 's/model="gpt-4"/model="llama-3.1-8b-instant"/' agent/progress_score.py

# Fix podcast.py
sed -i 's/client = OpenAI(api_key=_api_key)/client = OpenAI(api_key=_api_key, base_url=os.getenv("OPENAI_BASE_URL", "https:\/\/api.groq.com\/openai\/v1"))/' agent/podcast.py
sed -i 's/model="gpt-3.5-turbo"/model="llama-3.1-8b-instant"/' agent/podcast.py

# Comment out TTS (Groq doesn't support audio.speech)
sed -i 's/response = client.audio.speech.create/# response = client.audio.speech.create/' agent/podcast.py

# Clear pycache
rm -rf agent/__pycache__

echo "Done! LGMD now uses Groq (free)"
echo "Model: llama-3.1-8b-instant"
echo "Cost: $0"
