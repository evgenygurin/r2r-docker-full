"""
Code file filtering with gitignore support
"""
import fnmatch
import logging
from pathlib import Path
from typing import List, Set

from config import (
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    IGNORE_PATTERNS,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileFilter:
    """
    Filter code files by extension, size, and gitignore patterns

    ARCHITECTURE:
    - Extension-based filtering (только поддерживаемые языки)
    - Size limit для предотвращения OOM
    - Gitignore-style pattern matching
    - Recursive directory traversal
    """

    def __init__(
        self,
        repo_path: Path,
        extensions: dict = SUPPORTED_EXTENSIONS,
        max_size_bytes: int = MAX_FILE_SIZE_BYTES,
        ignore_patterns: List[str] = None
    ):
        self.repo_path = repo_path
        self.extensions = extensions
        self.max_size_bytes = max_size_bytes
        self.ignore_patterns = ignore_patterns or IGNORE_PATTERNS.copy()

        # Load .gitignore if exists
        self._load_gitignore()

    def _load_gitignore(self) -> None:
        """
        Load patterns from .gitignore

        NOTE: Упрощенная реализация, не поддерживает все git features
        """
        gitignore_path = self.repo_path / '.gitignore'

        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Remove leading slash
                    if line.startswith('/'):
                        line = line[1:]

                    self.ignore_patterns.append(line)

            logger.debug(f"Loaded {gitignore_path} with {len(self.ignore_patterns)} total patterns")

    def _is_ignored(self, path: Path) -> bool:
        """
        Check if path matches ignore patterns

        SIMPLIFIED: Проверяет каждый компонент пути
        """
        # Get relative path from repo root
        try:
            rel_path = path.relative_to(self.repo_path)
        except ValueError:
            # Path is outside repo
            return True

        # Check each path component
        path_str = str(rel_path)
        parts = path_str.split('/')

        for pattern in self.ignore_patterns:
            # Match against full path
            if fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path_str, f'**/{pattern}'):
                return True

            # Match against directory names
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        return False

    def _is_supported_file(self, path: Path) -> bool:
        """Check if file has supported extension"""
        return path.suffix in self.extensions

    def _is_size_ok(self, path: Path) -> bool:
        """Check if file size is within limit"""
        try:
            # Follow symlinks=False to skip broken symlinks
            size = path.stat(follow_symlinks=False).st_size

            # Skip symlinks entirely
            if path.is_symlink():
                return False

            return size <= self.max_size_bytes
        except (OSError, FileNotFoundError):
            # Broken symlink или file not accessible
            return False

    def filter_files(
        self,
        verbose: bool = False
    ) -> List[Path]:
        """
        Get all code files from repository

        Returns:
            List of Path objects for valid code files

        RECURSIVE: Обходит все директории кроме ignored
        """
        valid_files = []
        skipped_ignored = 0
        skipped_extension = 0
        skipped_size = 0

        for path in self.repo_path.rglob('*'):
            # Skip directories
            if path.is_dir():
                continue

            # Skip symlinks (broken или valid)
            if path.is_symlink():
                skipped_ignored += 1
                continue

            # Skip ignored
            if self._is_ignored(path):
                skipped_ignored += 1
                continue

            # Check extension
            if not self._is_supported_file(path):
                skipped_extension += 1
                continue

            # Check size
            if not self._is_size_ok(path):
                skipped_size += 1
                if verbose:
                    try:
                        size_mb = path.stat().st_size / 1024 / 1024
                        logger.warning(f"Skipping large file: {path.name} ({size_mb:.1f}MB)")
                    except (OSError, FileNotFoundError):
                        logger.warning(f"Skipping inaccessible file: {path.name}")
                continue

            valid_files.append(path)

        logger.info(f"Found {len(valid_files)} valid code files")
        logger.debug(f"Skipped: {skipped_ignored} ignored, {skipped_extension} unsupported, {skipped_size} too large")

        return valid_files

    def get_file_language(self, path: Path) -> str:
        """
        Get programming language from file extension

        Returns:
            Language name (e.g., 'python', 'javascript')
        """
        return self.extensions.get(path.suffix, 'unknown')

    def group_by_language(
        self,
        files: List[Path]
    ) -> dict[str, List[Path]]:
        """
        Group files by programming language

        Returns:
            Dict of {language: [file_paths]}
        """
        groups = {}

        for file_path in files:
            lang = self.get_file_language(file_path)

            if lang not in groups:
                groups[lang] = []

            groups[lang].append(file_path)

        return groups

    def get_relative_path(self, file_path: Path) -> str:
        """
        Get relative path from repo root

        Used for metadata 'file_path' field
        """
        try:
            return str(file_path.relative_to(self.repo_path))
        except ValueError:
            return str(file_path)

    def estimate_total_size(self, files: List[Path]) -> int:
        """
        Estimate total size of files in bytes

        MONITORING: Полезно для progress tracking
        """
        total = 0
        for path in files:
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return total
