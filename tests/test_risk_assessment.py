"""
Test Suite for Risk Assessment Module

Contains test cases for:
- Extremely unfavorable contracts
- Balanced contracts
- Highly favorable contracts
- Ambiguous contracts
"""

import unittest
from datetime import datetime

from risk_assessment import (
    RiskAssessmentEngine,
    RiskCategory,
    SeverityLevel,
    KeywordLibrary,
    FastScanner,
    RiskScorer,
    DocumentAggregator,
)
from risk_assessment.ai_analyzer import AnalysisContext


# ============ SAMPLE CONTRACTS ============

EXTREMELY_UNFAVORABLE_CONTRACT = """
SERVICE AGREEMENT

1. INDEMNIFICATION
The Customer shall indemnify and hold harmless the Provider, its officers, directors, employees, 
and agents from and against any and all claims, damages, losses, liabilities, costs, and expenses 
(including reasonable attorneys' fees) arising from or related to Customer's use of the Services. 
This indemnification shall be unlimited and irrevocable.

2. LIMITATION OF LIABILITY
TO THE FULLEST EXTENT PERMITTED BY LAW, PROVIDER SHALL NOT BE LIABLE FOR ANY CONSEQUENTIAL, 
INCIDENTAL, INDIRECT, SPECIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOST PROFITS, 
LOST REVENUE, OR LOST DATA. Customer waives all claims against Provider regardless of negligence.

3. INTELLECTUAL PROPERTY
Customer hereby assigns all right, title, and interest in and to any and all intellectual property, 
including future developments, created in connection with this Agreement. Customer waives all moral 
rights and agrees this is a work made for hire. Provider receives an exclusive, perpetual, worldwide, 
irrevocable license to use all Customer materials.

4. TERMINATION
This Agreement shall automatically renew for successive one-year periods unless terminated by Provider 
in its sole discretion. Customer may not terminate for convenience and has no right to terminate 
except upon material breach by Provider, which Provider may cure indefinitely. Termination fee equal 
to 100% of remaining term fees shall apply.

5. CONFIDENTIALITY
Customer's confidential information shall be kept confidential in perpetuity. Provider may share 
Customer information with affiliates without notice and has no obligation to return any materials. 
Provider waives no data protection obligations.

6. DISPUTE RESOLUTION
All disputes shall be resolved through binding arbitration in Singapore under ICC rules. Customer 
waives right to jury trial and waives class action rights. Each party bears own costs but Customer 
shall pay all Provider legal fees if Provider prevails. Loser pays all costs.

7. COMPLIANCE
Customer shall be strictly liable for all regulatory violations regardless of fault. Customer shall 
obtain all necessary permits at own expense and is subject to unlimited audit at any time.

8. FEES
All fees are non-refundable. Provider may adjust fees at any time in its sole discretion. 
Penalties compound daily at 18% interest. No cap on damages applies.
"""


BALANCED_CONTRACT = """
SERVICE AGREEMENT

1. INDEMNIFICATION
Each party agrees to indemnify and hold harmless the other party from claims arising from the 
indemnifying party's breach of this Agreement, gross negligence, or willful misconduct. 
Indemnification is capped at the greater of $100,000 or fees paid in the prior 12 months.
This indemnification is mutual and reciprocal.

2. LIMITATION OF LIABILITY
Neither party shall be liable for consequential, incidental, or indirect damages. Each party's 
total liability shall be limited to the amount of fees paid under this Agreement in the 12 months 
preceding the claim. This limitation applies mutually to both parties.

3. INTELLECTUAL PROPERTY
Each party retains ownership of its pre-existing intellectual property. Any jointly developed 
IP shall be owned jointly by both parties. Provider grants Customer a non-exclusive license to 
use the Services. Customer grants Provider a limited license to use Customer materials solely 
for providing the Services.

4. TERMINATION
Either party may terminate this Agreement for convenience upon 30 days written notice. Either 
party may terminate for cause upon material breach if the breach is not cured within 30 days 
after written notice. Upon termination, each party shall return the other's confidential information.

5. CONFIDENTIALITY
Both parties agree to maintain confidentiality of the other's confidential information for a 
period of 3 years following disclosure. Standard exceptions apply for publicly available information 
and information required to be disclosed by law. Each party shall return or destroy confidential 
information upon request.

6. DISPUTE RESOLUTION
The parties agree to attempt good faith negotiation for 30 days before initiating legal proceedings. 
Any disputes shall be resolved through mediation, then arbitration if necessary. Venue shall be 
the state where the Customer is located. Each party bears its own costs unless otherwise agreed.

7. PAYMENT
Payment is due Net-30 from invoice date. Late payments accrue interest at 1.5% per month. 
Provider may suspend services for invoices more than 60 days overdue after written notice.

8. FORCE MAJEURE
Neither party shall be liable for delays caused by circumstances beyond its reasonable control, 
including but not limited to acts of God, natural disasters, pandemic, or government actions.
"""


