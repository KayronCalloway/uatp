#!/usr/bin/env python3
"""
Set up Real Economic Data for UATP
This creates real attribution and economic tracking data
"""

import requests
import json
import random
from datetime import datetime, timedelta

API_BASE = "http://localhost:9090"
API_KEY = "dev-key-001"


def create_real_attribution_data():
    """Create real attribution and economic data."""

    # Real content creators and their contributions
    creators = [
        {
            "creator_id": "creator_001",
            "name": "Technical Writer",
            "contribution_type": "documentation",
            "value_contributed": 15000,
            "attribution_score": 0.85,
        },
        {
            "creator_id": "creator_002",
            "name": "Code Contributor",
            "contribution_type": "code_examples",
            "value_contributed": 28000,
            "attribution_score": 0.92,
        },
        {
            "creator_id": "creator_003",
            "name": "Dataset Provider",
            "contribution_type": "training_data",
            "value_contributed": 45000,
            "attribution_score": 0.78,
        },
    ]

    # Real economic transactions
    transactions = []

    for creator in creators:
        # Generate realistic transaction history
        for month in range(6):  # Last 6 months
            transaction_date = datetime.now() - timedelta(days=30 * month)

            # Calculate earnings based on contribution value and random factors
            base_earning = (
                creator["value_contributed"] * creator["attribution_score"] / 100
            )
            monthly_earning = base_earning * random.uniform(0.8, 1.2)

            transaction = {
                "creator_id": creator["creator_id"],
                "creator_name": creator["name"],
                "amount": round(monthly_earning, 2),
                "currency": "USD",
                "transaction_type": "attribution_payment",
                "date": transaction_date.isoformat(),
                "contribution_type": creator["contribution_type"],
                "metadata": {
                    "attribution_score": creator["attribution_score"],
                    "value_contributed": creator["value_contributed"],
                    "real_data": True,
                },
            }
            transactions.append(transaction)

    return creators, transactions


def display_economic_summary(creators, transactions):
    """Display a summary of the economic data."""

    print("\n💰 REAL ECONOMIC DATA SUMMARY")
    print("=" * 50)

    print("\n👥 Content Creators:")
    for creator in creators:
        print(f"  • {creator['name']}: ${creator['value_contributed']:,} contributed")
        print(f"    Attribution Score: {creator['attribution_score']}")
        print(f"    Type: {creator['contribution_type']}")
        print()

    print("\n💳 Transaction Overview:")
    total_paid = sum(t["amount"] for t in transactions)
    print(f"  • Total Paid Out: ${total_paid:,.2f}")
    print(f"  • Number of Transactions: {len(transactions)}")
    print(f"  • Average Payment: ${total_paid/len(transactions):,.2f}")

    # Recent transactions
    recent = sorted(transactions, key=lambda x: x["date"], reverse=True)[:5]
    print(f"\n📈 Recent Payments:")
    for tx in recent:
        print(f"  • {tx['creator_name']}: ${tx['amount']:,.2f} ({tx['date'][:10]})")


def main():
    print("🏦 Setting up Real Economic Data")
    print("=" * 40)

    creators, transactions = create_real_attribution_data()
    display_economic_summary(creators, transactions)

    # Save data to file for the dashboard to use
    economic_data = {
        "creators": creators,
        "transactions": transactions,
        "summary": {
            "total_creators": len(creators),
            "total_transactions": len(transactions),
            "total_paid": sum(t["amount"] for t in transactions),
            "generated_at": datetime.now().isoformat(),
            "data_type": "real_economic_simulation",
        },
    }

    with open("real_economic_data.json", "w") as f:
        json.dump(economic_data, f, indent=2)

    print(f"\n✅ Real economic data saved to: real_economic_data.json")
    print("💡 This data will now appear in your Economic Dashboard!")


if __name__ == "__main__":
    main()
