"""
AI Deep Analyzer using Groq Llama 3.1 70B

Layer 2 of the risk assessment system.
Performs deep AI-powered analysis of clauses to understand context and implications.
"""

import json
import os
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from .models import (
    RiskCategory,
    SeverityLevel,
    ClauseRisk,
    KeywordMatch,
)


@dataclass
class AnalysisContext:
    """Context for clause analysis"""
    document_type: str = "contract"
    user_role: str = "party_reviewing"  # e.g., service provider, customer, employee
    industry: str = "general"
    jurisdiction: str = "united_states"
    contract_value: Optional[float] = None


class AIAnalyzer:
    """
    AI-powered deep analysis using Groq Llama 3.1 70B.
    
    Features:
    - Understands clause context and implications
    - Evaluates actual risk vs. perceived risk
    - Considers industry standards and legal precedents
    - Generates human-readable explanations
    """
    
    # Groq model configuration
    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.3  # Lower temperature for more consistent analysis
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI Analyzer.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Groq client"""
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ImportError("Please install groq: pip install groq")
        return self._client
    
    def analyze_clause(
        self,
        clause_id: str,
        clause_text: str,
        context: AnalysisContext,
        keyword_matches: list[KeywordMatch] = None,
    ) -> ClauseRisk:
        """
        Perform deep AI analysis on a single clause.
        
        Args:
            clause_id: Unique identifier for the clause
            clause_text: The clause text to analyze
            context: Analysis context (document type, user role, etc.)
            keyword_matches: Pre-detected keyword matches from fast scanner
            
        Returns:
            ClauseRisk with detailed risk assessment
        """
        prompt = self._build_clause_analysis_prompt(clause_text, context, keyword_matches)
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return self._parse_clause_risk(clause_id, clause_text, result, keyword_matches)
            
        except Exception as e:
            # Fallback to rule-based assessment on API failure
            return self._fallback_analysis(clause_id, clause_text, keyword_matches, str(e))
    
    def analyze_clauses_batch(
        self,
        clauses: list[tuple[str, str]],  # List of (clause_id, clause_text)
        context: AnalysisContext,
        keyword_matches_map: dict[str, list[KeywordMatch]] = None,
    ) -> list[ClauseRisk]:
        """
        Analyze multiple clauses efficiently.
        
        Args:
            clauses: List of (clause_id, clause_text) tuples
            context: Analysis context
            keyword_matches_map: Dict mapping clause_id to keyword matches
            
        Returns:
            List of ClauseRisk assessments
        """
        keyword_matches_map = keyword_matches_map or {}
        results = []
        
        for clause_id, clause_text in clauses:
            keyword_matches = keyword_matches_map.get(clause_id, [])
            risk = self.analyze_clause(clause_id, clause_text, context, keyword_matches)
            results.append(risk)
        
        return results
    
    def generate_document_summary(
        self,
        clause_risks: list[ClauseRisk],
        context: AnalysisContext,
    ) -> dict:
        """
        Generate an executive summary of all identified risks.
        
        Args:
            clause_risks: List of clause-level risk assessments
            context: Analysis context
            
        Returns:
            Document-level summary with recommendations
        """
        prompt = self._build_summary_prompt(clause_risks, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._get_summary_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=self.TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return self._fallback_summary(clause_risks, str(e))
    
    def compare_to_market_standard(
        self,
        clause_text: str,
        clause_type: str,
        industry: str,
    ) -> dict:
        """
        Compare a clause to market/industry standards.
        
        Args:
            clause_text: The clause to compare
            clause_type: Type of clause (e.g., "liability", "termination")
            industry: Industry context
            
        Returns:
            Comparison analysis with benchmarking
        """
        prompt = self._build_comparison_prompt(clause_text, clause_type, industry)
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are a market analyst with deep knowledge of standard contract terms across industries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=self.TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "error": str(e),
                "industry_standard": "Unable to determine",
                "favorability": "unknown",
            }
    
    def _get_system_prompt(self) -> str:
        """System prompt for clause analysis"""
        return """You are a senior contract lawyer with 20 years of experience analyzing legal documents. 