HIGHLY_FAVORABLE_CONTRACT = """
SERVICE AGREEMENT

1. INDEMNIFICATION
Provider shall indemnify and hold harmless Customer from any and all claims arising from 
Provider's services, breach of agreement, or negligence. Provider's indemnification is 
unlimited. Customer's indemnification obligations are limited to $10,000.

2. LIMITATION OF LIABILITY
Provider shall be fully liable for all damages including consequential and incidental damages. 
Customer's liability is capped at $5,000 regardless of circumstances.

3. INTELLECTUAL PROPERTY
Customer retains all ownership of its intellectual property and any materials provided. 
All work product created by Provider shall be owned by Customer. Provider receives no 
license to Customer materials beyond what is strictly necessary for service delivery.

4. TERMINATION
Customer may terminate this Agreement at any time for any reason with 7 days notice. 
Provider may only terminate for Customer's material breach after 90 days cure period.
No termination fees apply to Customer. Provider shall pay Customer's transition costs.

5. CONFIDENTIALITY
Provider shall maintain strict confidentiality of Customer information for 10 years.
Customer has no confidentiality obligations. Provider shall certify destruction of all 
Customer information upon termination.

6. DISPUTE RESOLUTION
Any disputes shall be resolved in Customer's local jurisdiction. Provider waives right 
to jury trial. Customer retains all rights including class action. Provider shall pay 
all Customer legal fees regardless of outcome.

7. PAYMENT
Payment due Net-60. No late fees apply. Full refund available within 90 days for any reason.
Fees are fixed for 3 years with no increases permitted.

8. SERVICE LEVELS
Provider guarantees 99.99% uptime with service credits for any downtime. Provider is 
strictly liable for any service failures. Customer receives 10x refund for service issues.
"""


AMBIGUOUS_CONTRACT = """
AGREEMENT

1. RESPONSIBILITIES
The parties shall perform their obligations in a reasonable manner. Services will be 
provided as described. Payment terms to be determined. Quality standards shall apply.

2. LIABILITY
Liability shall be as permitted by law. Damages may be limited. Parties may seek 
remedies as appropriate. Some limitations may apply.

3. INTELLECTUAL PROPERTY
IP rights shall be addressed. Ownership will be determined based on circumstances.
Rights may be assigned or licensed depending on the situation.

4. TERM
This agreement continues until terminated. Termination may occur under certain 
circumstances. Notice period to be determined. Fees may apply.

5. CONFIDENTIALITY
Certain information may be confidential. Disclosure may be restricted in some cases.
Duration of obligations varies.

6. GENERAL
This agreement is governed by applicable law. Disputes shall be resolved through 
appropriate means. Amendments may be made by agreement.

The parties have agreed to these terms.
"""


