"""
RAG Chatbot Module for GenLegalAI

A Retrieval-Augmented Generation chatbot that:
- Understands legal documents deeply
- Provides accurate, cited answers
- Explains complex terms in plain language
- Never hallucinates information
"""

from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .retriever import Retriever
from .chat_engine import ChatEngine

__all__ = [
    "DocumentProcessor",
    "VectorStore", 
    "Retriever",
    "ChatEngine",
]
