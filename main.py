"""
GenLegalAI - Risk Assessment Module

A comprehensive legal document risk assessment system that:
1. Instantly scans documents for known dangerous patterns (Rule-Based Layer)
2. Deeply analyzes each clause using AI (Groq Llama 3.1 70B)
3. Scores risks from 0-100 with confidence levels
4. Categorizes risks into meaningful buckets
5. Generates actionable recommendations
6. Visualizes risk distribution
7. Prioritizes issues for action

Usage:
    # Run Streamlit UI
    streamlit run app.py
    
    # Or use programmatically
    from risk_assessment import RiskAssessmentEngine
    
    engine = RiskAssessmentEngine(api_key="your_groq_key")
    result = engine.analyze_document(contract_text)
    print(result.risk_summary.overall_score)
"""

import os
import sys


def main():
    """Main entry point for GenLegalAI Risk Assessment"""
    print("=" * 60)
    print("GenLegalAI - Legal Contract Risk Assessment")
    print("=" * 60)
    print()
    
    # Check if running demo
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    elif len(sys.argv) > 1 and sys.argv[1] == "ui":
        run_streamlit()
    else:
        print("Usage:")
        print("  python main.py demo    - Run a demo analysis")
        print("  python main.py ui      - Launch Streamlit UI")
        print("  streamlit run app.py   - Launch Streamlit UI directly")
        print()
        print("Or use as a library:")
        print("  from risk_assessment import RiskAssessmentEngine")
        print("  engine = RiskAssessmentEngine()")
        print("  result = engine.analyze_document(text)")


def run_demo():
    """Run a demo analysis on a sample contract"""
    print("Running demo analysis...")
    print()
    
    # Import the engine
    from risk_assessment import RiskAssessmentEngine
    
    # Sample contract clause
    sample_contract = """
    SERVICE AGREEMENT
    
    1. INDEMNIFICATION
    The Customer shall indemnify and hold harmless the Provider from any and all claims, 
    damages, losses, and expenses arising from Customer's use of the Services. This 
    indemnification is unlimited and irrevocable.
    
    2. LIMITATION OF LIABILITY
    Provider shall not be liable for any consequential, incidental, or indirect damages. 
    Provider's total liability shall be limited to $1,000 regardless of circumstances.
    
    3. TERMINATION
    This Agreement automatically renews annually unless terminated by Provider. Customer 
    may not terminate for convenience. Termination fee equal to 50% of annual fees applies.
    
    4. CONFIDENTIALITY
    Both parties agree to maintain confidentiality of the other's information for 3 years.
    Standard exceptions apply for publicly available information.
    
    5. PAYMENT
    Payment is due Net-30. Late fees of 1.5% per month apply. All fees are non-refundable.
    """
    
    # Create engine (without AI for demo - no API key needed)
    engine = RiskAssessmentEngine(use_ai=False)
    
    # Analyze document
    print("Analyzing sample contract...")
    result = engine.analyze_document(sample_contract, "sample_contract.txt")
    
    # Print results
    print()
    print("=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print()
    print(f"Overall Risk Score: {result.risk_summary.overall_score}/100")
    print(f"Risk Level: {result.risk_summary.overall_level.value}")
    print(f"Favorability: {result.overall_favorability}")
    print()
    
    print("Risk Distribution:")
    dist = result.risk_summary.distribution
    print(f"  🚨 Critical: {dist.critical}")
    print(f"  🔶 High: {dist.high}")
    print(f"  ⚠️  Medium: {dist.medium}")
    print(f"  ✅ Low: {dist.low}")
    print()
    
    print("Executive Summary:")
    print(f"  {result.executive_summary}")
    print()
    
    if result.top_risks:
        print("Top Risks:")
        for risk in result.top_risks[:3]:
            print(f"  {risk.rank}. {risk.clause_reference} (Score: {risk.score})")
            print(f"     Issue: {risk.issue}")
            print(f"     Action: {risk.action}")
            print()
    
    print("Action Plan:")
    for item in result.action_plan:
        print(f"  {item}")
    print()
    
    print("=" * 60)
    print("Demo complete!")
    print()
    print("For AI-powered analysis, set GROQ_API_KEY environment variable")
    print("and run: streamlit run app.py")


def run_streamlit():
    """Launch the Streamlit UI"""
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()
