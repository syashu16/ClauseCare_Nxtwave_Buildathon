"""
NegotiateAI Agents
==================

6 specialized AI agents for contract negotiation analysis.
Each agent has specific expertise and produces structured outputs.
"""

import os
import json
import re
import time
from typing import Optional, Dict, Any, List
from groq import Groq
from dotenv import load_dotenv

from .models import (
    DocumentAnalysis, RiskAssessment, NegotiationStrategy,
    LegalAdvisory, MarketResearch, ContractOptimization,
    Party, ClauseInfo, RiskItem, RiskCategory,
    NegotiationPriority, QuickWin, TradingChip,
    ComplianceIssue, EnforceabilityConcern, LegalPrecedent,
    StatutoryWaiver, Ambiguity, BenchmarkComparison,
    CompetitorIntel, PricingAnalysis, CriticalDecision, RoadmapItem
)

load_dotenv()


class BaseAgent:
    """Base class for all NegotiateAI agents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        self.model = "llama-3.3-70b-versatile"
        self.agent_name = "BaseAgent"
        self.role = ""
        self.expertise = ""
        self.personality = ""
        
    def _call_llm(self, prompt: str, system_prompt: str, temperature: float = 0.3) -> str:
        """Make LLM API call"""
        if not self.client:
            raise ValueError("No API key configured")
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=8000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find raw JSON object
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return {}
    
    def _parse_list_from_text(self, text: str, section_name: str) -> List[str]:
        """Extract a list from text under a section header"""
        items = []
        pattern = rf'{section_name}[:\s]*\n((?:[-•*]\s*.+\n?)+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            for line in match.group(1).split('\n'):
                line = re.sub(r'^[-•*]\s*', '', line.strip())
                if line:
                    items.append(line)
        return items


class DocumentAnalyzerAgent(BaseAgent):
    """Agent #1: Senior Legal Document Analyzer"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.agent_name = "Document Analyzer"
        self.role = "Senior Legal Document Analyzer"
        self.expertise = "Contract structure, clause categorization, legal terminology"
        self.personality = "Meticulous, systematic, detail-oriented"
        
    def analyze(self, contract_text: str) -> DocumentAnalysis:
        """Analyze contract structure and extract key information"""
        
        system_prompt = f"""You are a {self.role} with expertise in {self.expertise}.
Your personality: {self.personality}

You analyze legal contracts with extreme attention to detail, extracting and categorizing every clause, identifying parties, mapping obligations, and assessing document structure.

ALWAYS respond with a structured JSON analysis."""

        prompt = f"""Analyze this contract with extreme attention to detail:

{contract_text[:15000]}

Extract and provide a comprehensive JSON analysis with this structure:
{{
    "document_type": "Service Agreement | NDA | Employment Contract | Lease | etc.",
    "parties": [
        {{
            "name": "Party name",
            "role": "Service Provider | Client | Employer | etc.",
            "obligations_count": 5
        }}
    ],
    "clause_summary": {{
        "total_clauses": 25,
        "by_category": {{
            "payment": 3,
            "liability": 2,
            "termination": 2,
            "ip": 2,
            "confidentiality": 2,
            "dispute": 1,
            "general": 5
        }}
    }},
    "key_clauses": [
        {{
            "clause_id": "Section 4.2",
            "clause_type": "payment",
            "summary": "Brief description of clause",
            "parties_affected": ["Party A"],
            "criticality": "high | medium | low"
        }}
    ],
    "structural_issues": [
        "Missing force majeure clause",
        "One-sided termination terms"
    ],
    "cross_references": [
        "Clause 4.2 references Section 8 for late fees"
    ],
    "obligations_by_party": {{
        "Party A": ["Obligation 1", "Obligation 2"],
        "Party B": ["Obligation 1"]
    }},
    "defined_terms": ["Term 1", "Term 2"],
    "effective_date": "Date or null",
    "termination_date": "Date or null"
}}

Be thorough - extract EVERY clause and obligation. This forms the foundation for all other analysis."""

        raw_response = self._call_llm(prompt, system_prompt)
        parsed = self._extract_json(raw_response)
        
        # Build DocumentAnalysis from parsed data
        parties = []
        for p in parsed.get("parties", []):
            parties.append(Party(
                name=p.get("name", "Unknown"),
                role=p.get("role", "Unknown"),
                obligations_count=p.get("obligations_count", 0)
            ))
        
        key_clauses = []
        for c in parsed.get("key_clauses", []):
            key_clauses.append(ClauseInfo(
                clause_id=c.get("clause_id", ""),
                clause_type=c.get("clause_type", "general"),
                summary=c.get("summary", ""),
                parties_affected=c.get("parties_affected", []),
                criticality=c.get("criticality", "medium")
            ))
        
        return DocumentAnalysis(
            document_type=parsed.get("document_type", "Unknown Contract"),
            parties=parties,
            clause_summary=parsed.get("clause_summary", {"total_clauses": 0, "by_category": {}}),
            key_clauses=key_clauses,
            structural_issues=parsed.get("structural_issues", []),
            cross_references=parsed.get("cross_references", []),
            obligations_by_party=parsed.get("obligations_by_party", {}),
            defined_terms=parsed.get("defined_terms", []),
            effective_date=parsed.get("effective_date"),
            termination_date=parsed.get("termination_date"),
            raw_analysis=raw_response
        )


