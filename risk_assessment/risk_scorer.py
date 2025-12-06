"""
Risk Scoring System

Calculates risk scores using a sophisticated formula that considers:
- Keyword matches and their weights
- Clause complexity indicators
- Presence of qualifiers and caps
- Context multipliers from AI analysis
"""

from dataclasses import dataclass
from typing import Optional
import re
import math

from .models import (
    RiskCategory,
    SeverityLevel,
    ClauseRisk,
    KeywordMatch,
)


@dataclass
class ScoringFactors:
    """Factors that influence the risk score"""
    base_keyword_score: float = 0.0
    clause_length_modifier: float = 0.0
    obligation_count_modifier: float = 0.0
    qualifier_modifier: float = 0.0
    cap_modifier: float = 0.0
    mutual_language_modifier: float = 0.0
    standard_term_modifier: float = 0.0
    context_multiplier: float = 1.0
    final_score: int = 0


class RiskScorer:
    """
    Sophisticated risk scoring system.
    
    Score Calculation Formula:
    Base Score = Σ (Keyword Matches × Weight)
    
    Modifiers:
    + Clause length (longer = potentially more complex)
    + Number of "shall" (mandatory obligations)
    + Presence of qualifiers (e.g., "reasonable", "good faith")
    - Presence of caps/limits
    - Mutual/reciprocal language
    - Standard industry terms
    
    Context Multiplier (from AI analysis):
    × 0.5 = Standard industry practice
    × 1.0 = Neutral/typical
    × 1.5 = Unfavorable but negotiable
    × 2.0 = Highly unfavorable/unusual
    
    Final Score = (Base Score × Context Multiplier) capped at 100
    """
    
    # Positive modifiers (reduce risk)
    POSITIVE_QUALIFIERS = [
        "reasonable", "reasonably", "good faith", "mutual", "mutually",
        "reciprocal", "balanced", "fair", "proportionate", "customary",
        "standard", "industry standard", "commercially reasonable",
    ]
    
    CAP_INDICATORS = [
        "capped at", "not to exceed", "maximum", "cap of", "limited to",
        "up to", "ceiling", "no more than", "aggregate limit",
        r"\$\d+(?:,\d{3})*(?:\.\d{2})?", r"\d+\s*(?:times|x)\s*(?:the|annual|monthly)",
    ]
    
    MUTUAL_LANGUAGE = [
        "mutual", "mutually", "reciprocal", "both parties", "each party",
        "either party", "the parties", "jointly", "together",
    ]
    
    STANDARD_TERMS = [
        "net-30", "net 30", "net-60", "30 days", "60 days",
        "force majeure", "act of god", "commercially reasonable efforts",
        "material breach", "cure period", "good standing",
    ]
    
    # Negative modifiers (increase risk)
    OBLIGATION_MARKERS = [
        "shall", "must", "will", "agrees to", "undertakes to",
        "obligated to", "required to", "bound to", "warranted",
    ]
    
    EXTREME_LANGUAGE = [
        "unlimited", "without limit", "without limitation", "no cap",
        "sole discretion", "absolute", "irrevocable", "perpetual",
        "unconditional", "in any event", "under any circumstances",
    ]
    
    ONE_SIDED_MARKERS = [
        "at its option", "in its sole judgment", "without recourse",
        "waives all rights", "releases all claims", "holds harmless",
    ]
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        def compile_list(items):
            patterns = []
            for item in items:
                if item.startswith(r'\$') or item.startswith(r'\d'):
                    patterns.append(re.compile(item, re.IGNORECASE))
                else:
                    patterns.append(re.compile(r'\b' + re.escape(item) + r'\b', re.IGNORECASE))
            return patterns
        
        self._positive_patterns = compile_list(self.POSITIVE_QUALIFIERS)
        self._cap_patterns = compile_list(self.CAP_INDICATORS)
        self._mutual_patterns = compile_list(self.MUTUAL_LANGUAGE)
        self._standard_patterns = compile_list(self.STANDARD_TERMS)
        self._obligation_patterns = compile_list(self.OBLIGATION_MARKERS)
        self._extreme_patterns = compile_list(self.EXTREME_LANGUAGE)
        self._one_sided_patterns = compile_list(self.ONE_SIDED_MARKERS)
    
    def calculate_score(
        self,
        clause_text: str,
        keyword_matches: list[KeywordMatch],
        context_multiplier: float = 1.0,
        ai_score: Optional[int] = None,
    ) -> tuple[int, ScoringFactors]:
        """
        Calculate the risk score for a clause.
        
        Args:
            clause_text: The clause text
            keyword_matches: Detected keyword matches
            context_multiplier: AI-determined context multiplier (0.5-2.0)
            ai_score: Optional AI-suggested score to blend with rule-based
            
        Returns:
            Tuple of (final_score, scoring_factors)
        """
        factors = ScoringFactors()
        
        # 1. Base keyword score
        factors.base_keyword_score = self._calculate_base_score(keyword_matches)
        
        # 2. Clause length modifier (+0 to +10)
        factors.clause_length_modifier = self._calculate_length_modifier(clause_text)
        
        # 3. Obligation count modifier (+0 to +15)
        factors.obligation_count_modifier = self._calculate_obligation_modifier(clause_text)
        
        # 4. Extreme language modifier (+0 to +20)
        extreme_modifier = self._calculate_extreme_modifier(clause_text)
        
        # 5. One-sided language modifier (+0 to +15)
        one_sided_modifier = self._calculate_one_sided_modifier(clause_text)
        
        # 6. Positive qualifier modifier (-0 to -10)
        factors.qualifier_modifier = self._calculate_qualifier_modifier(clause_text)
        
        # 7. Cap/limit modifier (-0 to -15)
        factors.cap_modifier = self._calculate_cap_modifier(clause_text)
        
        # 8. Mutual language modifier (-0 to -10)
        factors.mutual_language_modifier = self._calculate_mutual_modifier(clause_text)
        
        # 9. Standard term modifier (-0 to -10)
        factors.standard_term_modifier = self._calculate_standard_modifier(clause_text)
        
        # Calculate pre-context score
        pre_context_score = (
            factors.base_keyword_score +
            factors.clause_length_modifier +
            factors.obligation_count_modifier +
            extreme_modifier +
            one_sided_modifier +
            factors.qualifier_modifier +  # Negative value
            factors.cap_modifier +  # Negative value
            factors.mutual_language_modifier +  # Negative value
            factors.standard_term_modifier  # Negative value
        )
        
        # Apply context multiplier
        factors.context_multiplier = max(0.5, min(2.0, context_multiplier))
        contextualized_score = pre_context_score * factors.context_multiplier
        
        # Blend with AI score if available
        if ai_score is not None:
            # Weight AI score more heavily (60-40 blend)
            final_score = (ai_score * 0.6) + (contextualized_score * 0.4)
        else:
            final_score = contextualized_score
        
        # Clamp to 0-100
        factors.final_score = max(0, min(100, int(round(final_score))))
        
        return factors.final_score, factors
    
    def _calculate_base_score(self, keyword_matches: list[KeywordMatch]) -> float:
        """Calculate base score from keyword weights"""
        if not keyword_matches:
            return 0.0
        
        # Sum of weights, with diminishing returns for many matches
        total_weight = sum(km.weight for km in keyword_matches)
        
        # Apply diminishing returns: score = weight * (1 - e^(-0.1 * count))
        count_factor = 1 - math.exp(-0.15 * len(keyword_matches))
        
        # Base score scales with total weight, capped contribution
        base = min(50, total_weight * 8 * count_factor)
        
        return base
    
    def _calculate_length_modifier(self, text: str) -> float:
        """Longer clauses may hide complexity"""
        word_count = len(text.split())
        
        if word_count < 50:
            return 0  # Short clause
        elif word_count < 100:
            return 3
        elif word_count < 200:
            return 5
        elif word_count < 400:
            return 8
        else:
            return 10  # Very long clause
    
    def _calculate_obligation_modifier(self, text: str) -> float:
        """Count mandatory obligation markers"""
        count = sum(1 for p in self._obligation_patterns if p.search(text))
        
        if count <= 1:
            return 0
        elif count <= 3:
            return 5
        elif count <= 5:
            return 10
        else:
            return 15
    
    def _calculate_extreme_modifier(self, text: str) -> float:
        """Check for extreme language"""
        count = sum(1 for p in self._extreme_patterns if p.search(text))
        
        if count == 0:
            return 0
        elif count == 1:
            return 8
        elif count == 2:
            return 15
        else:
            return 20
    
    def _calculate_one_sided_modifier(self, text: str) -> float:
        """Check for one-sided language"""
        count = sum(1 for p in self._one_sided_patterns if p.search(text))
        
        if count == 0:
            return 0
        elif count == 1:
            return 7
        else:
            return 15
    
    def _calculate_qualifier_modifier(self, text: str) -> float:
        """Check for positive qualifiers (reduces risk)"""
        count = sum(1 for p in self._positive_patterns if p.search(text))
        
        if count == 0:
            return 0
        elif count == 1:
            return -3
        elif count == 2:
            return -6
        else:
            return -10
    
    def _calculate_cap_modifier(self, text: str) -> float:
        """Check for caps/limits (reduces risk)"""
        count = sum(1 for p in self._cap_patterns if p.search(text))
        
        if count == 0:
            return 0
        elif count == 1:
            return -8
        elif count == 2:
            return -12
        else:
            return -15
    
    def _calculate_mutual_modifier(self, text: str) -> float:
        """Check for mutual/reciprocal language (reduces risk)"""
        count = sum(1 for p in self._mutual_patterns if p.search(text))
        
        if count == 0:
            return 0
        elif count == 1:
            return -4
        elif count == 2:
            return -7
        else:
            return -10
    
    def _calculate_standard_modifier(self, text: str) -> float:
        """Check for standard industry terms (reduces risk)"""
        count = sum(1 for p in self._standard_patterns if p.search(text))
        
        if count == 0:
            return 0
        elif count == 1:
            return -4
        elif count == 2:
            return -7
        else:
            return -10
    
    def determine_context_multiplier(
        self,
        ai_assessment: Optional[str] = None,
        industry: str = "general",
        clause_type: str = "general",
    ) -> float:
        """
        Determine the context multiplier based on AI assessment.
        
        Multiplier values:
        0.5 = Standard industry practice
        1.0 = Neutral/typical
        1.5 = Unfavorable but negotiable
        2.0 = Highly unfavorable/unusual
        """
        if ai_assessment:
            assessment_lower = ai_assessment.lower()
            
            if any(word in assessment_lower for word in ["standard", "typical", "normal", "common"]):
                return 0.5
            elif any(word in assessment_lower for word in ["unusual", "uncommon", "aggressive"]):
                return 1.5
            elif any(word in assessment_lower for word in ["extreme", "dangerous", "highly unfavorable"]):
                return 2.0
        
        # Default multipliers by clause type
        type_multipliers = {
            "indemnification": 1.2,
            "liability": 1.2,
            "termination": 1.0,
            "intellectual_property": 1.3,
            "confidentiality": 1.0,
            "non-compete": 1.3,
            "arbitration": 1.1,
            "warranty": 1.0,
        }
        
        return type_multipliers.get(clause_type.lower(), 1.0)
    
    def get_severity_from_score(self, score: int) -> SeverityLevel:
        """
        Determine severity level from risk score.
        
        0-30: LOW - Standard clauses, minimal risk
        31-60: MEDIUM - Worth reviewing, some concerns
        61-85: HIGH - Significant issues, negotiate before signing
        86-100: CRITICAL - Dangerous, may be deal-breaker
        """
        return SeverityLevel.from_score(score)
    
    def calculate_confidence(
        self,
        keyword_matches: list[KeywordMatch],
        clause_text: str,
        ai_analyzed: bool = False,
    ) -> int:
        """
        Calculate confidence score for the risk assessment.
        
        90-100%: Clear red flag, unambiguous
        70-89%: Strong indicators, context-dependent
        50-69%: Possible issue, needs expert review
        < 50%: Unclear, insufficient information
        """
        base_confidence = 50  # Start at neutral
        
        # More keyword matches = higher confidence
        if len(keyword_matches) >= 3:
            base_confidence += 15
        elif len(keyword_matches) >= 1:
            base_confidence += 8
        
        # High-weight keywords = higher confidence
        high_weight_count = sum(1 for km in keyword_matches if km.weight >= 2.5)
        base_confidence += min(15, high_weight_count * 5)
        
        # AI analysis boosts confidence
        if ai_analyzed:
            base_confidence += 15
        
        # Longer clauses may have more context
        word_count = len(clause_text.split())
        if word_count >= 50:
            base_confidence += 5
        
        # Clear red flag phrases boost confidence
        extreme_count = sum(1 for p in self._extreme_patterns if p.search(clause_text))
        if extreme_count > 0:
            base_confidence += 10
        
        return min(100, max(20, base_confidence))
    
    def explain_score(self, factors: ScoringFactors) -> str:
        """Generate human-readable explanation of score calculation"""
        parts = []
        
        parts.append(f"Base keyword score: {factors.base_keyword_score:.1f}")
        
        if factors.clause_length_modifier > 0:
            parts.append(f"Clause complexity: +{factors.clause_length_modifier:.1f}")
        
        if factors.obligation_count_modifier > 0:
            parts.append(f"Obligation markers: +{factors.obligation_count_modifier:.1f}")
        
        if factors.qualifier_modifier < 0:
            parts.append(f"Positive qualifiers: {factors.qualifier_modifier:.1f}")
        
        if factors.cap_modifier < 0:
            parts.append(f"Caps/limits present: {factors.cap_modifier:.1f}")
        
        if factors.mutual_language_modifier < 0:
            parts.append(f"Mutual language: {factors.mutual_language_modifier:.1f}")
        
        if factors.standard_term_modifier < 0:
            parts.append(f"Standard terms: {factors.standard_term_modifier:.1f}")
        
        if factors.context_multiplier != 1.0:
            parts.append(f"Context multiplier: ×{factors.context_multiplier:.1f}")
        
        parts.append(f"Final score: {factors.final_score}")
        
        return " | ".join(parts)
    
    def calculate_document_score(self, clause_scores: list[int]) -> int:
        """
        Calculate overall document risk score from clause scores.
        
        Uses weighted average that emphasizes high-risk clauses.
        """
        if not clause_scores:
            return 0
        
        # Weight by severity - high scores count more
        weighted_scores = []
        for score in clause_scores:
            if score >= 85:
                weight = 3.0
            elif score >= 60:
                weight = 2.0
            elif score >= 30:
                weight = 1.0
            else:
                weight = 0.5
            weighted_scores.append((score, weight))
        
        total_weight = sum(w for _, w in weighted_scores)
        weighted_sum = sum(s * w for s, w in weighted_scores)
        
        # Also factor in the maximum score
        max_score = max(clause_scores)
        avg_weighted = weighted_sum / total_weight
        
        # Blend: 60% weighted average, 40% max score influence
        final = (avg_weighted * 0.6) + (max_score * 0.4)
        
        return min(100, int(round(final)))
