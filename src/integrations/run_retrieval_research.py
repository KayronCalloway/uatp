#!/usr/bin/env python3
"""
Retrieval Autoresearch - Gemma optimizes retrieval rules
=========================================================

Uses Gemma to iteratively improve retrieval_rules.py to maximize
retrieval accuracy on the test cases.

Gold Standard: JSON config output eliminates syntax errors.

Usage:
    python3 -m src.integrations.run_retrieval_research [--iterations N]
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


RULES_FILE = Path(__file__).parent / "retrieval_rules.py"
BACKUP_DIR = Path(__file__).parent / "retrieval_backups"
RESULTS_FILE = Path(__file__).parent / "retrieval_results.jsonl"


# Template for rebuilding retrieval_rules.py from JSON config
RULES_TEMPLATE = '''#!/usr/bin/env python3
"""
Retrieval Rules - THE FILE GEMMA MODIFIES
==========================================

This file contains the knowledge retrieval optimization rules.
Gemma experiments with different rules to maximize retrieval_accuracy.

To run an experiment:
    python3 retrieval_evaluate.py

The metric is retrieval_accuracy (higher is better, max 1.0).
"""

from typing import Dict, List, Tuple

# ============================================================================
# RETRIEVAL RULES - Gemma modifies this section
# ============================================================================

# Query expansion: map vague queries to more specific terms
# Format: "trigger phrase" -> ["additional", "search", "terms"]
QUERY_EXPANSIONS: Dict[str, List[str]] = {query_expansions}

# Failure patterns: responses matching these are demoted
# Lower confidence multiplier = more demotion
FAILURE_PATTERNS: List[Tuple[str, float]] = {failure_patterns}

# Boost patterns: responses matching these get boosted
# Higher multiplier = more boost
# NOTE: Be specific! "you are" matches "You are analyzing UATP" which is wrong
BOOST_PATTERNS: List[Tuple[str, float]] = {boost_patterns}

# Demotion patterns: irrelevant content that should be ranked lower
DEMOTION_PATTERNS: List[Tuple[str, float]] = {demotion_patterns}

# Relevance threshold: minimum score to include a result
# Lower = more results, higher = stricter filtering
RELEVANCE_THRESHOLD: float = {relevance_threshold}

# Maximum results to consider for reranking
MAX_RESULTS: int = {max_results}

# Response weight: how much to weight the response vs the prompt in embeddings
# Higher = response matters more (where facts typically are)
RESPONSE_WEIGHT: int = {response_weight}


class RetrievalOptimizer:
    """Optimizes retrieval based on the rules above."""

    def expand_query(self, query: str) -> str:
        """Expand query with additional search terms."""
        query_lower = query.lower()
        expansions = []

        for trigger, terms in QUERY_EXPANSIONS.items():
            if trigger in query_lower:
                expansions.extend(terms)

        if expansions:
            return f"{{query}} {{' '.join(expansions)}}"
        return query

    def score_result(self, content: str, base_score: float) -> float:
        """Apply boost/demotion based on content patterns."""
        content_lower = content.lower()
        multiplier = 1.0

        # Apply failure demotions (worst one wins)
        for pattern, factor in FAILURE_PATTERNS:
            if pattern in content_lower:
                multiplier *= factor
                break

        # Apply content demotions (irrelevant content)
        for pattern, factor in DEMOTION_PATTERNS:
            if pattern in content_lower:
                multiplier *= factor
                break  # Only apply worst demotion

        # Apply boosts (cumulative, but only if not already demoted)
        if multiplier >= 0.5:
            for pattern, factor in BOOST_PATTERNS:
                if pattern in content_lower:
                    multiplier *= factor

        return base_score * multiplier

    def should_include(self, score: float) -> bool:
        """Check if result meets relevance threshold."""
        return score >= RELEVANCE_THRESHOLD

    def get_response_weight(self) -> int:
        """Get response weight for embedding."""
        return RESPONSE_WEIGHT

    def get_max_results(self) -> int:
        """Get max results to retrieve."""
        return MAX_RESULTS


# ============================================================================
# DO NOT MODIFY BELOW THIS LINE
# ============================================================================

def get_optimizer() -> RetrievalOptimizer:
    """Get the retrieval optimizer instance."""
    return RetrievalOptimizer()
'''


def parse_current_config() -> dict:
    """Parse current retrieval_rules.py into JSON config."""
    with open(RULES_FILE) as f:
        content = f.read()

    config = {}

    # Parse QUERY_EXPANSIONS
    match = re.search(r"QUERY_EXPANSIONS.*?=\s*(\{[^}]+\})", content, re.DOTALL)
    if match:
        try:
            config["query_expansions"] = eval(match.group(1))
        except Exception:
            config["query_expansions"] = {}

    # Parse FAILURE_PATTERNS
    match = re.search(r"FAILURE_PATTERNS.*?=\s*(\[[^\]]+\])", content, re.DOTALL)
    if match:
        try:
            config["failure_patterns"] = eval(match.group(1))
        except Exception:
            config["failure_patterns"] = []

    # Parse BOOST_PATTERNS
    match = re.search(r"BOOST_PATTERNS.*?=\s*(\[[^\]]+\])", content, re.DOTALL)
    if match:
        try:
            config["boost_patterns"] = eval(match.group(1))
        except Exception:
            config["boost_patterns"] = []

    # Parse DEMOTION_PATTERNS
    match = re.search(r"DEMOTION_PATTERNS.*?=\s*(\[[^\]]+\])", content, re.DOTALL)
    if match:
        try:
            config["demotion_patterns"] = eval(match.group(1))
        except Exception:
            config["demotion_patterns"] = []

    # Parse thresholds
    match = re.search(r"RELEVANCE_THRESHOLD.*?=\s*([\d.]+)", content)
    config["relevance_threshold"] = float(match.group(1)) if match else 0.012

    match = re.search(r"MAX_RESULTS.*?=\s*(\d+)", content)
    config["max_results"] = int(match.group(1)) if match else 10

    match = re.search(r"RESPONSE_WEIGHT.*?=\s*(\d+)", content)
    config["response_weight"] = int(match.group(1)) if match else 2

    return config


def config_to_python(config: dict) -> str:
    """Convert JSON config to Python code."""

    def format_dict(d):
        if not d:
            return "{}"
        lines = ["{"]
        for k, v in d.items():
            lines.append(f'    "{k}": {v!r},')
        lines.append("}")
        return "\n".join(lines)

    def format_list(lst):
        if not lst:
            return "[]"
        lines = ["["]
        for item in lst:
            lines.append(f"    {item!r},")
        lines.append("]")
        return "\n".join(lines)

    return RULES_TEMPLATE.format(
        query_expansions=format_dict(config.get("query_expansions", {})),
        failure_patterns=format_list(config.get("failure_patterns", [])),
        boost_patterns=format_list(config.get("boost_patterns", [])),
        demotion_patterns=format_list(config.get("demotion_patterns", [])),
        relevance_threshold=config.get("relevance_threshold", 0.012),
        max_results=config.get("max_results", 10),
        response_weight=config.get("response_weight", 2),
    )


def backup_rules():
    """Backup current rules file."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"retrieval_rules_{timestamp}.py"
    shutil.copy(RULES_FILE, backup_path)
    return backup_path