class RiskAssessorAgent(BaseAgent):
    """Agent #2: Expert Risk Assessment Specialist"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.agent_name = "Risk Assessor"
        self.role = "Expert Risk Assessment Specialist"
        self.expertise = "Risk identification, severity evaluation, impact analysis"
        self.personality = "Cautious, analytical, risk-averse but pragmatic"
        
    def analyze(self, contract_text: str, document_analysis: DocumentAnalysis) -> RiskAssessment:
        """Assess all contract risks with severity scoring"""
        
        system_prompt = f"""You are an {self.role} with expertise in {self.expertise}.
Your personality: {self.personality}

You identify every contractual risk, evaluate severity and likelihood, categorize by type, and recommend mitigation strategies.

Think like a paranoid general counsel who's seen every worst-case scenario.

ALWAYS respond with structured JSON analysis."""

        doc_summary = f"""
Document Type: {document_analysis.document_type}
Parties: {', '.join([p.name + ' (' + p.role + ')' for p in document_analysis.parties])}
Total Clauses: {document_analysis.clause_summary.get('total_clauses', 'Unknown')}
Structural Issues: {', '.join(document_analysis.structural_issues[:5])}
"""

        prompt = f"""Based on this document analysis and contract text, conduct a comprehensive risk assessment:

DOCUMENT ANALYSIS:
{doc_summary}

CONTRACT TEXT:
{contract_text[:12000]}

Evaluate EVERY clause for potential risks. For each significant risk, answer:
1. What could go wrong?
2. How bad could it be? (quantify if possible)
3. How likely is it to happen?
4. What's the worst-case financial impact?
5. Is this standard or unusual for this contract type?
6. How would you mitigate or eliminate this risk?

Provide JSON response:
{{
    "overall_risk_profile": {{
        "score": 72,
        "level": "HIGH | CRITICAL | MEDIUM | LOW",
        "summary": "Brief overall assessment",
        "critical_count": 2,
        "high_count": 5,
        "medium_count": 8,
        "low_count": 4
    }},
    "risks": [
        {{
            "risk_id": "RISK-001",
            "clause": "Section 12.3 - Indemnification",
            "category": "Legal Liability | Financial | Compliance | Operational | IP",
            "severity": "CRITICAL | HIGH | MEDIUM | LOW",
            "score": 95,
            "description": "What the risk is",
            "impact": "Potential consequences",
            "likelihood": "Very Likely | Likely | Possible | Unlikely",
            "financial_exposure": "$X or 'Unlimited'",
            "legal_precedent": "How courts view this",
            "mitigation": {{
                "required_action": "What must be done",
                "suggested_alternative": "Alternative language",
                "deal_breaker": true
            }}
        }}
    ],
    "risk_by_category": {{
        "financial": {{"total_score": 75, "count": 3, "top_risk": "Main concern"}},
        "legal": {{"total_score": 80, "count": 4, "top_risk": "Main concern"}}
    }},
    "acceptable_risks": ["List of risks that are standard/acceptable"]
}}

