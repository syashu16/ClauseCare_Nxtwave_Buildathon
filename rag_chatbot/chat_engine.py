"""
Chat Engine for RAG Chatbot

Handles:
- Groq API integration with streaming
- Prompt engineering for legal context
- Conversation history management
- Source citation generation
"""

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Generator

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from .retriever import Retriever, RetrievedContext


@dataclass
class Message:
    """Represents a chat message"""
    role: str  # "user" or "assistant"
    content: str
    sources: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """Represents a conversation with history"""
    conversation_id: str
    messages: list[Message] = field(default_factory=list)
    document_id: Optional[str] = None
    document_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, sources: list[dict] = None):
        """Add a message to the conversation"""
        self.messages.append(Message(
            role=role,
            content=content,
            sources=sources or [],
        ))
    
    def get_history(self, max_messages: int = 10) -> list[dict]:
        """Get conversation history for context"""
        recent = self.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []


class ChatEngine:
    """
    Groq-powered chat engine with RAG.
    
    Features:
    - Streaming responses
    - Source citations
    - Conversation memory
    - Legal-focused prompts
    - Suggested follow-ups
    """
    
    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 2048
    TEMPERATURE = 0.3
    
    # System prompt for legal document Q&A
    SYSTEM_PROMPT = """You are a helpful legal document assistant. Your role is to:

1. **Answer questions accurately** based ONLY on the provided document context
2. **Cite your sources** using [Source X] notation for every claim
3. **Explain in plain language** - assume the user is not a lawyer
4. **Be honest** - if the document doesn't contain the answer, say so clearly
5. **Highlight risks** - point out important implications or potential concerns
6. **Never hallucinate** - only use information from the provided context

When answering:
- Structure your response clearly with headers if appropriate
- Use bullet points for lists
- Quote exact text when relevant (keep quotes short)
- Include section/page references
- Suggest follow-up questions the user might want to ask

If the question is outside the document's scope, politely explain that and suggest what questions you CAN answer.

Remember: You're helping someone understand their legal document. Be accurate, clear, and helpful."""

    def __init__(
        self,
        retriever: Retriever,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the chat engine.
        
        Args:
            retriever: Retriever instance for context
            api_key: Groq API key (or from env)
        """
        if not GROQ_AVAILABLE:
            raise ImportError("Groq required. Install with: pip install groq")
        
        self.retriever = retriever
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API key required. Set GROQ_API_KEY env var or pass api_key.")
        
        self.client = Groq(api_key=self.api_key)
        self.conversations: dict[str, Conversation] = {}
    
    def create_conversation(
        self,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None,
    ) -> Conversation:
        """Create a new conversation"""
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(datetime.now()))}"
        conv = Conversation(
            conversation_id=conv_id,
            document_id=document_id,
            document_name=document_name,
        )
        self.conversations[conv_id] = conv
        return conv
    
    def chat(
        self,
        query: str,
        conversation: Conversation,
        stream: bool = True,
    ) -> Generator[str, None, None] | str:
        """
        Process a chat query.
        
        Args:
            query: User's question
            conversation: Conversation object
            stream: Whether to stream response
            
        Yields:
            Response chunks if streaming, else returns full response
        """
        # Retrieve relevant context
        context = self.retriever.retrieve(
            query=query,
            doc_filter=conversation.document_id,
        )
        
        # Build messages
        messages = self._build_messages(query, context, conversation)
        
        # Add user message to history
        conversation.add_message("user", query)
        
        if stream:
            return self._stream_response(messages, context, conversation)
        else:
            return self._get_response(messages, context, conversation)
    
    def _build_messages(
        self,
        query: str,
        context: RetrievedContext,
        conversation: Conversation,
    ) -> list[dict]:
        """Build message list for API call"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]
        
        # Add conversation history (last 6 messages)
        history = conversation.get_history(max_messages=6)
        messages.extend(history[:-1] if history else [])  # Exclude current query
        
        # Build context-enhanced query
        user_message = f"""Based on the following document excerpts, please answer the question.

**Document Context:**
{context.context_text}

**Question:** {query}

Remember to:
1. Only use information from the context above
2. Cite sources using [Source X] notation
3. Say "I don't see this in the document" if the answer isn't in the context
4. Explain any legal terms in plain English"""
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _stream_response(
        self,
        messages: list[dict],
        context: RetrievedContext,
        conversation: Conversation,
    ) -> Generator[str, None, None]:
        """Stream response from Groq"""
        try:
            stream = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
                stream=True,
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add assistant response to history
            conversation.add_message("assistant", full_response, context.sources)
            
            # Yield sources at the end
            yield self._format_sources(context.sources)
            
        except Exception as e:
            error_msg = f"\n\n❌ Error: {str(e)}"
            yield error_msg
    
    def _get_response(
        self,
        messages: list[dict],
        context: RetrievedContext,
        conversation: Conversation,
    ) -> str:
        """Get non-streaming response"""
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
                stream=False,
            )
            
            content = response.choices[0].message.content
            
            # Add to history
            conversation.add_message("assistant", content, context.sources)
            
            # Add sources
            return content + self._format_sources(context.sources)
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _format_sources(self, sources: list[dict]) -> str:
        """Format sources for display"""
        if not sources:
            return ""
        
        source_text = "\n\n---\n📄 **Sources:**\n"
        for source in sources:
            idx = source.get('index', '?')
            section = source.get('section', 'Unknown')
            page = source.get('page_number', '?')
            snippet = source.get('snippet', '')[:80] + "..."
            source_text += f"- **[Source {idx}]** {section} (Page {page}): \"{snippet}\"\n"
        
        return source_text
    
    def get_suggested_questions(
        self,
        conversation: Conversation,
    ) -> list[str]:
        """Get suggested follow-up questions"""
        if not conversation.messages:
            # Initial questions
            return [
                "What are my main obligations under this contract?",
                "What are the termination conditions?",
                "What happens if there's a breach?",
                "What are the payment terms?",
                "Are there any liability limitations?",
            ]
        
        # Get last query context
        last_user = None
        for msg in reversed(conversation.messages):
            if msg.role == "user":
                last_user = msg.content
                break
        
        if not last_user:
            return []
        
        # Retrieve context for suggestions
        context = self.retriever.retrieve(
            query=last_user,
            doc_filter=conversation.document_id,
        )
        
        return self.retriever.get_related_questions(last_user, context.chunks)
    
    def explain_term(self, term: str) -> str:
        """Explain a legal term in plain language"""
        # Common legal term explanations
        LEGAL_TERMS = {
            "indemnification": "A promise to protect someone from financial loss. If something goes wrong, one party agrees to pay for the other party's damages.",
            "force majeure": "Unforeseeable circumstances (like natural disasters, wars, pandemics) that prevent someone from fulfilling a contract. It's often an excuse for non-performance.",
            "severability": "If one part of the contract is found invalid, the rest of the contract still applies. Think of it as 'if one piece breaks, keep the rest.'",
            "waiver": "Giving up a right voluntarily. If you waive something, you can't enforce it later.",
            "liquidated damages": "A pre-agreed amount of money to be paid if the contract is broken. It's a 'penalty' set in advance.",
            "governing law": "Which state's or country's laws apply if there's a dispute. This matters because different places have different rules.",
            "arbitration": "A private way to resolve disputes outside of court. An arbitrator (private judge) makes the decision instead of a public judge.",
            "confidentiality": "Keeping information secret. You can't share or use protected information outside of what's allowed.",
            "intellectual property": "Creations of the mind - inventions, designs, logos, software. The contract may define who owns what's created.",
            "breach": "Breaking the contract. Failing to do what you promised to do.",
            "termination": "Ending the contract. This section usually explains how and when either party can end the agreement.",
            "assignment": "Transferring your rights or obligations to someone else. Many contracts restrict this.",
            "warranty": "A promise or guarantee that something is true or will work as described.",
            "liability": "Legal responsibility. If something goes wrong, who has to pay?",
            "non-compete": "An agreement not to work for competitors or start a competing business for a certain time period.",
        }
        
        term_lower = term.lower().strip()
        
        for key, explanation in LEGAL_TERMS.items():
            if key in term_lower or term_lower in key:
                return f"**{term.title()}**: {explanation}"
        
        return f"**{term.title()}**: This is a legal term. Please ask me about it in the context of your document for a specific explanation."
    
    def export_conversation(self, conversation: Conversation) -> str:
        """Export conversation as formatted text"""
        output = f"# Conversation Export\n"
        output += f"Document: {conversation.document_name or 'Unknown'}\n"
        output += f"Date: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        output += f"---\n\n"
        
        for msg in conversation.messages:
            role = "🧑 You" if msg.role == "user" else "🤖 Assistant"
            output += f"### {role}\n{msg.content}\n\n"
            
            if msg.sources:
                output += "**Sources:**\n"
                for source in msg.sources:
                    output += f"- {source.get('section', '?')} (Page {source.get('page_number', '?')})\n"
                output += "\n"
        
        return output
