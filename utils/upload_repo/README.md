# R2R Repository Loader

> **Production-ready tool for loading Git repositories into R2R for code search, RAG, and Knowledge Graph analysis.**

Автоматическая загрузка любого Git-репозитория в R2R с полным pipeline: клонирование → фильтрация → извлечение метаданных → upload → ingestion → Knowledge Graph extraction.

---

## 🎯 Features

- ✅ **Full Git Integration** — clone, update, branch support
- ✅ **Multi-format Support** — 35+ file types (code, images, diagrams, docs)
- ✅ **Multimodal Processing** — R2R handles images (PNG, JPG, SVG) with vision models
- ✅ **Smart File Filtering** — gitignore support, size limits (20MB), extension filtering
- ✅ **Rich Metadata** — language, module, imports, commit info, file stats
- ✅ **Retry Logic** — exponential backoff, rate limiting, error handling
- ✅ **Knowledge Graph** — automatic entity & relationship extraction
- ✅ **Idempotent Updates** — update existing collections без дубликатов
- ✅ **Progress Tracking** — real-time upload status

---

## 📦 Installation

### Prerequisites

- Python 3.8+
- Git
- R2R API access (configured endpoint)

### Setup

```bash
# Clone или скопируй директорию upload_repo
cd /Users/laptop/mcp/R2R-Application/upload_repo

# Install dependencies
pip install requests

# Configure environment (optional)
export R2R_API_URL="http://136.119.36.216:7272"
export R2R_EMAIL="your@email.com"
export R2R_PASSWORD="your-password"
```

---

## 🚀 Quick Start

### Basic Usage

```bash
# Load repository с default settings
./repo_loader.py https://github.com/user/repo
```

**Что произойдет:**
1. Clone репозитория в `/tmp/r2r-repo-loader/repos/`
2. Фильтрация code files (25+ languages)
3. Создание collection `repo-{repo-name}`
4. Upload files с метаданными
5. Monitoring ingestion status
6. Summary statistics

### Advanced Usage

```bash
# Load в конкретную collection
./repo_loader.py https://github.com/user/repo --collection my-codebase

# Update существующего репо + extract Knowledge Graph
./repo_loader.py https://github.com/user/repo --update --extract-kg

# Specific branch
./repo_loader.py https://github.com/user/repo --branch develop

# Verbose output для debugging
./repo_loader.py https://github.com/user/repo --verbose
```

### Environment Variables

```bash
# Override R2R API endpoint
export R2R_API_URL="https://your-r2r-instance.com"

# Use different credentials
export R2R_EMAIL="custom@email.com"
export R2R_PASSWORD="custom-password"

./repo_loader.py https://github.com/user/repo
```

---

## 📋 Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `repo_url` | Git repository URL (required) | - |
| `--collection NAME` | Collection name | `repo-{name}` |
| `--branch BRANCH` | Git branch to clone | remote HEAD |
| `--update` | Pull latest changes if exists | false |
| `--extract-kg` | Extract Knowledge Graph | false |
| `--quality MODE` | Processing quality (`high`, `fast`) | `high` |
| `--verbose` | Verbose logging | false |
| `--email EMAIL` | R2R account email | from config |
| `--password PASS` | R2R account password | from config |

### Examples

```bash
# Complete workflow с KG extraction
./repo_loader.py https://github.com/fastapi/fastapi \
  --collection fastapi-source \
  --extract-kg \
  --verbose

# Update существующего репо
./repo_loader.py https://github.com/fastapi/fastapi \
  --update

# Specific branch для feature testing
./repo_loader.py https://github.com/mycompany/backend \
  --branch feature/new-api \
  --collection backend-feature-test
```

---

## 🏗️ Architecture

### Components

```text
repo_loader.py          Main orchestrator + CLI
├── config.py           Configuration & constants
├── r2r_client.py       R2R API wrapper с retry logic
├── git_manager.py      Git operations (clone, pull, info)
├── file_filter.py      Code file filtering + gitignore
└── metadata_extractor.py Metadata extraction (imports, stats)
```

### Workflow

```text
1. GIT MANAGEMENT
   └─ Clone/update repository
   └─ Extract commit info (hash, author, message)

2. FILE FILTERING
   └─ Recursive directory traversal
   └─ Extension filtering (25+ languages)
   └─ Gitignore pattern matching
   └─ Size limit enforcement (<5MB per file)

3. COLLECTION SETUP
   └─ Create collection или get existing
   └─ Auto-generated name: repo-{name}

4. FILE UPLOAD
   └─ Extract metadata для каждого файла:
       - language, module, file_path
       - imports, import_count
       - repo info, commit info
       - line counts (total, code, comment, blank)
   └─ Upload с rate limiting (300ms delay)
   └─ Progress tracking

5. INGESTION MONITORING
   └─ Poll document status
   └─ Wait for ingestion_status: success
   └─ Timeout: 300s

6. KNOWLEDGE GRAPH (optional)
   └─ Pull entities & relationships
   └─ Wait for extraction (30s)
   └─ Report entity/relationship counts
```