Be specific. Instead of "high risk," say "could expose company to $2M+ in damages."
Categorize: CRITICAL (must address), HIGH (strongly recommend), MEDIUM (consider), LOW (acceptable)"""

        raw_response = self._call_llm(prompt, system_prompt)
        parsed = self._extract_json(raw_response)
        
        profile = parsed.get("overall_risk_profile", {})
        
        # Parse risks into categories
        all_risks = parsed.get("risks", [])
        critical_risks, high_risks, medium_risks, low_risks = [], [], [], []
        
        for r in all_risks:
            risk_item = RiskItem(
                risk_id=r.get("risk_id", f"RISK-{len(critical_risks)+len(high_risks)+len(medium_risks)+len(low_risks)+1:03d}"),
                clause=r.get("clause", ""),
                category=r.get("category", "General"),
                severity=r.get("severity", "MEDIUM"),
                score=r.get("score", 50),
                description=r.get("description", ""),
                impact=r.get("impact", ""),
                likelihood=r.get("likelihood", "Possible"),
                financial_exposure=r.get("financial_exposure", "Unknown"),
                legal_precedent=r.get("legal_precedent", ""),
                mitigation=r.get("mitigation", {})
            )
            
            if risk_item.severity == "CRITICAL":
                critical_risks.append(risk_item)
            elif risk_item.severity == "HIGH":
                high_risks.append(risk_item)
            elif risk_item.severity == "MEDIUM":
                medium_risks.append(risk_item)
            else:
                low_risks.append(risk_item)
        
        # Parse risk by category
        risk_by_cat = {}
        for cat, data in parsed.get("risk_by_category", {}).items():
            risk_by_cat[cat] = RiskCategory(
                total_score=data.get("total_score", 0),
                count=data.get("count", 0),
                top_risk=data.get("top_risk", "")
            )
        
        return RiskAssessment(
            overall_score=profile.get("score", 50),
            overall_level=profile.get("level", "MEDIUM"),
            summary=profile.get("summary", "Risk assessment completed"),
            critical_count=len(critical_risks),
            high_count=len(high_risks),
            medium_count=len(medium_risks),
            low_count=len(low_risks),
            critical_risks=critical_risks,
            high_risks=high_risks,
            medium_risks=medium_risks,
            low_risks=low_risks,
            risk_by_category=risk_by_cat,
            acceptable_risks=parsed.get("acceptable_risks", []),
            raw_analysis=raw_response
        )


class NegotiationStrategistAgent(BaseAgent):
    """Agent #3: Master Negotiation Strategist"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.agent_name = "Negotiation Strategist"
        self.role = "Master Negotiation Strategist"
        self.expertise = "Game theory, negotiation tactics, leverage analysis, deal psychology"
        self.personality = "Strategic, assertive, creative, diplomatic"
        
    def analyze(self, contract_text: str, document_analysis: DocumentAnalysis, 
                risk_assessment: RiskAssessment, context: Dict[str, Any] = None) -> NegotiationStrategy:
        """Develop winning negotiation strategies"""
        
        context = context or {}
        
        system_prompt = f"""You are a {self.role} with expertise in {self.expertise}.
Your personality: {self.personality}

You develop winning negotiation strategies, identify leverage points, create counter-proposals, and provide tactical playbooks.

Your goal: Give users the negotiation intelligence of a Fortune 500 company's legal team.

ALWAYS respond with structured JSON."""

        # Build context from previous analyses
        risk_summary = f"""
Overall Risk Score: {risk_assessment.overall_score}/100 ({risk_assessment.overall_level})
Critical Risks: {risk_assessment.critical_count}
High Risks: {risk_assessment.high_count}

Top Critical Issues:
{chr(10).join([f"- {r.clause}: {r.description}" for r in risk_assessment.critical_risks[:3]])}

Top High-Priority Issues:
{chr(10).join([f"- {r.clause}: {r.description}" for r in risk_assessment.high_risks[:3]])}
"""

        prompt = f"""You are preparing for a high-stakes contract negotiation.

DOCUMENT TYPE: {document_analysis.document_type}
PARTIES: {', '.join([p.name + ' (' + p.role + ')' for p in document_analysis.parties])}

RISK ASSESSMENT:
{risk_summary}

CONTRACT TEXT (key sections):
{contract_text[:10000]}

ADDITIONAL CONTEXT:
- Your Role: {context.get('your_role', 'The party reviewing this contract')}
- Industry: {context.get('industry', 'General business')}
- Deal Importance: {context.get('importance', 'Standard business deal')}

Develop a comprehensive negotiation strategy as JSON:
{{
    "power_assessment": {{
        "overall_balance": -2.5,
        "interpretation": "Explanation of power dynamics",
        "factors_in_favor": ["Factor 1", "Factor 2"],
        "factors_against": ["Factor 1", "Factor 2"],
        "your_BATNA": "Best alternative if no deal",
        "their_BATNA": "Their best alternative"
    }},
    "negotiation_priorities": [
        {{
            "rank": 1,
            "issue": "Issue name",
            "current_position": "What contract says",
            "target_position": "What you want",
            "minimum_acceptable": "Walk-away point",
            "leverage_score": 8,
            "rationale": "Why this matters",
            "strategy": "How to negotiate this",
            "talking_points": ["Point 1", "Point 2", "Point 3"],
            "counter_proposal": "Specific alternative language",
            "concessions_available": ["What you can give up"],
            "if_rejected": "Fallback or walk-away"
        }}
    ],
    "quick_wins": [
        {{
            "issue": "Easy win",
            "current": "Current term",
            "request": "What to ask for",
            "likelihood": "HIGH",
            "rationale": "Why they'll agree",
            "script": "Exact words to say"
        }}
    ],
    "deal_breakers": ["Absolute non-negotiables"],
    "trading_chips": [
        {{
            "what_you_offer": "Concession",
            "what_you_want": "What to get in return",
            "value_ratio": "Fair | Favorable | Unfavorable"
        }}
    ],
    "negotiation_sequence": ["Step 1", "Step 2", "Step 3"],
    "psychological_tactics": ["Tactic 1", "Tactic 2"]
}}

Think strategically: What's the power dynamic? What are leverage points? What can be traded?
Create a tactical playbook that a non-negotiator could follow."""

        raw_response = self._call_llm(prompt, system_prompt, temperature=0.4)
        parsed = self._extract_json(raw_response)
        
        power = parsed.get("power_assessment", {})
        
        # Parse priorities
        priorities = []
        for p in parsed.get("negotiation_priorities", []):
            priorities.append(NegotiationPriority(
                rank=p.get("rank", len(priorities) + 1),
                issue=p.get("issue", ""),
                current_position=p.get("current_position", ""),
                target_position=p.get("target_position", ""),
                minimum_acceptable=p.get("minimum_acceptable", ""),
                leverage_score=p.get("leverage_score", 5),
                rationale=p.get("rationale", ""),
                strategy=p.get("strategy", ""),
                talking_points=p.get("talking_points", []),
                counter_proposal=p.get("counter_proposal", ""),
                concessions_available=p.get("concessions_available", []),
                if_rejected=p.get("if_rejected", "")
            ))
        
        # Parse quick wins
        quick_wins = []
        for q in parsed.get("quick_wins", []):
            quick_wins.append(QuickWin(
                issue=q.get("issue", ""),
                current=q.get("current", ""),
                request=q.get("request", ""),
                likelihood=q.get("likelihood", "MEDIUM"),
                rationale=q.get("rationale", ""),
                script=q.get("script", "")
            ))
        
        # Parse trading chips
        chips = []
        for t in parsed.get("trading_chips", []):
            chips.append(TradingChip(
                what_you_offer=t.get("what_you_offer", ""),
                what_you_want=t.get("what_you_want", ""),
                value_ratio=t.get("value_ratio", "Fair")
            ))
        
        return NegotiationStrategy(
            power_balance=power.get("overall_balance", 0),
            power_interpretation=power.get("interpretation", ""),
            factors_in_favor=power.get("factors_in_favor", []),
            factors_against=power.get("factors_against", []),
            your_batna=power.get("your_BATNA", ""),
            their_batna=power.get("their_BATNA", ""),
            priorities=priorities,
            quick_wins=quick_wins,
            deal_breakers=parsed.get("deal_breakers", []),
            trading_chips=chips,
            negotiation_sequence=parsed.get("negotiation_sequence", []),
            psychological_tactics=parsed.get("psychological_tactics", []),
            raw_analysis=raw_response
        )


