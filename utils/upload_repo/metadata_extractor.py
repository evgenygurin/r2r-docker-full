"""
Metadata extraction from code files
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extract metadata from code files: language, module, imports

    SIMPLIFIED IMPLEMENTATION:
    - Regex-based extraction для основных языков
    - Не использует AST parsing (dependency-free)
    - Фокус на практичности, не на полноте
    """

    # Import patterns для разных языков
    IMPORT_PATTERNS = {
        'python': [
            r'^import\s+([\w.]+)',
            r'^from\s+([\w.]+)\s+import',
        ],
        'javascript': [
            r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ],
        'typescript': [
            r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ],
        'java': [
            r'^import\s+([\w.]+)',
        ],
        'go': [
            r'import\s+"([^"]+)"',
            r'import\s+\(\s*"([^"]+)"',
        ],
        'rust': [
            r'^use\s+([\w:]+)',
        ],
        'cpp': [
            r'#include\s+[<"]([^>"]+)[>"]',
        ],
        'c': [
            r'#include\s+[<"]([^>"]+)[>"]',
        ],
    }

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def extract_imports(
        self,
        file_path: Path,
        language: str
    ) -> List[str]:
        """
        Extract import statements from file

        Returns:
            List of imported module/package names

        SIMPLIFIED: Regex-based, может пропустить сложные cases
        """
        patterns = self.IMPORT_PATTERNS.get(language, [])

        if not patterns:
            return []

        imports = set()

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments
                    if line.startswith('#') or line.startswith('//'):
                        continue

                    for pattern in patterns:
                        match = re.match(pattern, line)
                        if match:
                            import_name = match.group(1)
                            imports.add(import_name)

        except Exception as e:
            logger.debug(f"Failed to extract imports from {file_path.name}: {e}")

        return sorted(list(imports))

    def extract_module_name(
        self,
        file_path: Path,
        repo_path: Path
    ) -> str:
        """
        Extract module name from file path

        Examples:
            src/services/auth.py -> services.auth
            lib/utils.js -> lib.utils
            auth.py -> auth

        CONVENTION: Dot-separated path без extension
        """
        try:
            rel_path = file_path.relative_to(repo_path)
        except ValueError:
            rel_path = file_path

        # Remove extension
        module_path = rel_path.with_suffix('')

        # Convert to dot notation
        module_name = str(module_path).replace('/', '.')

        # Remove leading dots
        module_name = module_name.lstrip('.')

        return module_name

    def extract_file_stats(self, file_path: Path) -> Dict[str, int]:
        """
        Extract basic file statistics

        Returns:
            Dict with lines_total, lines_code, lines_comment
        """
        stats = {
            'lines_total': 0,
            'lines_code': 0,
            'lines_comment': 0,
            'lines_blank': 0,
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stats['lines_total'] += 1

                    stripped = line.strip()

                    if not stripped:
                        stats['lines_blank'] += 1
                    elif stripped.startswith('#') or stripped.startswith('//'):
                        stats['lines_comment'] += 1
                    else:
                        stats['lines_code'] += 1

        except Exception as e:
            logger.debug(f"Failed to extract stats from {file_path.name}: {e}")

        return stats

    def build_metadata(
        self,
        file_path: Path,
        language: str,
        repo_url: str,
        repo_name: str,
        commit_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build complete metadata for file upload

        STRUCTURE:
        - source: 'codebase'
        - language: programming language
        - module: dot-separated module path
        - file_path: relative path from repo root
        - imports: список импортов
        - repo_name: название репозитория
        - repo_url: Git URL
        - commit_hash: Git commit
        - lines_*: статистика строк кода
        """
        rel_path = str(file_path.relative_to(self.repo_path))
        module_name = self.extract_module_name(file_path, self.repo_path)
        imports = self.extract_imports(file_path, language)
        stats = self.extract_file_stats(file_path)

        metadata = {
            # Core fields
            'source': 'codebase',
            'language': language,
            'module': module_name,
            'file_path': rel_path,

            # Repository info
            'repo_name': repo_name,
            'repo_url': repo_url,

            # Commit info
            'commit_hash': commit_info['hash'],
            'commit_hash_short': commit_info['hash_short'],
            'commit_message': commit_info['message'],
            'commit_author': commit_info['author_name'],
            'commit_date': commit_info['date'],

            # Code analysis
            'imports': imports,
            'import_count': len(imports),

            # Statistics
            **stats,
        }

        return metadata

    def extract_package_name(self, imports: List[str]) -> List[str]:
        """
        Extract top-level package names from imports

        Examples:
            ['fastapi.routing', 'pydantic'] -> ['fastapi', 'pydantic']

        USEFUL: Для фильтрации по external dependencies
        """
        packages = set()

        for import_name in imports:
            # Get first component
            if '.' in import_name:
                package = import_name.split('.')[0]
            else:
                package = import_name

            packages.add(package)

        return sorted(list(packages))
