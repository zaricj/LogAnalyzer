"""Tests for the GUI-agnostic pattern config model and its atomic save."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.models.pattern_config import IssueField, PatternConfig, PatternRule
from src.modules.io.regex_service import load_patterns_json, save_patterns_json

PROJECT_PATTERNS = Path(__file__).resolve().parents[1] / "patterns" / "patterns.json"


def _sample() -> dict:
    return {
        "app": {
            "base": {"separator": r"^(?P<time>\d{2}:\d{2}:\d{2})"},
            "patterns": {"first": r"user=(?P<user>\w+)", "second": r"id=(?P<id>\d+)"},
        }
    }


def test_round_trip_preserves_project_config() -> None:
    data = load_patterns_json(PROJECT_PATTERNS)
    assert PatternConfig.from_json(data).to_json() == data


def test_round_trip_preserves_order_and_unknown_keys() -> None:
    data = _sample()
    data["app"]["base"]["note"] = "kept"
    data["app"]["description"] = {"nested": [1, 2]}
    config = PatternConfig.from_json(data)
    assert [r.name for r in config.categories[0].rules] == ["first", "second"]
    assert config.to_json() == data


@pytest.mark.parametrize("bad", [[], {"app": []}, {"app": {"patterns": {"x": 1}}}, {"app": {"base": "x"}}])
def test_from_json_rejects_wrong_shapes(bad: object) -> None:
    with pytest.raises(TypeError):
        PatternConfig.from_json(bad)


def test_valid_config_has_no_issues() -> None:
    assert PatternConfig.from_json(_sample()).validate() == []


def test_validate_reports_each_problem_with_location() -> None:
    config = PatternConfig.from_json(_sample())
    category = config.categories[0]
    category.separator = "("
    category.rules[0].regex = "(?P<a>x"
    category.rules[1].name = "first"  # duplicate
    category.rules.append(PatternRule("", ""))

    issues = {(i.category, i.rule, i.field) for i in config.validate()}
    assert issues == {
        (0, None, IssueField.SEPARATOR),
        (0, 0, IssueField.REGEX),
        (0, 1, IssueField.NAME),
        (0, 2, IssueField.NAME),
        (0, 2, IssueField.REGEX),
    }


def test_validate_flags_duplicate_and_empty_categories() -> None:
    config = PatternConfig.from_json(_sample())
    config.categories.append(config.categories[0].__class__(name="app", separator="^x"))
    messages = [i.message for i in config.validate()]
    assert any("Duplicate category" in m for m in messages)
    assert any("at least one pattern" in m for m in messages)


def test_pattern_regex_is_validated_with_pattern_flags() -> None:
    # Inline global flags must lead the pattern; valid alone, still valid with MULTILINE|DOTALL.
    config = PatternConfig.from_json(_sample())
    config.categories[0].rules[0].regex = r"(?s)^a.b$"
    assert config.validate() == []


def test_unique_names() -> None:
    config = PatternConfig.from_json(_sample())
    assert config.unique_category_name("app") == "app_2"
    assert config.categories[0].unique_rule_name("first") == "first_2"


def test_save_is_atomic_and_keeps_backup(tmp_path: Path) -> None:
    target = tmp_path / "patterns.json"
    target.write_text('{"old": true}', encoding="utf-8")
    data = _sample()
    data["app"]["patterns"]["umlaut"] = "Integritätsbedingung"

    save_patterns_json(target, data)

    assert json.loads(target.read_text(encoding="utf-8")) == data
    assert "Integritätsbedingung" in target.read_text(encoding="utf-8")  # not \u-escaped
    assert (tmp_path / "patterns.json.bak").read_text(encoding="utf-8") == '{"old": true}'
    assert sorted(p.name for p in tmp_path.iterdir()) == ["patterns.json", "patterns.json.bak"]


def test_save_refuses_invalid_config_and_leaves_file_untouched(tmp_path: Path) -> None:
    target = tmp_path / "patterns.json"
    target.write_text("original", encoding="utf-8")
    data = _sample()
    data["app"]["patterns"]["first"] = "("

    with pytest.raises(ValueError):
        save_patterns_json(target, data)
    assert target.read_text(encoding="utf-8") == "original"
    assert [p.name for p in tmp_path.iterdir()] == ["patterns.json"]