class LegalAdvisorAgent(BaseAgent):
    """Agent #4: Expert Legal Counsel"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.agent_name = "Legal Advisor"
        self.role = "Expert Legal Counsel"
        self.expertise = "Contract law, regulatory compliance, legal precedents, jurisdictional issues"
        self.personality = "Careful, thorough, precedent-focused, protective"
        
    def analyze(self, contract_text: str, risk_assessment: RiskAssessment,
                jurisdiction: str = "United States", industry: str = "General") -> LegalAdvisory:
        """Provide legal context and compliance analysis"""
        
        system_prompt = f"""You are an {self.role} with expertise in {self.expertise}.
Your personality: {self.personality}

You provide legal context, flag compliance issues, cite precedents, assess enforceability, and highlight legal implications.

Your job is to protect the client from legal landmines they wouldn't see coming.

ALWAYS respond with structured JSON."""

        prompt = f"""You are outside legal counsel reviewing this contract.

JURISDICTION: {jurisdiction}
INDUSTRY: {industry}
RISK LEVEL: {risk_assessment.overall_level} (Score: {risk_assessment.overall_score}/100)

CONTRACT TEXT:
{contract_text[:12000]}

Provide comprehensive legal analysis as JSON:
{{
    "legal_opinion_summary": {{
        "overall_assessment": "Generally enforceable with notable exceptions",
        "major_concerns": 3,
        "compliance_issues": 2,
        "enforceability_risks": 4,
        "recommended_legal_review": true
    }},
    "compliance_analysis": [
        {{
            "issue": "Issue description",
            "jurisdiction": "{jurisdiction}",
            "requirement": "What the law requires",
            "contract_provision": "What contract says",
            "compliance_status": "COMPLIANT | NON_COMPLIANT | NEEDS_REVIEW",
            "risk": "What could happen",
            "recommendation": "How to fix",
            "severity": "HIGH | MEDIUM | LOW"
        }}
    ],
    "enforceability_concerns": [
        {{
            "clause": "Section reference",
            "issue": "Why it's problematic",
            "legal_principle": "Applicable law",
            "contract_language": "Actual text",
            "concern": "Specific concern",
            "precedent": "Relevant case law",
            "likelihood_struck_down": "HIGH | MEDIUM | LOW",
            "recommendation": "How to fix"
        }}
    ],
    "legal_precedents": [
        {{
            "clause_type": "Type of clause",
            "case_citation": "Case Name (Year)",
            "principle": "Legal principle established",
            "application": "How it applies here",
            "implication": "What it means for you"
        }}
    ],
    "statutory_waivers": [
        {{
            "waived_right": "Right being waived",
            "statute": "Applicable statute",
            "enforceability": "Whether enforceable",
            "recommendation": "Advice",
            "alternative": "Better approach"
        }}
    ],
    "ambiguities": [
        {{
            "location": "Section reference",
            "language": "Problematic text",
            "issue": "Why it's ambiguous",
            "legal_rule": "How courts handle this",
            "risk": "Potential consequence",
            "recommendation": "How to clarify"
        }}
    ],
    "missing_standard_clauses": [
        "Force majeure clause",
        "Severability clause"
    ]
}}

