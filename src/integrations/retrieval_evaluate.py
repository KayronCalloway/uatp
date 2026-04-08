#!/usr/bin/env python3
"""
Retrieval Evaluation - Measures retrieval accuracy
===================================================

Runs the test cases and measures how well the knowledge retrieval
finds the expected facts.

Usage:
    python3 -m src.integrations.retrieval_evaluate
    # or from project root:
    python3 src/integrations/retrieval_evaluate.py
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np


def load_tests() -> List[Dict[str, Any]]:
    """Load test cases from JSON file."""
    test_file = Path(__file__).parent / "retrieval_tests.json"
    with open(test_file) as f:
        data = json.load(f)
    return data["tests"]


def get_knowledge_engine():
    """Get the knowledge engine with current rules applied."""
    # Import here to pick up any rule changes
    from src.integrations.knowledge_engine import KnowledgeEngine
    from src.integrations.retrieval_rules import get_optimizer

    engine = KnowledgeEngine(db_path="uatp_dev.db")
    engine.start()

    # Wait for index to be ready
    for _ in range(30):
        if engine.ready and engine.index.size > 0:
            break
        time.sleep(1)

    return engine, get_optimizer()


def evaluate_query(
    engine, optimizer, query: str, expected_facts: List[str]
) -> Dict[str, Any]:
    """Evaluate a single query."""
    # Expand query using rules
    expanded_query = optimizer.expand_query(query)

    # Get embedding
    query_embedding = engine.embedder.embed(expanded_query)

    # Search with more results for reranking
    max_results = optimizer.get_max_results()
    results = engine.index.search(expanded_query, query_embedding, k=max_results)

    if not results:
        return {
            "query": query,
            "expanded": expanded_query,
            "success": False,
            "reason": "no_results",
            "top_content": None,
        }

    # Rerank results using optimizer
    reranked = []
    for item, score in results:
        if not optimizer.should_include(score):
            continue
        adjusted_score = optimizer.score_result(item.content, score)
        reranked.append((item, adjusted_score))

    # Sort by adjusted score
    reranked.sort(key=lambda x: x[1], reverse=True)

    if not reranked:
        return {
            "query": query,
            "expanded": expanded_query,
            "success": False,
            "reason": "filtered_out",
            "top_content": None,
        }

    # Check if top result contains any expected fact
    top_item, top_score = reranked[0]
    top_content = top_item.content.lower()

    found_fact = None
    for fact in expected_facts:
        if fact.lower() in top_content:
            found_fact = fact
            break

    success = found_fact is not None

    return {
        "query": query,
        "expanded": expanded_query,
        "success": success,
        "found_fact": found_fact,
        "top_score": top_score,
        "top_content": top_item.content[:200],
        "num_results": len(reranked),
    }


def run_evaluation() -> Dict[str, Any]:
    """Run full evaluation and return metrics."""
    print("Loading knowledge engine...")
    engine, optimizer = get_knowledge_engine()

    if engine.index.size == 0:
        print("ERROR: No items in knowledge index")
        return {"retrieval_accuracy": 0.0, "error": "empty_index"}

    print(f"Index ready: {engine.index.size} items")
    print(f"Embedding: {engine.embedder.embedding_type}")
    print()

    tests = load_tests()
    print(f"Running {len(tests)} test cases...")
    print()

    results = []
    for test in tests:
        result = evaluate_query(
            engine, optimizer, test["query"], test["expected_facts"]
        )
        result["category"] = test.get("category", "unknown")
        results.append(result)

        status = "PASS" if result["success"] else "FAIL"
        print(f"  [{status}] {test['query']}")
        if result["success"]:
            print(f"       Found: {result['found_fact']}")
        else:
            reason = result.get("reason", "not_found")
            if result.get("top_content"):
                print(f"       Got: {result['top_content'][:60]}...")
            else:
                print(f"       Reason: {reason}")

    print()

    # Calculate metrics
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    accuracy = passed / total if total > 0 else 0.0

    # Category breakdown
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if r["success"]:
            categories[cat]["passed"] += 1

    return {
        "retrieval_accuracy": accuracy,
        "passed": passed,
        "total": total,
        "categories": categories,
        "details": results,
    }


def print_results(metrics: Dict[str, Any]):
    """Print evaluation results."""
    print("=" * 50)
    print("RETRIEVAL EVALUATION RESULTS")
    print("=" * 50)
    print(f"retrieval_accuracy: {metrics['retrieval_accuracy']:.4f}")
    print(f"passed:            {metrics['passed']}/{metrics['total']}")
    print()

    if "categories" in metrics:
        print("By category:")
        for cat, stats in metrics["categories"].items():
            cat_acc = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {cat}: {stats['passed']}/{stats['total']} ({cat_acc:.0%})")

    print("---")
    print(f"retrieval_accuracy: {metrics['retrieval_accuracy']:.6f}")


if __name__ == "__main__":
    start_time = time.time()
    metrics = run_evaluation()
    elapsed = time.time() - start_time

    print()
    print_results(metrics)
    print(f"eval_seconds:      {elapsed:.1f}")
