"""
Configuration and constants for R2R Repository Loader
"""
import os
from pathlib import Path

# =============================================================================
# R2R API CONFIGURATION
# =============================================================================
R2R_API_URL = os.getenv('R2R_API_URL', 'http://localhost:7272')
R2R_EMAIL = os.getenv('R2R_EMAIL', '')
R2R_PASSWORD = os.getenv('R2R_PASSWORD', '')

# =============================================================================
# RATE LIMITING
# =============================================================================
# RATIONALE: Backend может не выдержать >10 req/sec, добавляем задержки
UPLOAD_DELAY_MS = 300  # 300ms между загрузками файлов
API_RETRY_ATTEMPTS = 3
API_RETRY_BACKOFF = 2  # Exponential backoff multiplier

# =============================================================================
# FILE FILTERING
# =============================================================================
# FORMULA: Основано на research из R2R_CODE_TESTING_FINAL_REPORT.md
# Code files поддерживаемые R2R (tested)
SUPPORTED_EXTENSIONS = {
    # Programming languages
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.jsx': 'javascript',
    '.java': 'java',
    '.cs': 'csharp',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.hpp': 'cpp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.r': 'r',
    '.m': 'objective-c',

    # Web/markup
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.vue': 'vue',

    # Shell/config
    '.sh': 'shell',
    '.bash': 'shell',
    '.zsh': 'shell',
    '.fish': 'shell',
    # YAML/TOML грузим как txt (R2R не поддерживает yaml/toml как DocumentType)
    '.yaml': 'txt',
    '.yml': 'txt',
    '.toml': 'txt',
    '.json': 'json',
    '.xml': 'txt',

    # Documentation
    '.md': 'markdown',
    '.rst': 'restructuredtext',
    '.txt': 'text',

    # Images (R2R multimodal processing)
    '.png': 'image',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.gif': 'image',
    '.svg': 'image',
    '.webp': 'image',

    # Diagrams
    '.puml': 'plantuml',
    '.plantuml': 'plantuml',
}

# RISK: Большие файлы могут вызвать timeout или OOM
# Images могут быть больше code файлов, увеличиваем limit
MAX_FILE_SIZE_MB = 20  # 20MB max per file (images, diagrams)
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Directories to ignore (gitignore-style patterns)
# NOTE: .gitignore паттерны загружаются автоматически в FileFilter._load_gitignore()
# Эти паттерны используются как fallback когда .gitignore отсутствует
IGNORE_PATTERNS = [
    # Version control
    '.git',
    '.svn',
    '.hg',
    '.bzr',

    # Python
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    '.coverage',
    'htmlcov',
    '*.egg-info',
    '.eggs',
    'venv',
    'env',
    '.env',
    '.venv',
    'pip-log.txt',
    'poetry.lock',
    'Pipfile.lock',
    'pdm.lock',

    # JavaScript/Node.js
    'node_modules',
    'bower_components',
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    'bun.lockb',
    '.next',
    '.nuxt',
    '.parcel-cache',
    '.cache',
    'npm-debug.log*',
    'yarn-debug.log*',
    'yarn-error.log*',

    # Java
    'target',
    '.gradle',
    '.mvn',
    '*.class',
    '*.jar',
    '*.war',
    '*.ear',

    # .NET/C#
    'bin',
    'obj',
    'packages',
    'packages.lock.json',
    '.vs',
    '*.suo',
    '*.user',

    # Go
    'vendor',
    'go.sum',
    'go.work.sum',

    # Rust
    'Cargo.lock',

    # Ruby
    '.bundle',
    'vendor/bundle',
    'Gemfile.lock',

    # PHP
    'vendor',
    'composer.lock',
    'composer.phar',

    # Swift
    'Package.resolved',

    # Dart/Flutter
    'pubspec.lock',

    # Elixir
    'mix.lock',

    # Build outputs (general)
    'dist',
    'build',
    'out',
    'release',
    'Debug',
    'Release',

    # Test coverage
    'coverage',
    '.nyc_output',

    # Logs and temp files
    'logs',
    '*.log',
    'tmp',
    'temp',
    '*.tmp',
    '*.temp',

    # IDEs and editors
    '.vscode',
    '.idea',
    '*.iml',
    '.sublime-workspace',
    '.sublime-project',
    '*.swp',
    '*.swo',
    '*~',
    '.project',
    '.classpath',
    '.settings',

    # OS files
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
]

# =============================================================================
# QUALITY SETTINGS
# =============================================================================
# RATIONALE: Основано на findings из R2R_CODE_TESTING_FINAL_REPORT.md
# Для code рекомендуется chunk_size 512-1024 (vs 1024 для text)
INGESTION_CONFIG = {
    'chunk_enrichment_settings': {
        'enable_chunk_enrichment': True,
    },
    'chunking_config': {
        # Code ~2x плотнее чем text, уменьшаем chunk size
        'chunk_size': 512,
        'chunk_overlap': 50,
    },
}

# Knowledge Graph entity types для code
KG_ENTITY_TYPES = [
    'function',
    'class',
    'variable',
    'module',
    'constant',
    'method',
    'interface',
    'type',
]

KG_RELATION_TYPES = [
    'calls',
    'imports',
    'uses',
    'defines',
    'inherits',
    'implements',
    'contains',
]

# =============================================================================
# TEMPORARY FILES
# =============================================================================
TEMP_DIR = Path('/tmp/r2r-repo-loader')
CACHE_DIR = TEMP_DIR / 'cache'
REPOS_DIR = TEMP_DIR / 'repos'

# Create temp directories
TEMP_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)