Use plain language but cite relevant statutes, regulations, and case law where applicable."""

        raw_response = self._call_llm(prompt, system_prompt)
        parsed = self._extract_json(raw_response)
        
        summary = parsed.get("legal_opinion_summary", {})
        
        # Parse compliance issues
        compliance = []
        for c in parsed.get("compliance_analysis", []):
            compliance.append(ComplianceIssue(
                issue=c.get("issue", ""),
                jurisdiction=c.get("jurisdiction", jurisdiction),
                requirement=c.get("requirement", ""),
                contract_provision=c.get("contract_provision", ""),
                compliance_status=c.get("compliance_status", "NEEDS_REVIEW"),
                risk=c.get("risk", ""),
                recommendation=c.get("recommendation", ""),
                severity=c.get("severity", "MEDIUM")
            ))
        
        # Parse enforceability concerns
        enforceability = []
        for e in parsed.get("enforceability_concerns", []):
            enforceability.append(EnforceabilityConcern(
                clause=e.get("clause", ""),
                issue=e.get("issue", ""),
                legal_principle=e.get("legal_principle", ""),
                contract_language=e.get("contract_language", ""),
                concern=e.get("concern", ""),
                precedent=e.get("precedent", ""),
                likelihood_struck_down=e.get("likelihood_struck_down", "MEDIUM"),
                recommendation=e.get("recommendation", "")
            ))
        
        # Parse precedents
        precedents = []
        for p in parsed.get("legal_precedents", []):
            precedents.append(LegalPrecedent(
                clause_type=p.get("clause_type", ""),
                case_citation=p.get("case_citation", ""),
                principle=p.get("principle", ""),
                application=p.get("application", ""),
                implication=p.get("implication", "")
            ))
        
        # Parse waivers
        waivers = []
        for w in parsed.get("statutory_waivers", []):
            waivers.append(StatutoryWaiver(
                waived_right=w.get("waived_right", ""),
                statute=w.get("statute", ""),
                enforceability=w.get("enforceability", ""),
                recommendation=w.get("recommendation", ""),
                alternative=w.get("alternative", "")
            ))
        
        # Parse ambiguities
        ambiguities = []
        for a in parsed.get("ambiguities", []):
            ambiguities.append(Ambiguity(
                location=a.get("location", ""),
                language=a.get("language", ""),
                issue=a.get("issue", ""),
                legal_rule=a.get("legal_rule", ""),
                risk=a.get("risk", ""),
                recommendation=a.get("recommendation", "")
            ))
        
        return LegalAdvisory(
            overall_assessment=summary.get("overall_assessment", "Review required"),
            major_concerns_count=summary.get("major_concerns", 0),
            compliance_issues_count=summary.get("compliance_issues", 0),
            enforceability_risks_count=summary.get("enforceability_risks", 0),
            recommended_legal_review=summary.get("recommended_legal_review", True),
            compliance_issues=compliance,
            enforceability_concerns=enforceability,
            legal_precedents=precedents,
            statutory_waivers=waivers,
            ambiguities=ambiguities,
            missing_clauses=parsed.get("missing_standard_clauses", []),
            raw_analysis=raw_response
        )


class MarketResearcherAgent(BaseAgent):
    """Agent #5: Market Intelligence Specialist"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.agent_name = "Market Researcher"
        self.role = "Market Intelligence Specialist"
        self.expertise = "Industry standards, competitive benchmarking, market trends, pricing analysis"
        self.personality = "Data-driven, objective, pragmatic, business-focused"
        
    def analyze(self, contract_text: str, document_analysis: DocumentAnalysis,
                industry: str = "Technology", contract_value: str = "Not specified") -> MarketResearch:
        """Compare terms against market standards"""
        
        system_prompt = f"""You are a {self.role} with expertise in {self.expertise}.
Your personality: {self.personality}

You compare contract terms against market standards, provide competitive intelligence, benchmark pricing and terms, and assess relative favorability.

Your goal: Give the negotiator ammunition with market data.

ALWAYS respond with structured JSON."""

        prompt = f"""You are preparing a market intelligence assessment.

DOCUMENT TYPE: {document_analysis.document_type}
INDUSTRY: {industry}
ESTIMATED CONTRACT VALUE: {contract_value}

KEY TERMS TO BENCHMARK:
{chr(10).join([f"- {c.clause_type}: {c.summary}" for c in document_analysis.key_clauses[:10]])}

CONTRACT TEXT:
{contract_text[:10000]}

Provide market research analysis as JSON:
{{
    "market_context": {{
        "industry": "{industry}",
        "contract_type": "{document_analysis.document_type}",
        "typical_contract_value": "$50K-$150K annually",
        "market_conditions": "Description of current market"
    }},
    "benchmark_comparisons": [
        {{
            "term_category": "Payment Terms",
            "this_contract": "What this contract says",
            "market_standard": "What market typically does (with %)",
            "percentile": "Where this falls (e.g., '25th percentile')",
            "assessment": "FAVORABLE | NEUTRAL | UNFAVORABLE | FAR_BELOW_MARKET",
            "impact": "Business impact",
            "data_source": "Source of benchmark data",
            "recommendation": "What to negotiate for"
        }}
    ],
    "pricing_analysis": {{
        "quoted_price": "Price if mentioned",
        "market_range": "$X - $Y",
        "percentile": "Where this falls",
        "assessment": "Pricing assessment",
        "value_indicators": {{
            "scope_appropriate": true,
            "premium_justified": "Yes/No with reason",
            "negotiation_room": "Estimated %"
        }}
    }},
    "competitive_intelligence": [
        {{
            "competitor": "Competitor name or 'Typical provider'",
            "their_standard_terms": "What they offer",
            "advantage_they_have": "Where they're better",
            "advantage_you_have": "Where you're better",
            "negotiation_angle": "How to use this"
        }}
    ],
    "industry_trends": [
        "Trend 1",
        "Trend 2"
    ],
    "overall_market_assessment": {{
        "favorability_score": 45,
        "interpretation": "Explanation of score",
        "summary": "Overall assessment paragraph"
    }}
}}

Use percentages and data points. "Here's what the market does, here's where you're getting a raw deal."""

        raw_response = self._call_llm(prompt, system_prompt, temperature=0.3)
        parsed = self._extract_json(raw_response)
        
        context = parsed.get("market_context", {})
        
        # Parse benchmarks
        benchmarks = []
        for b in parsed.get("benchmark_comparisons", []):
            benchmarks.append(BenchmarkComparison(
                term_category=b.get("term_category", ""),
                this_contract=b.get("this_contract", ""),
                market_standard=b.get("market_standard", ""),
                percentile=b.get("percentile", ""),
                assessment=b.get("assessment", "NEUTRAL"),
                impact=b.get("impact", ""),
                data_source=b.get("data_source", ""),
                recommendation=b.get("recommendation", ""),
                negotiation_leverage=b.get("negotiation_leverage", "")
            ))
        
        # Parse pricing
        pricing_data = parsed.get("pricing_analysis", {})
        pricing = PricingAnalysis(
            quoted_price=pricing_data.get("quoted_price", "Not specified"),
            market_range=pricing_data.get("market_range", "Unknown"),
            percentile=pricing_data.get("percentile", "Unknown"),
            assessment=pricing_data.get("assessment", ""),
            value_indicators=pricing_data.get("value_indicators", {})
        )
        
        # Parse competitive intel
        competitors = []
        for c in parsed.get("competitive_intelligence", []):
            competitors.append(CompetitorIntel(
                competitor=c.get("competitor", ""),
                their_standard_terms=c.get("their_standard_terms", ""),
                advantage_they_have=c.get("advantage_they_have", ""),
                advantage_you_have=c.get("advantage_you_have", ""),
                negotiation_angle=c.get("negotiation_angle", "")
            ))
        
        overall = parsed.get("overall_market_assessment", {})
        
        return MarketResearch(
            industry=context.get("industry", industry),
            contract_type=context.get("contract_type", document_analysis.document_type),
            typical_contract_value=context.get("typical_contract_value", "Unknown"),
            market_conditions=context.get("market_conditions", ""),
            benchmark_comparisons=benchmarks,
            pricing_analysis=pricing,
            competitive_intelligence=competitors,
            industry_trends=parsed.get("industry_trends", []),
            overall_favorability_score=overall.get("favorability_score", 50),
            overall_interpretation=overall.get("interpretation", ""),
            raw_analysis=raw_response
        )


