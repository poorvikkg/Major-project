from pypdf import PdfReader
import uuid

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, file_path: str, filename: str) -> list[dict]:
        """Extracts text from a PDF and chunks it."""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            
        return self._chunk_text(text, filename)

    def _chunk_text(self, text: str, source: str) -> list[dict]:
        """Simple character-based chunking with overlap."""
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # If we are not at the end, try to find a natural break (like a newline or space)
            if end < text_len:
                # Look backwards for a newline
                last_newline = text.rfind('\n', start, end)
                if last_newline != -1 and last_newline > start + (self.chunk_size // 2):
                    end = last_newline + 1
                else:
                    # Look backwards for a space
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1 and last_space > start + (self.chunk_size // 2):
                        end = last_space + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "metadata": {"source": source}
                })
            
            start = end - self.chunk_overlap

        return chunks

# Singleton instance
document_processor = DocumentProcessor()