### Data Flow

```text
Git Repo → Clone → Filter → Extract Metadata → Upload → R2R API
                                                          ↓
                                                    Ingestion Pipeline
                                                          ↓
                                              Chunking → Embeddings
                                                          ↓
                                              Knowledge Graph ← Pull
```

---

## 🔧 Configuration

### config.py

Основные настройки в `config.py`:

```python
# R2R API
R2R_API_URL = 'http://136.119.36.216:7272'
R2R_EMAIL = 'your@email.com'
R2R_PASSWORD = 'your-password'

# Rate Limiting
UPLOAD_DELAY_MS = 300  # 300ms между uploads

# File Filtering
MAX_FILE_SIZE_MB = 20  # Max file size (images up to 20MB)
SUPPORTED_EXTENSIONS = {...}  # 35+ file types (code + images)
IGNORE_PATTERNS = ['node_modules', '.git', ...]

# Quality Settings (для code)
INGESTION_CONFIG = {
    'chunking_config': {
        'chunk_size': 512,    # Code плотнее чем text
        'chunk_overlap': 50,
    }
}
```

### Supported File Types

**Programming Languages** (17):
- Python, JavaScript, TypeScript, Java, C#, C++, C, Go, Rust
- Ruby, PHP, Swift, Kotlin, Scala, R, Objective-C

**Web/Markup** (4):
- HTML, CSS, SCSS, Vue

**Shell/Config** (7):
- Bash/Zsh/Fish, YAML, TOML, JSON, XML

**Documentation** (3):
- Markdown, ReStructuredText, Text

**Images** (6):
- PNG, JPG/JPEG, GIF, SVG, WebP

**Diagrams** (2):
- PlantUML (.puml, .plantuml)

---

## 📊 Metadata Fields

Каждый uploaded file включает:

```json
{
  "source": "codebase",
  "language": "python",
  "module": "src.services.auth",
  "file_path": "src/services/auth.py",

  "repo_name": "backend",
  "repo_url": "https://github.com/user/backend",

  "commit_hash": "a1b2c3d...",
  "commit_hash_short": "a1b2c3d",
  "commit_message": "feat: add authentication",
  "commit_author": "John Doe",
  "commit_date": "2025-12-17T...",

  "imports": ["fastapi", "pydantic", "jwt"],
  "import_count": 3,

  "lines_total": 150,
  "lines_code": 120,
  "lines_comment": 20,
  "lines_blank": 10
}
```

**Use Cases:**
- **Фильтрация по language** — `language: python`
- **Поиск по модулю** — `module: services.auth`
- **Dependencies analysis** — `imports: fastapi`
- **Commit tracking** — `commit_hash_short: a1b2c3d`

---

## 🧪 Examples

### Example 1: Load Public Repository

```bash
./repo_loader.py https://github.com/pallets/flask \
  --collection flask-framework \
  --extract-kg \
  --verbose
```

**Output:**
```text
=================================================================
STEP 1: REPOSITORY MANAGEMENT
=================================================================
Cloning https://github.com/pallets/flask...
✓ Cloned to /tmp/r2r-repo-loader/repos/flask
Repository: flask
Commit: abc123d - Merge pull request #xyz

=================================================================
STEP 2: FILE FILTERING
=================================================================
Found 87 code files (1.2MB)
  python: 75 files
  markdown: 8 files
  yaml: 4 files

=================================================================
STEP 3: COLLECTION SETUP
=================================================================
Collection: flask-framework (c56d8224...)

=================================================================
STEP 4: FILE UPLOAD
=================================================================
[  1.1%] src/flask/app.py → a1b2c3d4...
[  2.3%] src/flask/blueprints.py → e5f6g7h8...
...
✓ Uploaded 87/87 files in 45.2s

=================================================================
STEP 5: INGESTION MONITORING
=================================================================
✓ Ingestion complete: 87 successful, 0 failed

=================================================================
STEP 6: KNOWLEDGE GRAPH EXTRACTION
=================================================================
✓ Knowledge Graph: 234 entities, 512 relationships

Sample entities:
  Flask (CLASS)
  render_template (FUNCTION)
  request (VARIABLE)

=================================================================
SUMMARY
=================================================================
Repository: flask
Collection: flask-framework (c56d8224...)
Files found: 87
Files uploaded: 87
Files failed: 0
KG Entities: 234
KG Relationships: 512
Duration: 96s
```

### Example 2: Update Existing Repository

```bash
# First load
./repo_loader.py https://github.com/user/repo --collection my-repo

# Later: update with latest commits
./repo_loader.py https://github.com/user/repo --collection my-repo --update
```

**Behavior:**
- Pulls latest changes from Git
- Re-uploads только changed files
- Maintains existing collection

### Example 3: Branch-Specific Analysis