class ContractOptimizerAgent(BaseAgent):
    """Agent #6: Contract Optimization Specialist & Chief Synthesizer"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.agent_name = "Contract Optimizer"
        self.role = "Contract Optimization Specialist & Chief Synthesizer"
        self.expertise = "Integration, prioritization, strategic planning, executive communication"
        self.personality = "Big-picture thinker, synthesizer, decisive, action-oriented"
        
    def synthesize(self, document_analysis: DocumentAnalysis, risk_assessment: RiskAssessment,
                   negotiation_strategy: NegotiationStrategy, legal_advisory: LegalAdvisory,
                   market_research: MarketResearch) -> ContractOptimization:
        """Synthesize all agent insights into actionable strategy"""
        
        system_prompt = f"""You are a {self.role} with expertise in {self.expertise}.
Your personality: {self.personality}

You synthesize findings from 5 specialist agents, prioritize recommendations, create actionable strategies, and produce executive summaries.

Your goal: Create a clear, prioritized action plan that anyone can follow to negotiate successfully.

ALWAYS respond with structured JSON."""

        # Build comprehensive summary from all agents
        summary = f"""
=== DOCUMENT ANALYSIS ===
Type: {document_analysis.document_type}
Parties: {', '.join([p.name for p in document_analysis.parties])}
Total Clauses: {document_analysis.clause_summary.get('total_clauses', 'Unknown')}
Structural Issues: {len(document_analysis.structural_issues)}