def restore_rules(backup_path: Path):
    """Restore rules from backup."""
    shutil.copy(backup_path, RULES_FILE)


def run_evaluation() -> dict:
    """Run the evaluation script and parse results."""
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "retrieval_evaluate.py")],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).parent.parent.parent,
        )

        output = result.stdout + result.stderr

        # Parse retrieval_accuracy from output
        match = re.search(r"retrieval_accuracy:\s*([\d.]+)", output)
        accuracy = float(match.group(1)) if match else 0.0

        # Parse passed/total
        match = re.search(r"passed:\s*(\d+)/(\d+)", output)
        if match:
            passed, total = int(match.group(1)), int(match.group(2))
        else:
            passed, total = 0, 0

        return {
            "retrieval_accuracy": accuracy,
            "passed": passed,
            "total": total,
            "output": output,
            "status": "success" if result.returncode == 0 else "error",
        }

    except subprocess.TimeoutExpired:
        return {"retrieval_accuracy": 0.0, "status": "timeout", "output": ""}
    except Exception as e:
        return {"retrieval_accuracy": 0.0, "status": "crash", "output": str(e)}


def load_recent_results(n: int = 10) -> list:
    """Load recent experiment results."""
    if not RESULTS_FILE.exists():
        return []

    results = []
    with open(RESULTS_FILE) as f:
        for line in f:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return results[-n:]


def save_result(result: dict):
    """Append result to results file."""
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(result) + "\n")


def get_best_accuracy(results: list) -> float:
    """Get best accuracy from results."""
    if not results:
        return 0.0
    return max(r.get("retrieval_accuracy", 0.0) for r in results)


def build_prompt(config: dict, recent_results: list, best_accuracy: float) -> str:
    """Build the prompt for Gemma - requesting compact JSON output."""
    # Compact current config
    compact_config = json.dumps(config, separators=(",", ":"))

    results_summary = (
        f"Last run: {recent_results[-1].get('passed', 0)}/{recent_results[-1].get('total', 0)} passed"
        if recent_results
        else "No previous runs"
    )

    return f"""Optimize retrieval. Accuracy: {best_accuracy:.4f}

Config: {compact_config}

{results_summary}

Tests: name->Kayron, rappers->Jay-Z/Kendrick, from->Gardena, signing->crypto

Add ONE improvement. Output compact JSON (no extra whitespace):
{{"description":"change desc","query_expansions":{{"trigger":["terms"]}},"failure_patterns":[["pattern",0.3]],"boost_patterns":[["pattern",1.5]],"demotion_patterns":[["pattern",0.3]],"relevance_threshold":0.012,"max_results":10,"response_weight":2}}

Output COMPLETE config. No markdown, just JSON."""


