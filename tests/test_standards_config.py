"""Tests for load_standards_config parsing and precedence."""

from __future__ import annotations

from reposage.standards.config import DEFAULT_STANDARDS_CONFIG, load_standards_config


def test_defaults_when_no_files(tmp_path) -> None:
    config, warnings = load_standards_config(tmp_path)

    assert config == DEFAULT_STANDARDS_CONFIG
    assert warnings == []


def test_reposage_toml_with_nested_tables(tmp_path) -> None:
    (tmp_path / "reposage.toml").write_text(
        "\n".join(
            [
                "[audit]",
                "min_commits = 10",
                "run_subprocess_checks = true",
                "[audit.thresholds]",
                "min_docstring_coverage = 0.9",
                "[audit.classify]",
                'serving_globs = ["src/api/*.py"]',
            ]
        ),
        encoding="utf-8",
    )

    config, warnings = load_standards_config(tmp_path)

    assert config.min_commits == 10
    assert config.run_subprocess_checks is True
    assert config.min_docstring_coverage == 0.9
    assert config.serving_globs == ("src/api/*.py",)
    assert warnings == []


def test_pyproject_table(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.reposage.audit]\nmin_commits = 7\n",
        encoding="utf-8",
    )

    config, warnings = load_standards_config(tmp_path)

    assert config.min_commits == 7
    assert warnings == []


def test_reposage_toml_overrides_pyproject(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.reposage.audit]\nmin_commits = 99\n",
        encoding="utf-8",
    )
    (tmp_path / "reposage.toml").write_text(
        "[audit]\nmin_commits = 3\n",
        encoding="utf-8",
    )

    config, _ = load_standards_config(tmp_path)

    assert config.min_commits == 3


def test_exclude_globs_parses_list(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.reposage.audit]\nexclude_globs = ["tests/fixtures/**", "examples/**"]\n',
        encoding="utf-8",
    )

    config, warnings = load_standards_config(tmp_path)

    assert config.exclude_globs == ("tests/fixtures/**", "examples/**")
    assert warnings == []


def test_secrets_exclude_globs_parses_list(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.reposage.audit]\nsecrets_exclude_globs = ["tests/**"]\n',
        encoding="utf-8",
    )

    config, warnings = load_standards_config(tmp_path)

    assert config.secrets_exclude_globs == ("tests/**",)
    assert warnings == []


def test_unknown_key_warning(tmp_path) -> None:
    (tmp_path / "reposage.toml").write_text(
        "[audit]\nbogus_key = 1\n",
        encoding="utf-8",
    )

    config, warnings = load_standards_config(tmp_path)

    assert config == DEFAULT_STANDARDS_CONFIG
    assert any("bogus_key" in warning for warning in warnings)


def test_malformed_toml_falls_back_to_defaults(tmp_path) -> None:
    (tmp_path / "reposage.toml").write_text("[audit\nmin_commits = ", encoding="utf-8")

    config, warnings = load_standards_config(tmp_path)

    assert config == DEFAULT_STANDARDS_CONFIG
    assert any("malformed toml" in warning for warning in warnings)
