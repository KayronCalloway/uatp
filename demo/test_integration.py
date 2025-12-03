#!/usr/bin/env python3
"""
Integration Test for E2E Demo
=============================

Simple test to validate that the end-to-end integration demo
components work correctly without running the full demo.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.dividend_bonds_service import dividend_bonds_service
from src.services.citizenship_service import citizenship_service


async def test_basic_integration():
    """Test basic integration between services."""

    print("🧪 Running Integration Test")
    print("=" * 40)

    # Test 1: Register IP Asset
    print("1️⃣ Testing IP Asset Registration...")
    try:
        asset = dividend_bonds_service.register_ip_asset(
            asset_id="test_integration_asset",
            asset_type="ai_models",
            owner_agent_id="test_agent",
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.9},
        )
        print(f"   ✅ Asset registered: {asset.asset_id}")
    except Exception as e:
        print(f"   ❌ Asset registration failed: {e}")
        return False

    # Test 2: Apply for Citizenship
    print("2️⃣ Testing Citizenship Application...")
    try:
        application_id = citizenship_service.apply_for_citizenship(
            agent_id="test_agent",
            jurisdiction="ai_rights_territory",
            citizenship_type="full",
        )
        print(f"   ✅ Application submitted: {application_id}")
    except Exception as e:
        print(f"   ❌ Citizenship application failed: {e}")
        return False

    # Test 3: Create Dividend Bond
    print("3️⃣ Testing Dividend Bond Creation...")
    try:
        capsule = dividend_bonds_service.create_dividend_bond_capsule(
            ip_asset_id="test_integration_asset",
            bond_type="revenue",
            issuer_agent_id="test_agent",
            face_value=25000.0,
            maturity_days=365,
        )
        print(f"   ✅ Bond created: {capsule.dividend_bond.bond_id}")
    except Exception as e:
        print(f"   ❌ Bond creation failed: {e}")
        return False

    # Test 4: Cross-Service Data Access
    print("4️⃣ Testing Cross-Service Integration...")
    try:
        # Get active bonds
        bonds = dividend_bonds_service.get_active_bonds("test_agent")
        print(f"   ✅ Found {len(bonds)} bonds for agent")

        # Get pending applications
        applications = citizenship_service.get_pending_applications(
            "ai_rights_territory"
        )
        print(f"   ✅ Found {len(applications)} pending applications")
    except Exception as e:
        print(f"   ❌ Cross-service access failed: {e}")
        return False

    print("\n✅ All integration tests passed!")
    return True


async def main():
    """Main test execution."""
    success = await test_basic_integration()

    if success:
        print("\n🎉 Integration test completed successfully!")
        print("   Ready to run full E2E demo")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed!")
        print("   Please fix issues before running demo")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