class TestKeywordLibrary(unittest.TestCase):
    """Test the keyword library"""
    
    def setUp(self):
        self.library = KeywordLibrary()
    
    def test_all_categories_present(self):
        """Ensure all 8 risk categories have keywords"""
        categories = self.library.get_all_categories()
        self.assertEqual(len(categories), 8)
        
        for category in RiskCategory:
            if category != RiskCategory.UNKNOWN:
                keywords = self.library.get_keywords(category)
                self.assertGreater(len(keywords), 10, f"Category {category} has too few keywords")
    
    def test_financial_keywords(self):
        """Test financial keyword detection"""
        text = "The fees are non-refundable and may include unlimited liability."
        results = self.library.search_category(text, RiskCategory.FINANCIAL)
        
        keywords_found = [entry.pattern for entry, _ in results]
        self.assertIn("non-refundable", keywords_found)
        self.assertIn("unlimited liability", keywords_found)
    
    def test_liability_keywords(self):
        """Test liability keyword detection"""
        text = "Customer shall indemnify and hold harmless Provider from all claims."
        results = self.library.search_category(text, RiskCategory.LEGAL_LIABILITY)
        
        keywords_found = [entry.pattern for entry, _ in results]
        self.assertIn("shall indemnify", keywords_found)
        self.assertIn("hold harmless", keywords_found)
    
    def test_search_all(self):
        """Test searching all categories"""
        text = "Unlimited liability with perpetual confidentiality and binding arbitration."
        results = self.library.search_all(text)
        
        self.assertIn(RiskCategory.FINANCIAL, results)  # unlimited liability
        self.assertIn(RiskCategory.CONFIDENTIALITY, results)  # perpetual confidentiality
        self.assertIn(RiskCategory.DISPUTE_RESOLUTION, results)  # binding arbitration


class TestFastScanner(unittest.TestCase):
    """Test the fast scanner"""
    
    def setUp(self):
        self.scanner = FastScanner()
    
    def test_scan_unfavorable_contract(self):
        """Test scanning extremely unfavorable contract"""
        result = self.scanner.scan_document(EXTREMELY_UNFAVORABLE_CONTRACT)
        
        # Should find many issues
        self.assertGreater(result.total_matches, 20)
        
        # Should have red flags
        self.assertGreater(len(result.red_flags), 5)
        
        # Should estimate high/critical risk
        self.assertIn(result.estimated_risk_level, [SeverityLevel.HIGH, SeverityLevel.CRITICAL])
        
        # Processing should be fast (< 1 second = 1000ms)
        self.assertLess(result.processing_time_ms, 1000)
    
    def test_scan_balanced_contract(self):
        """Test scanning balanced contract"""
        result = self.scanner.scan_document(BALANCED_CONTRACT)
        
        # Should find some issues but fewer than unfavorable
        self.assertGreater(result.total_matches, 5)
        self.assertLess(result.total_matches, 30)
        
        # Risk level should be lower
        self.assertIn(result.estimated_risk_level, [SeverityLevel.LOW, SeverityLevel.MEDIUM])
    
    def test_scan_clause(self):
        """Test scanning a single clause"""
        clause = "Customer shall indemnify Provider for unlimited liability exposure."
        result = self.scanner.scan_clause("test_clause", clause)
        
        self.assertGreater(len(result.keyword_matches), 0)
        self.assertTrue(result.needs_deep_analysis)
    
    def test_heatmap_generation(self):
        """Test heatmap data generation"""
        scan_result = self.scanner.scan_document(EXTREMELY_UNFAVORABLE_CONTRACT)
        heatmap = self.scanner.generate_heatmap_data(EXTREMELY_UNFAVORABLE_CONTRACT, scan_result)
        
        self.assertGreater(len(heatmap), 0)
        
        # Check heatmap structure
        for item in heatmap:
            self.assertIn('start', item)
            self.assertIn('end', item)
            self.assertIn('severity', item)


