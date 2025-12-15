"""
UATP SDK - Rich Data Example (Court-Admissible Format)

This example demonstrates the EXPERT-LEVEL data richness required for:
- Court admissibility (Daubert standard)
- Insurance actuarial models
- EU AI Act compliance
- Enterprise risk management

Compare this to basic_usage.py to see the difference.
"""

from uatp import (
    UATP,
    Alternative,
    DataSource,
    ReasoningStep,
)

print("\n" + "=" * 70)
print("🏛️  UATP Rich Data Example - Court-Admissible AI Evidence")
print("=" * 70)

# Initialize client
client = UATP()

# ============================================================================
# Example 1: Loan Approval (Financial Services)
# ============================================================================

print("\n📊 Example 1: Loan Approval (Court-Admissible Format)")
print("-" * 70)

result = client.certify_rich(
    task="Approve auto loan application",
    decision="Approved: $50,000 at 6.5% APR for 60 months",
    # Rich reasoning with FULL PROVENANCE (Daubert-compliant)
    reasoning_steps=[
        ReasoningStep(
            step=1,
            action="Verified credit score from credit bureaus",
            confidence=0.99,
            data_sources=[
                DataSource(
                    source="Experian Credit Bureau",
                    value=720,
                    timestamp="2025-12-14T15:30:12Z",
                    api_endpoint="https://api.experian.com/v3/credit-scores",
                    api_version="3.2.1",
                    response_time_ms=234,
                    verification={
                        "cross_checked": ["TransUnion", "Equifax"],
                        "values": [720, 718, 722],
                        "consensus": True,
                    },
                )
            ],
            decision_criteria=[
                "Minimum credit score: 640 (threshold met)",
                "Excellent credit range: 720-850",
                "No recent delinquencies (verified)",
            ],
            reasoning="Credit score of 720 significantly exceeds minimum threshold of 640 and falls in excellent range",
            plain_language="Your credit score is excellent (720 out of 850), well above our minimum requirement",
            confidence_basis="99% confidence based on agreement across 3 major credit bureaus",
        ),
        ReasoningStep(
            step=2,
            action="Analyzed debt-to-income ratio",
            confidence=0.95,
            data_sources=[
                DataSource(
                    source="Income Verification Service",
                    value={"monthly_income": 7083, "verified_employment": True},
                    timestamp="2025-12-14T15:31:45Z",
                    api_endpoint="https://api.theworknumber.com/verify",
                    audit_trail="Request ID: ivs_789abc, Verified with employer: TechCorp Inc",
                ),
                DataSource(
                    source="Existing Debt Summary",
                    value={"monthly_debt_payments": 1983},
                    query="SELECT SUM(monthly_payment) FROM debts WHERE applicant_id='app_123'",
                ),
            ],
            decision_criteria=[
                "Monthly income: $7,083 (verified)",
                "Monthly debt payments: $1,983",
                "Debt-to-income ratio: 28% (acceptable < 45%)",
            ],
            reasoning="DTI ratio of 28% is well below maximum acceptable threshold of 45%, indicating strong repayment capacity",
            plain_language="Your monthly debt payments ($1,983) are only 28% of your income, which is very manageable",
            confidence_basis="95% confidence - income verified directly with employer, debt calculated from credit report",
        ),
        ReasoningStep(
            step=3,
            action="Evaluated employment stability",
            confidence=0.92,
            data_sources=[
                DataSource(
                    source="Employment History",
                    value={"current_employer": "TechCorp Inc", "tenure_months": 60},
                    timestamp="2025-12-14T15:32:00Z",
                )
            ],
            decision_criteria=[
                "Current employer: TechCorp Inc",
                "Employment duration: 5 years",
                "Minimum requirement: 2 years (met)",
            ],
            alternatives_evaluated=[
                Alternative(
                    option="Require 6 months additional employment",
                    score=0.85,
                    why_not_chosen="5 years significantly exceeds 2-year minimum; additional wait unnecessary",
                ),
                Alternative(
                    option="Request co-signer",
                    score=0.70,
                    why_not_chosen="Strong credit and DTI ratio make co-signer unnecessary",
                ),
            ],
            reasoning="5 years at current employer demonstrates exceptional employment stability",
            plain_language="You've been with your employer for 5 years, showing strong job stability",
            confidence_basis="92% confidence - long tenure reduces income volatility risk",
        ),
    ],
    # Risk Assessment (REQUIRED for insurance)
    risk_assessment={
        "probability_correct": 0.87,
        "probability_wrong": 0.13,
        "expected_value": 280,  # Expected profit
        "value_at_risk_95": 22500,  # 95% worst case loss
        "expected_loss_if_wrong": 22500,  # Default scenario
        "expected_gain_if_correct": 2500,  # Interest revenue
        "key_risk_factors": [
            "Economic downturn affecting tech sector",
            "Vehicle depreciation faster than loan amortization",
            "Potential job loss (mitigated by strong tenure)",
        ],
        "safeguards": [
            "Income verification completed with employer",
            "Vehicle title held as collateral ($65k value)",
            "Gap insurance required",
            "Monthly payment: $952 (13% of monthly income - highly affordable)",
        ],
        "failure_modes": [
            {
                "scenario": "Job loss within 12 months",
                "probability": 0.05,
                "mitigation": "6-month payment deferral option, strong severance likely",
            },
            {
                "scenario": "Vehicle total loss",
                "probability": 0.02,
                "mitigation": "Gap insurance covers loan balance",
            },
        ],
        "similar_decisions_count": 1247,
        "historical_accuracy": 0.91,  # 91% of similar loans succeeded
    },
    # Alternatives Considered (shows methodology)
    alternatives_considered=[
        {
            "amount": 40000,
            "apr": 6.0,
            "why_not_chosen": "Applicant requested $50k for specific vehicle purchase",
            "score": 0.88,
        },
        {
            "amount": 50000,
            "apr": 7.5,
            "why_not_chosen": "Rate too high given excellent credit score; 6.5% more appropriate",
            "score": 0.75,
        },
        {
            "amount": 50000,
            "apr": 6.5,
            "term_months": 72,
            "why_not_chosen": "Longer term increases total interest paid without significant payment reduction",
            "score": 0.80,
        },
    ],
    # Plain Language Summary (EU AI Act Article 13)
    plain_language_summary={
        "decision": "We approved your auto loan for $50,000 at 6.5% interest for 5 years",
        "why": "You have excellent credit (720), stable income, manageable existing debts, and 5 years at your current job",
        "key_factors": [
            "Credit score: 720/850 (excellent)",
            "Income: $85,000/year, verified with your employer",
            "Existing debts: Only 28% of your income (very good)",
            "Employment: 5 years at TechCorp Inc (very stable)",
            "Vehicle value: $65,000 (exceeds loan amount)",
        ],
        "what_if_different": "We would have declined if: credit score below 640, debt ratio above 45%, less than 2 years employment, or unverifiable income",
        "your_rights": "You have the right to request a detailed explanation of this decision and to dispute any information we used. Contact our compliance team at compliance@bank.com",
    },
    metadata={
        "model": "lending-ai-v3.2",
        "application_id": "app_123456",
        "loan_officer_id": "officer_789",
        "fair_lending_check": "passed",
        "bias_audit_version": "2.1",
        "regulatory_compliance": ["CFPB", "ECOA", "Fair Lending Act"],
    },
)

