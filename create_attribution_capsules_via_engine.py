#!/usr/bin/env python3
"""
Create UATP 7.0 capsules with attribution features using the engine's methods.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from engine.capsule_engine import CapsuleEngine
from database.connection import get_database_manager


class AttributionDemo:
    """Creates attribution capsules using the engine's methods."""

    def __init__(self):
        self.db_manager = get_database_manager()
        self.engine = CapsuleEngine(self.db_manager, agent_id="attribution-demo-agent")

    async def create_capsules(self):
        """Create attribution-focused capsules using engine methods."""

        print("🚀 Creating UATP 7.0 attribution capsules...")
        print("=" * 70)

        # Connect to database
        await self.db_manager.connect()

        capsules_created = []

        # 1. AI Development Attribution
        prompt1 = """Analyze the attribution requirements for an AI-assisted neural network optimization project:

COLLABORATION ANALYSIS:
- Human Expert (senior-ml-engineer@company.com): Problem specification and requirements (30% attribution, $150 value)
- AI Assistant (Claude Sonnet 4): Algorithm design and implementation (50% attribution, $250 value)  
- Open Source (PyTorch community): Base framework and optimizers (20% attribution, $100 value)

TECHNICAL IMPLEMENTATION:
- Designed adaptive learning rate scheduler with momentum-based gradient accumulation
- Implemented comprehensive error handling, logging, and performance monitoring
- Achieved 23% faster convergence with 94% test coverage
- 347 lines of production-ready code

ECONOMIC DISTRIBUTION:
- Total project value: $500
- Attribution calculated using weighted contribution methodology
- Quality multiplier: 1.15x for exceeding performance targets
- Time decay factor: 0.98 (recent work maintains full value)

This represents a successful AI-human collaboration with clear attribution tracking and fair economic distribution according to UATP 7.0 principles."""

        capsule1 = await self.engine.create_capsule_from_prompt_async(
            prompt=prompt1, model="gpt-4-turbo"
        )
        capsules_created.append(capsule1.capsule_id)
        print(f"✅ Created AI Development Capsule: {capsule1.capsule_id}")

        # 2. Cross-Platform Collaboration
        prompt2 = """Document cross-platform AI collaboration attribution:

PLATFORM INTEGRATION:
- Claude Code: Automated code generation and review (40% attribution, $400 value)
- Cursor AI: Interactive pair programming assistance (40% attribution, $400 value)  
- GitHub/Git: Version control and coordination (20% attribution, $200 value)

COLLABORATION METRICS:
- 47 commits across 3 weeks
- 156 AI suggestions accepted and integrated
- 5 team members participating
- Full cross-platform compatibility achieved

ATTRIBUTION METHODOLOGY:
- Real-time contribution tracking across all platforms
- Automated reconciliation using UATP protocols
- 96% attribution accuracy with 3 conflicts resolved
- Transparent audit trail for all stakeholders

ECONOMIC OUTCOMES:
- Total project value: $1,000
- Platform fees: 5% of total value
- Human oversight: 15% attribution for architecture decisions
- AI systems: 85% attribution for implementation and optimization

This demonstrates successful federated development with comprehensive attribution tracking across multiple AI-assisted platforms."""

        capsule2 = await self.engine.create_capsule_from_prompt_async(
            prompt=prompt2, parent_capsule_id=capsule1.capsule_id, model="gpt-4-turbo"
        )
        capsules_created.append(capsule2.capsule_id)
        print(f"✅ Created Cross-Platform Capsule: {capsule2.capsule_id}")

        # 3. Economic Attribution Analysis
        prompt3 = """Perform comprehensive economic attribution analysis using FCDE principles:

FCDE ANALYSIS:
- Fair Creator Dividend Engine calculation applied
- Base project value: $10,000
- Contribution multiplier: 1.2x for high-impact work
- Fairness coefficient: 0.95 (excellent attribution transparency)

VALUE DISTRIBUTION:
- Human contributors: $2,500 (25%)
- AI attribution fund: $1,500 (15%) 
- Platform operational costs: $200 (2%)
- Future development fund: $800 (8%)
- Creator dividend pool: $5,000 (50%)

METHODOLOGY VERIFICATION:
- Statistical significance: p < 0.001
- Attribution fairness score: 0.94/1.0
- Economic efficiency rating: 0.87/1.0
- Transparency compliance: Enterprise level

STAKEHOLDER DISTRIBUTION:
- Primary researchers: 40% of creator dividend
- Contributing engineers: 35% of creator dividend  
- Quality assurance team: 15% of creator dividend
- Documentation team: 10% of creator dividend

This analysis demonstrates UATP 7.0's capability for fair, transparent, and economically sound attribution distribution across complex multi-stakeholder projects."""

        capsule3 = await self.engine.create_capsule_from_prompt_async(
            prompt=prompt3, parent_capsule_id=capsule2.capsule_id, model="gpt-4-turbo"
        )
        capsules_created.append(capsule3.capsule_id)
        print(f"✅ Created Economic Analysis Capsule: {capsule3.capsule_id}")

        print(f"\n🎉 Successfully created {len(capsules_created)} attribution capsules!")

        await self.display_summary(capsules_created)

        return capsules_created

    async def display_summary(self, capsule_ids):
        """Display a summary of created capsules."""

        print("\n" + "=" * 70)
        print("🎯 ATTRIBUTION CAPSULES CREATED")
        print("=" * 70)

        print(f"\n📊 Summary:")
        print(f"   • Total Capsules: {len(capsule_ids)}")
        print(f"   • Attribution Types: AI-Human, Cross-Platform, Economic")
        print(f"   • Features Demonstrated: FCDE, Multi-Platform, Economic Analysis")
        print(f"   • UATP Version: 7.0")
        print(f"   • Engine: OpenAI GPT-4 Turbo")

        print(f"\n🔗 Capsule IDs:")
        for i, capsule_id in enumerate(capsule_ids, 1):
            print(f"   {i}. {capsule_id}")

        print(f"\n✨ These capsules showcase:")
        print(f"   🤖 AI-Human collaborative attribution")
        print(f"   💰 Economic value distribution (FCDE)")
        print(f"   🌐 Cross-platform integration tracking")
        print(f"   📊 Comprehensive attribution analysis")
        print(f"   🔗 Parent-child capsule relationships")

        print(f"\n🎉 All capsules are now available in the UATP frontend!")
        print(f"📍 Visit: http://localhost:3000")


async def main():
    """Main function to create attribution capsules."""

    demo = AttributionDemo()
    await demo.create_capsules()


if __name__ == "__main__":
    asyncio.run(main())
