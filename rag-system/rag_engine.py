"""
RAG Engine - Main query engine
Retrieves relevant context and generates answers using Ollama
100% FREE - No API costs
"""

from ollama_client import OllamaClient
from vector_store import VectorStore
from typing import List, Dict

class RAGEngine:
    def __init__(self):
        self.ollama = OllamaClient()
        self.vector_store = VectorStore()
    
    def query(self, question: str, n_results: int = 5, temperature: float = 0.7) -> Dict:
        """
        Query the RAG system
        
        Returns:
            {
                'answer': str,
                'sources': List[Dict],
                'context_used': str
            }
        """
        
        # Step 1: Retrieve relevant documents
        print(f"🔍 Searching for relevant context...")
        relevant_docs = self.vector_store.search(question, n_results=n_results)
        
        if not relevant_docs:
            return {
                'answer': "I don't have enough information to answer that question. Please add more documents to the knowledge base.",
                'sources': [],
                'context_used': ''
            }
        
        # Step 2: Build context from retrieved documents
        context = "\n\n".join([
            f"[Source {i+1}]: {doc['text']}"
            for i, doc in enumerate(relevant_docs)
        ])
        
        print(f"📚 Found {len(relevant_docs)} relevant documents")
        
        # Step 3: Generate answer using Ollama
        system_prompt = """You are a helpful AI assistant. Answer questions based ONLY on the provided context.
If the context doesn't contain enough information to answer the question, say so.
Be concise but thorough. Cite sources when possible."""
        
        user_prompt = f"""Context:
{context}

Question: {question}

Answer based on the context above:"""
        
        print(f"🤖 Generating answer with Ollama...")
        answer = self.ollama.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        return {
            'answer': answer,
            'sources': relevant_docs,
            'context_used': context
        }
    
    def chat(self, messages: List[Dict], n_results: int = 3) -> str:
        """
        Chat with context retrieval
        
        messages format: [
            {'role': 'user', 'content': 'question'},
            {'role': 'assistant', 'content': 'answer'},
            ...
        ]
        """
        
        # Get last user message
        last_message = messages[-1]['content']
        
        # Retrieve relevant context
        relevant_docs = self.vector_store.search(last_message, n_results=n_results)
        
        if relevant_docs:
            context = "\n\n".join([doc['text'] for doc in relevant_docs])
            
            # Add context to system message
            system_message = {
                'role': 'system',
                'content': f"""You are a helpful AI assistant. Use the following context to answer questions:

{context}

Answer based on this context when relevant."""
            }
            
            messages_with_context = [system_message] + messages
        else:
            messages_with_context = messages
        
        return self.ollama.chat(messages_with_context)
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        return {
            'total_documents': self.vector_store.count(),
            'ollama_available': self.ollama.is_available(),
            'installed_models': self.ollama.list_models()
        }


# Test
if __name__ == "__main__":
    rag = RAGEngine()
    
    print("📊 RAG System Stats:")
    stats = rag.get_stats()
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Ollama: {'✅ Available' if stats['ollama_available'] else '❌ Not running'}")
    print(f"  Models: {', '.join(stats['installed_models'])}")
    
    if stats['total_documents'] > 0:
        print("\n🧪 Testing query...")
        result = rag.query("What is Python?")
        
        print(f"\n💬 Question: What is Python?")
        print(f"\n📝 Answer:\n{result['answer']}")
        print(f"\n📚 Used {len(result['sources'])} sources")
    else:
        print("\n⚠️  No documents in knowledge base. Add some first!")
        print("   Run: python ingest_documents.py --url <url>")