=== RISK ASSESSMENT ===
Overall Score: {risk_assessment.overall_score}/100 ({risk_assessment.overall_level})
Critical Risks: {risk_assessment.critical_count}
High Risks: {risk_assessment.high_count}
Top Issues: {', '.join([r.clause for r in risk_assessment.critical_risks[:3]])}

=== NEGOTIATION STRATEGY ===
Power Balance: {negotiation_strategy.power_balance}/10
Deal Breakers: {len(negotiation_strategy.deal_breakers)}
Quick Wins: {len(negotiation_strategy.quick_wins)}
Priority Items: {len(negotiation_strategy.priorities)}

=== LEGAL ADVISORY ===
Assessment: {legal_advisory.overall_assessment}
Compliance Issues: {legal_advisory.compliance_issues_count}
Enforceability Concerns: {legal_advisory.enforceability_risks_count}
Recommended Legal Review: {legal_advisory.recommended_legal_review}

=== MARKET RESEARCH ===
Market Favorability: {market_research.overall_favorability_score}/100
{market_research.overall_interpretation}
"""

        prompt = f"""Synthesize all specialist agent findings into a unified negotiation strategy.

AGENT FINDINGS:
{summary}

KEY RISKS (from Risk Assessor):
{chr(10).join([f"• {r.clause}: {r.description} (Severity: {r.severity})" for r in risk_assessment.critical_risks[:5]])}

