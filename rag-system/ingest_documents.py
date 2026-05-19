#!/usr/bin/env python3
"""
Document Ingestion Tool
Ingest books, articles, PDFs into the RAG system
"""

import argparse
from document_processor import DocumentProcessor
from vector_store import VectorStore

def main():
    parser = argparse.ArgumentParser(description='Ingest documents into RAG system')
    parser.add_argument('--url', help='URL to ingest')
    parser.add_argument('--file', help='Local file to ingest')
    parser.add_argument('--scrape', help='Website to scrape (multiple pages)')
    parser.add_argument('--max-pages', type=int, default=10, help='Max pages to scrape')
    
    args = parser.parse_args()
    
    processor = DocumentProcessor()
    store = VectorStore()
    
    documents = []
    
    if args.url:
        print(f"📥 Loading from URL: {args.url}")
        text = processor.load_from_url(args.url)
        if text:
            chunks = processor.chunk_text(text, metadata={'source': args.url, 'type': 'url'})
            documents.extend(chunks)
            print(f"✅ Created {len(chunks)} chunks from URL")
    
    elif args.file:
        print(f"📥 Loading from file: {args.file}")
        text = processor.load_from_file(args.file)
        if text:
            chunks = processor.chunk_text(text, metadata={'source': args.file, 'type': 'file'})
            documents.extend(chunks)
            print(f"✅ Created {len(chunks)} chunks from file")
    
    elif args.scrape:
        print(f"🕷️  Scraping website: {args.scrape}")
        documents = processor.scrape_website(args.scrape, max_pages=args.max_pages)
        print(f"✅ Scraped {len(documents)} chunks from {args.max_pages} pages")
    
    else:
        print("❌ Please provide --url, --file, or --scrape")
        return
    
    if documents:
        print(f"\n💾 Adding {len(documents)} documents to vector store...")
        added = store.add_documents(documents)
        print(f"✅ Successfully added {added} documents")
        print(f"📊 Total documents in store: {store.count()}")
    else:
        print("❌ No documents to add")


if __name__ == "__main__":
    main()
