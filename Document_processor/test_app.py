"""
Streamlit Interface for Document Processor.
Features: Dashboard layout, PII Toggle, Metadata, Chunking, and Visual Insights (WordCloud).
"""

import streamlit as st
from processor import DocumentProcessor
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json

def main():
    st.set_page_config(
        page_title="Smart DocParser Pro",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 Smart Document Pipeline")
    st.markdown("Extract text, analyze readability, and visualize content.")

    # --- Sidebar: Configuration ---
    with st.sidebar:
        st.header("⚙️ Pipeline Settings")
        
        # Feature Toggles
        st.subheader("Preprocessing")
        do_clean = st.checkbox("Normalize Whitespace", value=True)
        do_redact = st.checkbox("🛡️ Redact PII (Emails/Phones)", value=False)
        
        st.subheader("Chunking Strategy")
        enable_chunking = st.checkbox("Enable Text Chunking", value=False)
        chunk_size = st.slider("Chunk Size (Words)", 50, 1000, 200, disabled=not enable_chunking)
        overlap = st.slider("Overlap (Words)", 0, 100, 20, disabled=not enable_chunking)

        st.divider()
        st.info("Upload PDF, DOCX, TXT, or Images.")

    # --- Main Upload Section ---
    uploaded_file = st.file_uploader("Drop your document here", type=['pdf', 'docx', 'txt', 'png', 'jpg'])

    if uploaded_file and st.button("🚀 Run Pipeline"):
        processor = DocumentProcessor()
        
        with st.status("Processing document...", expanded=True) as status:
            # 1. Core Extraction
            status.write("🔍 Extracting text and metadata...")
            result = processor.process_document(uploaded_file)
            
            if result['status'] == 'error':
                status.update(label="❌ Failed", state="error")
                st.error(f"Pipeline Failed: {result['error_message']}")
                return
            else:
                raw_text = result['text']
                metadata = result['metadata']
                analysis = result.get('analysis', {})
                tables = result.get('tables', [])
                
                if tables:
                    status.write(f"📊 Extracted {len(tables)} table(s)...")
                
                # 2. Post-Processing Chain
                status.write("✨ Cleaning and Redacting...")
                processed_text = raw_text
                
                if do_clean:
                    processed_text = processor.clean_text(processed_text)
                
                if do_redact:
                    processed_text = processor.redact_pii(processed_text)
                
                chunks = []
                if enable_chunking:
                    status.write("🧩 Chunking text...")
                    chunks = processor.chunk_text(processed_text, chunk_size=chunk_size, overlap=overlap)
                
                status.update(label="✅ Processing Complete", state="complete", expanded=False)

                # --- Results Dashboard ---
                
                # Top Metrics
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("File Type", metadata.get('type', 'Unknown'))
                m2.metric("Tables Found", len(tables))
                m3.metric("Readability Score", analysis.get('readability_score', 'N/A'))
                m4.metric("Difficulty", analysis.get('difficulty', 'N/A'))
                m5.metric("Language", analysis.get('language', 'N/A'))

                st.divider()

                # Tabs for different views
                tab_visuals, tab_text, tab_tables, tab_debug = st.tabs([
                    "🎨 Visual Insights", 
                    "📄 Text Content",
                    "📊 Tables",
                    "⚙️ Metadata & Chunks"
                ])

                # 1. Visual Insights (Word Cloud)
                with tab_visuals:
                    st.subheader("☁️ Word Cloud")
                    if processed_text.strip():
                        try:
                            # Generate WordCloud
                            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(processed_text)
                            
                            # Display using Matplotlib
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis("off")
                            st.pyplot(fig)
                        except Exception as e:
                            st.warning(f"Could not generate word cloud: {e}")
                    else:
                        st.info("Not enough text for visualization.")

                # 2. Text View
                with tab_text:
                    st.subheader("Extracted Content")
                    st.text_area("Content", processed_text, height=600)
                    st.download_button("Download Text", processed_text)

                # 3. Tables View
                with tab_tables:
                    if tables:
                        st.subheader(f"📊 Extracted Tables ({len(tables)} found)")
                        
                        for idx, table_info in enumerate(tables, 1):
                            page_info = f" - Page {table_info.get('page', 'N/A')}" if 'page' in table_info else ""
                            st.markdown(f"### Table {idx}{page_info}")
                            st.caption(f"Size: {table_info['rows']} rows × {table_info['columns']} columns")
                            
                            # Display as DataFrame for better formatting
                            import pandas as pd
                            try:
                                df = pd.DataFrame(table_info['data'])
                                st.dataframe(df, use_container_width=True)
                            except Exception as e:
                                # Fallback to text representation
                                st.code(table_info['text_representation'])
                            
                            # Download option for individual table
                            csv_data = pd.DataFrame(table_info['data']).to_csv(index=False)
                            st.download_button(
                                f"Download Table {idx} as CSV",
                                csv_data,
                                f"table_{idx}.csv",
                                "text/csv",
                                key=f"download_table_{idx}"
                            )
                            
                            st.divider()
                    else:
                        st.info("No tables detected in this document.")

                # 4. Debug/Technical View
                with tab_debug:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("File Metadata")
                        st.json(metadata)
                    with col2:
                        st.subheader("Pipeline Config")
                        st.write({
                            "cleaning": do_clean,
                            "redaction": do_redact,
                            "chunking": enable_chunking,
                            "chunk_count": len(chunks)
                        })

                    if enable_chunking:
                        st.subheader("🧩 RAG Chunk Preview")
                        st.markdown(f"> **Strategy:** Fixed Size ({chunk_size} words) | Total Chunks: {len(chunks)}")
                        for i, chunk in enumerate(chunks):
                            st.info(f"**Chunk {i+1}**: {chunk[:150]}...")
                            with st.expander(f"View Full Chunk {i+1}"):
                                st.write(chunk)

if __name__ == "__main__":
    main()