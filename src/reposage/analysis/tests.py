"""Test detection heuristics."""

from __future__ import annotations

from pathlib import PurePosixPath

from reposage.models import FileRecord

TEST_DIRECTORY_NAMES = {"__tests__", "spec", "specs", "test", "tests"}

TEST_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rb", ".go", ".rs", ".java", ".cs"}


def detect_test_files(file_records: list[FileRecord]) -> list[str]:
    """Return file paths that look like automated tests."""

    test_files = [
        file_record.path for file_record in file_records if _is_test_file(file_record.path)
    ]
    test_files.sort()
    return test_files


def _is_test_file(path: str) -> bool:
    pure_path = PurePosixPath(path)
    if pure_path.suffix.lower() not in TEST_EXTENSIONS:
        return False
    if any(part.lower() in TEST_DIRECTORY_NAMES for part in pure_path.parts):
        return True
    file_name = pure_path.name.lower()
    return file_name.startswith("test_") or file_name.endswith(
        (
            "_test.py",
            ".spec.ts",
            ".spec.js",
            "test.java",
            "spec.java",
            "test.cs",
            "tests.cs",
            "spec.cs",
        )
    )
