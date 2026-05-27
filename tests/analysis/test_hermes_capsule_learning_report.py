import json
import subprocess
import sys
from pathlib import Path

from scripts.analysis.hermes_capsule_learning_report import (
    build_report_payload,
    render_markdown,
)


def test_render_markdown_marks_insufficient_data_and_signal_cleanup_required():
    markdown = render_markdown(
        {
            "summary": {
                "safe_to_promote_live": False,
                "eval_records": 9,
                "meta_contamination_count": 4,
            },
            "audit": {
                "capsules_total": 10,
                "hermes": {"capsules": 2, "user_signal_counts": {}},
            },
            "eval": {"records": 9, "signals": {}},
            "benchmark": {
                "promotion_gate": {"safe_to_promote_live": False},
                "ranking": [],
            },
            "failure_modes": {},
            "token_waste": {
                "long_answer_short_correction": 0,
                "estimated_wasted_tokens": 0,
                "phrases": {},
            },
            "tool_misses": {},
            "proposals": [],
            "signal_health": {
                "meta_contamination_count": 4,
                "clean_correction_chains": 9,
            },
        }
    )

    assert "Insufficient data for live behavior promotion" in markdown
    assert "Signal cleanup required" in markdown
    assert "safe_to_promote_live: false" in markdown


def test_report_counts_only_non_neutral_meta_signals_as_contamination(monkeypatch):
    from scripts.analysis import hermes_capsule_learning_report as report

    monkeypatch.setattr(
        report,
        "audit",
        lambda _db_path: {
            "capsules_total": 1,
            "hermes": {
                "capsules": 1,
                "steps_total": 1,
                "user_signal_counts": {},
                "meta_signal_counts": {"neutral": 80},
            },
        },
    )
    monkeypatch.setattr(report, "_load_or_build_records", lambda *_args, **_kwargs: [])

    payload = report.build_report_payload(output_path=None, dry_run=True)

    assert payload["summary"]["meta_contamination_count"] == 0
    assert payload["signal_health"]["meta_contamination_count"] == 0


def test_report_surfaces_meta_kind_counts(monkeypatch):
    from scripts.analysis import hermes_capsule_learning_report as report

    monkeypatch.setattr(
        report,
        "audit",
        lambda _db_path: {
            "capsules_total": 2,
            "hermes": {
                "capsules": 2,
                "steps_total": 2,
                "user_signal_counts": {},
                "meta_signal_counts": {"neutral": 2},
                "meta_kind_counts": {
                    "context_compaction": 1,
                    "background_process_notification": 1,
                },
            },
        },
    )
    monkeypatch.setattr(report, "_load_or_build_records", lambda *_args, **_kwargs: [])

    payload = report.build_report_payload(output_path=None, dry_run=True)

    assert payload["signal_health"]["meta_kind_counts"] == {
        "context_compaction": 1,
        "background_process_notification": 1,
    }


def test_report_payload_can_be_built_without_external_pythonpath(tmp_path):
    output = tmp_path / "report.md"

    payload = build_report_payload(output_path=output, dry_run=True)

    assert "audit" in payload
    assert "eval" in payload
    assert "summary" in payload
    assert payload["summary"]["safe_to_promote_live"] is False


def test_audit_script_runs_directly_without_external_pythonpath(tmp_path):
    script = (
        Path(__file__).resolve().parents[2]
        / "scripts/analysis/capsule_learning_audit.py"
    )
    empty_db = tmp_path / "empty.db"

    result = subprocess.run(
        [sys.executable, str(script), "--json", "--db", str(empty_db)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["capsules_total"] == 0
    assert payload["hermes"]["meta_kind_counts"] == {}


def test_report_payload_treats_missing_capsules_table_as_empty_dataset(tmp_path):
    output = tmp_path / "report.md"
    empty_db = tmp_path / "empty.db"

    payload = build_report_payload(db_path=empty_db, output_path=output, dry_run=True)

    assert payload["audit"]["capsules_total"] == 0
    assert payload["audit"]["hermes"]["capsules"] == 0
    assert payload["eval"]["records"] == 0
    assert payload["summary"]["safe_to_promote_live"] is False


def test_main_writes_markdown_report(tmp_path):
    from scripts.analysis.hermes_capsule_learning_report import main

    output = tmp_path / "report.md"
    exit_code = main(["--output", str(output), "--dry-run"])

    assert exit_code == 0
    assert output.exists()
    assert "Hermes Capsule Learning Report" in output.read_text()


def test_main_json_output_is_redacted(capsys, tmp_path):
    from scripts.analysis.hermes_capsule_learning_report import main

    output = tmp_path / "report.md"
    exit_code = main(["--output", str(output), "--json", "--dry-run"])

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "/Users/kay" not in captured
    assert "uatp_dev.db" in captured
