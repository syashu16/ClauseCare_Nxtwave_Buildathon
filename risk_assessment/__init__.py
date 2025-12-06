"""
GenLegalAI Risk Assessment Module

A two-tier risk assessment system that:
1. Instantly scans documents for known dangerous patterns (Rule-Based Layer)
2. Deeply analyzes each clause using AI to understand context and implications (AI Layer)
3. Scores risks from 0-100 with confidence levels
4. Categorizes risks into meaningful buckets (Financial, Legal, Operational, etc.)
5. Generates actionable recommendations for each identified risk
6. Visualizes risk distribution across the entire document
7. Prioritizes issues so users know what to tackle first
"""

from .models import (
    RiskCategory,
    SeverityLevel,
    ClauseRisk,
    DocumentRisk,
    RiskSummary,
    Recommendation,
)
from .keyword_library import KeywordLibrary
from .fast_scanner import FastScanner
from .ai_analyzer import AIAnalyzer
from .risk_scorer import RiskScorer
from .document_aggregator import DocumentAggregator
from .visualizations import RiskVisualizer
from .risk_assessment_engine import RiskAssessmentEngine

__version__ = "1.0.0"
__all__ = [
    "RiskCategory",
    "SeverityLevel",
    "ClauseRisk",
    "DocumentRisk",
    "RiskSummary",
    "Recommendation",
    "KeywordLibrary",
    "FastScanner",
    "AIAnalyzer",
    "RiskScorer",
    "DocumentAggregator",
    "RiskVisualizer",
    "RiskAssessmentEngine",
]
