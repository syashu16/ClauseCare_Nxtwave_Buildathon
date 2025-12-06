"""
FAISS Vector Store for RAG Chatbot

Uses FAISS for:
- In-memory vector storage (cloud compatible)
- Fast similarity search
- No persistence dependencies

This replaces ChromaDB for Streamlit Cloud deployment.
"""

import numpy as np
from typing import Optional, List
from dataclasses import dataclass

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

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


class FAISSVectorStore:
    """
    FAISS-based vector store for document chunks.
    
    Features:
    - In-memory storage (no file system dependencies)
    - Fast similarity search
    - Works on Streamlit Cloud
    - Sentence Transformer embeddings
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the FAISS vector store.
        
        Args:
            embedding_model: Sentence transformer model to use
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS required. Install with: pip install faiss-cpu")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("Sentence Transformers required. Install with: pip install sentence-transformers")
        
        self.embedding_model_name = embedding_model
        self.embedding_model = SentenceTransformer(embedding_model)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index (L2 distance)
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product for cosine similarity
        
        # Storage for chunk data (FAISS only stores vectors)
        self.chunks: List[dict] = []
        self.chunk_map: dict = {}  # chunk_id -> index
    
    def _embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        embeddings = self.embedding_model.encode(
            texts,
            normalize_embeddings=True,  # Normalize for cosine similarity
            show_progress_bar=False
        )
        return embeddings.astype('float32')
    
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
        
        texts = []
        new_chunks = []
        
        for chunk in document.chunks:
            texts.append(chunk.content)
            
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "doc_id": document.doc_id,
                "filename": document.filename,
                "section": chunk.section or "",
                "page_number": chunk.page_number or 0,
            }
            new_chunks.append(chunk_data)
        
        # Generate embeddings
        embeddings = self._embed(texts)
        
        # Add to FAISS index
        start_idx = len(self.chunks)
        self.index.add(embeddings)
        
        # Store chunk data
        for i, chunk_data in enumerate(new_chunks):
            self.chunk_map[chunk_data["chunk_id"]] = start_idx + i
            self.chunks.append(chunk_data)
        
        return len(new_chunks)
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        doc_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search for relevant chunks.
        
        Args:
            query: Search query
            n_results: Number of results to return
            doc_filter: Optional document ID to filter by
            
        Returns:
            List of SearchResult objects
        """
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self._embed([query])
        
        # Search more results if we need to filter
        search_n = n_results * 3 if doc_filter else n_results
        search_n = min(search_n, self.index.ntotal)
        
        # Search FAISS index
        scores, indices = self.index.search(query_embedding, search_n)
        
        # Convert to SearchResult objects
        search_results = []
        
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            
            chunk_data = self.chunks[idx]
            
            # Apply document filter
            if doc_filter and chunk_data.get("doc_id") != doc_filter:
                continue
            
            score = float(scores[0][i])
            
            search_results.append(SearchResult(
                chunk_id=chunk_data["chunk_id"],
                content=chunk_data["content"],
                score=score,
                metadata={
                    "doc_id": chunk_data.get("doc_id"),
                    "filename": chunk_data.get("filename"),
                    "section": chunk_data.get("section"),
                    "page_number": chunk_data.get("page_number"),
                },
                section=chunk_data.get("section"),
                page_number=chunk_data.get("page_number"),
            ))
            
            if len(search_results) >= n_results:
                break
        
        return search_results
    
    def delete_document(self, doc_id: str) -> int:
        """
        Mark chunks for a document as deleted.
        Note: FAISS doesn't support true deletion, so we rebuild.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        # Filter out chunks for this document
        remaining_chunks = [c for c in self.chunks if c.get("doc_id") != doc_id]
        deleted_count = len(self.chunks) - len(remaining_chunks)
        
        if deleted_count > 0:
            # Rebuild index
            self._rebuild_index(remaining_chunks)
        
        return deleted_count
    
    def _rebuild_index(self, chunks: List[dict]):
        """Rebuild FAISS index with given chunks"""
        self.chunks = []
        self.chunk_map = {}
        self.index = faiss.IndexFlatIP(self.dimension)
        
        if not chunks:
            return
        
        texts = [c["content"] for c in chunks]
        embeddings = self._embed(texts)
        
        self.index.add(embeddings)
        
        for i, chunk_data in enumerate(chunks):
            self.chunk_map[chunk_data["chunk_id"]] = i
            self.chunks.append(chunk_data)
    
    def clear(self):
        """Clear all documents from the store"""
        self.chunks = []
        self.chunk_map = {}
        self.index = faiss.IndexFlatIP(self.dimension)
    
    def get_stats(self) -> dict:
        """Get store statistics"""
        # Count unique documents
        doc_ids = set(c.get("doc_id") for c in self.chunks)
        
        return {
            "total_chunks": len(self.chunks),
            "total_documents": len(doc_ids),
            "index_size": self.index.ntotal,
            "embedding_model": self.embedding_model_name,
        }
    
    def list_documents(self) -> List[dict]:
        """List all documents in the store"""
        docs = {}
        
        for chunk in self.chunks:
            doc_id = chunk.get("doc_id")
            if doc_id and doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "filename": chunk.get("filename", "Unknown"),
                    "chunk_count": 0,
                }
            if doc_id:
                docs[doc_id]["chunk_count"] += 1
        
        return list(docs.values())


# Alias for backward compatibility
VectorStore = FAISSVectorStore