class TestRiskScorer(unittest.TestCase):
    """Test the risk scoring system"""
    
    def setUp(self):
        self.scorer = RiskScorer()
        self.scanner = FastScanner()
    
    def test_score_high_risk_clause(self):
        """Test scoring a high-risk clause"""
        clause = "Unlimited indemnification without limitation, irrevocable and perpetual."
        scan = self.scanner.scan_clause("test", clause)
        
        score, factors = self.scorer.calculate_score(clause, scan.keyword_matches)
        
        # Should be high score
        self.assertGreater(score, 60)
    
    def test_score_low_risk_clause(self):
        """Test scoring a low-risk clause"""
        clause = "Payment is due Net-30 following standard industry practice."
        scan = self.scanner.scan_clause("test", clause)
        
        score, factors = self.scorer.calculate_score(clause, scan.keyword_matches)
        
        # Should be lower score
        self.assertLess(score, 40)
    
    def test_modifiers_reduce_score(self):
        """Test that positive modifiers reduce score"""
        # Clause with caps and mutual language
        clause = """Each party shall indemnify the other, mutually and reciprocally, 
        for damages capped at $100,000 following commercially reasonable efforts."""
        scan = self.scanner.scan_clause("test", clause)
        
        score, factors = self.scorer.calculate_score(clause, scan.keyword_matches)
        
        # Modifiers should be negative (reducing score)
        self.assertLess(factors.cap_modifier, 0)
        self.assertLess(factors.mutual_language_modifier, 0)
    
    def test_severity_from_score(self):
        """Test severity level determination"""
        self.assertEqual(self.scorer.get_severity_from_score(20), SeverityLevel.LOW)
        self.assertEqual(self.scorer.get_severity_from_score(45), SeverityLevel.MEDIUM)
        self.assertEqual(self.scorer.get_severity_from_score(75), SeverityLevel.HIGH)
        self.assertEqual(self.scorer.get_severity_from_score(90), SeverityLevel.CRITICAL)
    
    def test_document_score(self):
        """Test document-level score calculation"""
        clause_scores = [85, 70, 45, 30, 20]
        doc_score = self.scorer.calculate_document_score(clause_scores)
        
        # Should emphasize high scores but not just take max
        self.assertGreater(doc_score, 50)
        self.assertLess(doc_score, 90)


class TestDocumentAggregator(unittest.TestCase):
    """Test the document aggregator"""
    
    def setUp(self):
        self.aggregator = DocumentAggregator()
    
    def test_aggregate_results(self):
        """Test aggregating clause risks"""
        # Create mock clause risks
        from risk_assessment.models import ClauseRisk
        
        risks = [
            ClauseRisk(
                clause_id="clause_1",
                clause_text="Test clause 1",
                clause_type="indemnification",
                category=RiskCategory.LEGAL_LIABILITY,
                severity=SeverityLevel.HIGH,
                score=75,
                confidence=85,
                primary_risk="High indemnification exposure",
                detailed_explanation="",
                specific_concerns=[],
                impact_if_triggered="",
                likelihood="HIGH",
                recommendation="Negotiate cap",
            ),
            ClauseRisk(
                clause_id="clause_2",
                clause_text="Test clause 2",
                clause_type="termination",
                category=RiskCategory.TERMINATION,
                severity=SeverityLevel.MEDIUM,
                score=50,
                confidence=80,
                primary_risk="Restrictive termination",
                detailed_explanation="",
                specific_concerns=[],
                impact_if_triggered="",
                likelihood="MEDIUM",
                recommendation="Review carefully",
            ),
        ]
        
        result = self.aggregator.aggregate(risks, "test.pdf", 5, 2.5)
        
        # Check basic structure
        self.assertEqual(result.metadata.filename, "test.pdf")
        self.assertEqual(result.metadata.clauses_analyzed, 2)
        
        # Check risk summary
        self.assertIn(result.risk_summary.overall_level, [SeverityLevel.MEDIUM, SeverityLevel.HIGH])
        
        # Check top risks are sorted
        if result.top_risks:
            self.assertEqual(result.top_risks[0].score, 75)
    
    def test_markdown_report(self):
        """Test markdown report generation"""
        from risk_assessment.models import ClauseRisk
        
        risks = [
            ClauseRisk(
                clause_id="clause_1",
                clause_text="Test",
                clause_type="liability",
                category=RiskCategory.LEGAL_LIABILITY,
                severity=SeverityLevel.HIGH,
                score=70,
                confidence=80,
                primary_risk="Test risk",
                detailed_explanation="",
                specific_concerns=[],
                impact_if_triggered="",
                likelihood="HIGH",
                recommendation="Test recommendation",
            ),
        ]
        
        result = self.aggregator.aggregate(risks, "test.pdf", 1, 1.0)
        markdown = self.aggregator.to_markdown_report(result)
        
        self.assertIn("# Risk Assessment Report", markdown)
        self.assertIn("test.pdf", markdown)


