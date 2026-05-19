"""
Example: Integrate RAG with TBN Protocol
Create a smart TBN bot that uses RAG knowledge
"""

import sys
sys.path.append('..')

from rag_engine import RAGEngine
from tbn import Bot

class SmartTBNBot(Bot):
    """
    A TBN bot with RAG-powered knowledge
    Can answer questions using ingested documents
    """
    
    def __init__(self, name="SmartBot"):
        super().__init__()
        self.name = name
        self.rag = RAGEngine()
        print(f"✅ {name} initialized with RAG knowledge")
        print(f"📚 Knowledge base: {self.rag.get_stats()['total_documents']} documents")
    
    def answer_question(self, question: str) -> dict:
        """Answer a question using RAG"""
        print(f"\n🤔 {self.name} thinking about: {question}")
        result = self.rag.query(question)
        return result
    
    def learn_from_file(self, filepath: str):
        """Ingest a new document"""
        from document_processor import DocumentProcessor
        from vector_store import VectorStore
        
        processor = DocumentProcessor()
        store = VectorStore()
        
        print(f"📖 Learning from: {filepath}")
        text = processor.load_from_file(filepath)
        chunks = processor.chunk_text(text, metadata={'source': filepath})
        added = store.add_documents(chunks)
        print(f"✅ Learned {added} new chunks")
    
    def learn_from_url(self, url: str):
        """Ingest content from URL"""
        from document_processor import DocumentProcessor
        from vector_store import VectorStore
        
        processor = DocumentProcessor()
        store = VectorStore()
        
        print(f"🌐 Learning from: {url}")
        text = processor.load_from_url(url)
        chunks = processor.chunk_text(text, metadata={'source': url})
        added = store.add_documents(chunks)
        print(f"✅ Learned {added} new chunks")


# Example usage
if __name__ == "__main__":
    # Create smart bot
    bot = SmartTBNBot("TBN Knowledge Bot")
    
    # Ask questions
    questions = [
        "What is machine learning?",
        "What is the TBN Protocol?",
        "What programming language is best for AI?"
    ]
    
    for q in questions:
        result = bot.answer_question(q)
        print(f"\n💬 Answer: {result['answer'][:200]}...")
        print(f"📚 Used {len(result['sources'])} sources")
        print("-" * 60)
