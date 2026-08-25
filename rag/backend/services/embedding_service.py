import os
from sentence_transformers import SentenceTransformer
from backend.config import settings

class EmbeddingService:
    def __init__(self):
        # Allow disabling multiprocessing for macOS/Windows issues occasionally seen in huggingface
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def embed_text(self, text: str) -> list[float]:
        """Embeds a single string into a vector."""
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embeds a list of strings into vectors."""
        return self.model.encode(texts).tolist()

# Singleton instance
embedding_service = EmbeddingService()
