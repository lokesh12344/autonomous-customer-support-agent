"""Vector store service using Chroma for semantic search."""

from typing import List, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.utils.config import settings


class VectorStoreService:
    """Service for managing Chroma vector store operations."""
    
    def __init__(self):
        """Initialize the Chroma vector store."""
        self.persist_directory = Path(settings.vectorstore_path)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
            )
        )
        
        # Get or create default collection for FAQs
        self.collection_name = "faq_collection"
        self.collection = None
    
    def get_or_create_collection(self, collection_name: Optional[str] = None):
        """
        Get or create a Chroma collection.
        
        Args:
            collection_name: Name of the collection to get/create
            
        Returns:
            chromadb.Collection: The collection object
        """
        name = collection_name or self.collection_name
        self.collection = self.client.get_or_create_collection(name=name)
        return self.collection
    
    def add_documents(self, documents: List[str], metadatas: Optional[List[dict]] = None, ids: Optional[List[str]] = None):
        """
        Add documents to the vector store.
        
        TODO: Implement document chunking and embedding
        This is a placeholder for future implementation.
        
        Args:
            documents: List of text documents to add
            metadatas: Optional metadata for each document
            ids: Optional unique IDs for each document
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        # Placeholder implementation
        print(f"📄 TODO: Add {len(documents)} documents to vector store")
        
        # Future: Actual implementation would be:
        # self.collection.add(
        #     documents=documents,
        #     metadatas=metadatas,
        #     ids=ids
        # )
    
    def query(self, query_text: str, n_results: int = 5) -> dict:
        """
        Query the vector store for similar documents.
        
        Args:
            query_text: The query text to search for
            n_results: Number of results to return
            
        Returns:
            dict: Query results with documents, distances, etc.
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"Error querying vector store: {e}")
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
                "ids": [[]]
            }


# Global vector store instance
_vectorstore = None


def get_vectorstore() -> VectorStoreService:
    """
    Get or create the global vector store instance.
    
    Returns:
        VectorStoreService: The vector store service instance
    """
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = VectorStoreService()
    return _vectorstore


if __name__ == "__main__":
    # Test vector store initialization
    print("🔍 Testing Vector Store...")
    vs = get_vectorstore()
    vs.get_or_create_collection()
    print(f"✅ Vector store initialized at: {vs.persist_directory}")