class TestRiskAssessmentEngine(unittest.TestCase):
    """Test the main risk assessment engine"""
    
    def setUp(self):
        # Use engine without AI for testing
        self.engine = RiskAssessmentEngine(use_ai=False)
    
    def test_analyze_unfavorable_contract(self):
        """Test analyzing extremely unfavorable contract"""
        result = self.engine.analyze_document(EXTREMELY_UNFAVORABLE_CONTRACT, "unfavorable.pdf")
        
        # Overall score should be high (risky)
        self.assertGreater(result.risk_summary.overall_score, 60)
        
        # Should have critical/high issues
        self.assertGreater(
            result.risk_summary.distribution.critical + result.risk_summary.distribution.high,
            2
        )
        
        # Should identify deal breakers
        self.assertGreater(len(result.deal_breakers) + len(result.must_address_immediately), 0)
    
    def test_analyze_balanced_contract(self):
        """Test analyzing balanced contract"""
        result = self.engine.analyze_document(BALANCED_CONTRACT, "balanced.pdf")
        
        # Overall score should be moderate
        self.assertLess(result.risk_summary.overall_score, 60)
        
        # Should have acceptable clauses
        self.assertGreater(len(result.acceptable_as_is), 0)
    
    def test_analyze_favorable_contract(self):
        """Test analyzing highly favorable contract"""
        result = self.engine.analyze_document(HIGHLY_FAVORABLE_CONTRACT, "favorable.pdf")
        
        # Overall score should be low (good for user)
        self.assertLess(result.risk_summary.overall_score, 50)
    
    def test_analyze_ambiguous_contract(self):
        """Test analyzing ambiguous contract"""
        result = self.engine.analyze_document(AMBIGUOUS_CONTRACT, "ambiguous.pdf")
        
        # Should detect medium risk due to uncertainty
        self.assertIn(
            result.risk_summary.overall_level,
            [SeverityLevel.MEDIUM, SeverityLevel.HIGH]
        )
    
    def test_quick_scan(self):
        """Test quick scan functionality"""
        result = self.engine.quick_scan(EXTREMELY_UNFAVORABLE_CONTRACT)
        
        self.assertGreater(result.total_matches, 0)
        self.assertIn(result.estimated_risk_level, [SeverityLevel.HIGH, SeverityLevel.CRITICAL])
    
    def test_analyze_single_clause(self):
        """Test single clause analysis"""
        clause = "Customer shall indemnify Provider with unlimited liability exposure."
        result = self.engine.analyze_clause(clause)
        
        self.assertIsNotNone(result)
        self.assertGreater(result.score, 50)
    
    def test_export_functions(self):
        """Test export functionality"""
        result = self.engine.analyze_document(BALANCED_CONTRACT, "test.pdf")
        
        # Test markdown export
        markdown = self.engine.export_markdown_report(result)
        self.assertIn("# Risk Assessment Report", markdown)
        
        # Test JSON export
        json_data = self.engine.export_json(result)
        self.assertIn("document_metadata", json_data)
        self.assertIn("risk_summary", json_data)
    
    def test_dashboard_generation(self):
        """Test dashboard data generation"""
        result = self.engine.analyze_document(BALANCED_CONTRACT, "test.pdf")
        dashboard = self.engine.get_dashboard(result)
        
        self.assertIn("overall_gauge", dashboard)
        self.assertIn("distribution_pie", dashboard)
        self.assertIn("metrics", dashboard)


class TestPerformance(unittest.TestCase):
    """Test performance requirements"""
    
    def setUp(self):
        self.engine = RiskAssessmentEngine(use_ai=False)
    
    def test_fast_scan_under_one_second(self):
        """Fast scan should complete in under 1 second"""
        import time
        
        start = time.time()
        self.engine.quick_scan(EXTREMELY_UNFAVORABLE_CONTRACT)
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 1.0, f"Fast scan took {elapsed:.2f}s, should be < 1s")
    
    def test_full_analysis_reasonable_time(self):
        """Full analysis (without AI) should complete in reasonable time"""
        import time
        
        start = time.time()
        self.engine.analyze_document(BALANCED_CONTRACT)
        elapsed = time.time() - start
        
        # Without AI, should complete very quickly
        self.assertLess(elapsed, 5.0, f"Analysis took {elapsed:.2f}s, should be < 5s")


if __name__ == "__main__":
    unittest.main(verbosity=2)
