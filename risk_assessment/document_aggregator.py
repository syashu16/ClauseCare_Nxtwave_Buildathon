"""
Document Aggregator

Layer 3 of the risk assessment system.
Combines all clause-level risks into document-level metrics and summaries.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .models import (
    RiskCategory,
    SeverityLevel,
    ClauseRisk,
    DocumentRisk,
    DocumentMetadata,
    RiskSummary,
    RiskDistribution,
    CategorySummary,
    TopRisk,
    ActionItem,
    Recommendation,
)
from .risk_scorer import RiskScorer


@dataclass
class PatternAnalysis:
    """Analysis of patterns across the document"""
    patterns: list[str]
    dominant_category: RiskCategory
    favorability_assessment: str
    one_sided_count: int
    mutual_count: int


class DocumentAggregator:
    """
    Aggregates clause-level risks into document-level insights.
    
    Features:
    - Calculates overall document risk score
    - Identifies risk patterns across clauses
    - Generates executive summary
    - Prioritizes action items
    - Creates dashboard-ready metrics
    """
    
    def __init__(self, risk_scorer: RiskScorer = None):
        self.risk_scorer = risk_scorer or RiskScorer()
    
    def aggregate(
        self,
        clause_risks: list[ClauseRisk],
        filename: str = "document",
        pages: int = 0,
        processing_time: float = 0.0,
        ai_summary: Optional[dict] = None,
    ) -> DocumentRisk:
        """
        Aggregate clause risks into a complete document risk assessment.
        
        Args:
            clause_risks: List of clause-level risk assessments
            filename: Name of the analyzed document
            pages: Number of pages in document
            processing_time: Total processing time in seconds
            ai_summary: Optional AI-generated summary
            
        Returns:
            Complete DocumentRisk assessment
        """
        if not clause_risks:
            return self._empty_document_risk(filename, pages, processing_time)
        
        # Create metadata
        metadata = DocumentMetadata(
            filename=filename,
            pages=pages,
            clauses_analyzed=len(clause_risks),
            analysis_timestamp=datetime.now(),
            processing_time_seconds=processing_time,
        )
        
        # Calculate risk summary
        risk_summary = self._calculate_risk_summary(clause_risks)
        
        # Get top risks
        top_risks = self._get_top_risks(clause_risks)
        
        # Calculate category summaries
        category_summaries = self._calculate_category_summaries(clause_risks)
        
        # Generate action items
        action_items = self._generate_action_items(clause_risks)
        
        # Analyze patterns
        pattern_analysis = self._analyze_patterns(clause_risks)
        
        # Generate lists
        must_address = [
            ActionItem(
                priority=i + 1,
                clause_reference=risk.clause_id,
                issue=risk.primary_risk,
                urgency="Critical risk requiring immediate attention",
                action=risk.recommendation,
            )
            for i, risk in enumerate(sorted(
                [r for r in clause_risks if r.severity == SeverityLevel.CRITICAL],
                key=lambda x: x.score,
                reverse=True
            )[:5])
        ]
        
        should_negotiate = [
            r.clause_id for r in clause_risks
            if r.severity == SeverityLevel.HIGH
        ]
        
        acceptable = [
            r.clause_id for r in clause_risks
            if r.severity == SeverityLevel.LOW and r.score < 25
        ]
        
        deal_breakers = [
            r.clause_id for r in clause_risks
            if r.score >= 90
        ]
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            clause_risks, risk_summary, pattern_analysis, ai_summary
        )
        
        # Determine overall favorability
        favorability = self._determine_favorability(clause_risks, pattern_analysis)
        
        # Market comparison
        comparison = self._generate_market_comparison(clause_risks, ai_summary)
        
        # Action plan
        action_plan = self._generate_action_plan(
            clause_risks, top_risks, must_address, should_negotiate
        )
        
        return DocumentRisk(
            metadata=metadata,
            risk_summary=risk_summary,
            executive_summary=executive_summary,
            clause_risks=clause_risks,
            top_risks=top_risks,
            category_summaries=category_summaries,
            must_address_immediately=must_address,
            should_negotiate=should_negotiate,
            acceptable_as_is=acceptable,
            deal_breakers=deal_breakers,
            comparison_to_market=comparison,
            overall_favorability=favorability,
            action_plan=action_plan,
        )
    
    def _calculate_risk_summary(self, clause_risks: list[ClauseRisk]) -> RiskSummary:
        """Calculate overall risk summary"""
        scores = [r.score for r in clause_risks]
        overall_score = self.risk_scorer.calculate_document_score(scores)
        overall_level = SeverityLevel.from_score(overall_score)
        
        # Count by severity
        distribution = RiskDistribution(
            critical=sum(1 for r in clause_risks if r.severity == SeverityLevel.CRITICAL),
            high=sum(1 for r in clause_risks if r.severity == SeverityLevel.HIGH),
            medium=sum(1 for r in clause_risks if r.severity == SeverityLevel.MEDIUM),
            low=sum(1 for r in clause_risks if r.severity == SeverityLevel.LOW),
        )
        
        # Determine favorability
        high_risk_ratio = (distribution.critical + distribution.high) / len(clause_risks)
        if high_risk_ratio > 0.5:
            favorability = "heavily_favors_other_party"
        elif high_risk_ratio > 0.3:
            favorability = "slightly_unfavorable"
        elif high_risk_ratio > 0.1:
            favorability = "balanced"
        else:
            favorability = "favorable"
        
        # Generate recommendation
        if overall_level == SeverityLevel.CRITICAL:
            recommendation = "DO NOT SIGN without significant negotiation. Multiple critical issues detected."
        elif overall_level == SeverityLevel.HIGH:
            recommendation = "Review high-risk clauses carefully before signing. Negotiation strongly recommended."
        elif overall_level == SeverityLevel.MEDIUM:
            recommendation = "Generally acceptable with some concerns. Consider negotiating key points."
        else:
            recommendation = "Contract appears balanced. Standard terms with minimal risk."
        
        return RiskSummary(
            overall_score=overall_score,
            overall_level=overall_level,
            distribution=distribution,
            favorability=favorability,
            recommendation=recommendation,
        )
    
    def _get_top_risks(self, clause_risks: list[ClauseRisk], limit: int = 10) -> list[TopRisk]:
        """Get the top risks sorted by score"""
        sorted_risks = sorted(clause_risks, key=lambda r: r.score, reverse=True)
        
        return [
            TopRisk(
                rank=i + 1,
                clause_id=risk.clause_id,
                clause_reference=f"{risk.clause_type.title()} - {risk.clause_id}",
                score=risk.score,
                issue=risk.primary_risk,
                action=risk.recommendation,
            )
            for i, risk in enumerate(sorted_risks[:limit])
            if risk.score >= 30  # Only include medium+ risk
        ]
    
    def _calculate_category_summaries(
        self,
        clause_risks: list[ClauseRisk]
    ) -> dict[RiskCategory, CategorySummary]:
        """Calculate summary for each risk category"""
        category_data = defaultdict(lambda: {"scores": [], "clauses": []})
        
        for risk in clause_risks:
            category_data[risk.category]["scores"].append(risk.score)
            category_data[risk.category]["clauses"].append(risk.clause_id)
        
        summaries = {}
        for category, data in category_data.items():
            if data["scores"]:
                summaries[category] = CategorySummary(
                    category=category,
                    count=len(data["scores"]),
                    average_score=sum(data["scores"]) / len(data["scores"]),
                    highest_score=max(data["scores"]),
                    clauses=data["clauses"],
                )
        
        return summaries
    
    def _generate_action_items(self, clause_risks: list[ClauseRisk]) -> list[ActionItem]:
        """Generate prioritized action items"""
        action_items = []
        
        # Sort by score descending
        sorted_risks = sorted(clause_risks, key=lambda r: r.score, reverse=True)
        
        for i, risk in enumerate(sorted_risks):
            if risk.score >= 30:  # Only include medium+ risk
                urgency = self._determine_urgency(risk)
                talking_point = self._generate_talking_point(risk)
                
                action_items.append(ActionItem(
                    priority=i + 1,
                    clause_reference=risk.clause_id,
                    issue=risk.primary_risk,
                    urgency=urgency,
                    action=risk.recommendation,
                    talking_point=talking_point,
                ))
        
        return action_items
    
    def _determine_urgency(self, risk: ClauseRisk) -> str:
        """Determine urgency level for a risk"""
        if risk.severity == SeverityLevel.CRITICAL:
            return "MUST address before signing - potential deal-breaker"
        elif risk.severity == SeverityLevel.HIGH:
            return "Should negotiate before signing"
        elif risk.severity == SeverityLevel.MEDIUM:
            return "Worth discussing but not critical"
        else:
            return "Low priority - standard clause"
    
    def _generate_talking_point(self, risk: ClauseRisk) -> str:
        """Generate a negotiation talking point"""
        category_talking_points = {
            RiskCategory.FINANCIAL: "Industry standard is to cap financial exposure at 1-2x annual contract value.",
            RiskCategory.LEGAL_LIABILITY: "We need to ensure liability is proportionate and mutual.",
            RiskCategory.TERMINATION: "We require reasonable termination rights for operational flexibility.",
            RiskCategory.INTELLECTUAL_PROPERTY: "We need to retain ownership of our core IP and pre-existing materials.",
            RiskCategory.CONFIDENTIALITY: "Confidentiality obligations should be mutual and time-limited.",
            RiskCategory.DISPUTE_RESOLUTION: "We prefer mediation before arbitration, with a neutral venue.",
            RiskCategory.COMPLIANCE: "Compliance obligations should be clearly defined with reasonable scope.",
            RiskCategory.OPERATIONAL: "We need reasonable flexibility in operational terms.",
        }
        
        return category_talking_points.get(
            risk.category,
            "This clause requires revision to be more balanced."
        )
    
    def _analyze_patterns(self, clause_risks: list[ClauseRisk]) -> PatternAnalysis:
        """Analyze patterns across the document"""
        patterns = []
        category_counts = defaultdict(int)
        high_risk_categories = defaultdict(int)
        
        for risk in clause_risks:
            category_counts[risk.category] += 1
            if risk.score >= 60:
                high_risk_categories[risk.category] += 1
        
        # Find dominant category
        if category_counts:
            dominant = max(category_counts.keys(), key=lambda c: category_counts[c])
        else:
            dominant = RiskCategory.UNKNOWN
        
        # Detect patterns
        if high_risk_categories:
            top_risk_category = max(
                high_risk_categories.keys(),
                key=lambda c: high_risk_categories[c]
            )
            if high_risk_categories[top_risk_category] >= 2:
                patterns.append(
                    f"Multiple high-risk {top_risk_category.value} clauses detected - "
                    f"contract may be unfavorable in this area"
                )
        
        # Check for one-sided vs mutual language
        one_sided_count = sum(
            1 for r in clause_risks
            if any(flag in r.red_flags for flag in ["one-sided", "unilateral", "sole discretion"])
        )
        mutual_count = sum(
            1 for r in clause_risks
            if any(factor in r.mitigating_factors for factor in ["mutual", "reciprocal", "balanced"])
        )
        
        if one_sided_count > mutual_count * 2:
            patterns.append("Contract language is predominantly one-sided")
            favorability = "heavily_favors_other_party"
        elif one_sided_count > mutual_count:
            patterns.append("Some clauses favor the other party")
            favorability = "slightly_unfavorable"
        elif mutual_count > one_sided_count:
            patterns.append("Contract contains balanced, mutual obligations")
            favorability = "balanced"
        else:
            favorability = "balanced"
        
        # Check for escalating obligations
        liability_risks = [r for r in clause_risks if r.category == RiskCategory.LEGAL_LIABILITY]
        if len(liability_risks) >= 3 and all(r.score >= 60 for r in liability_risks):
            patterns.append("All liability clauses heavily favor the other party")
        
        # Check for termination constraints
        term_risks = [r for r in clause_risks if r.category == RiskCategory.TERMINATION]
        if term_risks and all(r.score >= 50 for r in term_risks):
            patterns.append("Termination rights are restricted")
        
        return PatternAnalysis(
            patterns=patterns,
            dominant_category=dominant,
            favorability_assessment=favorability,
            one_sided_count=one_sided_count,
            mutual_count=mutual_count,
        )
    
    def _generate_executive_summary(
        self,
        clause_risks: list[ClauseRisk],
        risk_summary: RiskSummary,
        pattern_analysis: PatternAnalysis,
        ai_summary: Optional[dict] = None,
    ) -> str:
        """Generate executive summary"""
        if ai_summary and "executive_summary" in ai_summary:
            return ai_summary["executive_summary"]
        
        dist = risk_summary.distribution
        total = dist.total
        
        summary_parts = []
        
        # Overall assessment
        if risk_summary.overall_level == SeverityLevel.CRITICAL:
            summary_parts.append(
                "⚠️ This contract contains CRITICAL risks that require immediate attention."
            )
        elif risk_summary.overall_level == SeverityLevel.HIGH:
            summary_parts.append(
                "This contract has significant risks that should be addressed before signing."
            )
        elif risk_summary.overall_level == SeverityLevel.MEDIUM:
            summary_parts.append(
                "This contract has some areas of concern but is generally reasonable."
            )
        else:
            summary_parts.append(
                "This contract appears balanced with minimal risk."
            )
        
        # Statistics
        summary_parts.append(
            f"Analysis found {dist.critical} critical, {dist.high} high, "
            f"{dist.medium} medium, and {dist.low} low risk clauses."
        )
        
        # Patterns
        if pattern_analysis.patterns:
            summary_parts.append(pattern_analysis.patterns[0])
        
        return " ".join(summary_parts)
    
    def _determine_favorability(
        self,
        clause_risks: list[ClauseRisk],
        pattern_analysis: PatternAnalysis,
    ) -> str:
        """Determine overall favorability"""
        scores = [r.score for r in clause_risks]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score >= 70:
            return "heavily_favors_other_party"
        elif avg_score >= 50:
            return "slightly_unfavorable"
        elif avg_score >= 30:
            return "balanced"
        else:
            return "favorable"
    
    def _generate_market_comparison(
        self,
        clause_risks: list[ClauseRisk],
        ai_summary: Optional[dict] = None,
    ) -> str:
        """Generate market comparison text"""
        if ai_summary and "comparison_to_market" in ai_summary:
            return ai_summary["comparison_to_market"]
        
        scores = [r.score for r in clause_risks]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        if avg_score >= 70:
            return "This contract is significantly more restrictive than typical market agreements."
        elif avg_score >= 50:
            return "This contract is somewhat more restrictive than typical market agreements."
        elif avg_score >= 30:
            return "This contract is roughly in line with market standards, with some areas to review."
        else:
            return "This contract has favorable terms compared to typical market agreements."
    
    def _generate_action_plan(
        self,
        clause_risks: list[ClauseRisk],
        top_risks: list[TopRisk],
        must_address: list[ActionItem],
        should_negotiate: list[str],
    ) -> list[str]:
        """Generate prioritized action plan"""
        action_plan = []
        
        # Critical issues first
        if must_address:
            action_plan.append(
                f"1. Address {len(must_address)} critical issue(s) immediately: "
                f"{', '.join(a.clause_reference for a in must_address[:3])}"
            )
        
        # High priority negotiations
        if should_negotiate:
            action_plan.append(
                f"2. Negotiate {len(should_negotiate)} high-risk clause(s) before signing"
            )
        
        # Category-specific recommendations
        high_risk_categories = set(
            r.category for r in clause_risks
            if r.score >= 60
        )
        for category in list(high_risk_categories)[:2]:
            action_plan.append(
                f"3. Review all {category.value.replace('_', ' ')} clauses for balance"
            )
        
        # General recommendations
        action_plan.append("4. Have legal counsel review before signing")
        action_plan.append("5. Document any agreed changes in writing")
        
        return action_plan[:5]  # Limit to 5 items
    
    def _empty_document_risk(
        self,
        filename: str,
        pages: int,
        processing_time: float,
    ) -> DocumentRisk:
        """Create an empty document risk for documents with no clauses"""
        metadata = DocumentMetadata(
            filename=filename,
            pages=pages,
            clauses_analyzed=0,
            analysis_timestamp=datetime.now(),
            processing_time_seconds=processing_time,
        )
        
        return DocumentRisk(
            metadata=metadata,
            risk_summary=RiskSummary(
                overall_score=0,
                overall_level=SeverityLevel.LOW,
                distribution=RiskDistribution(),
                favorability="unknown",
                recommendation="No clauses found to analyze",
            ),
            executive_summary="No clauses were found in the document for analysis.",
            clause_risks=[],
            top_risks=[],
            category_summaries={},
            must_address_immediately=[],
            should_negotiate=[],
            acceptable_as_is=[],
            deal_breakers=[],
            comparison_to_market="Unable to compare - no clauses analyzed",
            overall_favorability="unknown",
            action_plan=["Upload a document with identifiable clauses for analysis"],
        )
    
    def generate_recommendations(
        self,
        document_risk: DocumentRisk,
    ) -> list[Recommendation]:
        """Generate structured recommendations from document risk"""
        recommendations = []
        
        for i, risk in enumerate(sorted(
            document_risk.clause_risks,
            key=lambda r: r.score,
            reverse=True
        )):
            if risk.score >= 30:  # Only include medium+ risk
                rec = Recommendation(
                    priority=i + 1,
                    category=risk.category,
                    title=risk.primary_risk[:100],
                    description=risk.detailed_explanation or risk.primary_risk,
                    clause_reference=risk.clause_id,
                    suggested_change=risk.alternative_language,
                    negotiation_tip=self._generate_talking_point(risk),
                )
                recommendations.append(rec)
        
        return recommendations[:20]  # Limit to top 20
    
    def to_markdown_report(self, document_risk: DocumentRisk) -> str:
        """Generate a markdown-formatted risk report"""
        lines = []
        
        # Header
        lines.append("# Risk Assessment Report")
        lines.append(f"\n**Document:** {document_risk.metadata.filename}")
        lines.append(f"**Analyzed:** {document_risk.metadata.analysis_timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Clauses Analyzed:** {document_risk.metadata.clauses_analyzed}")
        lines.append("")
        
        # Overall Score
        summary = document_risk.risk_summary
        emoji = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🔶", "CRITICAL": "🚨"}
        lines.append(f"## Overall Risk: {emoji.get(summary.overall_level.value, '')} {summary.overall_level.value}")
        lines.append(f"**Score:** {summary.overall_score}/100")
        lines.append(f"**Recommendation:** {summary.recommendation}")
        lines.append("")
        
        # Executive Summary
        lines.append("## Executive Summary")
        lines.append(document_risk.executive_summary)
        lines.append("")
        
        # Distribution
        lines.append("## Risk Distribution")
        dist = summary.distribution
        lines.append(f"- 🚨 Critical: {dist.critical}")
        lines.append(f"- 🔶 High: {dist.high}")
        lines.append(f"- ⚠️ Medium: {dist.medium}")
        lines.append(f"- ✅ Low: {dist.low}")
        lines.append("")
        
        # Critical Issues
        if document_risk.must_address_immediately:
            lines.append("## 🚨 Critical Issues (Must Address)")
            for action in document_risk.must_address_immediately:
                lines.append(f"\n### {action.priority}. {action.clause_reference}")
                lines.append(f"- **Issue:** {action.issue}")
                lines.append(f"- **Action:** {action.action}")
                if action.talking_point:
                    lines.append(f"- **Talking Point:** {action.talking_point}")
            lines.append("")
        
        # Top Risks
        if document_risk.top_risks:
            lines.append("## ⚠️ Top Risks")
            for risk in document_risk.top_risks[:5]:
                lines.append(f"\n### {risk.rank}. {risk.clause_reference} (Score: {risk.score}/100)")
                lines.append(f"- **Issue:** {risk.issue}")
                lines.append(f"- **Action:** {risk.action}")
            lines.append("")
        
        # Action Plan
        lines.append("## 📋 Action Plan")
        for item in document_risk.action_plan:
            lines.append(f"- {item}")
        lines.append("")
        
        # Acceptable Clauses
        if document_risk.acceptable_as_is:
            lines.append("## ✅ Acceptable Terms")
            lines.append(", ".join(document_risk.acceptable_as_is[:10]))
            lines.append("")
        
        return "\n".join(lines)
    
    def to_json(self, document_risk: DocumentRisk) -> dict:
        """Convert document risk to JSON-serializable dict"""
        return {
            "document_metadata": {
                "filename": document_risk.metadata.filename,
                "pages": document_risk.metadata.pages,
                "clauses_analyzed": document_risk.metadata.clauses_analyzed,
                "analysis_timestamp": document_risk.metadata.analysis_timestamp.isoformat(),
                "processing_time_seconds": document_risk.metadata.processing_time_seconds,
            },
            "risk_summary": {
                "overall_score": document_risk.risk_summary.overall_score,
                "overall_level": document_risk.risk_summary.overall_level.value,
                "distribution": {
                    "critical": document_risk.risk_summary.distribution.critical,
                    "high": document_risk.risk_summary.distribution.high,
                    "medium": document_risk.risk_summary.distribution.medium,
                    "low": document_risk.risk_summary.distribution.low,
                },
                "favorability": document_risk.risk_summary.favorability,
                "recommendation": document_risk.risk_summary.recommendation,
            },
            "executive_summary": document_risk.executive_summary,
            "top_risks": [
                {
                    "rank": r.rank,
                    "clause_id": r.clause_id,
                    "clause_reference": r.clause_reference,
                    "score": r.score,
                    "issue": r.issue,
                    "action": r.action,
                }
                for r in document_risk.top_risks
            ],
            "categories": {
                cat.value: {
                    "count": summary.count,
                    "avg_score": round(summary.average_score, 1),
                    "highest": summary.highest_score,
                }
                for cat, summary in document_risk.category_summaries.items()
            },
            "must_address_immediately": [
                {
                    "priority": a.priority,
                    "clause": a.clause_reference,
                    "issue": a.issue,
                    "urgency": a.urgency,
                    "action": a.action,
                }
                for a in document_risk.must_address_immediately
            ],
            "should_negotiate": document_risk.should_negotiate,
            "acceptable_as_is": document_risk.acceptable_as_is,
            "deal_breakers": document_risk.deal_breakers,
            "overall_favorability": document_risk.overall_favorability,
            "comparison_to_market": document_risk.comparison_to_market,
            "action_plan": document_risk.action_plan,
        }
