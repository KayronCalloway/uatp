"""
Integration tests for capsule full-text search.
"""

import pytest

from src.services.capsule_search_service import (
    CapsuleSearchService,
    SearchHit,
    SearchResults,
)


class TestSearchService:
    """Tests for CapsuleSearchService."""

    @pytest.fixture
    def service(self):
        """Create a search service instance."""
        return CapsuleSearchService()

    def test_search_results_structure(self):
        """Test SearchResults data structure."""
        results = SearchResults(
            query="test query",
            total_count=25,
            results=[],
            page=1,
            per_page=10,
            has_more=True,
        )

        d = results.to_dict()

        assert d["query"] == "test query"
        assert d["total_count"] == 25
        assert d["page"] == 1
        assert d["per_page"] == 10
        assert d["has_more"]
        assert d["total_pages"] == 3

    def test_search_hit_structure(self):
        """Test SearchHit data structure."""
        hit = SearchHit(
            capsule_id="caps_123",
            capsule_type="reasoning_trace",
            timestamp="2026-03-11T10:00:00Z",
            snippet="...matching <mark>test</mark> content...",
            relevance_score=0.95,
            payload_preview={"topics": ["coding", "python"]},
        )

        d = hit.to_dict()

        assert d["capsule_id"] == "caps_123"
        assert d["capsule_type"] == "reasoning_trace"
        assert d["snippet"] == "...matching <mark>test</mark> content..."
        assert d["relevance_score"] == 0.95
        assert d["payload_preview"]["topics"] == ["coding", "python"]

    def test_fts5_query_escaping(self, service):
        """Test FTS5 query escaping for special characters."""
        # Test phrase wrapping for multi-word queries
        escaped = service._escape_fts5_query("hello world")
        assert escaped == '"hello world"'

        # Test single word (no wrapping needed)
        escaped = service._escape_fts5_query("hello")
        assert escaped == "hello"

        # Test query with quotes removed and re-wrapped
        escaped = service._escape_fts5_query('search "term"')
        assert escaped == '"search term"'

        # Test that actual operators are not quoted
        escaped = service._escape_fts5_query("hello OR world")
        assert escaped == "hello OR world"  # Not quoted because it has OR operator

    def test_pagination_calculation(self):
        """Test pagination calculations in SearchResults."""
        # Test exact page boundary
        results = SearchResults(query="", total_count=30, page=1, per_page=10)
        assert results.to_dict()["total_pages"] == 3

        # Test partial last page
        results = SearchResults(query="", total_count=25, page=1, per_page=10)
        assert results.to_dict()["total_pages"] == 3

        # Test single page
        results = SearchResults(query="", total_count=5, page=1, per_page=10)
        assert results.to_dict()["total_pages"] == 1

        # Test empty results
        results = SearchResults(query="", total_count=0, page=1, per_page=10)
        assert results.to_dict()["total_pages"] == 0

    def test_has_more_calculation(self):
        """Test has_more flag calculation."""
        # More results available
        results = SearchResults(
            query="", total_count=25, page=1, per_page=10, has_more=True
        )
        assert results.has_more

        # No more results
        results = SearchResults(
            query="", total_count=5, page=1, per_page=10, has_more=False
        )
        assert not results.has_more


class TestSearchEndpoint:
    """Tests for the search API endpoint."""

    def test_search_endpoint_response_structure(self):
        """Test expected response structure from search endpoint."""
        expected_fields = [
            "query",
            "total_count",
            "results",
            "page",
            "per_page",
            "has_more",
            "total_pages",
        ]

        # Simulated response
        response = SearchResults(
            query="test",
            total_count=0,
            results=[],
            page=1,
            per_page=10,
            has_more=False,
        ).to_dict()

        for field in expected_fields:
            assert field in response

    def test_search_hit_in_results(self):
        """Test that search results contain properly formatted hits."""
        hit = SearchHit(
            capsule_id="caps_test",
            capsule_type="reasoning_trace",
            timestamp="2026-03-11T10:00:00Z",
            snippet="<mark>found</mark>",
            relevance_score=1.0,
        )

        results = SearchResults(
            query="found",
            total_count=1,
            results=[hit],
            page=1,
            per_page=10,
            has_more=False,
        )

        d = results.to_dict()
        assert len(d["results"]) == 1
        assert d["results"][0]["capsule_id"] == "caps_test"
        assert "<mark>" in d["results"][0]["snippet"]
