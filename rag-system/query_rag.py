#!/usr/bin/env python3
"""
Query the RAG system from command line
"""

import sys
from rag_engine import RAGEngine

def main():
    if len(sys.argv) < 2:
        print("Usage: python query_rag.py 'Your question here'")
        sys.exit(1)
    
    question = ' '.join(sys.argv[1:])
    
    print(f"🔍 Question: {question}\n")
    print("="*60)
    
    rag = RAGEngine()
    result = rag.query(question)
    
    print(f"\n💬 Answer:\n{result['answer']}")
    
    if result['sources']:
        print(f"\n📚 Sources ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n{i}. {source['text'][:200]}...")
            if source['metadata']:
                print(f"   Source: {source['metadata'].get('source', 'Unknown')}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
