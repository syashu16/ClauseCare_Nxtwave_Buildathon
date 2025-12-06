# 🏛️ ClauseCare - AI-Powered Legal Document Platform

<div align="center">

![ClauseCare](https://img.shields.io/badge/ClauseCare-Legal%20AI-blue?style=for-the-badge&logo=scale)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Cloud%20Ready-red?style=for-the-badge&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**An intelligent legal document analysis platform with 7 powerful AI modules**

[🚀 Live Demo](https://clausecare-nxtwave-buildathon.streamlit.app) | [📖 Documentation](#-features) | [🎥 Video Demo](#)

</div>

---

## 🎯 Problem Statement

Legal documents are complex, time-consuming to review, and often contain hidden risks that can cost businesses millions. Non-lawyers struggle to understand contract terms, and even legal professionals spend hours on routine document analysis.

**ClauseCare solves this by:**
- 🤖 Using AI to analyze contracts in seconds, not hours
- 🌐 Supporting 22+ Indian languages for accessibility
- 🎯 Identifying risks before you sign
- 💡 Explaining legal jargon in plain English
- 🤝 Providing negotiation strategies with multi-agent AI

---

## ✨ Features

### 1. 📊 Risk Assessment Engine
Comprehensive risk analysis with AI-powered insights.

| Feature | Description |
|---------|-------------|
| **Two-Tier Analysis** | Fast keyword scanning + Deep AI analysis |
| **8 Risk Categories** | Financial, Legal, Termination, IP, Confidentiality, Dispute, Compliance, Operational |
| **Risk Scoring** | 0-100 scores with confidence levels |
| **Visual Dashboards** | Gauges, heatmaps, pie charts, and more |
| **Actionable Recommendations** | Clear guidance for each identified risk |

### 2. 🤝 NegotiateAI - 6-Agent System
A revolutionary multi-agent system for contract negotiation intelligence.

| Agent | Role |
|-------|------|
| 📄 **Document Analyzer** | Extracts key terms, clauses, and structure |
| ⚠️ **Risk Assessor** | Identifies and prioritizes contract risks |
| 🎯 **Negotiation Strategist** | Creates negotiation tactics and BATNA analysis |
| ⚖️ **Legal Advisor** | Ensures compliance and identifies legal issues |
| 📈 **Market Researcher** | Provides industry benchmarks and market insights |
| 🔧 **Contract Optimizer** | Suggests improved clause language |

**Output:** Complete Negotiation Playbook with strategies, talking points, and success predictions.

### 3. 💬 RAG Document Chat
Chat with your legal documents using Retrieval-Augmented Generation.

- Ask questions in plain English
- Get cited answers with source references
- Legal term explanations
- Conversation history
- Powered by FAISS vector store (cloud-compatible)

### 4. ✨ Clause Simplification
Transform complex legal language into plain English.

- Flesch Reading Ease scores
- Before/after comparisons
- Batch processing
- Readability improvement metrics
- Legal jargon detection

### 5. 🌐 Language Translation
**Unique Feature:** Support for 22+ Indian languages!

| Languages Supported |
|---------------------|
| Hindi (हिन्दी), Bengali (বাংলা), Telugu (తెలుగు), Marathi (मराठी) |
| Tamil (தமிழ்), Gujarati (ગુજરાતી), Kannada (ಕನ್ನಡ), Malayalam (മലയാളം) |
| Odia (ଓଡ଼ିଆ), Punjabi (ਪੰਜਾਬੀ), Assamese (অসমীয়া), Sanskrit (संस्कृत) |
| Urdu (اردو), Konkani, Manipuri, Nepali, Sindhi, Dogri |
| Maithili, Bodo, Santali, Kashmiri |

**Translates:**
- Full legal documents
- Risk assessment summaries
- Negotiation strategies

### 6. 📄 Document Processor
Advanced document processing with multiple format support.

- **PDF Processing** with table extraction
- **DOCX Processing** with metadata
- **TXT/Plain Text** support
- **OCR** for scanned documents (when available)
- Text chunking for large documents
- Legal entity extraction (dates, amounts, references)

### 7. 🔐 User Authentication & History
Secure user system with persistent analysis history.

- User registration and login
- Password hashing (SHA-256 with salt)
- Analysis history tracking
- Personal dashboard
- Data persistence across sessions

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/syashu16/ClauseCare_Nxtwave_Buildathon.git
cd ClauseCare_Nxtwave_Buildathon

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set your API key
echo "GROQ_API_KEY=your_api_key_here" > .env
```

### Run the Application

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    📤 Document Upload                        │
│              (PDF, DOCX, TXT - Sidebar)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ 📊 Risk       │   │ 🤝 Negotiate  │   │ 💬 Document   │
│ Assessment    │   │ AI (6 Agents) │   │ Chat (RAG)    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ ✨ Clause     │   │ 🌐 Language   │   │ 📄 Document   │
│ Simplifier    │   │ Translation   │   │ Processor     │
└───────────────┘   └───────────────┘   └───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              🔐 User Auth & 💾 History Storage              │
│                    (JSON-based, Cloud Ready)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ClauseCare_Nxtwave_Buildathon/
│
├── app.py                      # 🎯 Main Streamlit Application (2900+ lines)
│
├── risk_assessment/            # 📊 Risk Analysis Module
│   ├── models.py               # Data models
│   ├── fast_scanner.py         # Keyword-based scanning
│   ├── ai_analyzer.py          # Groq AI integration
│   ├── risk_scorer.py          # Scoring algorithms
│   └── visualizations.py       # Charts & dashboards
│
├── negotiate_ai/               # 🤝 Multi-Agent Negotiation
│   ├── models.py               # Pydantic models for all agents
│   ├── agents.py               # 6 specialized AI agents
│   └── orchestrator.py         # Agent coordination
│
├── rag_chatbot/                # 💬 Document Chat
│   ├── faiss_store.py          # FAISS vector store (cloud-ready)
│   ├── retriever.py            # Context retrieval
│   └── chat_engine.py          # Conversation management
│
├── language_translator/        # 🌐 Translation Module
│   └── translator.py           # 22+ Indian languages
│
├── Document_processor/         # 📄 Document Processing
│   └── processor.py            # PDF, DOCX, TXT handling
│
├── Clause_Simplification/      # ✨ Simplification Module
│   └── cli_main.py             # Readability analysis
│
├── auth/                       # 🔐 Authentication
│   └── auth_manager.py         # Login, register, sessions
│
├── database/                   # 💾 Data Persistence
│   └── db_manager.py           # JSON-based storage
│
├── data/                       # 📂 User Data Storage
│   ├── users.json              # User accounts
│   └── history.json            # Analysis history
│
├── .streamlit/                 # ⚙️ Streamlit Config
│   └── config.toml             # Theme & settings
│
├── requirements.txt            # 📦 Dependencies
└── README.md                   # 📖 This file
```

---

## 🔧 Tech Stack

| Category | Technology |
|----------|------------|
| **Frontend** | Streamlit with responsive CSS |
| **AI Model** | Groq LLaMA 3.3 70B Versatile |
| **Vector Store** | FAISS (cloud-compatible) |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **PDF Processing** | PyMuPDF |
| **Data Validation** | Pydantic |
| **Auth** | Custom SHA-256 + Salt hashing |
| **Storage** | JSON files (Streamlit Cloud compatible) |

---

## 🌐 Deployment

### Streamlit Cloud (Recommended)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Settings:
   ```toml
   GROQ_API_KEY = "your-groq-api-key"
   ```
5. Deploy!

### Local Development

```bash
streamlit run app.py
```

---

## 📊 Buildathon Criteria Checklist

| Criteria | Status | Implementation |
|----------|--------|----------------|
| ✅ **Working Features** | Complete | 7 fully functional modules |
| ✅ **AI Integration** | Complete | Groq LLaMA 3.3, Multi-agent system, RAG |
| ✅ **Problem Statement** | Complete | Legal document analysis for Indian market |
| ✅ **UI Usability** | Complete | Clean Streamlit UI with navigation |
| ✅ **Responsiveness** | Complete | Mobile-friendly CSS breakpoints |
| ✅ **Data Persistence** | Complete | JSON-based cloud-compatible storage |
| ✅ **User Auth** | Complete | Secure login/register system |

---

## 🎥 Demo

[Watch the demo video](#) | [Try Live Demo](https://clausecare-nxtwave-buildathon.streamlit.app)

---

## 👥 Team

**Team Name:** ClauseCare

Built for **OpenAI × NxtWave Buildathon 2025** 🏆

---

## 📄 License

MIT License - feel free to use and modify!

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

<div align="center">

**Made with ❤️ for the OpenAI × NxtWave Buildathon 2025**

⭐ Star this repo if you found it helpful!

</div>