def call_gemma(prompt: str) -> str:
    """Call Gemma via Ollama API."""
    import requests

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4:latest",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 4000,
                },  # Increased for full JSON
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Error calling Gemma: {e}")
        return ""


def extract_json(response: str) -> dict:
    """Extract JSON config from Gemma's response."""
    # Try to find JSON block with closing ```
    match = re.search(r"```json\s*(.*?)```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON block even if truncated (no closing ```)
    match = re.search(r"```json\s*(\{.*)", response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        # Try to complete truncated JSON by adding closing braces
        for extra in ["", "}", "]}", "]}}", "]}]}", '"]}']:
            try:
                return json.loads(json_str + extra)
            except json.JSONDecodeError:
                continue

    # Try to find raw JSON starting with {
    match = re.search(r"(\{\"description\".*)", response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        for extra in ["", "}", "]}", "]}}", "]}]}", '"]}']:
            try:
                return json.loads(json_str + extra)
            except json.JSONDecodeError:
                continue

    return {}


def run_experiment():
    """Run one experiment iteration."""
    print("\n" + "=" * 60)
    print("RETRIEVAL AUTORESEARCH (JSON Mode)")
    print("=" * 60)

    # Load current config
    config = parse_current_config()
    recent_results = load_recent_results(10)
    best_accuracy = get_best_accuracy(recent_results)

    print(f"Current best accuracy: {best_accuracy:.4f}")
    print(f"Recent experiments: {len(recent_results)}")

    # Build prompt and call Gemma
    print("\nAsking Gemma for improvement...")
    prompt = build_prompt(config, recent_results, best_accuracy)
    response = call_gemma(prompt)

    if not response:
        print("ERROR: No response from Gemma")
        return None

    # Extract JSON config
    new_config = extract_json(response)
    description = new_config.pop("description", "No description")

    if not new_config or "query_expansions" not in new_config:
        print("ERROR: Could not extract valid JSON config")
        print("Response preview:", response[:500])
        save_result(
            {
                "commit": f"exp{len(recent_results) + 1}",
                "retrieval_accuracy": 0.0,
                "status": "json_error",
                "description": "Failed to parse JSON",
                "timestamp": datetime.now().isoformat(),
            }
        )
        return None

    print(f"Proposed change: {description}")

    # Backup current rules
    backup_path = backup_rules()
    print(f"Backed up to: {backup_path.name}")

    # Convert config to Python and write
    try:
        new_code = config_to_python(new_config)
        compile(new_code, "<string>", "exec")  # Validate syntax
    except Exception as e:
        print(f"ERROR: Generated invalid Python: {e}")
        save_result(
            {
                "commit": f"exp{len(recent_results) + 1}",
                "retrieval_accuracy": 0.0,
                "status": "syntax_error",
                "description": description,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return None

    with open(RULES_FILE, "w") as f:
        f.write(new_code)

    print("Evaluating new rules...")

    # Run evaluation
    result = run_evaluation()

    record = {
        "commit": f"exp{len(recent_results) + 1}",
        "retrieval_accuracy": result["retrieval_accuracy"],
        "passed": result.get("passed", 0),
        "total": result.get("total", 0),
        "status": result["status"],
        "description": description,
        "timestamp": datetime.now().isoformat(),
    }

    print(f"\nResult: accuracy={result['retrieval_accuracy']:.4f} ({record['status']})")

    # Decide whether to keep or revert
    if result["retrieval_accuracy"] > best_accuracy:
        print(f"IMPROVED! {best_accuracy:.4f} -> {result['retrieval_accuracy']:.4f}")
        record["action"] = "keep"
    else:
        print("No improvement. Reverting.")
        restore_rules(backup_path)
        record["action"] = "revert"

    save_result(record)
    return record


def main():
    parser = argparse.ArgumentParser(description="Retrieval Autoresearch")
    parser.add_argument(
        "--iterations", "-n", type=int, default=5, help="Number of iterations"
    )
    args = parser.parse_args()

    # Run baseline first
    print("Running baseline evaluation...")
    baseline = run_evaluation()
    save_result(
        {
            "commit": "baseline",
            "retrieval_accuracy": baseline["retrieval_accuracy"],
            "passed": baseline.get("passed", 0),
            "total": baseline.get("total", 0),
            "status": baseline["status"],
            "description": "initial baseline",
            "timestamp": datetime.now().isoformat(),
        }
    )
    print(f"Baseline accuracy: {baseline['retrieval_accuracy']:.4f}")

    # Run experiments
    for i in range(args.iterations):
        print(f"\n--- Iteration {i + 1}/{args.iterations} ---")
        result = run_experiment()

        if result and result.get("retrieval_accuracy", 0) >= 1.0:
            print("\nPERFECT ACCURACY ACHIEVED!")
            break

        time.sleep(2)

    # Final summary
    results = load_recent_results(100)
    best = get_best_accuracy(results)
    print("\n" + "=" * 60)
    print(f"FINAL BEST ACCURACY: {best:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
