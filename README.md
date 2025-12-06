# GenLegalAI - Risk Assessment Module

A comprehensive legal contract risk assessment system that analyzes documents for potential risks and provides actionable recommendations.

## 🎯 Features

- **Two-Tier Analysis**: Fast keyword scanning + AI deep analysis
- **8 Risk Categories**: Financial, Legal Liability, Termination, IP, Confidentiality, Dispute Resolution, Compliance, Operational
- **Risk Scoring**: 0-100 scores with confidence levels
- **Actionable Recommendations**: Clear guidance for each identified risk
- **Interactive Visualizations**: Dashboards, gauges, heatmaps, and charts
- **Export Options**: Markdown reports and JSON data

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd "NXTWAVE BUILDATHON"

# Install dependencies
pip install -r requirements.txt

# Set your Groq API key (for AI-powered analysis)
set GROQ_API_KEY=your_api_key_here  # Windows
export GROQ_API_KEY=your_api_key_here  # Linux/Mac
```

### Run the Application

```bash
# Launch Streamlit UI
streamlit run app.py

# Or run a demo
python main.py demo
```

### Use as a Library

```python
from risk_assessment import RiskAssessmentEngine

# Initialize engine
engine = RiskAssessmentEngine(api_key="your_groq_key")

# Analyze a document
result = engine.analyze_document(contract_text)

# Get results
print(f"Overall Risk: {result.risk_summary.overall_score}/100")
print(f"Risk Level: {result.risk_summary.overall_level.value}")

# Export report
markdown = engine.export_markdown_report(result)
```

## 📊 Risk Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Financial** | Money & payment risks | Unlimited liability, hidden fees, non-refundable deposits |
| **Legal Liability** | Responsibility risks | One-sided indemnification, warranty disclaimers |
| **Termination** | Exit risks | Auto-renewal, termination fees, lock-in periods |
| **Intellectual Property** | IP ownership risks | Full IP transfer, work-for-hire, moral rights waivers |
| **Confidentiality** | Data protection risks | Perpetual confidentiality, no return obligations |
| **Dispute Resolution** | Legal process risks | Binding arbitration, distant jurisdiction, class action waivers |
| **Compliance** | Regulatory risks | Strict liability, unlimited audit rights |
| **Operational** | Day-to-day risks | Exclusive dealing, non-compete clauses |

## 🔢 Risk Scoring

| Score Range | Severity | Meaning |
|-------------|----------|---------|
| 0-30 | LOW | Standard clauses, minimal risk |
| 31-60 | MEDIUM | Worth reviewing, some concerns |
| 61-85 | HIGH | Significant issues, negotiate before signing |
| 86-100 | CRITICAL | Dangerous, potential deal-breaker |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Input                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Fast Scanner (< 1 second)                         │
│  - Keyword matching (500+ patterns)                         │
│  - Pattern detection                                        │
│  - Initial heatmap generation                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: AI Deep Analysis (Groq Llama 3.1 70B)             │
│  - Context understanding                                     │
│  - Risk evaluation                                          │
│  - Recommendation generation                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Aggregation & Scoring                             │
│  - Document-level metrics                                   │
│  - Pattern identification                                   │
│  - Priority ranking                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Output: Dashboard, Reports, Visualizations                  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
risk_assessment/
├── __init__.py              # Package initialization
├── models.py                # Data models and types
├── keyword_library.py       # 500+ risk keywords/phrases
├── fast_scanner.py          # Rule-based fast scanning
├── ai_analyzer.py           # Groq AI integration
├── risk_scorer.py           # Scoring algorithm
├── document_aggregator.py   # Result aggregation
├── visualizations.py        # Charts and dashboards
└── risk_assessment_engine.py # Main orchestrator

app.py                       # Streamlit UI
main.py                      # CLI entry point
tests/
└── test_risk_assessment.py  # Test suite
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=risk_assessment

# Run specific test class
python -m pytest tests/test_risk_assessment.py::TestFastScanner -v
```

## 📈 API Reference

### RiskAssessmentEngine

```python
class RiskAssessmentEngine:
    def analyze_document(text, filename, context) -> DocumentRisk
    def quick_scan(text) -> QuickScanResult
    def analyze_clause(clause_text, context) -> ClauseRisk
    def get_dashboard(document_risk) -> dict
    def get_recommendations(document_risk) -> list[Recommendation]
    def export_markdown_report(document_risk) -> str
    def export_json(document_risk) -> dict
```

### DocumentRisk

```python
@dataclass
class DocumentRisk:
    metadata: DocumentMetadata
    risk_summary: RiskSummary
    executive_summary: str
    clause_risks: list[ClauseRisk]
    top_risks: list[TopRisk]
    must_address_immediately: list[ActionItem]
    should_negotiate: list[str]
    acceptable_as_is: list[str]
    deal_breakers: list[str]
    action_plan: list[str]
```

## 🔧 Configuration

### Analysis Context

```python
from risk_assessment.ai_analyzer import AnalysisContext

context = AnalysisContext(
    document_type="service_agreement",
    user_role="customer",
    industry="technology",
    jurisdiction="united_states",
    contract_value=100000.0
)

result = engine.analyze_document(text, context=context)
```

### Engine Options

```python
engine = RiskAssessmentEngine(
    api_key="your_groq_key",      # Groq API key
    use_ai=True,                   # Enable AI analysis
    parallel_analysis=True,        # Parallel processing
    max_workers=4                  # Number of workers
)
```

## 🎯 Success Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Accuracy | 95%+ | Correctly identifies dangerous clauses |
| Speed | < 15s | Full document analysis time |
| Clarity | High | Non-lawyers understand explanations |
| Actionability | 100% | Every risk has a recommendation |

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📧 Support

For questions or issues, please open a GitHub issue
