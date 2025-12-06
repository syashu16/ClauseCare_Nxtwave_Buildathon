"""
Risk Assessment Engine

Main orchestrator for the complete risk assessment workflow.
Coordinates fast scanning, AI analysis, scoring, and visualization.
"""

import time
import re
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import (
    RiskCategory,
    SeverityLevel,
    ClauseRisk,
    DocumentRisk,
    QuickScanResult,
    Recommendation,
)
from .keyword_library import KeywordLibrary
from .fast_scanner import FastScanner
from .ai_analyzer import AIAnalyzer, AnalysisContext
from .risk_scorer import RiskScorer
from .document_aggregator import DocumentAggregator
from .visualizations import RiskVisualizer


@dataclass
class ProgressCallback:
    """Callback for progress updates during analysis"""
    on_start: Optional[Callable[[str], None]] = None
    on_progress: Optional[Callable[[int, int, str], None]] = None  # current, total, message
    on_complete: Optional[Callable[[str], None]] = None


class RiskAssessmentEngine:
    """
    Main orchestrator for legal document risk assessment.
    
    Workflow:
    1. Fast Scan (< 1 second) - Keyword matching
    2. Deep Analysis (2-10 seconds per clause) - AI-powered
    3. Scoring & Aggregation - Calculate final scores
    4. Visualization - Generate charts and reports
    
    Usage:
        engine = RiskAssessmentEngine(api_key="your_groq_key")
        result = engine.analyze_document(document_text)
        
        # Get visualizations
        dashboard = engine.get_dashboard(result)
        
        # Export report
        markdown = engine.export_markdown_report(result)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        use_ai: bool = True,
        parallel_analysis: bool = True,
        max_workers: int = 4,
    ):
        """
        Initialize the Risk Assessment Engine.
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
            use_ai: Whether to use AI for deep analysis
            parallel_analysis: Whether to analyze clauses in parallel
            max_workers: Number of parallel workers for AI analysis
        """
        self.keyword_library = KeywordLibrary()
        self.fast_scanner = FastScanner(self.keyword_library)
        self.ai_analyzer = AIAnalyzer(api_key) if use_ai else None
        self.risk_scorer = RiskScorer()
        self.aggregator = DocumentAggregator(self.risk_scorer)
        self.visualizer = RiskVisualizer()
        
        self.use_ai = use_ai
        self.parallel_analysis = parallel_analysis
        self.max_workers = max_workers
    
    def analyze_document(
        self,
        text: str,
        filename: str = "document",
        context: Optional[AnalysisContext] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> DocumentRisk:
        """
        Perform complete risk assessment on a document.
        
        Args:
            text: Full document text
            filename: Document filename
            context: Analysis context (document type, user role, etc.)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete DocumentRisk assessment
        """
        start_time = time.time()
        context = context or AnalysisContext()
        
        # Notify start
        if progress_callback and progress_callback.on_start:
            progress_callback.on_start("Starting risk assessment...")
        
        # Step 1: Fast Scan
        if progress_callback and progress_callback.on_progress:
            progress_callback.on_progress(0, 100, "Scanning for risk patterns...")
        
        quick_scan = self.fast_scanner.scan_document(text)
        
        if progress_callback and progress_callback.on_progress:
            progress_callback.on_progress(
                10, 100, 
                f"Found {quick_scan.total_matches} potential issues. Analyzing clauses..."
            )
        
        # Step 2: Extract clauses
        clauses = self._extract_clauses(text)
        
        # Step 3: Analyze each clause
        clause_risks = []
        total_clauses = len(clauses)
        
        if self.use_ai and self.ai_analyzer and self.parallel_analysis:
            # Parallel AI analysis
            clause_risks = self._analyze_clauses_parallel(
                clauses, context, quick_scan, progress_callback, total_clauses
            )
        else:
            # Sequential analysis
            clause_risks = self._analyze_clauses_sequential(
                clauses, context, quick_scan, progress_callback, total_clauses
            )
        
        # Step 4: Generate AI summary if available
        ai_summary = None
        if self.use_ai and self.ai_analyzer and clause_risks:
            if progress_callback and progress_callback.on_progress:
                progress_callback.on_progress(90, 100, "Generating summary...")
            
            try:
                ai_summary = self.ai_analyzer.generate_document_summary(clause_risks, context)
            except Exception:
                ai_summary = None
        
        # Step 5: Aggregate results
        if progress_callback and progress_callback.on_progress:
            progress_callback.on_progress(95, 100, "Finalizing report...")
        
        processing_time = time.time() - start_time
        pages = max(1, len(text) // 3000)  # Estimate pages
        
        document_risk = self.aggregator.aggregate(
            clause_risks=clause_risks,
            filename=filename,
            pages=pages,
            processing_time=processing_time,
            ai_summary=ai_summary,
        )
        
        # Notify completion
        if progress_callback and progress_callback.on_complete:
            progress_callback.on_complete(
                f"Analysis complete. Overall risk: {document_risk.risk_summary.overall_level.value}"
            )
        
        return document_risk
    
    def quick_scan(self, text: str) -> QuickScanResult:
        """
        Perform only the fast scan (no AI analysis).
        
        Args:
            text: Document text
            
        Returns:
            QuickScanResult with immediate findings
        """
        return self.fast_scanner.scan_document(text)
    
    def analyze_clause(
        self,
        clause_text: str,
        context: Optional[AnalysisContext] = None,
    ) -> ClauseRisk:
        """
        Analyze a single clause.
        
        Args:
            clause_text: The clause text
            context: Analysis context
            
        Returns:
            ClauseRisk assessment
        """
        context = context or AnalysisContext()
        clause_id = "single_clause"
        
        # Fast scan
        scan_result = self.fast_scanner.scan_clause(clause_id, clause_text)
        
        # Deep analysis if AI available
        if self.use_ai and self.ai_analyzer:
            try:
                return self.ai_analyzer.analyze_clause(
                    clause_id,
                    clause_text,
                    context,
                    scan_result.keyword_matches,
                )
            except Exception:
                pass
        
        # Fallback to rule-based
        return self._rule_based_clause_analysis(clause_id, clause_text, scan_result)
    
    def get_dashboard(self, document_risk: DocumentRisk) -> dict:
        """
        Generate dashboard visualization data.
        
        Args:
            document_risk: Document risk assessment
            
        Returns:
            Dict with visualization data and figures
        """
        return self.visualizer.create_dashboard(document_risk)
    
    def get_risk_gauge(self, score: int, title: str = "Risk Score"):
        """Get a risk gauge visualization"""
        return self.visualizer.create_risk_gauge(score, title)
    
    def get_heatmap(self, text: str, scan_result: QuickScanResult) -> dict:
        """Get heatmap data for document visualization"""
        return self.visualizer.create_heatmap(text, scan_result)
    
    def get_recommendations(self, document_risk: DocumentRisk) -> list[Recommendation]:
        """Get structured recommendations from analysis"""
        return self.aggregator.generate_recommendations(document_risk)
    
    def export_markdown_report(self, document_risk: DocumentRisk) -> str:
        """Export analysis as markdown report"""
        return self.aggregator.to_markdown_report(document_risk)
    
    def export_json(self, document_risk: DocumentRisk) -> dict:
        """Export analysis as JSON"""
        return self.aggregator.to_json(document_risk)
    
    def _extract_clauses(self, text: str) -> list[tuple[str, str]]:
        """
        Extract individual clauses from document text.
        
        Returns:
            List of (clause_id, clause_text) tuples
        """
        clauses = []
        
        # Strategy 1: Look for numbered sections
        section_pattern = r'(?:^|\n)(\d+(?:\.\d+)*\.?\s*[A-Z][^.]*?[.:])'
        
        # Strategy 2: Split by paragraph for simpler documents
        paragraphs = text.split('\n\n')
        
        # Try to identify section headers
        section_headers = list(re.finditer(section_pattern, text, re.MULTILINE))
        
        if len(section_headers) >= 3:
            # Document has section structure
            for i, match in enumerate(section_headers):
                start = match.end()
                end = section_headers[i + 1].start() if i + 1 < len(section_headers) else len(text)
                
                clause_id = f"section_{i + 1}"
                header = match.group(1).strip()
                content = text[start:end].strip()
                
                if len(content) > 30:  # Skip very short sections
                    clauses.append((clause_id, f"{header}\n{content}"))
        else:
            # Fall back to paragraph splitting
            for i, para in enumerate(paragraphs):
                para = para.strip()
                if len(para) > 50:  # Skip short paragraphs
                    clause_id = f"paragraph_{i + 1}"
                    clauses.append((clause_id, para))
        
        # If still no clauses, treat entire document as one
        if not clauses:
            clauses.append(("full_document", text))
        
        return clauses
    
    def _analyze_clauses_parallel(
        self,
        clauses: list[tuple[str, str]],
        context: AnalysisContext,
        quick_scan: QuickScanResult,
        progress_callback: Optional[ProgressCallback],
        total_clauses: int,
    ) -> list[ClauseRisk]:
        """Analyze clauses in parallel using ThreadPoolExecutor"""
        clause_risks = []
        completed = 0
        
        # Build keyword matches map
        keyword_map = self._build_keyword_map(clauses, quick_scan)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for clause_id, clause_text in clauses:
                # Check if clause has keywords (prioritize for AI analysis)
                has_keywords = clause_id in keyword_map
                
                if has_keywords and self.ai_analyzer:
                    future = executor.submit(
                        self.ai_analyzer.analyze_clause,
                        clause_id,
                        clause_text,
                        context,
                        keyword_map.get(clause_id, []),
                    )
                else:
                    scan_result = self.fast_scanner.scan_clause(clause_id, clause_text)
                    future = executor.submit(
                        self._rule_based_clause_analysis,
                        clause_id,
                        clause_text,
                        scan_result,
                    )
                
                futures[future] = clause_id
            
            for future in as_completed(futures):
                try:
                    risk = future.result()
                    clause_risks.append(risk)
                except Exception as e:
                    # Create fallback risk on failure
                    clause_id = futures[future]
                    clause_text = next(ct for cid, ct in clauses if cid == clause_id)
                    scan_result = self.fast_scanner.scan_clause(clause_id, clause_text)
                    risk = self._rule_based_clause_analysis(clause_id, clause_text, scan_result)
                    clause_risks.append(risk)
                
                completed += 1
                if progress_callback and progress_callback.on_progress:
                    progress = 10 + int(80 * completed / total_clauses)
                    progress_callback.on_progress(
                        progress, 100,
                        f"Analyzed {completed}/{total_clauses} clauses..."
                    )
        
        # Sort by original order
        clause_order = {cid: i for i, (cid, _) in enumerate(clauses)}
        clause_risks.sort(key=lambda r: clause_order.get(r.clause_id, 999))
        
        return clause_risks
    
    def _analyze_clauses_sequential(
        self,
        clauses: list[tuple[str, str]],
        context: AnalysisContext,
        quick_scan: QuickScanResult,
        progress_callback: Optional[ProgressCallback],
        total_clauses: int,
    ) -> list[ClauseRisk]:
        """Analyze clauses sequentially"""
        clause_risks = []
        keyword_map = self._build_keyword_map(clauses, quick_scan)
        
        for i, (clause_id, clause_text) in enumerate(clauses):
            has_keywords = clause_id in keyword_map
            
            if has_keywords and self.use_ai and self.ai_analyzer:
                try:
                    risk = self.ai_analyzer.analyze_clause(
                        clause_id,
                        clause_text,
                        context,
                        keyword_map.get(clause_id, []),
                    )
                except Exception:
                    scan_result = self.fast_scanner.scan_clause(clause_id, clause_text)
                    risk = self._rule_based_clause_analysis(clause_id, clause_text, scan_result)
            else:
                scan_result = self.fast_scanner.scan_clause(clause_id, clause_text)
                risk = self._rule_based_clause_analysis(clause_id, clause_text, scan_result)
            
            clause_risks.append(risk)
            
            if progress_callback and progress_callback.on_progress:
                progress = 10 + int(80 * (i + 1) / total_clauses)
                progress_callback.on_progress(
                    progress, 100,
                    f"Analyzed {i + 1}/{total_clauses} clauses..."
                )
        
        return clause_risks
    
    def _build_keyword_map(
        self,
        clauses: list[tuple[str, str]],
        quick_scan: QuickScanResult,
    ) -> dict:
        """Map keyword matches to their respective clauses"""
        keyword_map = {}
        
        # This is a simplified mapping - in production, would use
        # actual character positions to map keywords to clauses
        for clause_id, clause_text in clauses:
            clause_keywords = []
            for km in quick_scan.keyword_matches:
                # Check if keyword appears in this clause
                if km.keyword.lower() in clause_text.lower():
                    clause_keywords.append(km)
            
            if clause_keywords:
                keyword_map[clause_id] = clause_keywords
        
        return keyword_map
    
    def _rule_based_clause_analysis(
        self,
        clause_id: str,
        clause_text: str,
        scan_result,
    ) -> ClauseRisk:
        """Perform rule-based clause analysis without AI"""
        
        # Calculate score
        score, factors = self.risk_scorer.calculate_score(
            clause_text,
            scan_result.keyword_matches,
            context_multiplier=1.0,
        )
        
        # Determine category from keyword matches
        if scan_result.keyword_matches:
            category_counts = {}
            for km in scan_result.keyword_matches:
                category_counts[km.category] = category_counts.get(km.category, 0) + km.weight
            
            category = max(category_counts.keys(), key=lambda c: category_counts[c])
        else:
            category = RiskCategory.UNKNOWN
        
        severity = SeverityLevel.from_score(score)
        confidence = self.risk_scorer.calculate_confidence(
            scan_result.keyword_matches,
            clause_text,
            ai_analyzed=False,
        )
        
        # Determine clause type
        clause_type = self._infer_clause_type(clause_text, category)
        
        # Generate explanation
        if scan_result.red_flags:
            primary_risk = f"Detected {len(scan_result.red_flags)} red flag(s): {scan_result.red_flags[0].description}"
        elif scan_result.keyword_matches:
            primary_risk = f"Contains {category.value.replace('_', ' ')} related terms requiring review"
        else:
            primary_risk = "Standard clause with minimal detected risk"
        
        # Generate recommendation
        if severity == SeverityLevel.CRITICAL:
            recommendation = "Have legal counsel review immediately. Consider rejecting or significantly revising."
        elif severity == SeverityLevel.HIGH:
            recommendation = "Negotiate changes to this clause before signing."
        elif severity == SeverityLevel.MEDIUM:
            recommendation = "Review carefully and consider negotiating."
        else:
            recommendation = "Clause appears standard. Review for completeness."
        
        return ClauseRisk(
            clause_id=clause_id,
            clause_text=clause_text,
            clause_type=clause_type,
            category=category,
            severity=severity,
            score=score,
            confidence=confidence,
            primary_risk=primary_risk,
            detailed_explanation=f"Risk score of {score}/100 based on {len(scan_result.keyword_matches)} keyword matches. {factors.final_score}",
            specific_concerns=[rf.description for rf in scan_result.red_flags[:5]],
            impact_if_triggered="Potential adverse terms if clause is enforced",
            likelihood="MEDIUM",
            recommendation=recommendation,
            red_flags=[rf.phrase for rf in scan_result.red_flags],
            keyword_matches=scan_result.keyword_matches,
            ai_analyzed=False,
            analysis_timestamp=datetime.now(),
        )
    
    def _infer_clause_type(self, clause_text: str, category: RiskCategory) -> str:
        """Infer the type of clause from text and category"""
        text_lower = clause_text.lower()
        
        type_keywords = {
            "indemnification": ["indemnif", "hold harmless"],
            "liability": ["liabilit", "liable", "damages"],
            "termination": ["terminat", "cancel", "expir"],
            "confidentiality": ["confidential", "nda", "non-disclosure"],
            "intellectual_property": ["intellectual property", "patent", "copyright", "trademark", "ip rights"],
            "warranty": ["warrant", "guarantee"],
            "payment": ["payment", "fee", "price", "invoice"],
            "insurance": ["insurance", "insured"],
            "force_majeure": ["force majeure", "act of god"],
            "dispute_resolution": ["arbitrat", "mediat", "jurisdiction", "governing law"],
            "non_compete": ["non-compete", "non-competition", "compete"],
            "assignment": ["assign", "transfer"],
        }
        
        for clause_type, keywords in type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return clause_type
        
        # Fall back to category
        return category.value if category != RiskCategory.UNKNOWN else "general"


# Convenience function for quick analysis
def analyze_contract(
    text: str,
    api_key: Optional[str] = None,
    use_ai: bool = True,
) -> DocumentRisk:
    """
    Convenience function for quick contract analysis.
    
    Args:
        text: Contract text
        api_key: Groq API key (optional if env var set)
        use_ai: Whether to use AI analysis
        
    Returns:
        DocumentRisk assessment
    """
    engine = RiskAssessmentEngine(api_key=api_key, use_ai=use_ai)
    return engine.analyze_document(text)
