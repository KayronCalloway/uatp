"""
Tests for Attribution Key Clustering (AKC) System

This module provides comprehensive tests for the AKC system including
knowledge source management, discovery, verification, and integration
with the FCDE engine.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.attribution.akc_system import (
    AKCSystem,
    KnowledgeSource,
    KnowledgeSourceType,
    VerificationStatus,
    KnowledgeCluster,
)
from src.attribution.knowledge_discovery import KnowledgeDiscovery
from src.economic.fcde_engine import FCDEEngine
from src.economic.common_attribution_fund import CommonAttributionFund
from src.economic.akc_integration import AKCFCDEIntegration


class TestAKCSystem:
    """Test suite for AKC system core functionality"""

    @pytest.fixture
    async def akc_system(self):
        """Create AKC system instance for testing"""
        fcde_engine = FCDEEngine()
        caf = CommonAttributionFund()
        akc_system = AKCSystem(fcde_engine, caf)
        await akc_system.initialize()
        return akc_system

    @pytest.fixture
    def sample_knowledge_source(self):
        """Create sample knowledge source for testing"""
        return KnowledgeSource(
            id=str(uuid4()),
            type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Sample Academic Paper",
            authors=["Dr. Jane Smith", "Dr. John Doe"],
            publication_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            doi="10.1234/example.paper",
            url="https://example.com/paper",
            verification_status=VerificationStatus.VERIFIED,
            confidence_score=0.9,
            usage_count=0,
            metadata={"journal": "Example Journal", "volume": "1"},
        )

    @pytest.mark.asyncio
    async def test_register_knowledge_source(self, akc_system, sample_knowledge_source):
        """Test registering a new knowledge source"""
        # Register source
        registered_source = await akc_system.register_knowledge_source(
            source_type=sample_knowledge_source.type,
            title=sample_knowledge_source.title,
            authors=sample_knowledge_source.authors,
            publication_date=sample_knowledge_source.publication_date,
            doi=sample_knowledge_source.doi,
            url=sample_knowledge_source.url,
            verification_status=sample_knowledge_source.verification_status,
            confidence_score=sample_knowledge_source.confidence_score,
            metadata=sample_knowledge_source.metadata,
        )

        # Verify registration
        assert registered_source.id in akc_system.knowledge_sources
        assert registered_source.title == sample_knowledge_source.title
        assert registered_source.authors == sample_knowledge_source.authors
        assert registered_source.doi == sample_knowledge_source.doi
        assert (
            registered_source.confidence_score
            == sample_knowledge_source.confidence_score
        )

    @pytest.mark.asyncio
    async def test_create_knowledge_cluster(self, akc_system):
        """Test creating a knowledge cluster"""
        # Create some test sources
        source1 = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Paper 1",
            authors=["Author 1"],
            confidence_score=0.8,
        )

        source2 = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Paper 2",
            authors=["Author 2"],
            confidence_score=0.9,
        )

        # Create cluster
        cluster = await akc_system.create_knowledge_cluster(
            name="Test Cluster",
            description="A test cluster",
            source_ids=[source1.id, source2.id],
        )

        # Verify cluster
        assert cluster.id in akc_system.knowledge_clusters
        assert cluster.name == "Test Cluster"
        assert len(cluster.sources) == 2
        assert cluster.cluster_hash is not None

    @pytest.mark.asyncio
    async def test_track_knowledge_usage(self, akc_system, sample_knowledge_source):
        """Test tracking knowledge usage"""
        # Register source
        source = await akc_system.register_knowledge_source(
            source_type=sample_knowledge_source.type,
            title=sample_knowledge_source.title,
            authors=sample_knowledge_source.authors,
            confidence_score=sample_knowledge_source.confidence_score,
        )

        initial_usage = source.usage_count
        capsule_id = f"caps_2024_01_01_{uuid4().hex[:16]}"

        # Track usage
        await akc_system.track_knowledge_usage(
            source_ids=[source.id], usage_context="Test usage", capsule_id=capsule_id
        )

        # Verify usage tracking
        updated_source = akc_system.knowledge_sources[source.id]
        assert updated_source.usage_count > initial_usage

    @pytest.mark.asyncio
    async def test_verify_knowledge_source(self, akc_system, sample_knowledge_source):
        """Test verifying a knowledge source"""
        # Register source with unknown status
        source = await akc_system.register_knowledge_source(
            source_type=sample_knowledge_source.type,
            title=sample_knowledge_source.title,
            authors=sample_knowledge_source.authors,
            verification_status=VerificationStatus.UNKNOWN,
            confidence_score=0.5,
        )

        # Verify source
        await akc_system.verify_knowledge_source(
            source_id=source.id,
            verifier_id="test_verifier",
            verification_status=VerificationStatus.VERIFIED,
            confidence_score=0.9,
        )

        # Check verification
        verified_source = akc_system.knowledge_sources[source.id]
        assert verified_source.verification_status == VerificationStatus.VERIFIED
        assert verified_source.confidence_score == 0.9
        assert verified_source.last_verified is not None

    @pytest.mark.asyncio
    async def test_search_knowledge_sources(self, akc_system):
        """Test searching knowledge sources"""
        # Create test sources
        await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Machine Learning Paper",
            authors=["ML Expert"],
            confidence_score=0.9,
        )

        await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.BOOK,
            title="Deep Learning Book",
            authors=["DL Expert"],
            confidence_score=0.8,
        )

        # Search by title
        results = await akc_system.search_knowledge_sources(
            query="machine learning", verified_only=False
        )

        assert len(results) >= 1
        assert any("machine learning" in result.title.lower() for result in results)

        # Search by type
        book_results = await akc_system.search_knowledge_sources(
            query="deep", source_type=KnowledgeSourceType.BOOK
        )

        assert len(book_results) >= 1
        assert all(result.type == KnowledgeSourceType.BOOK for result in book_results)

    @pytest.mark.asyncio
    async def test_get_knowledge_lineage(self, akc_system):
        """Test getting knowledge lineage for a capsule"""
        # Create test source
        source = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Test Paper",
            authors=["Test Author"],
            confidence_score=0.8,
        )

        capsule_id = f"caps_2024_01_01_{uuid4().hex[:16]}"

        # Track usage to create lineage
        await akc_system.track_knowledge_usage(
            source_ids=[source.id], usage_context="Test lineage", capsule_id=capsule_id
        )

        # Get lineage
        lineage = await akc_system.get_knowledge_lineage(capsule_id)

        assert lineage["capsule_id"] == capsule_id
        assert lineage["total_sources"] >= 1
        assert len(lineage["sources"]) >= 1

    @pytest.mark.asyncio
    async def test_get_system_stats(self, akc_system):
        """Test getting system statistics"""
        # Create some test data
        await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Test Paper 1",
            authors=["Author 1"],
            confidence_score=0.8,
        )

        await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.BOOK,
            title="Test Book 1",
            authors=["Author 2"],
            confidence_score=0.9,
        )

        # Get stats
        stats = await akc_system.get_system_stats()

        assert stats["total_sources"] >= 2
        assert stats["total_clusters"] >= 0
        assert "source_types" in stats
        assert "top_contributors" in stats
        assert KnowledgeSourceType.ACADEMIC_PAPER.value in stats["source_types"]
        assert KnowledgeSourceType.BOOK.value in stats["source_types"]


class TestKnowledgeDiscovery:
    """Test suite for knowledge discovery functionality"""

    @pytest.fixture
    def knowledge_discovery(self):
        """Create knowledge discovery instance for testing"""
        return KnowledgeDiscovery()

    @pytest.mark.asyncio
    async def test_discover_from_content_with_doi(self, knowledge_discovery):
        """Test discovering sources from content with DOI"""
        test_content = """
        This research builds on the work by Smith et al. (2023) published in
        Nature with DOI 10.1038/s41586-023-06174-6. The methodology follows
        standard practices described in the literature.
        """

        async with knowledge_discovery as kd:
            sources = await kd.discover_from_content(test_content)

            # Should find at least one source with DOI
            doi_sources = [s for s in sources if s.doi]
            assert len(doi_sources) >= 1

            # Check DOI format
            for source in doi_sources:
                assert source.doi.startswith("10.")

    @pytest.mark.asyncio
    async def test_discover_from_content_with_arxiv(self, knowledge_discovery):
        """Test discovering sources from content with arXiv ID"""
        test_content = """
        The transformer architecture was first introduced in arXiv:1706.03762
        and has since been widely adopted in natural language processing.
        """

        async with knowledge_discovery as kd:
            sources = await kd.discover_from_content(test_content)

            # Should find arXiv paper
            arxiv_sources = [s for s in sources if "arxiv" in s.url.lower()]
            assert len(arxiv_sources) >= 1

    @pytest.mark.asyncio
    async def test_discover_from_content_with_github(self, knowledge_discovery):
        """Test discovering sources from content with GitHub repository"""
        test_content = """
        The implementation is available at https://github.com/microsoft/DialoGPT
        and includes comprehensive documentation and examples.
        """

        async with knowledge_discovery as kd:
            sources = await kd.discover_from_content(test_content)

            # Should find GitHub repository
            github_sources = [
                s for s in sources if s.type == KnowledgeSourceType.CODE_REPOSITORY
            ]
            assert len(github_sources) >= 1

    @pytest.mark.asyncio
    async def test_batch_discover_and_verify(self, knowledge_discovery):
        """Test batch discovery and verification"""
        test_contents = [
            "This paper cites 10.1038/nature12373 for reference.",
            "The code is available at https://github.com/tensorflow/tensorflow",
            "See arXiv:1512.03385 for more details on ResNet architecture.",
        ]

        async with knowledge_discovery as kd:
            sources = await kd.batch_discover_and_verify(test_contents)

            # Should find multiple sources
            assert len(sources) >= 2

            # Should have different types
            source_types = {s.type for s in sources}
            assert len(source_types) >= 2


class TestAKCFCDEIntegration:
    """Test suite for AKC-FCDE integration"""

    @pytest.fixture
    async def akc_fcde_integration(self):
        """Create AKC-FCDE integration instance for testing"""
        fcde_engine = FCDEEngine()
        caf = CommonAttributionFund()
        akc_system = AKCSystem(fcde_engine, caf)
        await akc_system.initialize()

        integration = AKCFCDEIntegration(akc_system, fcde_engine)
        return integration

    @pytest.mark.asyncio
    async def test_process_ancestral_contributions(self, akc_fcde_integration):
        """Test processing ancestral contributions"""
        akc_system = akc_fcde_integration.akc_system

        # Create test source
        source = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Test Paper",
            authors=["Test Author"],
            confidence_score=0.8,
        )

        capsule_id = f"caps_2024_01_01_{uuid4().hex[:16]}"

        # Track usage
        await akc_system.track_knowledge_usage(
            source_ids=[source.id], usage_context="Test usage", capsule_id=capsule_id
        )

        # Process ancestral contributions
        dividends = await akc_fcde_integration.process_ancestral_contributions(
            capsule_id=capsule_id,
            total_revenue=Decimal("1000.0"),
            akc_contribution_percentage=Decimal("0.15"),
        )

        # Should have dividends for author
        assert len(dividends) >= 1
        assert "Test Author" in dividends
        assert dividends["Test Author"] > 0

    @pytest.mark.asyncio
    async def test_get_ancestral_attribution_report(self, akc_fcde_integration):
        """Test getting ancestral attribution report"""
        akc_system = akc_fcde_integration.akc_system

        # Create test source
        source = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Test Paper",
            authors=["Test Author"],
            confidence_score=0.8,
        )

        capsule_id = f"caps_2024_01_01_{uuid4().hex[:16]}"

        # Track usage
        await akc_system.track_knowledge_usage(
            source_ids=[source.id], usage_context="Test usage", capsule_id=capsule_id
        )

        # Process contributions
        await akc_fcde_integration.process_ancestral_contributions(
            capsule_id=capsule_id, total_revenue=Decimal("1000.0")
        )

        # Get report
        report = await akc_fcde_integration.get_ancestral_attribution_report(
            capsule_id=capsule_id
        )

        # Verify report structure
        assert report["capsule_id"] == capsule_id
        assert "lineage" in report
        assert "ancestral_contributions" in report
        assert report["knowledge_sources_count"] >= 1
        assert report["total_ancestral_contributors"] >= 1

    @pytest.mark.asyncio
    async def test_batch_process_ancestral_dividends(self, akc_fcde_integration):
        """Test batch processing of ancestral dividends"""
        akc_system = akc_fcde_integration.akc_system

        # Create test sources
        source1 = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Test Paper 1",
            authors=["Author 1"],
            confidence_score=0.8,
        )

        source2 = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.BOOK,
            title="Test Book 1",
            authors=["Author 2"],
            confidence_score=0.9,
        )

        # Create capsules and track usage
        capsule1_id = f"caps_2024_01_01_{uuid4().hex[:16]}"
        capsule2_id = f"caps_2024_01_01_{uuid4().hex[:16]}"

        await akc_system.track_knowledge_usage(
            [source1.id], "Test usage 1", capsule1_id
        )
        await akc_system.track_knowledge_usage(
            [source2.id], "Test usage 2", capsule2_id
        )

        # Batch process dividends
        capsule_usages = [
            (capsule1_id, Decimal("500.0")),
            (capsule2_id, Decimal("800.0")),
        ]

        results = await akc_fcde_integration.batch_process_ancestral_dividends(
            capsule_usages=capsule_usages
        )

        # Verify results
        assert len(results) == 2
        assert capsule1_id in results
        assert capsule2_id in results
        assert len(results[capsule1_id]) >= 1
        assert len(results[capsule2_id]) >= 1

    @pytest.mark.asyncio
    async def test_get_system_ancestral_stats(self, akc_fcde_integration):
        """Test getting system ancestral statistics"""
        akc_system = akc_fcde_integration.akc_system

        # Create test data
        source = await akc_system.register_knowledge_source(
            source_type=KnowledgeSourceType.ACADEMIC_PAPER,
            title="Test Paper",
            authors=["Test Author"],
            confidence_score=0.8,
        )

        capsule_id = f"caps_2024_01_01_{uuid4().hex[:16]}"

        # Track usage and process contributions
        await akc_system.track_knowledge_usage([source.id], "Test usage", capsule_id)
        await akc_fcde_integration.process_ancestral_contributions(
            capsule_id=capsule_id, total_revenue=Decimal("1000.0")
        )

        # Get stats
        stats = await akc_fcde_integration.get_system_ancestral_stats()

        # Verify stats
        assert stats["total_ancestral_contributions"] >= 1
        assert stats["total_ancestral_value"] >= 0
        assert stats["unique_contributors"] >= 1
        assert stats["capsules_with_ancestral_attribution"] >= 1
        assert "akc_system_stats" in stats


class TestAKCEndToEnd:
    """End-to-end tests for AKC system"""

    @pytest.mark.asyncio
    async def test_complete_akc_workflow(self):
        """Test complete AKC workflow from discovery to payout"""
        # Initialize system
        fcde_engine = FCDEEngine()
        caf = CommonAttributionFund()
        akc_system = AKCSystem(fcde_engine, caf)
        await akc_system.initialize()

        integration = AKCFCDEIntegration(akc_system, fcde_engine)

        # Step 1: Discover sources from content
        test_content = """
        This work builds on the seminal paper by Vaswani et al. (2017) 
        "Attention Is All You Need" published in NIPS. The original 
        implementation can be found at https://github.com/tensorflow/tensor2tensor.
        """

        async with KnowledgeDiscovery() as kd:
            discovered_sources = await kd.discover_from_content(test_content)

            # Step 2: Register discovered sources
            for source in discovered_sources:
                if source.id not in akc_system.knowledge_sources:
                    akc_system.knowledge_sources[source.id] = source
                    await akc_system._save_knowledge_source(source)

        # Step 3: Create knowledge cluster
        if len(akc_system.knowledge_sources) >= 2:
            source_ids = list(akc_system.knowledge_sources.keys())[:2]
            cluster = await akc_system.create_knowledge_cluster(
                name="Test Cluster",
                description="End-to-end test cluster",
                source_ids=source_ids,
            )

            assert cluster.id in akc_system.knowledge_clusters

        # Step 4: Simulate capsule usage
        capsule_id = f"caps_2024_01_01_{uuid4().hex[:16]}"
        source_ids = list(akc_system.knowledge_sources.keys())

        if source_ids:
            await akc_system.track_knowledge_usage(
                source_ids=source_ids,
                usage_context="End-to-end test usage",
                capsule_id=capsule_id,
            )

        # Step 5: Process ancestral contributions
        if source_ids:
            dividends = await integration.process_ancestral_contributions(
                capsule_id=capsule_id, total_revenue=Decimal("1000.0")
            )

            # Should have some dividends
            assert len(dividends) >= 1
            assert sum(dividends.values()) > 0

        # Step 6: Generate comprehensive report
        if source_ids:
            report = await integration.get_ancestral_attribution_report(
                capsule_id=capsule_id
            )

            # Verify report completeness
            assert report["capsule_id"] == capsule_id
            assert report["knowledge_sources_count"] >= 1
            assert report["total_ancestral_contributors"] >= 1
            assert report["total_ancestral_value"] >= 0

        # Step 7: Get system statistics
        stats = await integration.get_system_ancestral_stats()

        # Verify system state
        assert stats["total_ancestral_contributions"] >= 0
        assert stats["unique_contributors"] >= 0
        assert "akc_system_stats" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