Your role is to identify risks in contract clauses and explain them clearly to non-lawyers.

IMPORTANT GUIDELINES:
1. Be accurate - don't exaggerate risks but don't miss genuine concerns
2. Be practical - focus on risks that actually matter in real-world scenarios
3. Be clear - explain complex legal concepts in simple terms
4. Be actionable - always provide specific recommendations
5. Consider industry context - some terms that seem harsh are actually standard practice

When analyzing clauses:
- Think step by step about what the clause means
- Consider who the clause favors
- Evaluate worst-case scenarios
- Compare to market standards
- Provide concrete recommendations

You must respond ONLY with valid JSON matching the requested format."""

    def _get_summary_system_prompt(self) -> str:
        """System prompt for document summary"""
        return """You are a legal advisor preparing an executive briefing for a client.
Your task is to summarize risks across a contract and prioritize what needs attention.

Create clear, actionable summaries that help the client understand:
1. Overall contract safety
2. Top issues to address immediately
3. Items worth negotiating
4. Clauses that are acceptable
5. Potential deal-breakers
6. Recommended action plan

You must respond ONLY with valid JSON matching the requested format."""
    
    def _build_clause_analysis_prompt(
        self,
        clause_text: str,
        context: AnalysisContext,
        keyword_matches: list[KeywordMatch] = None,
    ) -> str:
        """Build the prompt for clause analysis"""
        
        keywords_info = ""
        if keyword_matches:
            keywords_list = [km.keyword for km in keyword_matches]
            keywords_info = f"\nDetected keywords/phrases that triggered this analysis: {', '.join(keywords_list)}"
        
        return f"""Analyze this contract clause for potential risks.

CLAUSE:
{clause_text}

CONTEXT:
- Document type: {context.document_type}
- Your client's role: {context.user_role}
- Industry: {context.industry}
- Jurisdiction: {context.jurisdiction}
{f"- Contract value: ${context.contract_value:,.2f}" if context.contract_value else ""}
{keywords_info}

Respond in this EXACT JSON format:
{{
  "risk_category": "financial|legal_liability|termination|intellectual_property|confidentiality|dispute_resolution|compliance|operational",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "risk_score": <0-100>,
  "confidence": <0-100>,
  "clause_type": "<type of clause, e.g., 'liability limitation', 'indemnification', 'termination'>",
  "primary_risk": "<One sentence describing the main danger>",
  "detailed_explanation": "<2-3 sentences explaining WHY this is risky in plain English>",
  "specific_concerns": [
    "<Concern 1>",
    "<Concern 2>"
  ],
  "impact_if_triggered": "<What bad thing could happen?>",
  "likelihood": "<How likely is this to cause problems? LOW/MEDIUM/HIGH>",
  "recommendation": "<What should the user do about this?>",
  "alternative_language": "<Suggest better wording, or null if clause is acceptable>",
  "red_flags": ["<flag1>", "<flag2>"],
  "mitigating_factors": ["<factor1>", "<factor2>"],
  "positive_elements": ["<element1>", "<element2>"],
  "negotiation_priority": "MUST_ADDRESS|SHOULD_NEGOTIATE|NICE_TO_HAVE|ACCEPTABLE",
  "market_comparison": "<How does this compare to typical contracts?>"
}}

Think step by step:
1. What is this clause trying to accomplish?
2. Who does it favor?
3. What's the worst-case scenario?
4. Is this standard practice or unusual?
5. How would I advise my client?"""

    def _build_summary_prompt(
        self,
        clause_risks: list[ClauseRisk],
        context: AnalysisContext,
    ) -> str:
        """Build prompt for document summary"""
        
        # Format clause risks for the prompt
        risks_text = ""
        for i, risk in enumerate(clause_risks, 1):
            risks_text += f"""
{i}. Clause {risk.clause_id} ({risk.clause_type})
   - Category: {risk.category.value}
   - Severity: {risk.severity.value}
   - Score: {risk.score}/100
   - Primary Risk: {risk.primary_risk}
   - Recommendation: {risk.recommendation}
