"""Tests for M9 TypeScript support."""

from __future__ import annotations

import json
from pathlib import Path

from reposage.analysis.quality import analyze_quality
from reposage.models import FileRecord, TSCodeSignals, TSConfig
from reposage.pipeline import build_audit_report
from reposage.reports.markdown import render_markdown_report
from reposage.scan.ts_analysis import analyze_typescript
from reposage.scan.ts_config import parse_tsconfig
from tests.conftest import fixture_path

# --- tsconfig parser ---


def test_parse_tsconfig_fixture() -> None:
    cfg = parse_tsconfig(fixture_path("ts_repo") / "tsconfig.json")
    assert cfg.strict is False
    assert cfg.no_implicit_any is True
    assert cfg.strict_null_checks is False
    assert cfg.target == "ES2020"
    assert cfg.module == "commonjs"
    assert cfg.path_aliases is True


def test_parse_tsconfig_missing_file(tmp_path: Path) -> None:
    result = parse_tsconfig(tmp_path / "tsconfig.json")
    assert result == TSConfig()


def test_parse_tsconfig_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "tsconfig.json").write_text("not json", encoding="utf-8")
    result = parse_tsconfig(tmp_path / "tsconfig.json")
    assert result == TSConfig()


def test_parse_tsconfig_strict_implies_sub_flags(tmp_path: Path) -> None:
    (tmp_path / "tsconfig.json").write_text(
        json.dumps({"compilerOptions": {"strict": True}}), encoding="utf-8"
    )
    cfg = parse_tsconfig(tmp_path / "tsconfig.json")
    assert cfg.strict is True
    assert cfg.no_implicit_any is True
    assert cfg.strict_null_checks is True


def test_parse_tsconfig_extends_one_level(tmp_path: Path) -> None:
    (tmp_path / "base.json").write_text(
        json.dumps({"compilerOptions": {"strict": True, "module": "commonjs"}}),
        encoding="utf-8",
    )
    (tmp_path / "child.json").write_text(
        json.dumps({"extends": "./base.json", "compilerOptions": {"target": "ES2020"}}),
        encoding="utf-8",
    )
    cfg = parse_tsconfig(tmp_path / "child.json")
    assert cfg.strict is True
    assert cfg.module == "commonjs"
    assert cfg.target == "ES2020"


def test_parse_tsconfig_extends_cycle(tmp_path: Path) -> None:
    (tmp_path / "a.json").write_text(
        json.dumps({"extends": "./b.json", "compilerOptions": {"target": "ES2020"}}),
        encoding="utf-8",
    )
    (tmp_path / "b.json").write_text(
        json.dumps({"extends": "./a.json", "compilerOptions": {"module": "commonjs"}}),
        encoding="utf-8",
    )
    result = parse_tsconfig(tmp_path / "a.json")
    assert isinstance(result, TSConfig)


def test_parse_tsconfig_extends_network_url_skipped(tmp_path: Path) -> None:
    (tmp_path / "tsconfig.json").write_text(
        json.dumps(
            {
                "extends": "https://example.com/tsconfig.json",
                "compilerOptions": {"target": "ESNext"},
            }
        ),
        encoding="utf-8",
    )
    cfg = parse_tsconfig(tmp_path / "tsconfig.json")
    assert cfg.target == "ESNext"


# --- ts_analysis ---


def test_analyze_typescript_fixture() -> None:
    ts_files = [
        FileRecord(path="src/app.ts", extension=".ts", size_bytes=0, line_count=0),
        FileRecord(path="src/utils.ts", extension=".ts", size_bytes=0, line_count=0),
    ]
    signals = analyze_typescript(fixture_path("ts_repo"), ts_files)
    assert signals.any_usage_count >= 4
    assert signals.untyped_exports == 1
    assert signals.type_assertion_count == 1


def test_analyze_typescript_empty_list(tmp_path: Path) -> None:
    result = analyze_typescript(tmp_path, [])
    assert result == TSCodeSignals()


# --- pipeline integration ---


def test_pipeline_sets_ts_config_for_ts_repo() -> None:
    report = build_audit_report(fixture_path("ts_repo"))
    assert report.ts_config is not None
    assert report.ts_config.no_implicit_any is True
    assert report.ts_analysis is not None
    assert report.ts_analysis.untyped_exports == 1


def test_pipeline_ts_config_none_for_python_repo() -> None:
    report = build_audit_report(fixture_path("python_repo"))
    assert report.ts_config is None
    assert report.ts_analysis is None


# --- quality signals ---


def test_quality_ts_missing_signals_appended() -> None:
    cfg = parse_tsconfig(fixture_path("ts_repo") / "tsconfig.json")
    result = analyze_quality(fixture_path("ts_repo"), [], ts_config=cfg)
    joined = "\n".join(result.missing_signals)
    assert "TypeScript strict mode not enabled" in joined
    assert "TypeScript strictNullChecks not enabled" in joined


def test_quality_score_unchanged_for_ts_repo() -> None:
    report = build_audit_report(fixture_path("ts_repo"))
    assert isinstance(report.quality.score, int)
    assert 0 <= report.quality.score <= 100


# --- renderers ---


def test_markdown_report_contains_ts_section() -> None:
    report = build_audit_report(fixture_path("ts_repo"))
    rendered = render_markdown_report(report)
    assert "## TypeScript" in rendered


def test_framework_detection_angular() -> None:
    report = build_audit_report(fixture_path("ts_repo"))
    assert "Angular" in report.inventory.frameworks