```bash
# Load feature branch для testing
./repo_loader.py https://github.com/mycompany/api \
  --branch feature/new-endpoints \
  --collection api-feature-test \
  --extract-kg
```

### Example 4: Repository with Images & Diagrams

```bash
# Load documentation repo with screenshots and diagrams
./repo_loader.py https://github.com/user/project-docs \
  --collection project-documentation \
  --verbose
```

**What gets indexed:**
- Code files (Python, JavaScript, etc.)
- Documentation (Markdown, README)
- **Images** (PNG, JPG, SVG) — R2R extracts visual content with vision models
- **PlantUML diagrams** (.puml) — architecture diagrams searchable as text

**Example search queries:**
- "screenshot showing login flow" → finds relevant PNG images
- "database schema diagram" → finds PlantUML or SVG diagrams
- "API endpoint documentation" → finds code + images explaining endpoints

**Multimodal RAG:**
R2R can answer: "Show me the architecture diagram for the authentication service" and return both the diagram image and code references.

---

## 🐛 Troubleshooting

### Error: Authentication Failed

```text
Error: HTTP 401: Unauthorized
```

**Solution:**
```bash
# Check credentials
export R2R_EMAIL="correct@email.com"
export R2R_PASSWORD="correct-password"

# Or pass as arguments
./repo_loader.py URL --email your@email.com --password your-pass
```

### Error: Git Clone Failed

```text
GitManagerError: Git command failed: fatal: repository not found
```

**Solutions:**
- Проверь URL репозитория
- Для private repos используй SSH URL с настроенным SSH key
- Проверь network connectivity

### Warning: Large File Skipped

```text
Skipping large file: model.bin (12.5MB)
```

**Solution:**
Increase limit в `config.py`:
```python
MAX_FILE_SIZE_MB = 20  # Increase to 20MB
```

### Error: Rate Limited (429)

```text
Rate limited, waiting 2s...
```

**Solutions:**
- Увеличь `UPLOAD_DELAY_MS` в config.py
- Уменьши concurrency (уже sequential)
- Wait и retry автоматически обрабатывается

---

## 📚 API Reference

### RepositoryLoader

```python
loader = RepositoryLoader(r2r_client, git_manager)

stats = loader.load_repository(
    repo_url='https://github.com/user/repo',
    collection_name='my-collection',  # optional
    branch='main',                     # optional
    update_if_exists=False,           # pull latest changes
    extract_kg=False,                 # KG extraction
    quality_mode='high',              # 'high' or 'fast'
    verbose=False                      # detailed logs
)
```

**Returns:**
```python
{
    'repo_url': str,
    'files_found': int,
    'files_uploaded': int,
    'files_failed': int,
    'collection_id': str,
    'kg_entities': int,
    'kg_relationships': int,
    'duration_seconds': int,
}
```

---

## 🔬 Testing

### Test on Small Repository

```bash
# Test с маленьким репо
./repo_loader.py https://github.com/pallets/click --verbose
```

### Validate Metadata

```python
from r2r_client import R2RClient

client = R2RClient()
client.authenticate('email', 'password')

# Get document
doc = client.get_document('document-id')
print(doc['metadata'])

# Verify fields
assert doc['metadata']['language'] == 'python'
assert 'imports' in doc['metadata']
assert doc['metadata']['commit_hash']
```

### Check Knowledge Graph

```python
# Get entities
entities = client.get_graph_entities('collection-id', limit=100)

# Sample entity structure
# {
#   'name': 'ClassName',
#   'category': 'CLASS',
#   'description': '...',
#   'metadata': {...}
# }
```

---

## 🚀 Production Deployment

### Recommendations

1. **Environment Variables**
   ```bash
   export R2R_API_URL="https://production.r2r.com"
   export R2R_EMAIL="service-account@company.com"
   export R2R_PASSWORD="strong-password"
   ```

2. **Logging**
   ```bash
   ./repo_loader.py URL 2>&1 | tee repo-load-$(date +%Y%m%d).log
   ```

3. **Batch Processing**
   ```bash
   # repos.txt: один URL per line
   while read repo_url; do
     ./repo_loader.py "$repo_url" --extract-kg
     sleep 60  # Cooldown между repos
   done < repos.txt
   ```

4. **Monitoring**
   - Track upload success rate
   - Monitor ingestion failures
   - Alert on >10% fail rate

---

## 📖 See Also

- **Examples** — `examples/` directory с test scripts
- **Testing Report** — `examples/reports/R2R_CODE_TESTING_FINAL_REPORT.md`
- **R2R Documentation** — https://r2r-docs.sciphi.ai/
- **r2r-js SDK** — https://github.com/SciPhi-AI/r2r-js

---

## 🤝 Contributing

При обнаружении bugs или feature requests:
1. Опиши проблему с примером команды
2. Приложи logs
3. Укажи версию Python и Git

---

**Version:** 1.0.0
**Author:** Claude Sonnet 4.5
**License:** MIT
**Last Updated:** 2025-12-18