"""
        
        return f"""Review this risk analysis and create a clear executive summary.

CONTEXT:
- Document type: {context.document_type}
- Client's role: {context.user_role}
- Industry: {context.industry}

IDENTIFIED RISKS:
{risks_text}

Create a JSON response:
{{
  "overall_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "overall_score": <0-100>,
  "executive_summary": "<2-3 sentence overview of document safety>",
  "must_address_immediately": [
    {{
      "clause": "<Which clause>",
      "issue": "<What's wrong>",
      "urgency": "<Why it matters>"
    }}
  ],
  "should_negotiate": ["<List of negotiable items>"],
  "acceptable_as_is": ["<List of standard/safe clauses>"],
  "deal_breakers": ["<Issues that might kill the deal>"],
  "overall_favorability": "heavily_favors_other_party|slightly_unfavorable|balanced|favorable",
  "comparison_to_market": "<How does this compare to typical contracts?>",
  "action_plan": [
    "1. <First thing to do>",
    "2. <Second priority>",
    "3. <Third priority>"
  ],
  "risk_patterns": ["<Any patterns noticed, e.g., 'all liability clauses favor the other party'>"],
  "key_strengths": ["<Positive aspects of the contract>"]
}}"""

    def _build_comparison_prompt(
        self,
        clause_text: str,
        clause_type: str,
        industry: str,
    ) -> str:
        """Build prompt for market comparison"""
        return f"""Compare this {clause_type} clause to industry standards for {industry}.

CLAUSE:
{clause_text}

