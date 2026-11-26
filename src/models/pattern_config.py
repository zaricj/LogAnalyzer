"""Editable, GUI-agnostic representation of a patterns config file.

The JSON on disk maps a category name to ``{"base": {"separator": ...},
"patterns": {name: regex, ...}}``. Dicts are awkward to edit in place (renaming
a key changes its identity, order is significant because the first non-empty
match wins), so the editor works on ordered dataclasses and converts back to
the JSON shape when saving.

Loading is deliberately lenient about regex content: a config with a broken
regex can still be opened, so it can be repaired in the editor. Structural
problems (wrong JSON types) are rejected.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.modules.io.regex_service import PATTERN_FLAGS

SEPARATOR_KEY = "separator"


class IssueField(Enum):
    CATEGORY = "category"
    NAME = "name"
    SEPARATOR = "separator"
    REGEX = "regex"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One problem that blocks saving.

    ``category`` indexes ``PatternConfig.categories``; ``rule`` indexes that
    category's ``rules`` and is ``None`` for category level problems.
    """

    category: int
    rule: int | None
    field: IssueField
    message: str


@dataclass(slots=True)
class PatternRule:
    """A named extraction regex (one entry of a category's ``patterns``)."""

    name: str
    regex: str


@dataclass(slots=True)
class PatternCategory:
    """One top-level pattern key: an event separator plus ordered rules."""

    name: str
    separator: str = ""
    rules: list[PatternRule] = field(default_factory=list)
    # Unknown keys are carried through untouched so saving never loses data.
    extra_base: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, name: str, data: Any) -> PatternCategory:
        if not isinstance(data, dict):
            raise TypeError(f"Category '{name}' must be a JSON object")
        base = data.get("base", {})
        patterns = data.get("patterns", {})
        if not isinstance(base, dict):
            raise TypeError(f"'base' in category '{name}' must be a JSON object")
        if not isinstance(patterns, dict):
            raise TypeError(f"'patterns' in category '{name}' must be a JSON object")

        separator = base.get(SEPARATOR_KEY, "")
        if not isinstance(separator, str):
            raise TypeError(f"'separator' in category '{name}' must be a string")
        rules: list[PatternRule] = []
        for rule_name, regex in patterns.items():
            if not isinstance(regex, str):
                raise TypeError(f"Pattern '{rule_name}' in category '{name}' must be a string")
            rules.append(PatternRule(rule_name, regex))

        return cls(
            name=name,
            separator=separator,
            rules=rules,
            extra_base={k: copy.deepcopy(v) for k, v in base.items() if k != SEPARATOR_KEY},
            extra={k: copy.deepcopy(v) for k, v in data.items() if k not in ("base", "patterns")},
        )

    def to_json(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "base": {SEPARATOR_KEY: self.separator, **copy.deepcopy(self.extra_base)},
            "patterns": {rule.name: rule.regex for rule in self.rules},
        }
        data.update(copy.deepcopy(self.extra))
        return data

    def unique_rule_name(self, stem: str = "new_pattern") -> str:
        return _unique_name(stem, {rule.name for rule in self.rules})


@dataclass(slots=True)
class PatternConfig:
    """The whole patterns config: an ordered list of categories."""

    categories: list[PatternCategory] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Any) -> PatternConfig:
        if not isinstance(data, dict):
            raise TypeError("Patterns config must be a JSON object")
        return cls([PatternCategory.from_json(name, value) for name, value in data.items()])

    def to_json(self) -> dict[str, Any]:
        """Serialise back to the on-disk shape (call only when ``validate()`` is empty)."""
        return {category.name: category.to_json() for category in self.categories}

    def clone(self) -> PatternConfig:
        return copy.deepcopy(self)

    def unique_category_name(self, stem: str = "new_category") -> str:
        return _unique_name(stem, {category.name for category in self.categories})

    def validate(self) -> list[ValidationIssue]:
        """Return every problem that would make the config unusable or ambiguous."""
        issues: list[ValidationIssue] = []
        seen_categories: set[str] = set()

        for ci, category in enumerate(self.categories):
            name = category.name.strip()
            if not name:
                issues.append(ValidationIssue(ci, None, IssueField.NAME, "Category name must not be empty."))
            elif name != category.name:
                issues.append(
                    ValidationIssue(ci, None, IssueField.NAME, "Category name has leading/trailing spaces.")
                )
            elif name in seen_categories:
                issues.append(ValidationIssue(ci, None, IssueField.NAME, f"Duplicate category name '{name}'."))
            seen_categories.add(name)

            if not category.separator:
                issues.append(
                    ValidationIssue(ci, None, IssueField.SEPARATOR, "Event separator must not be empty.")
                )
            elif error := regex_error(category.separator):
                issues.append(ValidationIssue(ci, None, IssueField.SEPARATOR, f"Separator: {error}"))

            if not category.rules:
                issues.append(
                    ValidationIssue(ci, None, IssueField.CATEGORY, "Add at least one pattern.")
                )

            seen_rules: set[str] = set()
            for ri, rule in enumerate(category.rules):
                rule_name = rule.name.strip()
                if not rule_name:
                    issues.append(ValidationIssue(ci, ri, IssueField.NAME, "Pattern name must not be empty."))
                elif rule_name != rule.name:
                    issues.append(
                        ValidationIssue(ci, ri, IssueField.NAME, "Pattern name has leading/trailing spaces.")
                    )
                elif rule_name in seen_rules:
                    issues.append(
                        ValidationIssue(ci, ri, IssueField.NAME, f"Duplicate pattern name '{rule_name}'.")
                    )
                seen_rules.add(rule_name)

                if not rule.regex:
                    issues.append(ValidationIssue(ci, ri, IssueField.REGEX, "Regex must not be empty."))
                elif error := regex_error(rule.regex, PATTERN_FLAGS):
                    issues.append(ValidationIssue(ci, ri, IssueField.REGEX, error))

        return issues


def regex_error(pattern: str, flags: int = 0) -> str | None:
    """Return a readable compile error for ``pattern``, or ``None`` if it compiles."""
    try:
        re.compile(pattern, flags)
    except re.error as exc:
        position = f" at position {exc.pos}" if exc.pos is not None else ""
        return f"Invalid regex{position}: {exc.msg}"
    return None


def _unique_name(stem: str, taken: set[str]) -> str:
    if stem not in taken:
        return stem
    index = 2
    while f"{stem}_{index}" in taken:
        index += 1
    return f"{stem}_{index}"
