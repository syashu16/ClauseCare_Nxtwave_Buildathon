"""
Data models for the Risk Assessment Module
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


class RiskCategory(Enum):
    """Categories of legal risks"""
    FINANCIAL = "financial"
    LEGAL_LIABILITY = "legal_liability"
    TERMINATION = "termination"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    CONFIDENTIALITY = "confidentiality"
    DISPUTE_RESOLUTION = "dispute_resolution"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Risk severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_score(cls, score: int) -> "SeverityLevel":
        """Determine severity level from risk score"""
        if score <= 30:
            return cls.LOW
        elif score <= 60:
            return cls.MEDIUM
        elif score <= 85:
            return cls.HIGH
        else:
            return cls.CRITICAL


@dataclass
class RedFlag:
    """A detected red flag in a clause"""
    phrase: str
    category: RiskCategory
    weight: float
    position: tuple[int, int]  # start, end positions in text
    description: str


@dataclass
class KeywordMatch:
    """A matched keyword in the text"""
    keyword: str
    category: RiskCategory
    weight: float
    position: tuple[int, int]
    context: str  # surrounding text for context


@dataclass
class ClauseRisk:
    """Risk assessment for a single clause"""
    clause_id: str
    clause_text: str
    clause_type: str
    
    # Risk scores
    category: RiskCategory
    severity: SeverityLevel
    score: int  # 0-100
    confidence: int  # 0-100
    
    # Explanations
    primary_risk: str
    detailed_explanation: str
    specific_concerns: list[str]
    impact_if_triggered: str
    likelihood: str
    
    # Recommendations
    recommendation: str
    alternative_language: Optional[str] = None
    
    # Flags
    red_flags: list[str] = field(default_factory=list)
    mitigating_factors: list[str] = field(default_factory=list)
    positive_elements: list[str] = field(default_factory=list)
    
    # Metadata
    keyword_matches: list[KeywordMatch] = field(default_factory=list)
    ai_analyzed: bool = False
    analysis_timestamp: Optional[datetime] = None


@dataclass
class CategorySummary:
    """Summary of risks for a specific category"""
    category: RiskCategory
    count: int
    average_score: float
    highest_score: int
    clauses: list[str]  # clause IDs


@dataclass
class TopRisk:
    """A top-priority risk item"""
    rank: int
    clause_id: str
    clause_reference: str  # e.g., "Section 12.3 - Indemnification"
    score: int
    issue: str
    action: str


@dataclass
class RiskDistribution:
    """Distribution of risks by severity"""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    
    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low


@dataclass
class RiskSummary:
    """Summary of document-level risk"""
    overall_score: int
    overall_level: SeverityLevel
    distribution: RiskDistribution
    favorability: str  # heavily_favors_other_party, slightly_unfavorable, balanced, favorable
    recommendation: str


@dataclass
class ActionItem:
    """An action item from the risk assessment"""
    priority: int
    clause_reference: str
    issue: str
    urgency: str
    action: str
    talking_point: Optional[str] = None


@dataclass
class DocumentMetadata:
    """Metadata about the analyzed document"""
    filename: str
    pages: int
    clauses_analyzed: int
    analysis_timestamp: datetime
    processing_time_seconds: float


@dataclass
class DocumentRisk:
    """Complete risk assessment for a document"""
    metadata: DocumentMetadata
    
    # Summary
    risk_summary: RiskSummary
    executive_summary: str
    
    # Detailed results
    clause_risks: list[ClauseRisk]
    top_risks: list[TopRisk]
    category_summaries: dict[RiskCategory, CategorySummary]
    
    # Action items
    must_address_immediately: list[ActionItem]
    should_negotiate: list[str]
    acceptable_as_is: list[str]
    deal_breakers: list[str]
    
    # Comparison
    comparison_to_market: str
    overall_favorability: str
    
    # Action plan
    action_plan: list[str]


@dataclass
class Recommendation:
    """A structured recommendation"""
    priority: int
    category: RiskCategory
    title: str
    description: str
    clause_reference: str
    suggested_change: Optional[str] = None
    negotiation_tip: Optional[str] = None


@dataclass
class QuickScanResult:
    """Result from the fast rule-based scan"""
    total_matches: int
    keyword_matches: list[KeywordMatch]
    red_flags: list[RedFlag]
    category_counts: dict[RiskCategory, int]
    estimated_risk_level: SeverityLevel
    clauses_to_deep_analyze: list[str]  # clause IDs needing AI analysis
    processing_time_ms: float