Respond with:
{{
  "industry_standard": "<What do most contracts say?>",
  "this_contract_position": "<What does THIS contract say?>",
  "favorability": "much_worse|slightly_worse|typical|slightly_better|much_better",
  "negotiation_leverage": "HIGH|MEDIUM|LOW",
  "market_data": "<e.g., '85% of SaaS contracts cap liability at 12 months fees'>",
  "precedent_examples": "<Real-world examples of better clauses>",
  "recommendation": "<What should the client push for?>"
}}"""

    def _parse_clause_risk(
        self,
        clause_id: str,
        clause_text: str,
        result: dict,
        keyword_matches: list[KeywordMatch] = None,
    ) -> ClauseRisk:
        """Parse AI response into ClauseRisk object"""
        
        # Map string category to enum
        category_map = {
            "financial": RiskCategory.FINANCIAL,
            "legal_liability": RiskCategory.LEGAL_LIABILITY,
            "termination": RiskCategory.TERMINATION,
            "intellectual_property": RiskCategory.INTELLECTUAL_PROPERTY,
            "confidentiality": RiskCategory.CONFIDENTIALITY,
            "dispute_resolution": RiskCategory.DISPUTE_RESOLUTION,
            "compliance": RiskCategory.COMPLIANCE,
            "operational": RiskCategory.OPERATIONAL,
        }
        
        category = category_map.get(
            result.get("risk_category", "").lower(),
            RiskCategory.UNKNOWN
        )
        
        # Map string severity to enum
        severity_map = {
            "LOW": SeverityLevel.LOW,
            "MEDIUM": SeverityLevel.MEDIUM,
            "HIGH": SeverityLevel.HIGH,
            "CRITICAL": SeverityLevel.CRITICAL,
        }
        severity = severity_map.get(
            result.get("severity", "MEDIUM").upper(),
            SeverityLevel.MEDIUM
        )
        
        return ClauseRisk(
            clause_id=clause_id,
            clause_text=clause_text,
            clause_type=result.get("clause_type", "unknown"),
            category=category,
            severity=severity,
            score=min(100, max(0, result.get("risk_score", 50))),
            confidence=min(100, max(0, result.get("confidence", 70))),
            primary_risk=result.get("primary_risk", "Risk identified"),
            detailed_explanation=result.get("detailed_explanation", ""),
            specific_concerns=result.get("specific_concerns", []),
            impact_if_triggered=result.get("impact_if_triggered", ""),
            likelihood=result.get("likelihood", "MEDIUM"),
            recommendation=result.get("recommendation", "Review this clause carefully"),
            alternative_language=result.get("alternative_language"),
            red_flags=result.get("red_flags", []),
            mitigating_factors=result.get("mitigating_factors", []),
            positive_elements=result.get("positive_elements", []),
            keyword_matches=keyword_matches or [],
            ai_analyzed=True,
            analysis_timestamp=datetime.now(),
        )
    
    def _fallback_analysis(
        self,
        clause_id: str,
        clause_text: str,
        keyword_matches: list[KeywordMatch] = None,
        error: str = "",
    ) -> ClauseRisk:
        """Fallback analysis when AI is unavailable"""
        
        # Determine category from keyword matches
        if keyword_matches:
            category_counts = {}
            for km in keyword_matches:
                category_counts[km.category] = category_counts.get(km.category, 0) + 1
            category = max(category_counts.keys(), key=lambda c: category_counts[c])
            
            # Calculate basic score from weights
            total_weight = sum(km.weight for km in keyword_matches)
            score = min(100, int(total_weight * 15))
        else:
            category = RiskCategory.UNKNOWN
            score = 30
        
        severity = SeverityLevel.from_score(score)
        
        return ClauseRisk(
            clause_id=clause_id,
            clause_text=clause_text,
            clause_type=category.value.replace("_", " ").title() if category != RiskCategory.UNKNOWN else "General Clause",
            category=category,
            severity=severity,
            score=score,
            confidence=40,  # Low confidence for fallback
            primary_risk=f"Risk indicators detected in this {category.value.replace('_', ' ')} clause",
            detailed_explanation=f"This clause contains keywords typically associated with {category.value.replace('_', ' ')} risks. AI deep analysis was not available. Consider professional review.",
            specific_concerns=[km.keyword for km in (keyword_matches or [])[:5]],
            impact_if_triggered="Requires professional assessment to determine specific impact",
            likelihood="MEDIUM",
            recommendation="Review this clause carefully and consult a legal professional if concerned",
            red_flags=[km.keyword for km in (keyword_matches or []) if km.weight >= 2.5],
            keyword_matches=keyword_matches or [],
            ai_analyzed=False,
            analysis_timestamp=datetime.now(),
        )
    
    def _fallback_summary(self, clause_risks: list[ClauseRisk], error: str) -> dict:
        """Fallback summary when AI is unavailable"""
        
        # Calculate basic statistics
        scores = [r.score for r in clause_risks]
        avg_score = sum(scores) / len(scores) if scores else 50
        
        critical_count = sum(1 for r in clause_risks if r.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for r in clause_risks if r.severity == SeverityLevel.HIGH)
        
        if critical_count > 0:
            overall_level = "CRITICAL"
        elif high_count > 2:
            overall_level = "HIGH"
        elif avg_score > 50:
            overall_level = "MEDIUM"
        else:
            overall_level = "LOW"
        
        # Get top risks
        top_risks = sorted(clause_risks, key=lambda r: r.score, reverse=True)[:5]
        
        return {
            "overall_risk_level": overall_level,
            "overall_score": int(avg_score),
            "executive_summary": f"AI summary unavailable ({error}). Manual review recommended. Found {critical_count} critical and {high_count} high-risk clauses.",
            "must_address_immediately": [
                {"clause": r.clause_id, "issue": r.primary_risk, "urgency": "High score detected"}
                for r in top_risks[:3] if r.score >= 70
            ],
            "should_negotiate": [r.clause_id for r in top_risks if 50 <= r.score < 70],
            "acceptable_as_is": [r.clause_id for r in clause_risks if r.score < 30],
            "deal_breakers": [r.clause_id for r in clause_risks if r.score >= 90],
            "overall_favorability": "unknown",
            "comparison_to_market": "Unable to determine without AI analysis",
            "action_plan": [
                "1. Have a legal professional review critical clauses",
                "2. Negotiate high-risk items before signing",
                "3. Retry analysis when AI service is available"
            ],
        }
