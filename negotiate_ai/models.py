"""
NegotiateAI Data Models
=======================

Pydantic models for structured agent outputs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNKNOWN = "UNKNOWN"


class Assessment(str, Enum):
    FAVORABLE = "FAVORABLE"
    NEUTRAL = "NEUTRAL"
    UNFAVORABLE = "UNFAVORABLE"
    FAR_BELOW_MARKET = "FAR_BELOW_MARKET"
    ABOVE_MARKET = "ABOVE_MARKET"


@dataclass
class Party:
    """Contract party information"""
    name: str
    role: str
    obligations_count: int = 0
    details: Dict[str, str] = field(default_factory=dict)


@dataclass
class ClauseInfo:
    """Individual clause information"""
    clause_id: str
    clause_type: str
    summary: str
    full_text: str = ""
    parties_affected: List[str] = field(default_factory=list)
    criticality: str = "medium"
    cross_references: List[str] = field(default_factory=list)


@dataclass
class StructuralIssue:
    """Document structural issue"""
    issue: str
    severity: str = "medium"
    recommendation: str = ""


@dataclass
class DocumentAnalysis:
    """Output from Document Analyzer Agent"""
    document_type: str
    parties: List[Party]
    clause_summary: Dict[str, Any]
    key_clauses: List[ClauseInfo]
    structural_issues: List[str]
    cross_references: List[str]
    obligations_by_party: Dict[str, List[str]] = field(default_factory=dict)
    defined_terms: List[str] = field(default_factory=list)
    effective_date: Optional[str] = None
    termination_date: Optional[str] = None
    raw_analysis: str = ""


@dataclass
class RiskItem:
    """Individual risk item"""
    risk_id: str
    clause: str
    category: str
    severity: str
    score: int
    description: str
    impact: str
    likelihood: str
    financial_exposure: str = "Unknown"
    legal_precedent: str = ""
    mitigation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskCategory:
    """Risk by category summary"""
    total_score: int
    count: int
    top_risk: str


@dataclass
class RiskAssessment:
    """Output from Risk Assessor Agent"""
    overall_score: int
    overall_level: str
    summary: str
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    critical_risks: List[RiskItem]
    high_risks: List[RiskItem]
    medium_risks: List[RiskItem]
    low_risks: List[RiskItem]
    risk_by_category: Dict[str, RiskCategory]
    acceptable_risks: List[str]
    raw_analysis: str = ""


@dataclass
class PowerFactor:
    """Power dynamics factor"""
    factor: str
    impact: str  # "in_your_favor" or "against_you"
    weight: int = 1


@dataclass
class NegotiationPriority:
    """Single negotiation priority item"""
    rank: int
    issue: str
    current_position: str
    target_position: str
    minimum_acceptable: str
    leverage_score: int
    rationale: str
    strategy: str
    talking_points: List[str]
    counter_proposal: str = ""
    concessions_available: List[str] = field(default_factory=list)
    if_rejected: str = ""


@dataclass
class QuickWin:
    """Quick win negotiation opportunity"""
    issue: str
    current: str
    request: str
    likelihood: str
    rationale: str
    script: str


@dataclass
class TradingChip:
    """Quid pro quo opportunity"""
    what_you_offer: str
    what_you_want: str
    value_ratio: str


@dataclass
class NegotiationStrategy:
    """Output from Negotiation Strategist Agent"""
    power_balance: float  # -10 to +10
    power_interpretation: str
    factors_in_favor: List[str]
    factors_against: List[str]
    your_batna: str
    their_batna: str
    priorities: List[NegotiationPriority]
    quick_wins: List[QuickWin]
    deal_breakers: List[str]
    trading_chips: List[TradingChip]
    negotiation_sequence: List[str]
    psychological_tactics: List[str]
    raw_analysis: str = ""


@dataclass
class ComplianceIssue:
    """Legal compliance issue"""
    issue: str
    jurisdiction: str
    requirement: str
    contract_provision: str
    compliance_status: str
    risk: str
    recommendation: str
    severity: str


@dataclass
class EnforceabilityConcern:
    """Contract enforceability concern"""
    clause: str
    issue: str
    legal_principle: str
    contract_language: str
    concern: str
    precedent: str
    likelihood_struck_down: str
    recommendation: str


@dataclass
class LegalPrecedent:
    """Relevant legal precedent"""
    clause_type: str
    case_citation: str
    principle: str
    application: str
    implication: str


@dataclass
class StatutoryWaiver:
    """Statutory right being waived"""
    waived_right: str
    statute: str
    enforceability: str
    recommendation: str
    alternative: str


@dataclass
class Ambiguity:
    """Contract ambiguity"""
    location: str
    language: str
    issue: str
    legal_rule: str
    risk: str
    recommendation: str


@dataclass
class LegalAdvisory:
    """Output from Legal Advisor Agent"""
    overall_assessment: str
    major_concerns_count: int
    compliance_issues_count: int
    enforceability_risks_count: int
    recommended_legal_review: bool
    compliance_issues: List[ComplianceIssue]
    enforceability_concerns: List[EnforceabilityConcern]
    legal_precedents: List[LegalPrecedent]
    statutory_waivers: List[StatutoryWaiver]
    ambiguities: List[Ambiguity]
    missing_clauses: List[str]
    raw_analysis: str = ""


@dataclass
class BenchmarkComparison:
    """Market benchmark comparison"""
    term_category: str
    this_contract: str
    market_standard: str
    percentile: str
    assessment: str
    impact: str
    data_source: str = ""
    recommendation: str = ""
    negotiation_leverage: str = ""


@dataclass
class CompetitorIntel:
    """Competitive intelligence"""
    competitor: str
    their_standard_terms: str
    advantage_they_have: str
    advantage_you_have: str
    negotiation_angle: str


@dataclass
class PricingAnalysis:
    """Pricing analysis"""
    quoted_price: str
    market_range: str
    percentile: str
    assessment: str
    value_indicators: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketResearch:
    """Output from Market Research Agent"""
    industry: str
    contract_type: str
    typical_contract_value: str
    market_conditions: str
    benchmark_comparisons: List[BenchmarkComparison]
    pricing_analysis: PricingAnalysis
    competitive_intelligence: List[CompetitorIntel]
    industry_trends: List[str]
    overall_favorability_score: int
    overall_interpretation: str
    raw_analysis: str = ""


@dataclass
class CriticalDecision:
    """Critical decision point"""
    decision: str
    recommendation: str
    rationale: str
    alternative: str
    business_impact: str
    decision_maker: str


@dataclass
class RoadmapItem:
    """Negotiation roadmap item"""
    rank: int
    issue: str
    current: str
    target: str
    minimum: str
    priority: str
    strategy: str
    success_likelihood: str
    talking_points: List[str]
    if_rejected: str = ""
    if_accepted: str = ""


@dataclass
class ContractOptimization:
    """Output from Contract Optimizer Agent (Synthesizer)"""
    overall_assessment: str
    recommendation: str
    confidence_level: str
    key_insights: List[str]
    estimated_success_rate: str
    recommended_timeline: str
    critical_decisions: List[CriticalDecision]
    phase_1_critical: List[RoadmapItem]
    phase_2_high_priority: List[RoadmapItem]
    phase_3_optimization: List[RoadmapItem]
    success_metrics: List[str]
    risk_mitigation_summary: str
    next_steps: List[str]
    raw_analysis: str = ""


@dataclass
class NegotiationPlaybook:
    """Complete negotiation playbook - final output"""
    timestamp: str
    document_name: str
    document_analysis: DocumentAnalysis
    risk_assessment: RiskAssessment
    negotiation_strategy: NegotiationStrategy
    legal_advisory: LegalAdvisory
    market_research: MarketResearch
    optimization: ContractOptimization
    executive_summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        import dataclasses
        return dataclasses.asdict(self)


@dataclass
class AgentOutput:
    """Generic agent output wrapper"""
    agent_name: str
    status: str  # "success", "error", "partial"
    execution_time: float
    output: Any
    raw_response: str = ""
    error_message: str = ""