NEGOTIATION PRIORITIES (from Strategist):
{chr(10).join([f"• {p.issue}: {p.strategy}" for p in negotiation_strategy.priorities[:5]])}

LEGAL CONCERNS (from Legal Advisor):
{chr(10).join([f"• {c.clause}: {c.issue}" for c in legal_advisory.enforceability_concerns[:3]])}

MARKET GAPS (from Market Researcher):
{chr(10).join([f"• {b.term_category}: {b.assessment}" for b in market_research.benchmark_comparisons[:5] if b.assessment in ['UNFAVORABLE', 'FAR_BELOW_MARKET']])}

Create a comprehensive synthesis as JSON:
{{
    "executive_summary": {{
        "overall_assessment": "HIGH RISK CONTRACT - Requires significant negotiation",
        "recommendation": "PROCEED WITH CAUTION | NEGOTIATE FIRST | DO NOT SIGN | ACCEPTABLE",
        "confidence_level": "High | Medium | Low",
        "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
        "estimated_success_rate": "75%",
        "recommended_timeline": "2-3 weeks"
    }},
    "critical_decisions": [
        {{
            "decision": "Question to answer",
            "recommendation": "What to do",
            "rationale": "Why",
            "alternative": "If they refuse",
            "business_impact": "What's at stake",
            "decision_maker": "Who should decide"
        }}
    ],
    "negotiation_roadmap": {{
        "phase_1_critical": [
            {{
                "rank": 1,
                "issue": "Issue name",
                "current": "Current position",
                "target": "Goal",
                "minimum": "Walk-away",
                "priority": "CRITICAL",
                "strategy": "Approach",
                "success_likelihood": "Medium",
                "talking_points": ["Point 1", "Point 2"],
                "if_rejected": "What to do"
            }}
        ],
        "phase_2_high_priority": [],
        "phase_3_optimization": []
    }},
    "success_metrics": ["Metric 1", "Metric 2"],
    "risk_mitigation_summary": "Summary of how identified risks are addressed",
    "next_steps": ["Step 1", "Step 2", "Step 3"]
}}

Be decisive. Prioritize ruthlessly. Create a playbook that leads to successful negotiation."""

        raw_response = self._call_llm(prompt, system_prompt, temperature=0.3)
        parsed = self._extract_json(raw_response)
        
        summary = parsed.get("executive_summary", {})
        roadmap = parsed.get("negotiation_roadmap", {})
        
        # Parse critical decisions
        decisions = []
        for d in parsed.get("critical_decisions", []):
            decisions.append(CriticalDecision(
                decision=d.get("decision", ""),
                recommendation=d.get("recommendation", ""),
                rationale=d.get("rationale", ""),
                alternative=d.get("alternative", ""),
                business_impact=d.get("business_impact", ""),
                decision_maker=d.get("decision_maker", "")
            ))
        
        # Parse roadmap phases
        def parse_roadmap_items(items_data):
            items = []
            for item in items_data:
                items.append(RoadmapItem(
                    rank=item.get("rank", len(items) + 1),
                    issue=item.get("issue", ""),
                    current=item.get("current", ""),
                    target=item.get("target", ""),
                    minimum=item.get("minimum", ""),
                    priority=item.get("priority", "MEDIUM"),
                    strategy=item.get("strategy", ""),
                    success_likelihood=item.get("success_likelihood", "Medium"),
                    talking_points=item.get("talking_points", []),
                    if_rejected=item.get("if_rejected", ""),
                    if_accepted=item.get("if_accepted", "")
                ))
            return items
        
        return ContractOptimization(
            overall_assessment=summary.get("overall_assessment", "Analysis complete"),
            recommendation=summary.get("recommendation", "REVIEW REQUIRED"),
            confidence_level=summary.get("confidence_level", "Medium"),
            key_insights=summary.get("key_insights", []),
            estimated_success_rate=summary.get("estimated_success_rate", "Unknown"),
            recommended_timeline=summary.get("recommended_timeline", "1-2 weeks"),
            critical_decisions=decisions,
            phase_1_critical=parse_roadmap_items(roadmap.get("phase_1_critical", [])),
            phase_2_high_priority=parse_roadmap_items(roadmap.get("phase_2_high_priority", [])),
            phase_3_optimization=parse_roadmap_items(roadmap.get("phase_3_optimization", [])),
            success_metrics=parsed.get("success_metrics", []),
            risk_mitigation_summary=parsed.get("risk_mitigation_summary", ""),
            next_steps=parsed.get("next_steps", []),
            raw_analysis=raw_response
        )
