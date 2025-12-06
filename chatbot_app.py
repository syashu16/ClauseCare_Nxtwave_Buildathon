"""
Streamlit UI for RAG Chatbot

A beautiful, responsive chat interface for legal document Q&A.
"""

import streamlit as st
import os
from datetime import datetime

# Import RAG components
try:
    from rag_chatbot.document_processor import DocumentProcessor
    from rag_chatbot.vector_store import VectorStore
    from rag_chatbot.retriever import Retriever
    from rag_chatbot.chat_engine import ChatEngine, Conversation
except ImportError:
    st.error("RAG chatbot module not found. Please ensure it's in the Python path.")
    st.stop()


# Page configuration
st.set_page_config(
    page_title="GenLegalAI - Document Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .chat-message.assistant {
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
    }
    .chat-message .content {
        color: #333;
    }
    .source-card {
        background-color: #fff8e1;
        border: 1px solid #ffcc80;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin: 0.25rem 0;
        font-size: 0.85rem;
    }
    .suggested-question {
        background-color: #e8f5e9;
        border: 1px solid #a5d6a7;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        display: inline-block;
    }
    .suggested-question:hover {
        background-color: #c8e6c9;
    }
    .document-info {
        background-color: #f3e5f5;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .legal-term {
        background-color: #fff3e0;
        padding: 0.75rem;
        border-radius: 0.5rem;
        border-left: 3px solid #ff9800;
        margin: 0.5rem 0;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = None
    if 'retriever' not in st.session_state:
        st.session_state.retriever = None
    if 'chat_engine' not in st.session_state:
        st.session_state.chat_engine = None
    if 'conversation' not in st.session_state:
        st.session_state.conversation = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'document_loaded' not in st.session_state:
        st.session_state.document_loaded = False
    if 'document_name' not in st.session_state:
        st.session_state.document_name = None
    if 'suggested_questions' not in st.session_state:
        st.session_state.suggested_questions = []


def initialize_rag_system(api_key: str):
    """Initialize the RAG system components"""
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore(
            collection_name="legal_docs",
            persist_directory="./chroma_db"
        )
    
    if st.session_state.retriever is None:
        st.session_state.retriever = Retriever(
            vector_store=st.session_state.vector_store,
            max_context_tokens=4000,
            top_k=5,
        )
    
    if st.session_state.chat_engine is None and api_key:
        st.session_state.chat_engine = ChatEngine(
            retriever=st.session_state.retriever,
            api_key=api_key,
        )


def process_uploaded_document(uploaded_file, processor: DocumentProcessor):
    """Process an uploaded document"""
    try:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        
        with st.spinner(f"Processing {filename}..."):
            document = processor.process_file(file_bytes, filename)
            
            # Add to vector store
            chunks_added = st.session_state.vector_store.add_document(document)
            
            # Create conversation
            if st.session_state.chat_engine:
                st.session_state.conversation = st.session_state.chat_engine.create_conversation(
                    document_id=document.doc_id,
                    document_name=filename,
                )
            
            st.session_state.document_loaded = True
            st.session_state.document_name = filename
            st.session_state.messages = []
            
            # Set initial suggested questions
            st.session_state.suggested_questions = [
                "What is this document about?",
                "What are my main obligations?",
                "What are the termination conditions?",
                "What are the payment terms?",
                "Are there any liability limitations?",
            ]
            
            return document, chunks_added
            
    except Exception as e:
        st.error(f"Error processing document: {str(e)}")
        return None, 0


def render_message(role: str, content: str, sources: list = None):
    """Render a chat message"""
    css_class = "user" if role == "user" else "assistant"
    icon = "🧑" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <div><strong>{icon} {'You' if role == 'user' else 'Assistant'}</strong></div>
        <div class="content">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_sources(sources: list):
    """Render source citations"""
    if not sources:
        return
    
    with st.expander("📄 View Sources", expanded=False):
        for source in sources:
            section = source.get('section', 'Unknown')
            page = source.get('page_number', '?')
            snippet = source.get('snippet', '')[:150] + "..."
            
            st.markdown(f"""
            <div class="source-card">
                <strong>[Source {source.get('index', '?')}]</strong> {section} (Page {page})<br>
                <em>"{snippet}"</em>
            </div>
            """, unsafe_allow_html=True)


def render_suggested_questions():
    """Render suggested follow-up questions"""
    if not st.session_state.suggested_questions:
        return
    
    st.markdown("**💡 You might also ask:**")
    cols = st.columns(min(len(st.session_state.suggested_questions), 3))
    
    for i, question in enumerate(st.session_state.suggested_questions[:6]):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(question, key=f"suggested_{i}", use_container_width=True):
                return question
    
    return None


def main():
    """Main Streamlit application"""
    init_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("💬 GenLegalAI")
        st.subheader("Document Chat")
        
        st.markdown("---")
        
        # API Configuration
        api_key = st.text_input(
            "🔑 Groq API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            help="Enter your Groq API key"
        )
        
        if api_key:
            try:
                initialize_rag_system(api_key)
                st.success("✅ Connected to Groq")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
        
        st.markdown("---")
        
        # Document Upload
        st.subheader("📄 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a legal document",
            type=["pdf", "docx", "txt"],
            help="Upload a contract or legal document to chat about"
        )
        
        if uploaded_file and not st.session_state.document_loaded:
            processor = DocumentProcessor(
                chunk_size=500,
                chunk_overlap=100,
            )
            doc, chunks = process_uploaded_document(uploaded_file, processor)
            
            if doc:
                st.success(f"✅ Loaded {doc.total_chunks} chunks")
        
        # Document info
        if st.session_state.document_loaded:
            st.markdown("---")
            st.markdown(f"**Current Document:**")
            st.info(st.session_state.document_name)
            
            if st.button("🗑️ Clear Document", use_container_width=True):
                if st.session_state.vector_store:
                    st.session_state.vector_store.clear()
                st.session_state.document_loaded = False
                st.session_state.document_name = None
                st.session_state.messages = []
                st.session_state.conversation = None
                st.rerun()
        
        st.markdown("---")
        
        # Legal term lookup
        st.subheader("📚 Legal Terms")
        term = st.text_input("Look up a term", placeholder="e.g., indemnification")
        
        if term and st.session_state.chat_engine:
            explanation = st.session_state.chat_engine.explain_term(term)
            st.markdown(f"""
            <div class="legal-term">
                {explanation}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Export conversation
        if st.session_state.messages:
            if st.button("📥 Export Chat", use_container_width=True):
                if st.session_state.conversation:
                    export_text = st.session_state.chat_engine.export_conversation(
                        st.session_state.conversation
                    )
                    st.download_button(
                        "Download",
                        export_text,
                        file_name="chat_export.md",
                        mime="text/markdown",
                    )
    
    # Main content
    st.title("Chat with Your Legal Document")
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar to start chatting.")
        st.stop()
    
    if not st.session_state.document_loaded:
        st.info("📄 Please upload a legal document in the sidebar to begin.")
        
        # Show example questions
        st.markdown("### Once you upload a document, you can ask questions like:")
        example_questions = [
            "What are my main obligations under this contract?",
            "What happens if I want to terminate early?",
            "What are the payment terms and deadlines?",
            "Who is liable if something goes wrong?",
            "What information do I need to keep confidential?",
        ]
        
        for q in example_questions:
            st.markdown(f"- _{q}_")
        
        st.stop()
    
    # Document info bar
    st.markdown(f"""
    <div class="document-info">
        📄 <strong>Chatting about:</strong> {st.session_state.document_name}
    </div>
    """, unsafe_allow_html=True)
    
    # Chat messages
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages:
            render_message(msg["role"], msg["content"])
            if msg.get("sources"):
                render_sources(msg["sources"])
    
    # Suggested questions (if no messages yet)
    if not st.session_state.messages:
        selected_question = render_suggested_questions()
        if selected_question:
            st.session_state.pending_question = selected_question
            st.rerun()
    
    # Chat input
    st.markdown("---")
    
    # Check for pending question from button click
    pending = st.session_state.get('pending_question')
    
    prompt = st.chat_input("Ask a question about your document...")
    
    # Use pending question if available
    if pending:
        prompt = pending
        del st.session_state.pending_question
    
    if prompt:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })
        
        # Display user message
        with chat_container:
            render_message("user", prompt)
        
        # Generate response
        if st.session_state.chat_engine and st.session_state.conversation:
            with st.spinner("Thinking..."):
                # Create placeholder for streaming
                response_placeholder = st.empty()
                full_response = ""
                sources = []
                
                try:
                    # Stream response
                    for chunk in st.session_state.chat_engine.chat(
                        query=prompt,
                        conversation=st.session_state.conversation,
                        stream=True,
                    ):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    
                    # Get sources from conversation
                    if st.session_state.conversation.messages:
                        last_msg = st.session_state.conversation.messages[-1]
                        sources = last_msg.sources
                    
                    # Add to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources,
                    })
                    
                    # Update suggested questions
                    st.session_state.suggested_questions = \
                        st.session_state.chat_engine.get_suggested_questions(
                            st.session_state.conversation
                        )
                    
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
        
        st.rerun()
    
    # Show suggested questions after response
    if st.session_state.messages:
        st.markdown("---")
        selected = render_suggested_questions()
        if selected:
            st.session_state.pending_question = selected
            st.rerun()


if __name__ == "__main__":
    main()
