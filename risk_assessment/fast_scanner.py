"""
Fast Rule-Based Scanner

Layer 1 of the risk assessment system.
Performs sub-second scanning of documents for known high-risk keywords and patterns.
"""

import time
from dataclasses import dataclass
from collections import defaultdict

from .models import (
    RiskCategory,
    SeverityLevel,
    KeywordMatch,
    RedFlag,
    QuickScanResult,
)
from .keyword_library import KeywordLibrary


@dataclass
class ClauseScanResult:
    """Scan result for a single clause"""
    clause_id: str
    clause_text: str
    keyword_matches: list[KeywordMatch]
    red_flags: list[RedFlag]
    category_scores: dict[RiskCategory, float]
    estimated_severity: SeverityLevel
    needs_deep_analysis: bool


class FastScanner:
    """
    Fast rule-based scanner for immediate risk detection.
    
    Features:
    - Scans entire document in < 1 second
    - Pattern matching for dangerous clause structures
    - Immediate red flags for critical issues
    - Generates quick risk heatmap
    """
    
    # Critical phrases that always trigger red flags
    CRITICAL_PHRASES = [
        ("unlimited liability", RiskCategory.LEGAL_LIABILITY),
        ("waives all rights", RiskCategory.LEGAL_LIABILITY),
        ("irrevocable", RiskCategory.TERMINATION),
        ("perpetual", RiskCategory.TERMINATION),
        ("assigns all right, title, and interest", RiskCategory.INTELLECTUAL_PROPERTY),
        ("exclusive, perpetual, worldwide", RiskCategory.INTELLECTUAL_PROPERTY),
        ("waive data protection", RiskCategory.CONFIDENTIALITY),
        ("personal guarantee", RiskCategory.LEGAL_LIABILITY),
        ("sole discretion", RiskCategory.OPERATIONAL),
        ("without limitation", RiskCategory.FINANCIAL),
        ("no right to terminate", RiskCategory.TERMINATION),
        ("strict liability", RiskCategory.COMPLIANCE),
    ]
    
    # Structural patterns that indicate high risk
    DANGEROUS_PATTERNS = [
        # One-sided language patterns
        r"\b(?:you|party\s+a|customer|licensee|user)\s+(?:shall|must|will|agrees?\s+to)\s+(?:indemnify|hold\s+harmless)",
        # Broad scope language
        r"\b(?:any\s+and\s+all|all\s+and\s+any)\s+(?:claims?|damages?|losses?|liabilities?)",
        # Unlimited scope
        r"\bwithout\s+(?:limit(?:ation)?|exception|restriction)\b",
        # Mandatory arbitration with distant venue
        r"\b(?:binding\s+)?arbitration.*(?:in|at)\s+(?:Singapore|Hong\s+Kong|London|Switzerland)",
        # No cure period
        r"\bimmediate\s+termination\s+(?:without|with\s+no)\s+(?:cure|notice)",
    ]
    
    def __init__(self, keyword_library: KeywordLibrary = None):
        self.keyword_library = keyword_library or KeywordLibrary()
        self._compile_dangerous_patterns()
    
    def _compile_dangerous_patterns(self):
        """Compile dangerous patterns for efficient matching"""
        import re
        self._compiled_dangerous = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.DANGEROUS_PATTERNS
        ]
    
    def scan_document(self, text: str) -> QuickScanResult:
        """
        Perform fast scan of entire document.
        
        Args:
            text: Full document text
            
        Returns:
            QuickScanResult with detected issues
        """
        start_time = time.perf_counter()
        
        keyword_matches = []
        red_flags = []
        category_counts = defaultdict(int)
        
        # Step 1: Scan for all keywords
        all_matches = self.keyword_library.search_all(text)
        
        for category, matches in all_matches.items():
            for keyword_entry, positions in matches:
                for start, end, matched_text in positions:
                    # Get context around the match
                    context = self.keyword_library.get_context(text, start, end)
                    
                    keyword_match = KeywordMatch(
                        keyword=keyword_entry.pattern,
                        category=category,
                        weight=keyword_entry.weight,
                        position=(start, end),
                        context=context,
                    )
                    keyword_matches.append(keyword_match)
                    category_counts[category] += 1
                    
                    # Check if this is a critical phrase (red flag)
                    if keyword_entry.weight >= 2.5:
                        red_flag = RedFlag(
                            phrase=matched_text,
                            category=category,
                            weight=keyword_entry.weight,
                            position=(start, end),
                            description=keyword_entry.description,
                        )
                        red_flags.append(red_flag)
        
        # Step 2: Check for dangerous structural patterns
        for pattern in self._compiled_dangerous:
            for match in pattern.finditer(text):
                # Determine category based on pattern content
                category = self._categorize_pattern_match(match.group())
                red_flag = RedFlag(
                    phrase=match.group()[:100],  # Truncate long matches
                    category=category,
                    weight=3.0,
                    position=(match.start(), match.end()),
                    description="Dangerous structural pattern detected",
                )
                red_flags.append(red_flag)
        
        # Step 3: Check for critical phrases
        text_lower = text.lower()
        for phrase, category in self.CRITICAL_PHRASES:
            if phrase.lower() in text_lower:
                # Already counted in keyword matches, just ensure flagged
                pass
        
        # Calculate estimated risk level
        total_weight = sum(km.weight for km in keyword_matches)
        critical_count = len([rf for rf in red_flags if rf.weight >= 3.0])
        
        if critical_count >= 3 or total_weight > 50:
            estimated_level = SeverityLevel.CRITICAL
        elif critical_count >= 1 or total_weight > 30:
            estimated_level = SeverityLevel.HIGH
        elif total_weight > 15:
            estimated_level = SeverityLevel.MEDIUM
        else:
            estimated_level = SeverityLevel.LOW
        
        # Identify clauses needing deep analysis
        clauses_to_analyze = self._identify_clauses_for_deep_analysis(
            keyword_matches, red_flags, text
        )
        
        processing_time = (time.perf_counter() - start_time) * 1000  # ms
        
        return QuickScanResult(
            total_matches=len(keyword_matches),
            keyword_matches=keyword_matches,
            red_flags=red_flags,
            category_counts=dict(category_counts),
            estimated_risk_level=estimated_level,
            clauses_to_deep_analyze=clauses_to_analyze,
            processing_time_ms=processing_time,
        )
    
    def scan_clause(self, clause_id: str, clause_text: str) -> ClauseScanResult:
        """
        Scan a single clause for risk indicators.
        
        Args:
            clause_id: Unique identifier for the clause
            clause_text: The clause text to analyze
            
        Returns:
            ClauseScanResult with detailed clause analysis
        """
        keyword_matches = []
        red_flags = []
        category_scores = defaultdict(float)
        
        # Search for keywords
        all_matches = self.keyword_library.search_all(clause_text)
        
        for category, matches in all_matches.items():
            for keyword_entry, positions in matches:
                for start, end, matched_text in positions:
                    context = self.keyword_library.get_context(clause_text, start, end, 50)
                    
                    keyword_match = KeywordMatch(
                        keyword=keyword_entry.pattern,
                        category=category,
                        weight=keyword_entry.weight,
                        position=(start, end),
                        context=context,
                    )
                    keyword_matches.append(keyword_match)
                    category_scores[category] += keyword_entry.weight
                    
                    if keyword_entry.weight >= 2.5:
                        red_flag = RedFlag(
                            phrase=matched_text,
                            category=category,
                            weight=keyword_entry.weight,
                            position=(start, end),
                            description=keyword_entry.description,
                        )
                        red_flags.append(red_flag)
        
        # Check dangerous patterns
        for pattern in self._compiled_dangerous:
            for match in pattern.finditer(clause_text):
                category = self._categorize_pattern_match(match.group())
                red_flag = RedFlag(
                    phrase=match.group()[:100],
                    category=category,
                    weight=3.0,
                    position=(match.start(), match.end()),
                    description="Dangerous structural pattern",
                )
                red_flags.append(red_flag)
                category_scores[category] += 3.0
        
        # Calculate clause severity
        total_weight = sum(category_scores.values())
        has_critical = any(rf.weight >= 3.0 for rf in red_flags)
        
        if has_critical or total_weight > 10:
            severity = SeverityLevel.CRITICAL if has_critical else SeverityLevel.HIGH
            needs_deep = True
        elif total_weight > 5:
            severity = SeverityLevel.MEDIUM
            needs_deep = True
        elif total_weight > 2:
            severity = SeverityLevel.MEDIUM
            needs_deep = len(keyword_matches) > 0
        else:
            severity = SeverityLevel.LOW
            needs_deep = len(red_flags) > 0
        
        return ClauseScanResult(
            clause_id=clause_id,
            clause_text=clause_text,
            keyword_matches=keyword_matches,
            red_flags=red_flags,
            category_scores=dict(category_scores),
            estimated_severity=severity,
            needs_deep_analysis=needs_deep,
        )
    
    def _categorize_pattern_match(self, matched_text: str) -> RiskCategory:
        """Determine the risk category for a pattern match"""
        text_lower = matched_text.lower()
        
        if any(word in text_lower for word in ['indemnify', 'hold harmless', 'liable', 'liability']):
            return RiskCategory.LEGAL_LIABILITY
        elif any(word in text_lower for word in ['arbitration', 'jurisdiction', 'venue', 'court']):
            return RiskCategory.DISPUTE_RESOLUTION
        elif any(word in text_lower for word in ['terminate', 'termination', 'cancel']):
            return RiskCategory.TERMINATION
        elif any(word in text_lower for word in ['damage', 'claim', 'loss']):
            return RiskCategory.FINANCIAL
        else:
            return RiskCategory.OPERATIONAL
    
    def _identify_clauses_for_deep_analysis(
        self,
        keyword_matches: list[KeywordMatch],
        red_flags: list[RedFlag],
        full_text: str
    ) -> list[str]:
        """
        Identify which parts of the document need deep AI analysis.
        Returns list of text segments or clause identifiers.
        """
        # Group matches by approximate location (paragraph boundaries)
        paragraphs = full_text.split('\n\n')
        clauses_to_analyze = []
        
        char_position = 0
        for i, para in enumerate(paragraphs):
            para_start = char_position
            para_end = char_position + len(para)
            
            # Check if any matches fall in this paragraph
            has_match = any(
                para_start <= km.position[0] < para_end
                for km in keyword_matches
            ) or any(
                para_start <= rf.position[0] < para_end
                for rf in red_flags
            )
            
            if has_match and len(para.strip()) > 20:  # Skip very short paragraphs
                clauses_to_analyze.append(f"paragraph_{i}")
            
            char_position = para_end + 2  # Account for \n\n
        
        return clauses_to_analyze
    
    def generate_heatmap_data(self, text: str, scan_result: QuickScanResult) -> list[dict]:
        """
        Generate data for risk heatmap visualization.
        
        Returns list of dicts with position, severity, and category info.
        """
        heatmap_data = []
        
        # Process all keyword matches
        for km in scan_result.keyword_matches:
            heatmap_data.append({
                'start': km.position[0],
                'end': km.position[1],
                'category': km.category.value,
                'severity': self._weight_to_severity(km.weight).value,
                'weight': km.weight,
                'keyword': km.keyword,
                'is_red_flag': km.weight >= 2.5,
            })
        
        # Add red flag positions
        for rf in scan_result.red_flags:
            # Check if already added via keyword match
            already_added = any(
                h['start'] == rf.position[0] and h['end'] == rf.position[1]
                for h in heatmap_data
            )
            if not already_added:
                heatmap_data.append({
                    'start': rf.position[0],
                    'end': rf.position[1],
                    'category': rf.category.value,
                    'severity': 'CRITICAL' if rf.weight >= 3.0 else 'HIGH',
                    'weight': rf.weight,
                    'keyword': rf.phrase,
                    'is_red_flag': True,
                })
        
        # Sort by position
        heatmap_data.sort(key=lambda x: x['start'])
        
        return heatmap_data
    
    def _weight_to_severity(self, weight: float) -> SeverityLevel:
        """Convert keyword weight to severity level"""
        if weight >= 2.5:
            return SeverityLevel.CRITICAL
        elif weight >= 2.0:
            return SeverityLevel.HIGH
        elif weight >= 1.5:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def get_summary_stats(self, scan_result: QuickScanResult) -> dict:
        """Generate summary statistics from scan result"""
        severity_counts = defaultdict(int)
        for km in scan_result.keyword_matches:
            severity = self._weight_to_severity(km.weight)
            severity_counts[severity.value] += 1
        
        return {
            'total_matches': scan_result.total_matches,
            'red_flag_count': len(scan_result.red_flags),
            'categories_affected': len(scan_result.category_counts),
            'severity_distribution': dict(severity_counts),
            'estimated_risk': scan_result.estimated_risk_level.value,
            'processing_time_ms': round(scan_result.processing_time_ms, 2),
            'needs_deep_analysis_count': len(scan_result.clauses_to_deep_analyze),
            'category_breakdown': {
                cat.value: count
                for cat, count in scan_result.category_counts.items()
            },
        }
