"""The ADR index in docs/architecture.md stays aligned with docs/decisions/."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = REPO_ROOT / "docs" / "architecture.md"
DECISIONS = REPO_ROOT / "docs" / "decisions"

_INDEX_ROW = re.compile(
    r"^\| \[ADR-\d+\]\((decisions/[^)]+)\) \|",
    re.MULTILINE,
)


def indexed_decision_files(architecture_text: str) -> list[str]:
    return _INDEX_ROW.findall(architecture_text)


def decision_record_names(decisions_dir: Path) -> set[str]:
    return {path.name for path in decisions_dir.glob("adr-*.md")}


def missing_from_index(architecture_text: str, decisions_dir: Path) -> list[str]:
    indexed = {Path(link).name for link in indexed_decision_files(architecture_text)}
    return sorted(decision_record_names(decisions_dir) - indexed)


def missing_index_targets(architecture_text: str, docs_dir: Path) -> list[str]:
    return [
        link
        for link in indexed_decision_files(architecture_text)
        if not (docs_dir / link).is_file()
    ]


def test_every_decision_record_has_an_index_row() -> None:
    missing = missing_from_index(ARCHITECTURE.read_text(encoding="utf-8"), DECISIONS)
    assert missing == [], f"decision records missing from the ADR index: {missing}"


def test_every_index_row_links_a_file_that_exists() -> None:
    missing = missing_index_targets(
        ARCHITECTURE.read_text(encoding="utf-8"), REPO_ROOT / "docs"
    )
    assert missing == [], f"ADR index rows link missing files: {missing}"


def test_a_row_that_links_a_missing_file_is_reported(tmp_path: Path) -> None:
    table = (
        "| ADR | Title | Status |\n"
        "|---|---|---|\n"
        "| [ADR-001](decisions/adr-001-example.md) | Example | Accepted |\n"
        "| [ADR-099](decisions/adr-099-missing.md) | Missing | Accepted |\n"
    )
    (tmp_path / "decisions").mkdir()
    (tmp_path / "decisions" / "adr-001-example.md").write_text("# ADR-001\n")
    assert missing_index_targets(table, tmp_path) == ["decisions/adr-099-missing.md"]
