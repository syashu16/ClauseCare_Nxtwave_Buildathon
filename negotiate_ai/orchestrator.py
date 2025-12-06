"""
NegotiateAI Orchestrator
========================

Coordinates all 6 agents to produce a comprehensive negotiation playbook.
Manages the workflow, timing, and agent interactions.
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from .models import NegotiationPlaybook, AgentOutput
from .agents import (
    DocumentAnalyzerAgent,
    RiskAssessorAgent,
    NegotiationStrategistAgent,
    LegalAdvisorAgent,
    MarketResearcherAgent,
    ContractOptimizerAgent
)


@dataclass
class OrchestrationProgress:
    """Track orchestration progress"""
    current_agent: str = ""
    current_step: int = 0
    total_steps: int = 6
    status: str = "pending"
    message: str = ""
    elapsed_time: float = 0.0


class NegotiateAIOrchestrator:
    """
    Orchestrates the 6-agent NegotiateAI system.
    
    Workflow:
    1. Document Analyzer → Extracts structure and clauses
    2. Risk Assessor → Identifies and scores risks (uses #1)
    3. Negotiation Strategist → Develops tactics (uses #1, #2)
    4. Legal Advisor → Provides legal context (uses #2)
    5. Market Researcher → Benchmarks terms (uses #1)
    6. Contract Optimizer → Synthesizes all (uses #1-5)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
        # Initialize all agents
        self.document_analyzer = DocumentAnalyzerAgent(api_key)
        self.risk_assessor = RiskAssessorAgent(api_key)
        self.negotiation_strategist = NegotiationStrategistAgent(api_key)
        self.legal_advisor = LegalAdvisorAgent(api_key)
        self.market_researcher = MarketResearcherAgent(api_key)
        self.contract_optimizer = ContractOptimizerAgent(api_key)
        
        # Progress tracking
        self.progress = OrchestrationProgress()
        self.agent_outputs: Dict[str, AgentOutput] = {}
        
    def _update_progress(self, agent_name: str, step: int, status: str, message: str):
        """Update progress tracking"""
        self.progress.current_agent = agent_name
        self.progress.current_step = step
        self.progress.status = status
        self.progress.message = message
        
    def run_full_analysis(
        self,
        contract_text: str,
        document_name: str = "Contract",
        context: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[OrchestrationProgress], None]] = None
    ) -> NegotiationPlaybook:
        """
        Run the complete 6-agent analysis pipeline.
        
        Args:
            contract_text: Full text of the contract
            document_name: Name of the document for reference
            context: Additional context (industry, jurisdiction, etc.)
            progress_callback: Optional callback for progress updates
            
        Returns:
            NegotiationPlaybook with all agent analyses
        """
        context = context or {}
        start_time = time.time()
        
        def report_progress(agent: str, step: int, status: str, msg: str):
            self._update_progress(agent, step, status, msg)
            self.progress.elapsed_time = time.time() - start_time
            if progress_callback:
                progress_callback(self.progress)
        
        # ===== AGENT 1: Document Analyzer =====
        report_progress("Document Analyzer", 1, "running", "Analyzing contract structure...")
        agent1_start = time.time()
        
        try:
            document_analysis = self.document_analyzer.analyze(contract_text)
            self.agent_outputs["document_analyzer"] = AgentOutput(
                agent_name="Document Analyzer",
                status="success",
                execution_time=time.time() - agent1_start,
                output=document_analysis,
                raw_response=document_analysis.raw_analysis
            )
            report_progress("Document Analyzer", 1, "complete", 
                          f"Found {document_analysis.clause_summary.get('total_clauses', 0)} clauses")
        except Exception as e:
            report_progress("Document Analyzer", 1, "error", str(e))
            raise
        
        # ===== AGENT 2: Risk Assessor =====
        report_progress("Risk Assessor", 2, "running", "Evaluating contract risks...")
        agent2_start = time.time()
        
        try:
            risk_assessment = self.risk_assessor.analyze(contract_text, document_analysis)
            self.agent_outputs["risk_assessor"] = AgentOutput(
                agent_name="Risk Assessor",
                status="success",
                execution_time=time.time() - agent2_start,
                output=risk_assessment,
                raw_response=risk_assessment.raw_analysis
            )
            report_progress("Risk Assessor", 2, "complete",
                          f"Risk Score: {risk_assessment.overall_score}/100 ({risk_assessment.overall_level})")
        except Exception as e:
            report_progress("Risk Assessor", 2, "error", str(e))
            raise
        
        # ===== AGENT 3: Negotiation Strategist =====
        report_progress("Negotiation Strategist", 3, "running", "Developing negotiation strategy...")
        agent3_start = time.time()
        
        try:
            negotiation_strategy = self.negotiation_strategist.analyze(
                contract_text, document_analysis, risk_assessment, context
            )
            self.agent_outputs["negotiation_strategist"] = AgentOutput(
                agent_name="Negotiation Strategist",
                status="success",
                execution_time=time.time() - agent3_start,
                output=negotiation_strategy,
                raw_response=negotiation_strategy.raw_analysis
            )
            report_progress("Negotiation Strategist", 3, "complete",
                          f"Identified {len(negotiation_strategy.priorities)} priority items")
        except Exception as e:
            report_progress("Negotiation Strategist", 3, "error", str(e))
            raise
        
        # ===== AGENT 4: Legal Advisor =====
        report_progress("Legal Advisor", 4, "running", "Reviewing legal compliance...")
        agent4_start = time.time()
        
        try:
            legal_advisory = self.legal_advisor.analyze(
                contract_text, 
                risk_assessment,
                jurisdiction=context.get("jurisdiction", "United States"),
                industry=context.get("industry", "General")
            )
            self.agent_outputs["legal_advisor"] = AgentOutput(
                agent_name="Legal Advisor",
                status="success",
                execution_time=time.time() - agent4_start,
                output=legal_advisory,
                raw_response=legal_advisory.raw_analysis
            )
            report_progress("Legal Advisor", 4, "complete",
                          f"Found {legal_advisory.compliance_issues_count} compliance issues")
        except Exception as e:
            report_progress("Legal Advisor", 4, "error", str(e))
            raise
        
        # ===== AGENT 5: Market Researcher =====
        report_progress("Market Researcher", 5, "running", "Benchmarking against market...")
        agent5_start = time.time()
        
        try:
            market_research = self.market_researcher.analyze(
                contract_text,
                document_analysis,
                industry=context.get("industry", "Technology"),
                contract_value=context.get("contract_value", "Not specified")
            )
            self.agent_outputs["market_researcher"] = AgentOutput(
                agent_name="Market Researcher",
                status="success",
                execution_time=time.time() - agent5_start,
                output=market_research,
                raw_response=market_research.raw_analysis
            )
            report_progress("Market Researcher", 5, "complete",
                          f"Market Score: {market_research.overall_favorability_score}/100")
        except Exception as e:
            report_progress("Market Researcher", 5, "error", str(e))
            raise
        
        # ===== AGENT 6: Contract Optimizer (Synthesizer) =====
        report_progress("Contract Optimizer", 6, "running", "Synthesizing recommendations...")
        agent6_start = time.time()
        
        try:
            optimization = self.contract_optimizer.synthesize(
                document_analysis,
                risk_assessment,
                negotiation_strategy,
                legal_advisory,
                market_research
            )
            self.agent_outputs["contract_optimizer"] = AgentOutput(
                agent_name="Contract Optimizer",
                status="success",
                execution_time=time.time() - agent6_start,
                output=optimization,
                raw_response=optimization.raw_analysis
            )
            report_progress("Contract Optimizer", 6, "complete",
                          f"Strategy: {optimization.recommendation}")
        except Exception as e:
            report_progress("Contract Optimizer", 6, "error", str(e))
            raise
        
        # ===== BUILD FINAL PLAYBOOK =====
        total_time = time.time() - start_time
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            document_analysis, risk_assessment, negotiation_strategy,
            legal_advisory, market_research, optimization
        )
        
        playbook = NegotiationPlaybook(
            timestamp=datetime.now().isoformat(),
            document_name=document_name,
            document_analysis=document_analysis,
            risk_assessment=risk_assessment,
            negotiation_strategy=negotiation_strategy,
            legal_advisory=legal_advisory,
            market_research=market_research,
            optimization=optimization,
            executive_summary=executive_summary
        )
        
        report_progress("Complete", 6, "complete", 
                       f"Analysis complete in {total_time:.1f}s")
        
        return playbook
    
    def _generate_executive_summary(self, doc, risk, strategy, legal, market, opt) -> str:
        """Generate a human-readable executive summary"""
        
        summary = f"""
# NEGOTIATION INTELLIGENCE REPORT

## Document: {doc.document_type}
**Parties:** {', '.join([p.name + ' (' + p.role + ')' for p in doc.parties])}

---

## 🎯 BOTTOM LINE

**Overall Assessment:** {opt.overall_assessment}

**Recommendation:** {opt.recommendation}

**Estimated Negotiation Success Rate:** {opt.estimated_success_rate}

---

## ⚠️ RISK PROFILE

| Metric | Value |
|--------|-------|
| Risk Score | {risk.overall_score}/100 |
| Risk Level | {risk.overall_level} |
| Critical Issues | {risk.critical_count} |
| High-Priority Issues | {risk.high_count} |

**Top Critical Risks:**
"""
        for r in risk.critical_risks[:3]:
            summary += f"\n- **{r.clause}**: {r.description}"
        
        summary += f"""

---

## 💪 POWER DYNAMICS

**Balance Score:** {strategy.power_balance}/10 {'(In your favor)' if strategy.power_balance > 0 else '(Against you)' if strategy.power_balance < 0 else '(Neutral)'}

**Factors in Your Favor:**
"""
        for f in strategy.factors_in_favor[:3]:
            summary += f"\n- {f}"
        
        summary += """

**Factors Against You:**
"""
        for f in strategy.factors_against[:3]:
            summary += f"\n- {f}"
        
        summary += f"""

---

## 📊 MARKET POSITION

**Market Favorability:** {market.overall_favorability_score}/100

**Key Market Gaps:**
"""
        unfavorable = [b for b in market.benchmark_comparisons if b.assessment in ['UNFAVORABLE', 'FAR_BELOW_MARKET']]
        for b in unfavorable[:3]:
            summary += f"\n- **{b.term_category}**: {b.this_contract} vs Market: {b.market_standard}"
        
        summary += f"""

---

## ⚖️ LEGAL CONCERNS

**Assessment:** {legal.overall_assessment}
**Compliance Issues:** {legal.compliance_issues_count}
**Enforceability Risks:** {legal.enforceability_risks_count}
**Recommended Legal Review:** {'Yes' if legal.recommended_legal_review else 'No'}

---

## 🎮 NEGOTIATION STRATEGY

### Phase 1: Critical Issues (Must Address)
"""
        for item in opt.phase_1_critical[:3]:
            summary += f"\n**{item.rank}. {item.issue}**\n"
            summary += f"   - Current: {item.current}\n"
            summary += f"   - Target: {item.target}\n"
            summary += f"   - Strategy: {item.strategy}\n"
        
        summary += """

### Quick Wins (High Success Probability)
"""
        for qw in strategy.quick_wins[:3]:
            summary += f"\n- **{qw.issue}**: {qw.script}"
        
        summary += f"""

### Deal Breakers
"""
        for db in strategy.deal_breakers[:5]:
            summary += f"\n- ❌ {db}"
        
        summary += f"""

---

## 📋 NEXT STEPS

"""
        for i, step in enumerate(opt.next_steps[:5], 1):
            summary += f"{i}. {step}\n"
        
        summary += f"""

---

*Analysis generated by NegotiateAI Multi-Agent System*
*Confidence Level: {opt.confidence_level}*
*Recommended Timeline: {opt.recommended_timeline}*
"""
        
        return summary
    
    def run_single_agent(
        self,
        agent_name: str,
        contract_text: str,
        **kwargs
    ) -> AgentOutput:
        """Run a single agent for targeted analysis"""
        
        start_time = time.time()
        
        agents = {
            "document_analyzer": self.document_analyzer,
            "risk_assessor": self.risk_assessor,
            "negotiation_strategist": self.negotiation_strategist,
            "legal_advisor": self.legal_advisor,
            "market_researcher": self.market_researcher,
            "contract_optimizer": self.contract_optimizer
        }
        
        agent = agents.get(agent_name.lower().replace(" ", "_"))
        if not agent:
            return AgentOutput(
                agent_name=agent_name,
                status="error",
                execution_time=0,
                output=None,
                error_message=f"Unknown agent: {agent_name}"
            )
        
        try:
            if agent_name == "document_analyzer":
                result = agent.analyze(contract_text)
            elif agent_name == "risk_assessor":
                doc_analysis = kwargs.get("document_analysis")
                if not doc_analysis:
                    doc_analysis = self.document_analyzer.analyze(contract_text)
                result = agent.analyze(contract_text, doc_analysis)
            else:
                result = agent.analyze(contract_text, **kwargs)
            
            return AgentOutput(
                agent_name=agent.agent_name,
                status="success",
                execution_time=time.time() - start_time,
                output=result,
                raw_response=getattr(result, 'raw_analysis', '')
            )
        except Exception as e:
            return AgentOutput(
                agent_name=agent.agent_name,
                status="error",
                execution_time=time.time() - start_time,
                output=None,
                error_message=str(e)
            )
    
    def get_agent_timing(self) -> Dict[str, float]:
        """Get execution time for each agent"""
        return {
            name: output.execution_time 
            for name, output in self.agent_outputs.items()
        }
    
    def get_total_time(self) -> float:
        """Get total orchestration time"""
        return self.progress.elapsed_time
