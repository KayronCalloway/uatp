#!/usr/bin/env python3
"""
Clear hardcoded mock data from frontend components to match empty production database
"""

# Read compliance dashboard
with open(
    "/Users/kay/uatp-capsule-engine/frontend/src/components/compliance/compliance-dashboard.tsx",
    "r",
) as f:
    compliance_content = f.read()

# Replace mock data with empty arrays in compliance dashboard
compliance_content = compliance_content.replace(
    """  const mockStats: ComplianceStats = {
    total_frameworks: 8,
    active_frameworks: 6,
    overall_compliance_score: 0.89,
    open_violations: 12,
    resolved_this_month: 28,
    upcoming_assessments: 3
  };""",
    """  const mockStats: ComplianceStats = {
    total_frameworks: 0,
    active_frameworks: 0,
    overall_compliance_score: 0,
    open_violations: 0,
    resolved_this_month: 0,
    upcoming_assessments: 0
  };""",
)

# Find and replace the mockFrameworks array - replace everything between the brackets
import re

# Replace mockFrameworks array with empty array
compliance_content = re.sub(
    r"const mockFrameworks: ComplianceFramework\[\] = \[.*?\];",
    "const mockFrameworks: ComplianceFramework[] = [];",
    compliance_content,
    flags=re.DOTALL,
)

# Replace mockViolations array with empty array
compliance_content = re.sub(
    r"const mockViolations: ComplianceViolation\[\] = \[.*?\];",
    "const mockViolations: ComplianceViolation[] = [];",
    compliance_content,
    flags=re.DOTALL,
)

# Write back compliance dashboard
with open(
    "/Users/kay/uatp-capsule-engine/frontend/src/components/compliance/compliance-dashboard.tsx",
    "w",
) as f:
    f.write(compliance_content)

print("✅ Cleared mock data from compliance dashboard")

# Read payment dashboard
with open(
    "/Users/kay/uatp-capsule-engine/frontend/src/components/payments/payment-dashboard.tsx",
    "r",
) as f:
    payment_content = f.read()

# Replace mock data with empty/zero values in payment dashboard
payment_content = payment_content.replace(
    """  const mockSummary: PayoutSummary = {
    total_earned: 12847.50,
    total_paid: 10250.00,
    pending_payouts: 2597.50,
    this_month_earnings: 3420.00,
    last_payout_date: new Date(Date.now() - 86400000 * 15).toISOString(),
    next_payout_date: new Date(Date.now() + 86400000 * 15).toISOString()
  };""",
    """  const mockSummary: PayoutSummary = {
    total_earned: 0,
    total_paid: 0,
    pending_payouts: 0,
    this_month_earnings: 0,
    last_payout_date: '',
    next_payout_date: ''
  };""",
)

# Replace mockPaymentMethods array with empty array
payment_content = re.sub(
    r"const mockPaymentMethods: PaymentMethod\[\] = \[.*?\];",
    "const mockPaymentMethods: PaymentMethod[] = [];",
    payment_content,
    flags=re.DOTALL,
)

# Replace mockTransactions array with empty array
payment_content = re.sub(
    r"const mockTransactions: Transaction\[\] = \[.*?\];",
    "const mockTransactions: Transaction[] = [];",
    payment_content,
    flags=re.DOTALL,
)

# Write back payment dashboard
with open(
    "/Users/kay/uatp-capsule-engine/frontend/src/components/payments/payment-dashboard.tsx",
    "w",
) as f:
    f.write(payment_content)

print("✅ Cleared mock data from payment dashboard")

print("\n" + "=" * 60)
print("FRONTEND MOCK DATA CLEANUP COMPLETE")
print("=" * 60)
print("\nAll hardcoded demo data removed from:")
print("  - Compliance Dashboard (stats, frameworks, violations)")
print("  - Payment Dashboard (summary, methods, transactions)")
print("\nFrontend now displays empty state matching production database.")
print("=" * 60)
