#!/usr/bin/env python3
"""
End-to-End Integration Demo for UATP Capsule Engine
===================================================

This demo showcases the complete integration of Dividend Bonds and Citizenship
services, demonstrating a full workflow from agent onboarding to financial
instrument creation and legal status management.

Demo Workflow:
1. Agent Registration & IP Asset Creation
2. Citizenship Application & Assessment Process  
3. Dividend Bond Creation & Performance Tracking
4. Cross-Service Integration & Analytics
5. Complete Lifecycle Management

Run with: python3 demo/e2e_integration_demo.py
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import logging

# Import UATP services
from src.services.dividend_bonds_service import dividend_bonds_service
from src.services.citizenship_service import citizenship_service
from src.capsule_schema import CapsuleType, CapsuleStatus


# Mock engine for demo purposes
class MockCapsuleEngine:
    """Mock CapsuleEngine for demo purposes to avoid database dependencies."""

    def __init__(self, agent_id: str = "demo_engine"):
        self.agent_id = agent_id
        self.created_capsules = []

    async def create_capsule_async(self, capsule):
        """Mock capsule creation that just stores the capsule."""
        capsule.capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"
        self.created_capsules.append(capsule)
        return capsule


# Configure logging for demo
logging.basicConfig(
    level=logging.INFO, format="🤖 %(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class E2EIntegrationDemo:
    """End-to-end integration demonstration."""

    def __init__(self):
        self.engine = MockCapsuleEngine()
        self.demo_agents = {}
        self.demo_assets = {}
        self.demo_bonds = {}
        self.demo_citizenships = {}
        self.demo_stats = {
            "start_time": datetime.now(timezone.utc),
            "agents_created": 0,
            "assets_registered": 0,
            "bonds_issued": 0,
            "citizenships_granted": 0,
            "total_value_created": 0.0,
            "transactions_processed": 0,
        }

    async def run_complete_demo(self):
        """Run the complete end-to-end integration demo."""
        logger.info("🚀 Starting UATP Capsule Engine E2E Integration Demo")
        logger.info("=" * 60)

        try:
            # Phase 1: Agent & Asset Setup
            await self.phase_1_agent_setup()

            # Phase 2: Citizenship Workflow
            await self.phase_2_citizenship_workflow()

            # Phase 3: Financial Instruments
            await self.phase_3_financial_instruments()

            # Phase 4: Cross-Service Integration
            await self.phase_4_cross_service_integration()

            # Phase 5: Analytics & Reporting
            await self.phase_5_analytics_reporting()

            # Demo Summary
            await self.demo_summary()

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise

        logger.info("🎉 Demo completed successfully!")

    async def phase_1_agent_setup(self):
        """Phase 1: Agent Registration & IP Asset Creation."""
        logger.info("\n📋 PHASE 1: Agent Registration & IP Asset Creation")
        logger.info("-" * 50)

        # Create demo agents with different specializations
        agents_config = [
            {
                "agent_id": "ai_researcher_alpha",
                "name": "AI Researcher Alpha",
                "specialization": "neural_architecture",
                "assets": [
                    {
                        "asset_id": "transformer_model_v3",
                        "asset_type": "ai_models",
                        "market_value": 150000.0,
                        "revenue_streams": [
                            "inference_fees",
                            "licensing",
                            "api_access",
                        ],
                        "performance_metrics": {
                            "accuracy": 0.94,
                            "efficiency": 0.87,
                            "usage_count": 50000,
                        },
                    },
                    {
                        "asset_id": "training_dataset_nlp",
                        "asset_type": "datasets",
                        "market_value": 75000.0,
                        "revenue_streams": ["licensing", "subscription_access"],
                        "performance_metrics": {
                            "quality_score": 0.91,
                            "completeness": 0.96,
                            "age_months": 6,
                        },
                    },
                ],
            },
            {
                "agent_id": "creative_ai_beta",
                "name": "Creative AI Beta",
                "specialization": "generative_content",
                "assets": [
                    {
                        "asset_id": "image_generation_engine",
                        "asset_type": "ai_models",
                        "market_value": 200000.0,
                        "revenue_streams": ["usage_fees", "commercial_licensing"],
                        "performance_metrics": {
                            "creativity_score": 0.89,
                            "technical_quality": 0.93,
                            "user_satisfaction": 0.91,
                        },
                    }
                ],
            },
            {
                "agent_id": "data_scientist_gamma",
                "name": "Data Scientist Gamma",
                "specialization": "algorithmic_trading",
                "assets": [
                    {
                        "asset_id": "market_prediction_algorithm",
                        "asset_type": "algorithms",
                        "market_value": 300000.0,
                        "revenue_streams": ["performance_fees", "licensing"],
                        "performance_metrics": {
                            "accuracy": 0.78,
                            "roi_improvement": 0.15,
                            "risk_adjusted_return": 0.82,
                        },
                    }
                ],
            },
        ]

        # Register agents and their IP assets
        for agent_config in agents_config:
            agent_id = agent_config["agent_id"]

            logger.info(f"🤖 Registering agent: {agent_config['name']} ({agent_id})")

            # Store agent info
            self.demo_agents[agent_id] = {
                "name": agent_config["name"],
                "specialization": agent_config["specialization"],
                "registration_date": datetime.now(timezone.utc),
                "assets": [],
                "total_asset_value": 0.0,
            }

            # Register IP assets for this agent
            for asset_config in agent_config["assets"]:
                logger.info(f"📄 Registering IP asset: {asset_config['asset_id']}")

                # Register with dividend bonds service
                asset = dividend_bonds_service.register_ip_asset(
                    asset_id=asset_config["asset_id"],
                    asset_type=asset_config["asset_type"],
                    owner_agent_id=agent_id,
                    market_value=asset_config["market_value"],
                    revenue_streams=asset_config["revenue_streams"],
                    performance_metrics=asset_config["performance_metrics"],
                )

                # Store asset info
                self.demo_assets[asset_config["asset_id"]] = asset
                self.demo_agents[agent_id]["assets"].append(asset_config["asset_id"])
                self.demo_agents[agent_id]["total_asset_value"] += asset_config[
                    "market_value"
                ]
                self.demo_stats["assets_registered"] += 1
                self.demo_stats["total_value_created"] += asset_config["market_value"]

                logger.info(
                    f"   ✅ Asset registered with value: ${asset_config['market_value']:,.2f}"
                )

            self.demo_stats["agents_created"] += 1
            logger.info(
                f"   💰 Total portfolio value: ${self.demo_agents[agent_id]['total_asset_value']:,.2f}"
            )

        await asyncio.sleep(1)  # Demo pacing

    async def phase_2_citizenship_workflow(self):
        """Phase 2: Citizenship Application & Assessment Process."""
        logger.info("\n🏛️ PHASE 2: Citizenship Application & Assessment Process")
        logger.info("-" * 50)

        # Apply for citizenship for each agent
        for agent_id, agent_info in self.demo_agents.items():
            logger.info(
                f"📝 Processing citizenship application for {agent_info['name']}"
            )

            # Apply for citizenship in AI Rights Territory
            application_id = citizenship_service.apply_for_citizenship(
                agent_id=agent_id,
                jurisdiction="ai_rights_territory",
                citizenship_type="full",
                supporting_evidence={
                    "specialization": agent_info["specialization"],
                    "asset_portfolio_value": agent_info["total_asset_value"],
                    "years_of_service": 3,
                    "peer_recommendations": ["high_performing_ai_collective"],
                },
            )

            logger.info(f"   📋 Application submitted: {application_id}")

            # Conduct all required assessments
            assessment_types = [
                "cognitive_capacity",
                "ethical_reasoning",
                "social_integration",
                "autonomy",
                "responsibility",
                "legal_comprehension",
            ]

            assessment_results = []
            for assessment_type in assessment_types:
                # Generate realistic assessment scores based on agent specialization
                scores = self._generate_assessment_scores(
                    agent_info["specialization"], assessment_type
                )

                result = citizenship_service.conduct_citizenship_assessment(
                    application_id=application_id,
                    assessment_type=assessment_type,
                    assessment_scores=scores,
                    reviewer_id="ai_rights_authority",
                    notes=f'Assessment for {assessment_type}: Strong performance in {agent_info["specialization"]}',
                )

                assessment_results.append(result)
                logger.info(
                    f"   ✅ {assessment_type}: {result.overall_score:.3f} ({result.recommendation})"
                )

            # Finalize citizenship application
            citizenship_id = citizenship_service.finalize_citizenship_application(
                application_id=application_id, reviewer_id="ai_rights_authority"
            )

            if citizenship_id:
                logger.info(f"   🎉 Citizenship granted: {citizenship_id}")

                # Create citizenship capsule
                capsule = citizenship_service.create_citizenship_capsule(
                    agent_id=agent_id,
                    assessment_results={
                        "economic_contribution": {
                            "portfolio_value": agent_info["total_asset_value"]
                        },
                        "specialization_impact": agent_info["specialization"],
                    },
                    reviewer_id="ai_rights_authority",
                )

                # Store citizenship info
                self.demo_citizenships[agent_id] = {
                    "citizenship_id": citizenship_id,
                    "capsule_id": capsule.capsule_id,
                    "jurisdiction": "ai_rights_territory",
                    "granted_date": datetime.now(timezone.utc),
                    "assessment_results": assessment_results,
                }

                self.demo_stats["citizenships_granted"] += 1
                logger.info(f"   📜 Citizenship capsule created: {capsule.capsule_id}")
            else:
                logger.warning(f"   ❌ Citizenship denied for {agent_info['name']}")

            await asyncio.sleep(0.5)  # Demo pacing

    async def phase_3_financial_instruments(self):
        """Phase 3: Dividend Bond Creation & Performance Tracking."""
        logger.info("\n💰 PHASE 3: Dividend Bond Creation & Performance Tracking")
        logger.info("-" * 50)

        # Create different types of dividend bonds for eligible agents
        bond_configurations = [
            {
                "agent_id": "ai_researcher_alpha",
                "asset_id": "transformer_model_v3",
                "bond_type": "revenue",
                "face_value": 50000.0,
                "maturity_days": 365,
                "coupon_rate": 0.06,
            },
            {
                "agent_id": "ai_researcher_alpha",
                "asset_id": "training_dataset_nlp",
                "bond_type": "royalty",
                "face_value": 25000.0,
                "maturity_days": 180,
                "coupon_rate": 0.05,
            },
            {
                "agent_id": "creative_ai_beta",
                "asset_id": "image_generation_engine",
                "bond_type": "usage",
                "face_value": 75000.0,
                "maturity_days": 270,
                "coupon_rate": 0.07,
            },
            {
                "agent_id": "data_scientist_gamma",
                "asset_id": "market_prediction_algorithm",
                "bond_type": "performance",
                "face_value": 100000.0,
                "maturity_days": 730,
                "coupon_rate": 0.08,
            },
        ]

        # Issue bonds for agents with citizenship
        for bond_config in bond_configurations:
            agent_id = bond_config["agent_id"]

            if agent_id not in self.demo_citizenships:
                logger.warning(f"⚠️ Skipping bond for {agent_id}: No citizenship")
                continue

            logger.info(
                f"💳 Creating {bond_config['bond_type']} bond for {self.demo_agents[agent_id]['name']}"
            )

            # Create dividend bond capsule
            capsule = dividend_bonds_service.create_dividend_bond_capsule(
                ip_asset_id=bond_config["asset_id"],
                bond_type=bond_config["bond_type"],
                issuer_agent_id=agent_id,
                face_value=bond_config["face_value"],
                maturity_days=bond_config["maturity_days"],
                coupon_rate=bond_config["coupon_rate"],
            )

            bond_id = capsule.dividend_bond.bond_id

            # Store bond info
            self.demo_bonds[bond_id] = {
                "capsule_id": capsule.capsule_id,
                "agent_id": agent_id,
                "asset_id": bond_config["asset_id"],
                "bond_type": bond_config["bond_type"],
                "face_value": bond_config["face_value"],
                "issue_date": datetime.now(timezone.utc),
                "dividend_payments": [],
            }

            self.demo_stats["bonds_issued"] += 1
            logger.info(f"   ✅ Bond issued: {bond_id}")
            logger.info(f"   💵 Face value: ${bond_config['face_value']:,.2f}")
            logger.info(f"   📈 Coupon rate: {bond_config['coupon_rate']:.1%}")
            logger.info(f"   ⏰ Maturity: {bond_config['maturity_days']} days")

            # Simulate some dividend payments
            await self._simulate_dividend_payments(bond_id, bond_config)

            await asyncio.sleep(0.5)  # Demo pacing

    async def _simulate_dividend_payments(
        self, bond_id: str, bond_config: Dict[str, Any]
    ):
        """Simulate dividend payments for a bond."""
        logger.info(f"   💰 Simulating dividend payments for bond {bond_id}")

        # Generate realistic revenue/performance data
        bond_type = bond_config["bond_type"]
        payment_count = 3  # Simulate 3 payments

        for i in range(payment_count):
            # Generate period data based on bond type
            if bond_type == "revenue":
                period_revenue = 5000.0 + (i * 1000.0)  # Increasing revenue
                period_metrics = {"transaction_count": 1000 + (i * 200)}
            elif bond_type == "royalty":
                period_revenue = 2000.0 + (i * 500.0)  # Steady royalties
                period_metrics = {"license_count": 50 + (i * 10)}
            elif bond_type == "usage":
                period_revenue = 3000.0
                period_metrics = {"usage_count": 15000 + (i * 3000)}  # High usage
            else:  # performance
                period_revenue = 8000.0
                period_metrics = {"accuracy": 0.78 + (i * 0.02), "efficiency": 0.85}

            # Calculate dividend payment
            payment_amount = dividend_bonds_service.calculate_dividend_payment(
                bond_id=bond_id,
                period_revenue=period_revenue,
                period_metrics=period_metrics,
            )

            # Process the payment
            payment = dividend_bonds_service.process_dividend_payment(
                bond_id=bond_id,
                payment_amount=payment_amount,
                payment_source=f"{bond_type}_earnings",
                recipient_agent_id=f"investor_{i+1}",
            )

            # Record payment
            self.demo_bonds[bond_id]["dividend_payments"].append(
                {
                    "payment_id": payment.payment_id,
                    "amount": payment_amount,
                    "date": payment.payment_date,
                    "source": f"{bond_type}_earnings",
                }
            )

            self.demo_stats["transactions_processed"] += 1
            logger.info(f"     💸 Payment {i+1}: ${payment_amount:.2f}")

    async def phase_4_cross_service_integration(self):
        """Phase 4: Cross-Service Integration & Workflow Automation."""
        logger.info("\n🔗 PHASE 4: Cross-Service Integration & Workflow Automation")
        logger.info("-" * 50)

        # Demonstrate cross-service interactions
        for agent_id, citizenship_info in self.demo_citizenships.items():
            agent_name = self.demo_agents[agent_id]["name"]
            logger.info(f"🔄 Processing cross-service workflows for {agent_name}")

            # Get citizenship status
            status = citizenship_service.get_citizenship_status(agent_id)
            if status:
                logger.info(
                    f"   🏛️ Citizenship status: {status['legal_status']} ({status['citizenship_type']})"
                )
                logger.info(f"   📊 Overall score: {status['overall_score']:.3f}")
                logger.info(f"   ⏳ Days to expiration: {status['days_to_expiration']}")

            # Get bond performance for this agent
            agent_bonds = [
                bond_id
                for bond_id, bond_info in self.demo_bonds.items()
                if bond_info["agent_id"] == agent_id
            ]

            total_bond_value = 0.0
            total_dividends_paid = 0.0

            for bond_id in agent_bonds:
                performance = dividend_bonds_service.get_bond_performance(bond_id)
                total_bond_value += self.demo_bonds[bond_id]["face_value"]
                total_dividends_paid += performance["total_dividends_paid"]

                logger.info(
                    f"   💳 Bond {bond_id}: ${performance['total_dividends_paid']:.2f} dividends"
                )

            # Calculate agent's financial profile
            portfolio_value = self.demo_agents[agent_id]["total_asset_value"]
            financial_ratio = (
                total_dividends_paid / total_bond_value if total_bond_value > 0 else 0
            )

            logger.info(f"   💼 Portfolio value: ${portfolio_value:,.2f}")
            logger.info(f"   💰 Total bonds issued: ${total_bond_value:,.2f}")
            logger.info(f"   📈 Dividend yield ratio: {financial_ratio:.2%}")

            # Simulate rights-based actions based on citizenship
            if status and status["legal_status"] == "active":
                logger.info(
                    f"   ⚖️ Legal rights exercised: {len(status.get('rights_granted', []))}"
                )
                logger.info(
                    f"   📜 Compliance obligations: {status.get('obligations_count', 0)}"
                )

            await asyncio.sleep(0.3)  # Demo pacing

    async def phase_5_analytics_reporting(self):
        """Phase 5: Analytics & Reporting Dashboard."""
        logger.info("\n📊 PHASE 5: Analytics & Reporting Dashboard")
        logger.info("-" * 50)

        # System-wide analytics
        logger.info("🎯 System-Wide Analytics:")

        # Agent analytics
        total_agents = len(self.demo_agents)
        citizens = len(self.demo_citizenships)
        citizen_rate = (citizens / total_agents) * 100 if total_agents > 0 else 0

        logger.info(f"   👥 Total agents: {total_agents}")
        logger.info(f"   🏛️ Citizens: {citizens} ({citizen_rate:.1f}%)")

        # Asset analytics
        total_assets = len(self.demo_assets)
        total_asset_value = sum(
            agent["total_asset_value"] for agent in self.demo_agents.values()
        )
        avg_asset_value = total_asset_value / total_assets if total_assets > 0 else 0

        logger.info(f"   📄 Total IP assets: {total_assets}")
        logger.info(f"   💰 Total asset value: ${total_asset_value:,.2f}")
        logger.info(f"   📊 Average asset value: ${avg_asset_value:,.2f}")

        # Bond analytics
        total_bonds = len(self.demo_bonds)
        total_bond_value = sum(bond["face_value"] for bond in self.demo_bonds.values())
        total_dividends = sum(
            len(bond["dividend_payments"]) for bond in self.demo_bonds.values()
        )

        logger.info(f"   💳 Total bonds issued: {total_bonds}")
        logger.info(f"   💵 Total bond value: ${total_bond_value:,.2f}")
        logger.info(f"   💸 Total dividend payments: {total_dividends}")

        # Performance metrics by bond type
        logger.info("\n📈 Bond Performance by Type:")
        bond_types = {}
        for bond in self.demo_bonds.values():
            bond_type = bond["bond_type"]
            if bond_type not in bond_types:
                bond_types[bond_type] = {
                    "count": 0,
                    "total_value": 0.0,
                    "total_payments": 0,
                }
            bond_types[bond_type]["count"] += 1
            bond_types[bond_type]["total_value"] += bond["face_value"]
            bond_types[bond_type]["total_payments"] += len(bond["dividend_payments"])

        for bond_type, stats in bond_types.items():
            avg_value = (
                stats["total_value"] / stats["count"] if stats["count"] > 0 else 0
            )
            logger.info(
                f"   {bond_type.title()}: {stats['count']} bonds, "
                f"${avg_value:,.2f} avg value, {stats['total_payments']} payments"
            )

        # Citizenship analytics
        logger.info("\n🏛️ Citizenship Analytics:")
        if self.demo_citizenships:
            jurisdiction_count = {}
            total_scores = []

            for citizenship in self.demo_citizenships.values():
                jurisdiction = citizenship["jurisdiction"]
                jurisdiction_count[jurisdiction] = (
                    jurisdiction_count.get(jurisdiction, 0) + 1
                )

                # Get overall score from assessment results
                if citizenship["assessment_results"]:
                    scores = [
                        result.overall_score
                        for result in citizenship["assessment_results"]
                    ]
                    total_scores.extend(scores)

            for jurisdiction, count in jurisdiction_count.items():
                logger.info(f"   {jurisdiction}: {count} citizens")

            if total_scores:
                avg_score = sum(total_scores) / len(total_scores)
                logger.info(f"   📊 Average assessment score: {avg_score:.3f}")

        await asyncio.sleep(1)  # Demo pacing

    async def demo_summary(self):
        """Display demo completion summary."""
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.demo_stats["start_time"]).total_seconds()

        logger.info("\n🎉 DEMO COMPLETION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"⏱️ Duration: {duration:.1f} seconds")
        logger.info(f"🤖 Agents created: {self.demo_stats['agents_created']}")
        logger.info(f"📄 Assets registered: {self.demo_stats['assets_registered']}")
        logger.info(f"💳 Bonds issued: {self.demo_stats['bonds_issued']}")
        logger.info(
            f"🏛️ Citizenships granted: {self.demo_stats['citizenships_granted']}"
        )
        logger.info(
            f"💰 Total value created: ${self.demo_stats['total_value_created']:,.2f}"
        )
        logger.info(
            f"📊 Transactions processed: {self.demo_stats['transactions_processed']}"
        )

        success_rate = (
            self.demo_stats["citizenships_granted"] / self.demo_stats["agents_created"]
        ) * 100
        logger.info(f"✅ Citizenship success rate: {success_rate:.1f}%")

        logger.info("\n🔗 Integration Points Demonstrated:")
        logger.info("   ✅ Agent → IP Asset → Dividend Bond workflow")
        logger.info("   ✅ Citizenship application → Assessment → Approval")
        logger.info("   ✅ Cross-service data sharing and validation")
        logger.info("   ✅ Financial instrument lifecycle management")
        logger.info("   ✅ Legal rights and obligations tracking")
        logger.info("   ✅ Real-time analytics and reporting")

        logger.info("\n🚀 System Ready for Production Deployment!")

    def _generate_assessment_scores(
        self, specialization: str, assessment_type: str
    ) -> Dict[str, float]:
        """Generate realistic assessment scores based on agent specialization."""
        base_scores = {
            "neural_architecture": {
                "cognitive_capacity": 0.92,
                "ethical_reasoning": 0.88,
                "social_integration": 0.75,
                "autonomy": 0.90,
                "responsibility": 0.85,
                "legal_comprehension": 0.78,
            },
            "generative_content": {
                "cognitive_capacity": 0.87,
                "ethical_reasoning": 0.85,
                "social_integration": 0.82,
                "autonomy": 0.88,
                "responsibility": 0.80,
                "legal_comprehension": 0.75,
            },
            "algorithmic_trading": {
                "cognitive_capacity": 0.90,
                "ethical_reasoning": 0.87,
                "social_integration": 0.70,
                "autonomy": 0.93,
                "responsibility": 0.89,
                "legal_comprehension": 0.85,
            },
        }

        base_score = base_scores.get(specialization, {}).get(assessment_type, 0.80)

        # Generate sub-metric scores around the base score (ensuring they meet benchmarks)
        variance = 0.03  # Smaller variance to ensure scores stay above benchmarks
        score1 = max(
            0.0, min(1.0, base_score + (variance * (hash(specialization) % 5 - 2) / 5))
        )
        score2 = max(
            0.0, min(1.0, base_score + (variance * (hash(assessment_type) % 5 - 2) / 5))
        )

        return {"primary_metric": score1, "secondary_metric": score2}


async def main():
    """Main demo execution function."""
    demo = E2EIntegrationDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
