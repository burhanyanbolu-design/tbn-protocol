"""
Ollama Client - FREE Local AI
No API costs, runs on your server
"""

import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama3.2"
        self.embed_model = "nomic-embed-text"
    
    def generate(self, prompt, system_prompt=None, temperature=0.7):
        """Generate text using Ollama"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            return f"Error: {str(e)}"
    
    def embed(self, text):
        """Generate embeddings using Ollama"""
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": self.embed_model,
            "prompt": text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def chat(self, messages, temperature=0.7):
        """Chat with Ollama (conversation format)"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            return f"Error: {str(e)}"
    
    def is_available(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self):
        """List installed models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except:
            return []


# Test function
if __name__ == "__main__":
    client = OllamaClient()
    
    print("🔍 Checking Ollama status...")
    if client.is_available():
        print("✅ Ollama is running!")
        print(f"📦 Installed models: {', '.join(client.list_models())}")
        
        print("\n🧪 Testing text generation...")
        response = client.generate("What is artificial intelligence? Answer in 2 sentences.")
        print(f"Response: {response}")
        
        print("\n🧪 Testing embeddings...")
        embedding = client.embed("Hello world")
        if embedding:
            print(f"✅ Embedding generated ({len(embedding)} dimensions)")
        else:
            print("❌ Embedding failed")
    else:
        print("❌ Ollama is not running!")
        print("Start it with: ollama serve")
