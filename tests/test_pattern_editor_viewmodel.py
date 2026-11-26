"""Tests for the pattern editor ViewModel (headless, no widgets)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from src.viewmodels.main_viewmodel import MainViewModel
from src.viewmodels.pattern_editor_viewmodel import (
    IssueRole,
    PatternEditorViewModel,
    PatternTableModel,
    SaveOutcome,
)

SAMPLE = {
    "alpha": {
        "base": {"separator": r"^(?P<time>\d{2}:\d{2}:\d{2})"},
        "patterns": {"first": r"user=(?P<user>\w+)", "second": r"id=(?P<id>\d+)"},
    },
    "beta": {
        "base": {"separator": r"^\["},
        "patterns": {"default": r"(?P<msg>.+)"},
    },
}


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "patterns.json"
    path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    return path


@pytest.fixture
def editor(qapp: QApplication, config_file: Path) -> PatternEditorViewModel:
    return PatternEditorViewModel(config_file, initial_category="beta")


def _saved(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_opens_on_initial_category(editor: PatternEditorViewModel) -> None:
    assert editor.current_category == 1
    assert editor.separator == r"^\["
    assert editor.columns == ["timestamp", "msg"]
    assert not editor.is_dirty and not editor.can_save


def test_edit_marks_dirty_and_editing_back_clears_it(editor: PatternEditorViewModel) -> None:
    editor.set_separator("^X")
    assert editor.is_dirty and editor.can_save
    editor.set_separator(r"^\[")
    assert not editor.is_dirty


def test_invalid_regex_blocks_save_and_is_exposed_per_item(editor: PatternEditorViewModel, config_file: Path) -> None:
    editor.set_pattern_regex(0, "(?P<msg>")
    assert editor.is_dirty and not editor.can_save
    assert "Invalid regex" in editor.pattern_issue(0)
    model = editor.patterns_model
    assert model.index(0, PatternTableModel.REGEX_COLUMN).data(IssueRole)
    assert editor.categories_model.index(1).data(IssueRole)
    assert editor.save() is SaveOutcome.INVALID
    assert _saved(config_file) == SAMPLE


def test_table_edits_via_model_set_data(editor: PatternEditorViewModel, config_file: Path) -> None:
    model = editor.patterns_model
    assert model.setData(model.index(0, PatternTableModel.NAME_COLUMN), "renamed")
    assert model.setData(model.index(0, PatternTableModel.REGEX_COLUMN), r"(?P<text>.+)")
    assert editor.columns == ["timestamp", "text"]
    assert editor.save() is SaveOutcome.SAVED
    assert _saved(config_file)["beta"]["patterns"] == {"renamed": r"(?P<text>.+)"}


def test_add_move_remove_patterns_keeps_order(editor: PatternEditorViewModel, config_file: Path) -> None:
    editor.select_category(0)
    row = editor.add_pattern(after_row=0)
    assert row == 1
    editor.set_pattern_regex(row, r"(?P<extra>x)")
    assert editor.move_pattern(row, -1) == 0
    assert editor.move_pattern(0, -1) == 0  # already at the top
    editor.remove_pattern(2)  # "second"
    assert editor.save() is SaveOutcome.SAVED
    assert list(_saved(config_file)["alpha"]["patterns"]) == ["new_pattern", "first"]


def test_add_and_rename_category(editor: PatternEditorViewModel, config_file: Path) -> None:
    row = editor.add_category()
    assert editor.current_category == row == 2
    assert not editor.can_save  # new category starts with an empty regex
    editor.categories_model.setData(editor.categories_model.index(row), "gamma", Qt.ItemDataRole.EditRole)
    editor.set_pattern_regex(0, r"(?P<g>.)")
    assert editor.save() is SaveOutcome.SAVED
    assert list(_saved(config_file)) == ["alpha", "beta", "gamma"]


def test_duplicate_category_name_blocks_save(editor: PatternEditorViewModel) -> None:
    editor.rename_category(1, "alpha")
    assert not editor.can_save
    assert "Duplicate category" in editor.summary()


def test_remove_all_categories_emits_selection(editor: PatternEditorViewModel) -> None:
    seen: list[int] = []
    editor.current_category_changed.connect(seen.append)
    editor.remove_category(1)
    editor.remove_category(0)
    assert seen[-1] == -1 and editor.current_category == -1
    assert editor.patterns_model.rowCount() == 0


def test_revert_restores_last_saved_state(editor: PatternEditorViewModel) -> None:
    editor.remove_category(0)
    editor.revert()
    assert [c.name for c in editor.config.categories] == ["alpha", "beta"]
    assert editor.current_category == 1  # still on "beta", back at its original row
    assert not editor.is_dirty


def test_conflict_when_file_changed_on_disk(editor: PatternEditorViewModel, config_file: Path) -> None:
    editor.set_separator("^X")
    config_file.write_text(json.dumps({"external": SAMPLE["alpha"]}), encoding="utf-8")
    stat = config_file.stat()
    os.utime(config_file, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))

    assert editor.save() is SaveOutcome.CONFLICT
    assert list(_saved(config_file)) == ["external"]
    assert editor.save(overwrite_external_changes=True) is SaveOutcome.SAVED
    assert _saved(config_file)["beta"]["base"]["separator"] == "^X"


def test_new_file_is_created_on_save(qapp: QApplication, tmp_path: Path) -> None:
    path = tmp_path / "sub" / "new.json"
    editor = PatternEditorViewModel(path)
    assert editor.is_new_file and editor.current_category == -1
    editor.add_category()
    editor.set_pattern_regex(0, r"(?P<a>.)")
    assert editor.save() is SaveOutcome.SAVED
    assert list(_saved(path)) == ["new_category"]


def test_unparseable_file_reports_load_error(qapp: QApplication, tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    editor = PatternEditorViewModel(path)
    assert editor.load_error
    assert editor.save() is SaveOutcome.INVALID
    assert path.read_text(encoding="utf-8") == "{not json"


def test_broken_regex_file_can_be_opened_and_repaired(qapp: QApplication, tmp_path: Path) -> None:
    path = tmp_path / "patterns.json"
    broken = json.loads(json.dumps(SAMPLE))
    broken["alpha"]["patterns"]["first"] = "("
    path.write_text(json.dumps(broken), encoding="utf-8")
    editor = PatternEditorViewModel(path)
    assert not editor.load_error and editor.issue_count == 1
    editor.set_pattern_regex(0, SAMPLE["alpha"]["patterns"]["first"])
    assert editor.save() is SaveOutcome.SAVED


def test_main_viewmodel_reloads_after_save(qapp: QApplication, config_file: Path, tmp_path: Path) -> None:
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    main = MainViewModel(settings=settings)
    main.set_patterns_config(str(config_file))
    assert main.pattern_keys == ["alpha", "beta"]

    editor = main.create_pattern_editor()
    assert editor is not None
    editor.rename_category(0, "alpha_renamed")
    assert editor.save() is SaveOutcome.SAVED
    assert main.pattern_keys == ["alpha_renamed", "beta"]
    main.shutdown()
