"""
Document Processor - Ingests books, articles, PDFs, etc.
Chunks them into manageable pieces for RAG
"""

import re
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from pathlib import Path

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_from_url(self, url: str) -> str:
        """Load text content from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # If it's HTML, extract text
            if 'text/html' in response.headers.get('content-type', ''):
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                text = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                return text
            else:
                return response.text
        except Exception as e:
            print(f"Error loading URL {url}: {e}")
            return ""
    
    def load_from_file(self, filepath: str) -> str:
        """Load text from local file"""
        try:
            path = Path(filepath)
            
            if path.suffix == '.txt':
                return path.read_text(encoding='utf-8')
            
            elif path.suffix == '.pdf':
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(str(path))
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
                except ImportError:
                    print("Install pypdf: pip install pypdf")
                    return ""
            
            elif path.suffix in ['.doc', '.docx']:
                try:
                    from docx import Document
                    doc = Document(str(path))
                    return '\n'.join([para.text for para in doc.paragraphs])
                except ImportError:
                    print("Install python-docx: pip install python-docx")
                    return ""

            elif path.suffix == '.epub':
                try:
                    import ebooklib
                    from ebooklib import epub
                    from bs4 import BeautifulSoup as BS
                    book = epub.read_epub(str(path))
                    text_parts = []
                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            soup = BS(item.get_content(), 'html.parser')
                            text_parts.append(soup.get_text())
                    return '\n'.join(text_parts)
                except ImportError:
                    print("Install ebooklib: pip install ebooklib")
                    return ""

            else:
                # Try reading as text
                return path.read_text(encoding='utf-8', errors='ignore')
        
        except Exception as e:
            print(f"Error loading file {filepath}: {e}")
            return ""
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = {
                    'text': chunk_text,
                    'start': start,
                    'end': end,
                    'metadata': metadata or {}
                }
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def scrape_website(self, base_url: str, max_pages: int = 10) -> List[Dict]:
        """Scrape multiple pages from a website"""
        visited = set()
        to_visit = [base_url]
        documents = []
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited:
                continue
            
            visited.add(url)
            print(f"Scraping: {url}")
            
            text = self.load_from_url(url)
            if text:
                chunks = self.chunk_text(text, metadata={'source': url})
                documents.extend(chunks)
            
            # Find more links (simple implementation)
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/'):
                        full_url = base_url.rstrip('/') + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Only follow links from same domain
                    if base_url in full_url and full_url not in visited:
                        to_visit.append(full_url)
            except:
                pass
        
        return documents


# Test
if __name__ == "__main__":
    processor = DocumentProcessor()
    
    # Test with a sample text
    sample_text = """
    Artificial Intelligence (AI) is intelligence demonstrated by machines, 
    in contrast to the natural intelligence displayed by humans and animals. 
    Leading AI textbooks define the field as the study of "intelligent agents": 
    any device that perceives its environment and takes actions that maximize 
    its chance of successfully achieving its goals.
    """ * 10  # Repeat to make it longer
    
    chunks = processor.chunk_text(sample_text, metadata={'source': 'test'})
    print(f"✅ Created {len(chunks)} chunks from sample text")
    print(f"First chunk: {chunks[0]['text'][:100]}...")
