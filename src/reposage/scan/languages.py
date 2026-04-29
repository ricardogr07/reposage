"""Language detection heuristics."""

from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from reposage.models import FileRecord, LanguageStat

EXTENSION_LANGUAGE_MAP = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "React JSX",
    ".kt": "Kotlin",
    ".md": "Markdown",
    ".mjs": "JavaScript",
    ".py": "Python",
    ".rb": "Ruby",
    ".cs": "C#",
    ".csx": "C# Script",
    ".fs": "F#",
    ".rs": "Rust",
    ".scss": "SCSS",
    ".vb": "Visual Basic",
    ".sh": "Shell",
    ".sql": "SQL",
    ".svg": "SVG",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "React TSX",
    ".txt": "Text",
    ".yaml": "YAML",
    ".yml": "YAML",
}

SPECIAL_FILENAMES = {
    "dockerfile": "Docker",
    "makefile": "Makefile",
}


def detect_languages(file_records: list[FileRecord]) -> list[LanguageStat]:
    """Infer repository languages from file extensions and special filenames."""

    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for file_record in file_records:
        language = _detect_language(file_record)
        if language is None:
            continue
        totals[language][0] += 1
        totals[language][1] += file_record.size_bytes

    languages = [
        LanguageStat(language=name, file_count=counts[0], total_bytes=counts[1])
        for name, counts in totals.items()
    ]
    languages.sort(key=lambda item: (-item.total_bytes, item.language))
    return languages


def _detect_language(file_record: FileRecord) -> str | None:
    file_name = PurePosixPath(file_record.path).name
    special = SPECIAL_FILENAMES.get(file_name.lower())
    if special is not None:
        return special
    return EXTENSION_LANGUAGE_MAP.get(file_record.extension or "")
