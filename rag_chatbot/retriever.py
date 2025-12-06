"""
Retriever for RAG Chatbot

Handles:
- Query processing
- Semantic search
- Result reranking
- Context assembly
"""

from dataclasses import dataclass, field
from typing import Optional

from .vector_store import VectorStore, SearchResult


@dataclass
class RetrievedContext:
    """Assembled context for LLM"""
    query: str
    chunks: list[SearchResult]
    context_text: str
    sources: list[dict] = field(default_factory=list)
    total_tokens_estimate: int = 0
    
    def get_citation_text(self) -> str:
        """Get formatted citation text"""
        citations = []
        for i, source in enumerate(self.sources, 1):
            section = source.get('section', 'Unknown Section')
            page = source.get('page_number', '?')
            snippet = source.get('snippet', '')[:100] + "..."
            citations.append(f"[{i}] Section: {section} (Page {page}): \"{snippet}\"")
        return "\n".join(citations)


class Retriever:
    """
    Retrieves relevant context from vector store.
    
    Features:
    - Query expansion for legal terms
    - Semantic search with reranking
    - Context window management
    - Source tracking for citations
    """
    
    # Legal term expansions for better retrieval
    LEGAL_EXPANSIONS = {
        "terminate": ["termination", "cancel", "end", "cessation"],
        "liability": ["liable", "responsibility", "damages", "indemnify"],
        "payment": ["fee", "compensation", "price", "cost", "invoice"],
        "confidential": ["confidentiality", "NDA", "proprietary", "trade secret"],
        "breach": ["violation", "default", "failure to comply", "non-compliance"],
        "warranty": ["guarantee", "representation", "assurance"],
        "indemnify": ["indemnification", "hold harmless", "defend"],
        "intellectual property": ["IP", "patent", "copyright", "trademark"],
        "dispute": ["arbitration", "litigation", "mediation", "resolution"],
        "force majeure": ["act of god", "unforeseen", "beyond control"],
    }
    
    def __init__(
        self,
        vector_store: VectorStore,
        max_context_tokens: int = 4000,
        top_k: int = 5,
        rerank: bool = True,
    ):
        """
        Initialize the retriever.
        
        Args:
            vector_store: VectorStore instance
            max_context_tokens: Maximum tokens for context
            top_k: Number of chunks to retrieve
            rerank: Whether to rerank results
        """
        self.vector_store = vector_store
        self.max_context_tokens = max_context_tokens
        self.top_k = top_k
        self.rerank = rerank
    
    def retrieve(
        self,
        query: str,
        doc_filter: Optional[str] = None,
        expand_query: bool = True,
    ) -> RetrievedContext:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User's question
            doc_filter: Optional document ID to filter
            expand_query: Whether to expand legal terms
            
        Returns:
            RetrievedContext with assembled context
        """
        # Expand query with legal terms
        search_query = query
        if expand_query:
            search_query = self._expand_query(query)
        
        # Search vector store
        results = self.vector_store.search(
            query=search_query,
            n_results=self.top_k * 2,  # Get more for reranking
            doc_filter=doc_filter,
        )
        
        # Rerank if enabled
        if self.rerank and len(results) > self.top_k:
            results = self._rerank_results(query, results)[:self.top_k]
        else:
            results = results[:self.top_k]
        
        # Assemble context
        context_text, sources = self._assemble_context(results)
        
        # Estimate tokens (rough: 4 chars = 1 token)
        token_estimate = len(context_text) // 4
        
        return RetrievedContext(
            query=query,
            chunks=results,
            context_text=context_text,
            sources=sources,
            total_tokens_estimate=token_estimate,
        )
    
    def _expand_query(self, query: str) -> str:
        """Expand query with related legal terms"""
        query_lower = query.lower()
        expansions = []
        
        for term, related in self.LEGAL_EXPANSIONS.items():
            if term in query_lower:
                expansions.extend(related[:2])  # Add top 2 related terms
        
        if expansions:
            return f"{query} {' '.join(expansions)}"
        return query
    
    def _rerank_results(
        self,
        query: str,
        results: list[SearchResult]
    ) -> list[SearchResult]:
        """
        Rerank results based on multiple signals.
        
        Considers:
        - Semantic similarity (from vector search)
        - Keyword overlap
        - Section relevance
        """
        query_terms = set(query.lower().split())
        
        scored_results = []
        for result in results:
            # Base score from vector search
            score = result.score
            
            # Boost for keyword overlap
            content_lower = result.content.lower()
            keyword_matches = sum(1 for term in query_terms if term in content_lower)
            keyword_boost = keyword_matches * 0.05
            
            # Boost for exact phrase match
            if query.lower() in content_lower:
                keyword_boost += 0.1
            
            # Boost for section relevance
            section = result.section or ""
            section_boost = 0
            if any(term in section.lower() for term in query_terms):
                section_boost = 0.05
            
            final_score = score + keyword_boost + section_boost
            scored_results.append((final_score, result))
        
        # Sort by final score
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        return [r for _, r in scored_results]
    
    def _assemble_context(
        self,
        results: list[SearchResult]
    ) -> tuple[str, list[dict]]:
        """
        Assemble context string and sources from results.
        
        Returns:
            Tuple of (context_text, sources_list)
        """
        context_parts = []
        sources = []
        current_tokens = 0
        
        for i, result in enumerate(results):
            # Estimate tokens for this chunk
            chunk_tokens = len(result.content) // 4
            
            # Check if we'd exceed limit
            if current_tokens + chunk_tokens > self.max_context_tokens:
                break
            
            # Format chunk with source info
            section = result.section or "Document"
            page = result.page_number or "?"
            
            context_parts.append(
                f"[Source {i+1} - {section} (Page {page})]\n{result.content}"
            )
            
            # Track source for citation
            sources.append({
                "index": i + 1,
                "section": section,
                "page_number": page,
                "snippet": result.content[:200],
                "score": result.score,
                "chunk_id": result.chunk_id,
            })
            
            current_tokens += chunk_tokens
        
        context_text = "\n\n---\n\n".join(context_parts)
        
        return context_text, sources
    
    def get_related_questions(
        self,
        query: str,
        results: list[SearchResult]
    ) -> list[str]:
        """Generate related questions based on retrieved content"""
        # Extract key topics from results
        topics = set()
        
        for result in results[:3]:
            section = result.section
            if section:
                topics.add(section)
        
        # Generate questions
        questions = []
        
        if "liability" in query.lower() or "indemnif" in query.lower():
            questions.append("What are the limits on liability in this contract?")
            questions.append("Who is responsible for third-party claims?")
        
        if "terminat" in query.lower():
            questions.append("What happens after termination?")
            questions.append("Are there any survival clauses?")
        
        if "payment" in query.lower() or "fee" in query.lower():
            questions.append("What are the payment terms and due dates?")
            questions.append("What happens if payment is late?")
        
        if "confidential" in query.lower():
            questions.append("How long does confidentiality last?")
            questions.append("What information is excluded from confidentiality?")
        
        # Add section-based questions
        for topic in list(topics)[:2]:
            questions.append(f"What are my obligations under the {topic} section?")
        
        return questions[:5]
