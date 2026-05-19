"""
Vector Store - Stores document embeddings in ChromaDB
FREE, runs locally, no cloud costs
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict
from ollama_client import OllamaClient
import hashlib

class VectorStore:
    def __init__(self, persist_directory="./chroma_db"):
        """Initialize ChromaDB with local storage"""
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="tbn_knowledge",
            metadata={"description": "TBN RAG Knowledge Base"}
        )
        
        self.ollama = OllamaClient()
    
    def add_documents(self, documents: List[Dict]) -> int:
        """Add documents to vector store"""
        if not documents:
            return 0
        
        print(f"📥 Adding {len(documents)} documents to vector store...")
        
        ids = []
        texts = []
        embeddings = []
        metadatas = []
        
        for i, doc in enumerate(documents):
            text = doc['text']
            
            # Generate unique ID
            doc_id = hashlib.md5(text.encode()).hexdigest()
            
            # Generate embedding using Ollama
            embedding = self.ollama.embed(text)
            
            if embedding:
                ids.append(doc_id)
                texts.append(text)
                embeddings.append(embedding)
                metadatas.append(doc.get('metadata', {}))
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(documents)} documents...")
        
        if ids:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"✅ Added {len(ids)} documents to vector store")
        
        return len(ids)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant documents"""
        # Generate query embedding
        query_embedding = self.ollama.embed(query)
        
        if not query_embedding:
            return []
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        documents = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
        
        return documents
    
    def count(self) -> int:
        """Get total number of documents"""
        return self.collection.count()
    
    def clear(self):
        """Clear all documents"""
        self.client.delete_collection("tbn_knowledge")
        self.collection = self.client.get_or_create_collection(
            name="tbn_knowledge",
            metadata={"description": "TBN RAG Knowledge Base"}
        )
        print("✅ Vector store cleared")


# Test
if __name__ == "__main__":
    store = VectorStore()
    
    print(f"📊 Current document count: {store.count()}")
    
    # Test adding documents
    test_docs = [
        {
            'text': 'Python is a high-level programming language known for its simplicity.',
            'metadata': {'source': 'test', 'topic': 'programming'}
        },
        {
            'text': 'Machine learning is a subset of artificial intelligence.',
            'metadata': {'source': 'test', 'topic': 'AI'}
        },
        {
            'text': 'The TBN Protocol provides trust infrastructure for AI agents.',
            'metadata': {'source': 'test', 'topic': 'TBN'}
        }
    ]
    
    store.add_documents(test_docs)
    
    # Test search
    print("\n🔍 Testing search...")
    results = store.search("What is Python?", n_results=2)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['text'][:100]}...")
        print(f"   Distance: {result['distance']:.4f}")
