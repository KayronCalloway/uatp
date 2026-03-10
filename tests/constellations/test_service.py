import pytest

from constellations import InMemoryGraphStore
from constellations.service import ConstellationsService


@pytest.fixture()
def service() -> ConstellationsService:  # fresh service per test
    store = InMemoryGraphStore()
    return ConstellationsService(store)


def test_lineage_mutations_and_queries(service: ConstellationsService):
    # Build a tiny chain A -> B -> C
    service.add_edge("A", "B")
    service.add_edge("B", "C")

    # Ancestors
    assert set(service.ancestors("C")) == {"A", "B"}
    assert service.ancestors("C", depth=1) == ["B"]

    # Descendants
    assert set(service.descendants("A")) == {"B", "C"}
    assert service.descendants("A", depth=1) == ["B"]

    # Lineage (genesis → target)
    assert service.lineage("C") == ["A", "B", "C"]

    # Export structure
    exported = service.export()
    assert set(exported["nodes"]) == {"A", "B", "C"}
    assert len(exported["edges"]) == 2