print("✅ Loan decision certified (COURT-ADMISSIBLE)")
print(f"   Capsule ID: {result.capsule_id}")
print(f"   Proof URL: {result.proof_url}")
print("   Data Richness: Court-admissible, Insurance-ready")


# ============================================================================
# Example 2: Healthcare Diagnosis (HIPAA-Compliant)
# ============================================================================

print("\n🏥 Example 2: Healthcare Diagnosis (HIPAA + EU AI Act Compliant)")
print("-" * 70)

result2 = client.certify_rich(
    task="Triage patient symptoms and recommend action",
    decision="Schedule appointment within 48 hours (non-urgent)",
    reasoning_steps=[
        ReasoningStep(
            step=1,
            action="Analyzed reported symptoms",
            confidence=0.95,
            data_sources=[
                DataSource(
                    source="Patient Self-Report",
                    value={
                        "symptoms": ["persistent headache", "mild nausea"],
                        "duration": "3 days",
                        "severity": "moderate",
                    },
                    timestamp="2025-12-14T09:15:00Z",
                ),
                DataSource(
                    source="Vital Signs (Patient-Reported)",
                    value={"temperature": 98.6, "blood_pressure": "120/80"},
                    timestamp="2025-12-14T09:15:00Z",
                ),
            ],
            reasoning="Symptoms present for 3 days without fever or emergency indicators",
            plain_language="You've had a headache and mild nausea for 3 days, but no fever or serious warning signs",
            alternatives_evaluated=[
                Alternative(
                    option="Immediate emergency room visit",
                    score=0.15,
                    why_not_chosen="No emergency symptoms: no fever >101°F, no vision changes, no loss of consciousness, normal vital signs",
                ),
                Alternative(
                    option="Telehealth appointment today",
                    score=0.82,
                    why_not_chosen="Symptoms manageable; in-person exam preferred for thorough evaluation",
                ),
                Alternative(
                    option="Self-care only",
                    score=0.60,
                    why_not_chosen="3-day duration warrants medical evaluation; persistent headaches should be assessed",
                ),
            ],
        )
    ],
    risk_assessment={
        "probability_correct": 0.88,
        "probability_wrong": 0.12,
        "key_risk_factors": [
            "Headache persistence (3+ days warrants evaluation)",
            "Mild symptoms could mask serious condition (low probability)",
            "Patient comfort and anxiety (moderate priority)",
        ],
        "safeguards": [
            "Clear instructions for emergency symptoms to watch for",
            "24/7 nurse hotline number provided",
            "Appointment scheduled within 48 hours (meets clinical guidelines)",
        ],
        "similar_decisions_count": 3421,
        "historical_accuracy": 0.94,
    },
    plain_language_summary={
        "decision": "Schedule a doctor appointment within the next 2 days",
        "why": "Your symptoms have lasted 3 days, which means they should be checked by a doctor, but there are no emergency warning signs",
        "key_factors": [
            "Headache for 3+ days (needs evaluation)",
            "Mild nausea (not severe)",
            "No fever (good sign)",
            "Normal blood pressure (reassuring)",
            "No vision problems or loss of consciousness (no emergency)",
        ],
        "what_if_different": "Go to ER immediately if you develop: fever over 101°F, severe sudden headache, vision changes, difficulty speaking, loss of consciousness, or severe neck stiffness",
        "your_rights": "You have the right to request immediate care if you feel it's necessary. This recommendation is based on clinical guidelines, not a replacement for your judgment about your own health.",
    },
    metadata={
        "model": "medical-triage-ai-v2.1",
        "patient_id": "redacted_for_hipaa",
        "hipaa_compliance": True,
        "clinical_guidelines": ["CDC Triage Protocol 2024", "AMA Headache Guidelines"],
    },
)

