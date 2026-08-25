import chromadb
from chromadb.config import Settings
from backend.config import settings

class ChromaService:
    def __init__(self):
        # Initialize a persistent client
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        # Create or get standard collections
        self.crime_stats = self.client.get_or_create_collection("crime_statistics")
        self.fir_docs = self.client.get_or_create_collection("fir_documents")
        
        # We will dynamically create collections for uploaded_documents during session

    def get_collection(self, name: str):
        """Retrieve a specific collection."""
        return self.client.get_or_create_collection(name)
        
    def add_to_collection(self, collection_name: str, ids: list[str], embeddings: list[list[float]], metadatas: list[dict], documents: list[str]):
        """Add vectors to a collection."""
        collection = self.get_collection(collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def search_collection(self, collection_name: str, query_embedding: list[float], n_results: int = 5):
        """Search a collection by vector."""
        collection = self.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

# Singleton instance
chroma_service = ChromaService()
