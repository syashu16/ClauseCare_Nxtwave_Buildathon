"""
NegotiateAI Multi-Agent System
==============================

A 6-agent collaborative AI system for contract negotiation intelligence.

Agents:
1. Document Analyzer - Extracts and categorizes clauses
2. Risk Assessor - Identifies and scores risks
3. Negotiation Strategist - Develops tactical playbooks
4. Legal Advisor - Provides legal context and compliance
5. Market Researcher - Benchmarks against industry standards
6. Contract Optimizer - Synthesizes all insights

"""

from .models import (
    AgentOutput,
    DocumentAnalysis,
    RiskAssessment,
    NegotiationStrategy,
    LegalAdvisory,
    MarketResearch,
    ContractOptimization,
    NegotiationPlaybook
)

from .agents import (
    DocumentAnalyzerAgent,
    RiskAssessorAgent,
    NegotiationStrategistAgent,
    LegalAdvisorAgent,
    MarketResearcherAgent,
    ContractOptimizerAgent
)

from .orchestrator import NegotiateAIOrchestrator

__all__ = [
    'AgentOutput',
    'DocumentAnalysis',
    'RiskAssessment', 
    'NegotiationStrategy',
    'LegalAdvisory',
    'MarketResearch',
    'ContractOptimization',
    'NegotiationPlaybook',
    'DocumentAnalyzerAgent',
    'RiskAssessorAgent',
    'NegotiationStrategistAgent',
    'LegalAdvisorAgent',
    'MarketResearcherAgent',
    'ContractOptimizerAgent',
    'NegotiateAIOrchestrator'
]
