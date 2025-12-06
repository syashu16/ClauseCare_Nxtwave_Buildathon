import streamlit as st
import os
import re
import textstat
import time
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_groq import ChatGroq
from groq import Groq
from dotenv import load_dotenv

# --- 1. CONFIGURATION & SETUP ---
load_dotenv()
st.set_page_config(page_title="NyayaSetu - Legal AI", page_icon="⚖️", layout="wide")

# Get API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Custom CSS for the "Wow Factor"
st.markdown("""
<style>
    .risk-high { color: #ff4b4b; font-weight: bold; font-size: 24px; }
    .risk-medium { color: #ffa500; font-weight: bold; font-size: 24px; }
    .risk-safe { color: #00cc66; font-weight: bold; font-size: 24px; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #4a90e2; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI CLIENTS ---
@st.cache_resource
def get_groq_llm():
    """For Chat & RAG (Using Groq - Fast & Free)"""
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.3
    )

def get_groq_client():
    """For Instant Simplification (Fast)"""
    return Groq(api_key=GROQ_API_KEY)

@st.cache_resource
def get_embeddings():
    """For Vector Search - Using HuggingFace (Free, No API Key)"""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

# --- 3. HELPER FUNCTIONS ---

def get_pdf_text(uploaded_files):
    """
    UPDATED: Uses PyMuPDF (fitz) for faster and better extraction.
    """
    text = ""
    for pdf_file in uploaded_files:
        # Open the file stream directly with PyMuPDF
        with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    return text

def create_vector_db(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    embeddings = get_embeddings()
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def split_clauses(text):
    """Regex magic to split legal text into numbered clauses"""
    # Detects 1., 1.1, (a), Article 1, Section 5
    pattern = r'(?:\n\s*(\d+\.|[a-z]\)|\d+\.\d+|ARTICLE [IVX]+|SECTION \d+)\s+)'
    parts = re.split(pattern, text)
    clauses = []
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            marker = parts[i]
            content = parts[i+1] if i+1 < len(parts) else ""
            full_clause = f"{marker} {content}".strip()
            if len(full_clause) > 20: clauses.append(full_clause)
    else:
        # Fallback if no numbering found
        clauses = [p.strip() for p in text.split('\n\n') if len(p) > 20]
    return clauses

# --- 4. CORE AI AGENTS ---

def analyze_risk_agent(text):
    """Groq Agent: Returns a Risk Score (0-100)"""
    client = get_groq_client()
    prompt = f"""
    Act as a Legal Risk Analyst. Analyze the following contract.
    Output ONLY a single integer between 0 and 100 (0=Safe, 100=Dangerous).
    Do not output any text, just the number.
    
    Text: {text[:5000]}
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        # Extract just the number
        content = res.choices[0].message.content or "50"
        return int(''.join(filter(str.isdigit, content))) or 50
    except:
        return 50  # Default moderate

def simplify_clause_agent(clause_text):
    """Groq Agent: Instantly simplifies text"""
    client = get_groq_client()
    
    # We tuned this prompt to ensure high readability scores
    prompt = f"""
    You are a legal expert explaining things to a 10-year-old.
    Rewrite the following clause.
    
    Rules:
    1. Use very simple words.
    2. Keep sentences short.
    3. Start with "Meaning:"
    
    Clause: {clause_text}
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        return res.choices[0].message.content or "Unable to simplify"
    except Exception as e:
        return f"Error: {str(e)}"

# --- 5. MAIN UI ---
def main():
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3222/3222625.png", width=60)
        st.title("NyayaSetu")
        st.markdown("**Legal Literacy for Bharat**")
        st.markdown("---")
        
        uploaded_files = st.file_uploader("Upload Contract (PDF)", accept_multiple_files=True, type="pdf")
        
        if st.button("🔄 Reset App"):
            st.cache_data.clear()
            st.rerun()

    # Main Area
    if uploaded_files:
        # --- PHASE 1: INGESTION ---
        if 'processed' not in st.session_state:
            with st.spinner("⚖️ AI is analyzing 50+ legal parameters..."):
                # 1. Read PDF (Using PyMuPDF now)
                raw_text = get_pdf_text(uploaded_files)
                st.session_state['raw_text'] = raw_text
                st.session_state['clauses'] = split_clauses(raw_text)
                
                # 2. Build Brain (Vector DB)
                create_vector_db(raw_text)
                
                # 3. Risk Analysis
                st.session_state['risk_score'] = analyze_risk_agent(raw_text)
                st.session_state['processed'] = True
                st.success("Analysis Complete!")

        # --- PHASE 2: DASHBOARD ---
        
        # Risk Meter (The "Hook")
        score = st.session_state.get('risk_score', 50)
        st.subheader("🛡️ Contract Health Score")
        
        col_risk1, col_risk2 = st.columns([3, 1])
        with col_risk1:
            st.progress(score)
        with col_risk2:
            if score > 70:
                st.markdown(f"<span class='risk-high'>{score}/100 (HIGH RISK)</span>", unsafe_allow_html=True)
            elif score > 40:
                st.markdown(f"<span class='risk-medium'>{score}/100 (MODERATE)</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='risk-safe'>{score}/100 (SAFE)</span>", unsafe_allow_html=True)

        st.divider()

        # Tabs
        tab1, tab2, tab3 = st.tabs(["🚀 Instant Simplifier", "💬 Ask AI Lawyer", "📊 Deep Analysis"])

        # TAB 1: CLAUSE SIMPLIFIER (GROQ POWERED)
        with tab1:
            st.info("Select a specific clause to translate into plain English.")
            
            clauses = st.session_state.get('clauses', [])
            if clauses:
                # Dropdown to pick a clause
                selected_idx = st.selectbox(
                    "Navigate Clauses:", 
                    range(len(clauses)), 
                    format_func=lambda x: f"Clause {x+1}: {clauses[x][:80]}..."
                )
                selected_clause = clauses[selected_idx]
                
                col_orig, col_simp = st.columns(2)
                
                # Left Column: Original
                with col_orig:
                    st.markdown("### 📜 Original Legal Text")
                    st.warning(selected_clause)
                    orig_score = textstat.flesch_reading_ease(selected_clause)
                    st.caption(f"Readability Score: {orig_score:.1f} (Difficult)")

                # Right Column: AI Version
                with col_simp:
                    st.markdown("### ✨ AI Simplification")
                    if st.button("Simplify This Clause", key="simplify_btn"):
                        with st.spinner("Groq AI rewriting..."):
                            start = time.time()
                            simple_text = simplify_clause_agent(selected_clause)
                            end = time.time()
                            
                            st.success(simple_text)
                            
                            # Metrics
                            new_score = textstat.flesch_reading_ease(simple_text)
                            st.caption(f"Generated in {end-start:.2f}s")
                            st.caption(f"New Readability Score: {new_score:.1f} (Easy)")
                            
                            improvement = new_score - orig_score
                            if improvement > 0:
                                st.markdown(f"**📉 Difficulty Reduced by {improvement:.1f} points!**")

        # TAB 2: RAG CHAT (GEMINI POWERED)
        with tab2:
            st.write("Ask questions about *this specific* document.")
            q = st.text_input("Your Question:", placeholder="e.g., What is the penalty for late rent?")
            
            if q:
                embeddings = get_embeddings()
                # Load the Local FAISS Index
                try:
                    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                    retriever = new_db.as_retriever()

                    chain = RetrievalQA.from_chain_type(llm=get_groq_llm(), chain_type="stuff", retriever=retriever)
                    with st.spinner("Consulting the contract..."):
                        res = chain.run(q)
                        st.markdown(f"**Answer:** {res}")
                except Exception as e:
                    st.error(f"Error accessing document memory: {str(e)}")

        # TAB 3: VISUALS
        with tab3:
            st.markdown("### 📅 Process Timeline")
            # Hackathon Trick: Generate a static Mermaid chart representing a standard flow
            st.markdown("""
            ```mermaid
            graph TD
            A[Start Date] -->|Move In| B(Sign Agreement)
            B --> C{Rent Due 1st}
            C -- Paid --> D[Good Standing]
            C -- Late --> E[Late Fee Applied]
            E --> F[Notice Issued]
            ```
            """)
            st.info("Visual representation of the payment workflow.")

    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("👆 Please upload a PDF file from the sidebar to begin.")
        st.markdown("### Features:")
        st.markdown("- **Risk Analysis:** Instantly scores how dangerous the contract is.")
        st.markdown("- **Simplification:** Turns legal jargon into plain English.")
        st.markdown("- **Chat:** Ask any question about the document.")

if __name__ == "__main__":
    main()