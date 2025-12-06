"""
Comprehensive Keyword Library for Legal Risk Detection

Contains 50-100 high-risk keywords/phrases per category with weights.
"""

from dataclasses import dataclass, field
from typing import Optional
import re

from .models import RiskCategory


@dataclass
class KeywordEntry:
    """A keyword or phrase to detect"""
    pattern: str
    weight: float  # 1.0 = normal, 2.0 = high concern, 3.0 = critical
    description: str
    is_regex: bool = False
    context_required: Optional[str] = None  # requires this context to be relevant
    negation_pattern: Optional[str] = None  # if this pattern exists, reduce weight


class KeywordLibrary:
    """
    Comprehensive library of legal risk keywords and phrases.
    Each category contains patterns with associated weights.
    """
    
    def __init__(self):
        self._keywords: dict[RiskCategory, list[KeywordEntry]] = {}
        self._compiled_patterns: dict[RiskCategory, list[tuple[re.Pattern, KeywordEntry]]] = {}
        self._initialize_keywords()
        self._compile_patterns()
    
    def _initialize_keywords(self):
        """Initialize all keyword categories"""
        self._keywords = {
            RiskCategory.FINANCIAL: self._get_financial_keywords(),
            RiskCategory.LEGAL_LIABILITY: self._get_liability_keywords(),
            RiskCategory.TERMINATION: self._get_termination_keywords(),
            RiskCategory.INTELLECTUAL_PROPERTY: self._get_ip_keywords(),
            RiskCategory.CONFIDENTIALITY: self._get_confidentiality_keywords(),
            RiskCategory.DISPUTE_RESOLUTION: self._get_dispute_keywords(),
            RiskCategory.COMPLIANCE: self._get_compliance_keywords(),
            RiskCategory.OPERATIONAL: self._get_operational_keywords(),
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        for category, keywords in self._keywords.items():
            self._compiled_patterns[category] = []
            for kw in keywords:
                if kw.is_regex:
                    pattern = re.compile(kw.pattern, re.IGNORECASE | re.MULTILINE)
                else:
                    # Escape special regex chars and make word boundary matching
                    escaped = re.escape(kw.pattern)
                    pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
                self._compiled_patterns[category].append((pattern, kw))
    
    def get_keywords(self, category: RiskCategory) -> list[KeywordEntry]:
        """Get all keywords for a category"""
        return self._keywords.get(category, [])
    
    def get_compiled_patterns(self, category: RiskCategory) -> list[tuple[re.Pattern, KeywordEntry]]:
        """Get compiled regex patterns for a category"""
        return self._compiled_patterns.get(category, [])
    
    def get_all_categories(self) -> list[RiskCategory]:
        """Get all risk categories"""
        return list(self._keywords.keys())
    
    # ========== FINANCIAL RISK KEYWORDS ==========
    def _get_financial_keywords(self) -> list[KeywordEntry]:
        return [
            # Unlimited liability
            KeywordEntry("unlimited liability", 3.0, "No cap on financial exposure"),
            KeywordEntry("unlimited financial", 3.0, "No cap on financial exposure"),
            KeywordEntry("without limitation", 2.5, "Potentially unlimited scope"),
            KeywordEntry("no cap", 2.5, "Missing liability cap"),
            KeywordEntry("no limit", 2.5, "Missing limit on obligations"),
            KeywordEntry("uncapped", 2.5, "No ceiling on amounts"),
            
            # Hidden fees
            KeywordEntry("additional fees", 1.5, "May indicate hidden costs"),
            KeywordEntry("processing fee", 1.0, "Additional processing costs"),
            KeywordEntry("administrative fee", 1.0, "Administrative charges"),
            KeywordEntry("service charge", 1.0, "Extra service charges"),
            KeywordEntry("convenience fee", 1.5, "Hidden convenience charges"),
            KeywordEntry("handling fee", 1.0, "Extra handling costs"),
            KeywordEntry("setup fee", 1.0, "Initial setup costs"),
            KeywordEntry("maintenance fee", 1.0, "Ongoing maintenance costs"),
            
            # Non-refundable
            KeywordEntry("non-refundable", 2.0, "Cannot recover payments"),
            KeywordEntry("nonrefundable", 2.0, "Cannot recover payments"),
            KeywordEntry("no refund", 2.5, "Refunds prohibited"),
            KeywordEntry("refund shall not", 2.0, "Refund restrictions"),
            KeywordEntry("forfeiture", 2.0, "Loss of payments/deposits"),
            KeywordEntry("forfeited", 2.0, "Loss of payments/deposits"),
            
            # Price increases
            KeywordEntry("sole discretion to adjust", 2.5, "Unilateral price changes"),
            KeywordEntry("adjust fees at any time", 2.5, "Unpredictable fee changes"),
            KeywordEntry("price increase", 1.5, "Potential cost escalation"),
            KeywordEntry("automatically increase", 2.0, "Automatic cost increases"),
            KeywordEntry("automatically renew at increased", 2.5, "Auto-renewal with price hike"),
            KeywordEntry(r"increase\s+(?:by|of)\s+\d+%", 1.5, "Percentage increase specified", is_regex=True),
            KeywordEntry("annual increase", 1.5, "Yearly price escalation"),
            KeywordEntry("escalation clause", 1.5, "Price escalation provision"),
            KeywordEntry("cost of living adjustment", 1.0, "COLA increases"),
            KeywordEntry("CPI adjustment", 1.0, "Inflation-based increases"),
            
            # Penalties
            KeywordEntry("penalty", 1.5, "Financial penalties"),
            KeywordEntry("penalties compound", 2.5, "Compounding penalties"),
            KeywordEntry("late fee", 1.5, "Late payment penalties"),
            KeywordEntry("interest rate of", 1.5, "Interest charges"),
            KeywordEntry(r"interest\s+(?:rate|of)\s+\d+%", 1.5, "Interest rate specified", is_regex=True),
            KeywordEntry("default rate", 2.0, "Default interest rate"),
            KeywordEntry("liquidated damages", 1.5, "Preset damage amounts"),
            KeywordEntry("acceleration clause", 2.0, "Payment acceleration on default"),
            
            # Payment terms
            KeywordEntry("payment in advance", 1.0, "Prepayment required"),
            KeywordEntry("upfront payment", 1.0, "Advance payment required"),
            KeywordEntry("upon signing", 1.0, "Payment at contract signing"),
            KeywordEntry("net-60", 1.0, "60-day payment terms"),
            KeywordEntry("net-90", 1.5, "90-day payment terms"),
            KeywordEntry("upon receipt", 1.0, "Immediate payment required"),
            KeywordEntry("within 7 days", 1.0, "Short payment window"),
            
            # Currency/Exchange
            KeywordEntry("currency fluctuation", 1.5, "Currency exchange risk"),
            KeywordEntry("exchange rate", 1.0, "Currency exchange exposure"),
            KeywordEntry("bears the exchange risk", 2.0, "One party bears FX risk"),
            
            # Deposits/Collateral
            KeywordEntry("security deposit", 1.0, "Deposit required"),
            KeywordEntry("performance bond", 1.5, "Bond requirement"),
            KeywordEntry("letter of credit", 1.5, "LOC requirement"),
            KeywordEntry("escrow", 1.0, "Escrow arrangement"),
            
            # Tax
            KeywordEntry("responsible for all taxes", 1.5, "Full tax liability"),
            KeywordEntry("plus applicable taxes", 1.0, "Additional tax costs"),
            KeywordEntry("exclusive of taxes", 1.0, "Taxes not included"),
            KeywordEntry("gross up", 1.5, "Tax gross-up obligation"),
            
            # Insurance
            KeywordEntry("maintain insurance", 1.0, "Insurance requirement"),
            KeywordEntry(r"insurance\s+(?:of|coverage)\s+\$?\d+", 1.5, "Specific insurance amounts", is_regex=True),
            KeywordEntry("name as additional insured", 1.0, "Additional insured requirement"),
        ]
    
    # ========== LEGAL LIABILITY KEYWORDS ==========
    def _get_liability_keywords(self) -> list[KeywordEntry]:
        return [
            # Indemnification
            KeywordEntry("shall indemnify", 2.0, "Indemnification obligation"),
            KeywordEntry("will indemnify", 2.0, "Indemnification obligation"),
            KeywordEntry("agrees to indemnify", 2.0, "Indemnification agreement"),
            KeywordEntry("indemnify and hold harmless", 2.5, "Strong indemnity clause"),
            KeywordEntry("defend, indemnify", 2.5, "Defense and indemnity obligation"),
            KeywordEntry("unlimited indemnification", 3.0, "No cap on indemnity"),
            KeywordEntry("broad indemnification", 2.5, "Wide indemnity scope"),
            KeywordEntry("indemnify for any and all", 2.5, "Broad indemnity scope"),
            
            # Hold harmless
            KeywordEntry("hold harmless", 2.0, "Hold harmless provision"),
            KeywordEntry("save harmless", 2.0, "Save harmless provision"),
            KeywordEntry("harmless from any", 2.0, "Broad hold harmless"),
            
            # Waivers
            KeywordEntry("waive all claims", 3.0, "Waiver of all claims"),
            KeywordEntry("waives any right", 2.5, "Rights waiver"),
            KeywordEntry("waives the right to", 2.5, "Specific rights waiver"),
            KeywordEntry("release from liability", 2.5, "Liability release"),
            KeywordEntry("releases from all liability", 3.0, "Complete liability release"),
            KeywordEntry("releases and discharges", 2.5, "Release and discharge"),
            KeywordEntry("forever release", 3.0, "Permanent release"),
            KeywordEntry("knowingly and voluntarily waive", 2.5, "Voluntary waiver language"),
            
            # Liability limitations
            KeywordEntry("to the fullest extent permitted by law", 2.0, "Maximum legal liability"),
            KeywordEntry("to the maximum extent", 2.0, "Maximum extent language"),
            KeywordEntry("in no event shall", 1.5, "Liability limitation language"),
            KeywordEntry("under no circumstances", 2.0, "Absolute limitation"),
            KeywordEntry("shall not be liable for", 1.5, "Liability exclusion"),
            KeywordEntry("excludes all liability", 2.5, "Complete liability exclusion"),
            KeywordEntry("disclaims all liability", 2.5, "Complete liability disclaimer"),
            
            # Consequential damages
            KeywordEntry("consequential damages", 1.5, "Consequential damages mention"),
            KeywordEntry("incidental damages", 1.5, "Incidental damages mention"),
            KeywordEntry("special damages", 1.5, "Special damages mention"),
            KeywordEntry("punitive damages", 1.5, "Punitive damages mention"),
            KeywordEntry("indirect damages", 1.5, "Indirect damages mention"),
            KeywordEntry("excludes consequential", 1.0, "Excludes consequential (may be standard)"),
            KeywordEntry("including but not limited to lost profits", 2.0, "Broad damages inclusion"),
            
            # Warranty disclaimers
            KeywordEntry("as is", 1.5, "As-is sale/service"),
            KeywordEntry("as-is", 1.5, "As-is sale/service"),
            KeywordEntry("with all faults", 2.0, "No warranty provision"),
            KeywordEntry("without warranty", 2.0, "No warranty"),
            KeywordEntry("no warranties", 2.0, "No warranties given"),
            KeywordEntry("disclaims all warranties", 2.5, "Complete warranty disclaimer"),
            KeywordEntry("warranty of merchantability", 1.0, "UCC warranty mention"),
            KeywordEntry("warranty of fitness", 1.0, "Fitness warranty mention"),
            
            # Joint liability
            KeywordEntry("joint and several", 2.5, "Joint and several liability"),
            KeywordEntry("jointly and severally", 2.5, "Joint and several liability"),
            KeywordEntry("personal guarantee", 2.5, "Personal guarantee required"),
            KeywordEntry("personally liable", 2.5, "Personal liability exposure"),
            KeywordEntry("guarantor", 2.0, "Guarantor obligation"),
            
            # Gross negligence
            KeywordEntry("gross negligence", 1.5, "Gross negligence standard"),
            KeywordEntry("willful misconduct", 1.5, "Willful misconduct standard"),
            KeywordEntry("even if advised of", 2.0, "Liability even if warned"),
            KeywordEntry("regardless of negligence", 2.5, "Strict liability standard"),
            
            # Third party claims
            KeywordEntry("third party claims", 1.5, "Third party claim exposure"),
            KeywordEntry("any claims by third parties", 2.0, "Third party indemnity"),
            KeywordEntry("third party losses", 1.5, "Third party loss exposure"),
        ]
    
    # ========== TERMINATION KEYWORDS ==========
    def _get_termination_keywords(self) -> list[KeywordEntry]:
        return [
            # Automatic renewal
            KeywordEntry("automatically renews", 2.0, "Auto-renewal clause"),
            KeywordEntry("automatically renew", 2.0, "Auto-renewal clause"),
            KeywordEntry("auto-renewal", 2.0, "Auto-renewal clause"),
            KeywordEntry("auto renewal", 2.0, "Auto-renewal clause"),
            KeywordEntry("renew automatically", 2.0, "Auto-renewal clause"),
            KeywordEntry("automatically extended", 2.0, "Auto-extension"),
            KeywordEntry("unless terminated", 1.5, "Conditional termination"),
            KeywordEntry("unless cancelled", 1.5, "Conditional cancellation"),
            KeywordEntry("evergreen", 2.0, "Evergreen contract"),
            KeywordEntry("successive renewal", 1.5, "Successive renewals"),
            
            # Termination restrictions
            KeywordEntry("may not terminate", 2.5, "Cannot terminate"),
            KeywordEntry("cannot terminate", 2.5, "Cannot terminate"),
            KeywordEntry("shall not terminate", 2.5, "Cannot terminate"),
            KeywordEntry("no right to terminate", 3.0, "No termination right"),
            KeywordEntry("irrevocable", 3.0, "Cannot be revoked"),
            KeywordEntry("non-cancelable", 2.5, "Cannot cancel"),
            KeywordEntry("non-cancellable", 2.5, "Cannot cancel"),
            KeywordEntry("binding and irrevocable", 3.0, "Binding and irrevocable"),
            
            # Termination fees
            KeywordEntry("termination fee", 2.0, "Termination fee required"),
            KeywordEntry("early termination fee", 2.0, "Early termination penalty"),
            KeywordEntry("cancellation fee", 2.0, "Cancellation fee"),
            KeywordEntry("termination penalty", 2.5, "Termination penalty"),
            KeywordEntry("break fee", 2.0, "Break fee"),
            KeywordEntry("liquidated damages upon termination", 2.5, "Preset termination damages"),
            KeywordEntry("termination fee equal to", 2.5, "Specific termination fee"),
            KeywordEntry("remaining term", 2.0, "Payment for remaining term"),
            KeywordEntry("pay for the remainder", 2.5, "Full term payment obligation"),
            
            # Notice periods
            KeywordEntry(r"\d+\s*days?['\"]?\s+(?:prior\s+)?(?:written\s+)?notice", 1.0, "Notice period specified", is_regex=True),
            KeywordEntry("30 days notice", 1.0, "30-day notice period"),
            KeywordEntry("60 days notice", 1.5, "60-day notice period"),
            KeywordEntry("90 days notice", 2.0, "90-day notice period"),
            KeywordEntry("180 days notice", 2.5, "180-day notice period"),
            KeywordEntry("one year notice", 3.0, "One year notice period"),
            KeywordEntry("12 months notice", 3.0, "12-month notice period"),
            
            # Lock-in periods
            KeywordEntry("minimum term", 1.5, "Minimum term commitment"),
            KeywordEntry("initial term", 1.0, "Initial term period"),
            KeywordEntry("lock-in period", 2.0, "Lock-in period"),
            KeywordEntry("commitment period", 1.5, "Commitment period"),
            KeywordEntry("binding for", 1.5, "Binding duration"),
            
            # Perpetual obligations
            KeywordEntry("perpetual", 2.5, "Perpetual/forever term"),
            KeywordEntry("in perpetuity", 3.0, "Forever term"),
            KeywordEntry("survives termination indefinitely", 3.0, "Indefinite survival"),
            KeywordEntry("survives termination", 1.5, "Survival clause"),
            KeywordEntry("survive the termination", 1.5, "Survival clause"),
            KeywordEntry("shall survive", 1.0, "Survival provision"),
            KeywordEntry("continuing obligations", 1.5, "Ongoing obligations post-termination"),
            
            # For cause vs convenience
            KeywordEntry("terminate for convenience", 0.5, "Termination for convenience (good)"),
            KeywordEntry("terminate without cause", 0.5, "Termination without cause (good)"),
            KeywordEntry("for cause only", 2.0, "Only for-cause termination"),
            KeywordEntry("material breach only", 2.0, "Only material breach allows termination"),
            KeywordEntry("only upon material breach", 2.0, "Restrictive termination"),
            
            # Cure periods
            KeywordEntry("cure period", 1.0, "Cure period provided"),
            KeywordEntry("opportunity to cure", 1.0, "Cure opportunity"),
            KeywordEntry(r"\d+\s*days?\s+to\s+cure", 1.0, "Specific cure period", is_regex=True),
            KeywordEntry("no cure period", 2.5, "No opportunity to cure"),
            KeywordEntry("immediate termination", 2.0, "Immediate termination right"),
        ]
    
    # ========== INTELLECTUAL PROPERTY KEYWORDS ==========
    def _get_ip_keywords(self) -> list[KeywordEntry]:
        return [
            # IP transfer
            KeywordEntry("assigns all rights", 2.5, "Full IP assignment"),
            KeywordEntry("assign all rights, title", 3.0, "Complete IP transfer"),
            KeywordEntry("assigns all right, title, and interest", 3.0, "Full IP transfer"),
            KeywordEntry("transfer of ownership", 2.5, "Ownership transfer"),
            KeywordEntry("transfers all intellectual property", 3.0, "IP transfer"),
            KeywordEntry("hereby assigns", 2.0, "IP assignment"),
            KeywordEntry("irrevocably assigns", 3.0, "Irrevocable IP assignment"),
            
            # Work for hire
            KeywordEntry("work made for hire", 2.5, "Work for hire doctrine"),
            KeywordEntry("work for hire", 2.5, "Work for hire doctrine"),
            KeywordEntry("works for hire", 2.5, "Work for hire doctrine"),
            KeywordEntry("deemed work for hire", 2.5, "Work for hire classification"),
            KeywordEntry("shall be considered work for hire", 2.5, "Work for hire designation"),
            
            # License scope
            KeywordEntry("exclusive license", 2.0, "Exclusive license grant"),
            KeywordEntry("exclusive, perpetual", 3.0, "Perpetual exclusive license"),
            KeywordEntry("exclusive, worldwide", 2.5, "Worldwide exclusive license"),
            KeywordEntry("exclusive, perpetual, worldwide", 3.0, "Broadest exclusive license"),
            KeywordEntry("exclusive, irrevocable", 3.0, "Irrevocable exclusive license"),
            KeywordEntry("non-exclusive license", 0.5, "Non-exclusive license (better)"),
            KeywordEntry("sublicensable", 1.5, "Can be sublicensed"),
            KeywordEntry("right to sublicense", 1.5, "Sublicense rights"),
            KeywordEntry("transferable license", 1.5, "Transferable license"),
            
            # Future rights
            KeywordEntry("future developments", 2.5, "Future IP included"),
            KeywordEntry("including future", 2.5, "Future work included"),
            KeywordEntry("future improvements", 2.0, "Future improvements included"),
            KeywordEntry("derivatives and modifications", 2.0, "Derivative works included"),
            KeywordEntry("all derivative works", 2.5, "All derivatives included"),
            KeywordEntry("any improvements", 2.0, "Improvements included"),
            KeywordEntry("enhancements and modifications", 1.5, "Enhancements included"),
            
            # Moral rights
            KeywordEntry("waives moral rights", 2.5, "Moral rights waiver"),
            KeywordEntry("waive moral rights", 2.5, "Moral rights waiver"),
            KeywordEntry("moral rights waiver", 2.5, "Moral rights waiver"),
            KeywordEntry("waives all moral rights", 3.0, "Complete moral rights waiver"),
            KeywordEntry("waives any moral rights", 2.5, "Moral rights waiver"),
            
            # Patent/Trademark
            KeywordEntry("patent assignment", 2.0, "Patent assignment"),
            KeywordEntry("assigns all patents", 2.5, "All patents assigned"),
            KeywordEntry("trademark assignment", 2.0, "Trademark assignment"),
            KeywordEntry("assigns all trademarks", 2.5, "All trademarks assigned"),
            KeywordEntry("copyright assignment", 2.0, "Copyright assignment"),
            
            # Background IP
            KeywordEntry("background IP", 1.0, "Background IP mentioned"),
            KeywordEntry("pre-existing IP", 1.0, "Pre-existing IP mentioned"),
            KeywordEntry("retains ownership of background", 0.5, "Retains background IP (good)"),
            KeywordEntry("license to background IP", 1.5, "Background IP licensed"),
            
            # Source code
            KeywordEntry("source code", 1.0, "Source code mentioned"),
            KeywordEntry("source code escrow", 1.0, "Source code escrow"),
            KeywordEntry("deliver source code", 2.0, "Source code delivery required"),
            KeywordEntry("access to source code", 2.0, "Source code access"),
            
            # No reverse engineering
            KeywordEntry("reverse engineer", 1.5, "Reverse engineering mention"),
            KeywordEntry("decompile", 1.5, "Decompilation mention"),
            KeywordEntry("disassemble", 1.5, "Disassembly mention"),
        ]
    
    # ========== CONFIDENTIALITY KEYWORDS ==========
    def _get_confidentiality_keywords(self) -> list[KeywordEntry]:
        return [
            # Duration
            KeywordEntry("perpetual confidentiality", 3.0, "Forever confidentiality"),
            KeywordEntry("indefinite confidentiality", 3.0, "Indefinite confidentiality"),
            KeywordEntry("confidential in perpetuity", 3.0, "Perpetual confidentiality"),
            KeywordEntry(r"confidential(?:ity)?\s+(?:for|period\s+of)\s+\d+\s+years?", 1.0, "Time-limited confidentiality", is_regex=True),
            KeywordEntry("10 years", 2.0, "Long confidentiality period"),
            KeywordEntry("15 years", 2.5, "Very long confidentiality"),
            KeywordEntry("20 years", 3.0, "Extremely long confidentiality"),
            
            # Scope
            KeywordEntry("all information", 2.0, "Broad confidentiality scope"),
            KeywordEntry("any information", 2.0, "Broad confidentiality scope"),
            KeywordEntry("all materials", 1.5, "Broad materials scope"),
            KeywordEntry("any and all information", 2.5, "Very broad scope"),
            KeywordEntry("regardless of whether marked", 2.0, "Unmarked info included"),
            KeywordEntry("whether or not marked confidential", 2.0, "Unmarked info included"),
            
            # Third party sharing
            KeywordEntry("may share with affiliates", 1.5, "Affiliate sharing permitted"),
            KeywordEntry("share with affiliates without notice", 2.5, "Unnotified affiliate sharing"),
            KeywordEntry("share with third parties", 2.0, "Third party sharing permitted"),
            KeywordEntry("disclose to subcontractors", 1.5, "Subcontractor disclosure"),
            KeywordEntry("without prior consent", 2.0, "Disclosure without consent"),
            KeywordEntry("in its sole discretion", 2.5, "Discretionary disclosure"),
            KeywordEntry("sole discretion to disclose", 2.5, "Discretionary disclosure"),
            
            # Return/Destruction
            KeywordEntry("no obligation to return", 2.5, "No return obligation"),
            KeywordEntry("not required to return", 2.5, "No return requirement"),
            KeywordEntry("need not return", 2.0, "No return requirement"),
            KeywordEntry("may retain copies", 1.5, "May keep copies"),
            KeywordEntry("retain archival copies", 1.0, "Archival copies permitted"),
            KeywordEntry("return or destroy", 0.5, "Return/destroy obligation (good)"),
            KeywordEntry("certify destruction", 0.5, "Destruction certification (good)"),
            
            # Data protection
            KeywordEntry("waives data protection", 3.0, "Data protection waiver"),
            KeywordEntry("waive data protection rights", 3.0, "Data protection waiver"),
            KeywordEntry("no liability for data", 2.5, "No data liability"),
            KeywordEntry("not responsible for data security", 2.5, "No security responsibility"),
            KeywordEntry("data breach", 1.5, "Data breach mentioned"),
            KeywordEntry("security incident", 1.5, "Security incident mentioned"),
            
            # One-sided
            KeywordEntry("your confidential information", 1.0, "One-way confidentiality check"),
            KeywordEntry("receiving party shall", 1.5, "One-sided obligation"),
            KeywordEntry("disclosing party may", 1.5, "One-sided rights"),
            KeywordEntry("mutual confidentiality", 0.5, "Mutual obligations (good)"),
            KeywordEntry("reciprocal obligations", 0.5, "Reciprocal (good)"),
            
            # Exceptions
            KeywordEntry("publicly available", 0.5, "Public info exception (standard)"),
            KeywordEntry("independently developed", 0.5, "Independent development exception"),
            KeywordEntry("rightfully received", 0.5, "Prior receipt exception"),
            KeywordEntry("required by law", 0.5, "Legal requirement exception"),
            KeywordEntry("court order", 0.5, "Court order exception"),
        ]
    
    # ========== DISPUTE RESOLUTION KEYWORDS ==========
    def _get_dispute_keywords(self) -> list[KeywordEntry]:
        return [
            # Arbitration
            KeywordEntry("binding arbitration", 2.0, "Mandatory arbitration"),
            KeywordEntry("mandatory arbitration", 2.0, "Mandatory arbitration"),
            KeywordEntry("shall be resolved through arbitration", 1.5, "Arbitration required"),
            KeywordEntry("submit to arbitration", 1.5, "Arbitration submission"),
            KeywordEntry("AAA arbitration", 1.5, "AAA arbitration rules"),
            KeywordEntry("JAMS arbitration", 1.5, "JAMS arbitration rules"),
            KeywordEntry("ICC arbitration", 1.5, "ICC arbitration rules"),
            KeywordEntry("final and binding", 2.0, "Final binding decision"),
            KeywordEntry("arbitration shall be final", 2.0, "Final arbitration"),
            KeywordEntry("no appeal", 2.5, "No appeal rights"),
            
            # Jurisdiction
            KeywordEntry("exclusive jurisdiction", 1.5, "Exclusive jurisdiction clause"),
            KeywordEntry("exclusive jurisdiction in", 2.0, "Specific exclusive jurisdiction"),
            KeywordEntry("courts of", 1.0, "Court jurisdiction specified"),
            KeywordEntry("shall be brought in", 1.5, "Venue specified"),
            KeywordEntry("only in the courts", 2.0, "Single court option"),
            KeywordEntry("irrevocably submits", 2.0, "Irrevocable jurisdiction"),
            KeywordEntry("consents to jurisdiction", 1.5, "Jurisdiction consent"),
            KeywordEntry("personal jurisdiction", 1.5, "Personal jurisdiction"),
            KeywordEntry("foreign jurisdiction", 2.5, "Foreign court jurisdiction"),
            
            # Venue
            KeywordEntry("venue shall be", 1.5, "Venue specified"),
            KeywordEntry("exclusive venue", 2.0, "Single venue option"),
            KeywordEntry("State of Delaware", 1.5, "Delaware venue"),
            KeywordEntry("State of New York", 1.5, "NY venue"),
            KeywordEntry("State of California", 1.5, "California venue"),
            KeywordEntry("London, England", 2.0, "London venue"),
            KeywordEntry("Singapore", 1.5, "Singapore venue"),
            KeywordEntry("Hong Kong", 1.5, "Hong Kong venue"),
            
            # Jury trial waiver
            KeywordEntry("waives right to jury trial", 2.5, "Jury trial waiver"),
            KeywordEntry("waive jury trial", 2.5, "Jury trial waiver"),
            KeywordEntry("waives right to trial by jury", 2.5, "Jury trial waiver"),
            KeywordEntry("bench trial", 1.5, "Bench trial only"),
            KeywordEntry("judge alone", 1.5, "Judge-only trial"),
            
            # Class action waiver
            KeywordEntry("waives class action", 2.5, "Class action waiver"),
            KeywordEntry("class action waiver", 2.5, "Class action waiver"),
            KeywordEntry("waives right to class action", 2.5, "Class action waiver"),
            KeywordEntry("individual basis only", 2.0, "Individual claims only"),
            KeywordEntry("no class proceedings", 2.5, "No class proceedings"),
            KeywordEntry("representative action", 2.0, "Representative action waiver"),
            
            # Legal fees
            KeywordEntry("each party bears own costs", 1.5, "Each pays own fees"),
            KeywordEntry("own legal fees", 1.0, "Own fees"),
            KeywordEntry("prevailing party", 2.0, "Fee shifting"),
            KeywordEntry("prevailing party entitled to fees", 2.0, "Winner gets fees"),
            KeywordEntry("loser pays", 2.5, "Loser pays costs"),
            KeywordEntry("losing party shall pay", 2.5, "Loser pays"),
            KeywordEntry("recover attorneys' fees", 2.0, "Fee recovery clause"),
            KeywordEntry("reasonable attorneys' fees", 1.5, "Fee recovery"),
            
            # Mediation
            KeywordEntry("mediation", 0.5, "Mediation step (often good)"),
            KeywordEntry("good faith negotiation", 0.5, "Negotiation step (often good)"),
            KeywordEntry("escalation procedure", 0.5, "Escalation process"),
            KeywordEntry("informal dispute resolution", 0.5, "Informal resolution"),
            
            # Statute of limitations
            KeywordEntry("one year limitation", 2.0, "Short statute of limitations"),
            KeywordEntry("6 month limitation", 2.5, "Very short limitation period"),
            KeywordEntry("must bring claim within", 1.5, "Limitation period"),
            KeywordEntry("shortened limitation", 2.0, "Shortened limitation period"),
        ]
    
    # ========== COMPLIANCE KEYWORDS ==========
    def _get_compliance_keywords(self) -> list[KeywordEntry]:
        return [
            # Regulatory compliance
            KeywordEntry("shall comply with all applicable laws", 1.0, "General compliance"),
            KeywordEntry("responsible for compliance", 2.0, "Compliance responsibility"),
            KeywordEntry("sole responsibility for compliance", 2.5, "Sole compliance burden"),
            KeywordEntry("all regulatory requirements", 1.5, "Regulatory requirements"),
            KeywordEntry("all applicable regulations", 1.0, "Regulatory compliance"),
            KeywordEntry("regulatory violations", 2.0, "Violation responsibility"),
            
            # Permits and licenses
            KeywordEntry("obtain all necessary permits", 2.0, "Permit obligation"),
            KeywordEntry("at own expense", 1.5, "Cost burden indicator"),
            KeywordEntry("all necessary licenses", 1.5, "License requirements"),
            KeywordEntry("maintain all permits", 1.5, "Ongoing permit requirement"),
            KeywordEntry("shall obtain at its expense", 2.0, "Cost obligation"),
            KeywordEntry("responsible for obtaining", 1.5, "Obligation to obtain"),
            
            # Strict liability
            KeywordEntry("strict liability", 2.5, "Strict liability standard"),
            KeywordEntry("strictly liable", 2.5, "Strict liability"),
            KeywordEntry("regardless of fault", 2.5, "Liability without fault"),
            KeywordEntry("without regard to negligence", 2.5, "Liability without negligence"),
            KeywordEntry("absolute liability", 3.0, "Absolute liability"),
            
            # Audits
            KeywordEntry("subject to audit", 1.5, "Audit rights"),
            KeywordEntry("unlimited audit", 2.5, "Unlimited audit rights"),
            KeywordEntry("audit at any time", 2.0, "Unrestricted audit timing"),
            KeywordEntry("audit upon reasonable notice", 1.0, "Standard audit right"),
            KeywordEntry("records retention", 1.0, "Records requirement"),
            KeywordEntry("maintain records for", 1.0, "Records retention period"),
            KeywordEntry("inspection rights", 1.5, "Inspection rights"),
            KeywordEntry("right to inspect", 1.5, "Inspection rights"),
            
            # Reporting
            KeywordEntry("reporting obligations", 1.5, "Reporting requirements"),
            KeywordEntry("shall report", 1.0, "Reporting requirement"),
            KeywordEntry("monthly reporting", 1.0, "Monthly reports"),
            KeywordEntry("quarterly reporting", 1.0, "Quarterly reports"),
            KeywordEntry("provide reports", 1.0, "Report provision"),
            
            # Government
            KeywordEntry("government approval", 2.0, "Government approval required"),
            KeywordEntry("regulatory approval", 1.5, "Regulatory approval"),
            KeywordEntry("government consent", 2.0, "Government consent required"),
            KeywordEntry("prior government approval", 2.0, "Prior government approval"),
            
            # Export/Import
            KeywordEntry("export control", 1.5, "Export controls apply"),
            KeywordEntry("export restrictions", 1.5, "Export restrictions"),
            KeywordEntry("export compliance", 1.5, "Export compliance"),
            KeywordEntry("ITAR", 2.0, "ITAR restrictions"),
            KeywordEntry("EAR", 1.5, "EAR restrictions"),
            KeywordEntry("sanctions", 2.0, "Sanctions compliance"),
            KeywordEntry("OFAC", 2.0, "OFAC compliance"),
            
            # Industry-specific
            KeywordEntry("HIPAA", 1.5, "HIPAA compliance"),
            KeywordEntry("GDPR", 1.5, "GDPR compliance"),
            KeywordEntry("PCI DSS", 1.5, "PCI compliance"),
            KeywordEntry("SOC 2", 1.0, "SOC 2 compliance"),
            KeywordEntry("ISO 27001", 1.0, "ISO compliance"),
            KeywordEntry("CCPA", 1.5, "CCPA compliance"),
            
            # Certifications
            KeywordEntry("shall certify", 1.5, "Certification requirement"),
            KeywordEntry("provide certification", 1.5, "Certification obligation"),
            KeywordEntry("annual certification", 1.5, "Annual certification"),
            KeywordEntry("written certification", 1.0, "Written certification"),
        ]
    
    # ========== OPERATIONAL KEYWORDS ==========
    def _get_operational_keywords(self) -> list[KeywordEntry]:
        return [
            # Performance standards
            KeywordEntry("time is of the essence", 2.5, "Strict time requirements"),
            KeywordEntry("time shall be of the essence", 2.5, "Strict timing"),
            KeywordEntry("strict compliance", 2.0, "Strict compliance required"),
            KeywordEntry("material breach", 1.5, "Material breach standard"),
            KeywordEntry("substantial performance", 1.0, "Substantial performance"),
            KeywordEntry("best efforts", 1.0, "Best efforts standard"),
            KeywordEntry("commercially reasonable efforts", 0.5, "Reasonable efforts (good)"),
            KeywordEntry("reasonable efforts", 0.5, "Reasonable efforts (good)"),
            
            # SLAs
            KeywordEntry("service level agreement", 1.0, "SLA mentioned"),
            KeywordEntry("SLA", 1.0, "SLA mentioned"),
            KeywordEntry("uptime", 1.0, "Uptime requirement"),
            KeywordEntry("99.9%", 1.0, "High uptime requirement"),
            KeywordEntry("99.99%", 1.5, "Very high uptime"),
            KeywordEntry("service credits", 0.5, "Service credits (remedy)"),
            KeywordEntry("response time", 1.0, "Response time requirements"),
            KeywordEntry("resolution time", 1.0, "Resolution time requirements"),
            
            # Force majeure
            KeywordEntry("force majeure", 0.5, "Force majeure provision"),
            KeywordEntry("act of God", 0.5, "Force majeure provision"),
            KeywordEntry("no force majeure", 2.5, "No force majeure protection"),
            KeywordEntry("force majeure shall not apply", 2.5, "FM exclusion"),
            KeywordEntry("excused from performance", 0.5, "Performance excuse"),
            KeywordEntry("beyond reasonable control", 0.5, "FM language"),
            KeywordEntry("including pandemic", 0.5, "Pandemic FM coverage"),
            
            # Approval rights
            KeywordEntry("requires prior written approval", 2.0, "Prior approval needed"),
            KeywordEntry("subject to approval", 1.5, "Approval requirement"),
            KeywordEntry("consent required", 1.5, "Consent requirement"),
            KeywordEntry("prior written consent", 1.5, "Written consent needed"),
            KeywordEntry("shall not unreasonably withhold", 0.5, "Reasonable consent"),
            KeywordEntry("in its sole discretion", 2.5, "Discretionary approval"),
            KeywordEntry("may withhold consent", 2.0, "May refuse consent"),
            KeywordEntry("absolute discretion", 2.5, "Absolute discretion"),
            
            # Exclusivity
            KeywordEntry("exclusive dealing", 2.5, "Exclusive dealing requirement"),
            KeywordEntry("exclusive arrangement", 2.0, "Exclusive arrangement"),
            KeywordEntry("sole and exclusive", 2.5, "Sole and exclusive"),
            KeywordEntry("exclusive right", 2.0, "Exclusive rights"),
            KeywordEntry("shall not deal with", 2.0, "Dealing restriction"),
            KeywordEntry("shall not contract with", 2.0, "Contracting restriction"),
            KeywordEntry("non-exclusive", 0.5, "Non-exclusive (good)"),
            
            # Non-compete
            KeywordEntry("non-compete", 2.0, "Non-compete provision"),
            KeywordEntry("non-competition", 2.0, "Non-competition provision"),
            KeywordEntry("shall not compete", 2.5, "Competition restriction"),
            KeywordEntry("competing business", 2.0, "Competing business restriction"),
            KeywordEntry("compete within", 2.0, "Competition scope"),
            KeywordEntry("competitive activity", 2.0, "Competitive activity restriction"),
            
            # Non-solicitation
            KeywordEntry("non-solicitation", 1.5, "Non-solicitation provision"),
            KeywordEntry("shall not solicit", 1.5, "Solicitation restriction"),
            KeywordEntry("employee solicitation", 1.5, "Employee solicitation restriction"),
            KeywordEntry("customer solicitation", 1.5, "Customer solicitation restriction"),
            
            # Change control
            KeywordEntry("change order", 1.0, "Change order process"),
            KeywordEntry("change request", 1.0, "Change request process"),
            KeywordEntry("scope change", 1.0, "Scope change process"),
            KeywordEntry("modification requires written", 0.5, "Written modification (good)"),
            KeywordEntry("no oral modification", 0.5, "No oral mod (good)"),
            
            # Assignment
            KeywordEntry("may assign", 1.5, "Assignment permitted"),
            KeywordEntry("shall not assign", 1.0, "Assignment restricted"),
            KeywordEntry("may not assign without", 1.0, "Conditional assignment"),
            KeywordEntry("freely assignable", 2.0, "Free assignment"),
            KeywordEntry("assignment requires consent", 1.0, "Assignment consent"),
            KeywordEntry("change of control", 1.5, "Change of control provision"),
            
            # Subcontracting
            KeywordEntry("may subcontract", 1.5, "Subcontracting permitted"),
            KeywordEntry("shall not subcontract", 1.5, "No subcontracting"),
            KeywordEntry("remains responsible for subcontractor", 1.5, "Subcontractor liability"),
            KeywordEntry("subcontractor performance", 1.5, "Subcontractor obligations"),
        ]
    
    def search_all(self, text: str) -> dict[RiskCategory, list[tuple[KeywordEntry, list[tuple[int, int, str]]]]]:
        """
        Search text for all keyword matches across all categories.
        Returns dict mapping category to list of (keyword, matches) tuples.
        Each match is (start, end, matched_text).
        """
        results = {}
        for category in self._compiled_patterns:
            category_results = []
            for pattern, keyword in self._compiled_patterns[category]:
                matches = []
                for match in pattern.finditer(text):
                    matches.append((match.start(), match.end(), match.group()))
                if matches:
                    category_results.append((keyword, matches))
            if category_results:
                results[category] = category_results
        return results
    
    def search_category(self, text: str, category: RiskCategory) -> list[tuple[KeywordEntry, list[tuple[int, int, str]]]]:
        """Search text for keywords in a specific category"""
        results = []
        if category not in self._compiled_patterns:
            return results
        
        for pattern, keyword in self._compiled_patterns[category]:
            matches = []
            for match in pattern.finditer(text):
                matches.append((match.start(), match.end(), match.group()))
            if matches:
                results.append((keyword, matches))
        return results
    
    def get_context(self, text: str, start: int, end: int, context_chars: int = 100) -> str:
        """Get surrounding context for a match"""
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        
        prefix = "..." if context_start > 0 else ""
        suffix = "..." if context_end < len(text) else ""
        
        return prefix + text[context_start:context_end] + suffix