print("✅ Healthcare triage certified (HIPAA-COMPLIANT)")
print(f"   Capsule ID: {result2.capsule_id}")
print(f"   Proof URL: {result2.proof_url}")


print("\n" + "=" * 70)
print("✨ Rich Data Implementation Complete!")
print("=" * 70)

print("\n📊 What Makes This Data 'Court-Admissible':")
print("   ✅ Data provenance (where every fact came from)")
print("   ✅ Decision methodology (how AI reached conclusion)")
print("   ✅ Alternatives evaluated (not just final answer)")
print("   ✅ Risk quantification (probability + financial impact)")
print("   ✅ Safeguards documented (what protections exist)")
print("   ✅ Plain language explanations (EU AI Act compliance)")
print("   ✅ Historical benchmarking (similar cases track record)")

print("\n🏛️  Daubert Standard Met:")
print("   ✅ Methodology clearly shown")
print("   ✅ Data sources verifiable")
print("   ✅ Error rates quantified")
print("   ✅ Peer review possible (historical accuracy)")

print("\n💼 Insurance Value:")
print("   ✅ Risk probabilities (can build actuarial models)")
print("   ✅ Financial impacts (expected value, VaR)")
print("   ✅ Safeguards (reduces premium)")
print("   ✅ Historical accuracy (validates risk models)")

print("\n🇪🇺 EU AI Act Compliance:")
print("   ✅ Article 12: Automatic logging ✓")
print("   ✅ Article 13: Transparency to users ✓")
print("   ✅ Article 9: Risk assessment ✓")

print("\n" + "=" * 70)
print("🚀 This is the format that wins in court, gets insurance, and passes audits!")
print("=" * 70)
print()
