"""
Vector Store for RAG Chatbot

Uses ChromaDB for:
- Storing document embeddings
- Fast similarity search
- Persistent storage
"""

import os
from typing import Optional
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from .document_processor import DocumentChunk, ProcessedDocument


@dataclass
class SearchResult:
    """Represents a search result from vector store"""
    chunk_id: str
    content: str
    score: float
    metadata: dict
    section: Optional[str] = None
    page_number: Optional[int] = None


class VectorStore:
    """
    ChromaDB-based vector store for document chunks.
    
    Features:
    - Automatic embedding generation
    - Persistent storage
    - Fast similarity search
    - Metadata filtering
    """
    
    def __init__(
        self,
        collection_name: str = "legal_documents",
        persist_directory: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Directory for persistent storage
            embedding_model: Sentence transformer model to use
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB required. Install with: pip install chromadb")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory or "./chroma_db"
        self.embedding_model_name = embedding_model
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection with embedding function
        self._embedding_function = self._create_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _create_embedding_function(self):
        """Create embedding function for ChromaDB"""
        try:
            from chromadb.utils import embedding_functions
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name
            )
        except Exception:
            # Fallback to default
            return None
    
    def add_document(self, document: ProcessedDocument) -> int:
        """
        Add a processed document to the vector store.
        
        Args:
            document: ProcessedDocument with chunks
            
        Returns:
            Number of chunks added
        """
        if not document.chunks:
            return 0
        
        ids = []
        documents = []
        metadatas = []
        
        for chunk in document.chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            metadatas.append({
                "doc_id": document.doc_id,
                "filename": document.filename,
                "section": chunk.section or "",
                "page_number": chunk.page_number or 0,
                "chunk_id": chunk.chunk_id,
            })
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        
        return len(ids)
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        doc_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            n_results: Number of results to return
            doc_filter: Optional document ID to filter by
            
        Returns:
            List of SearchResult objects
        """
        # Build filter
        where_filter = None
        if doc_filter:
            where_filter = {"doc_id": doc_filter}
        
        # Query collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results and results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                # Convert distance to similarity score (cosine)
                distance = results['distances'][0][i] if results['distances'] else 0
                score = 1 - distance  # Convert distance to similarity
                
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                
                search_results.append(SearchResult(
                    chunk_id=chunk_id,
                    content=results['documents'][0][i],
                    score=score,
                    metadata=metadata,
                    section=metadata.get('section'),
                    page_number=metadata.get('page_number'),
                ))
        
        return search_results
    
    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        # Get all chunks for this document
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )
        
        if results and results['ids']:
            self.collection.delete(ids=results['ids'])
            return len(results['ids'])
        
        return 0
    
    def clear(self):
        """Clear all documents from the collection"""
        # Delete and recreate collection
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_stats(self) -> dict:
        """Get collection statistics"""
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }
    
    def list_documents(self) -> list[dict]:
        """List all documents in the collection"""
        results = self.collection.get(include=["metadatas"])
        
        # Extract unique documents
        docs = {}
        if results and results['metadatas']:
            for meta in results['metadatas']:
                doc_id = meta.get('doc_id')
                if doc_id and doc_id not in docs:
                    docs[doc_id] = {
                        "doc_id": doc_id,
                        "filename": meta.get('filename', 'Unknown'),
                        "chunk_count": 0,
                    }
                if doc_id:
                    docs[doc_id]["chunk_count"] += 1
        
        return list(docs.values())
