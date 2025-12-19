---
paths:
  - "docker/user_configs/r2r.toml"
  - "**/r2r.toml"
---

# R2R Configuration Reference

## Critical Configuration Rules

- **NEVER** edit r2r.toml directly on server - always edit locally first
- **ALWAYS** validate TOML syntax before upload: `python -c "import toml; toml.load('file.toml')"`
- **ALWAYS** restart R2R after configuration changes
- **ALWAYS** check logs after restart to verify config loaded correctly

## Configuration Sections

### [app] - Application Settings

```toml
[app]
project_name = "r2r-project"
default_max_documents_per_user = 100
default_max_chunks_per_user = 10000
default_max_collections_per_user = 5
default_max_upload_size = 2000000  # 2MB default

# LLM shortcuts for app-level models
quality_llm = "anthropic/claude-3-opus-20240229"  # Best quality
fast_llm = "openai/gpt-4o-mini"                   # Fast tasks
vlm = "openai/gpt-4-vision-preview"               # Vision
audio_lm = "openai/whisper-1"                     # Transcription
planning_llm = "openai/gpt-4o"                    # Planning tasks
reasoning_llm = "anthropic/claude-3-opus-20240229" # Reasoning

# File-specific upload limits
[app.max_upload_size_by_type]
  pdf = 30000000   # 30MB for PDFs
  docx = 10000000  # 10MB for Word docs
  txt = 5000000    # 5MB for text
  csv = 10000000   # 10MB for CSV
  py = 5000000     # 5MB for Python files
  js = 5000000     # 5MB for JavaScript
```

**Common Issues:**
- Upload fails → Check `max_upload_size_by_type` for file extension
- User quota exceeded → Adjust `default_max_documents_per_user`

### [embedding] - Embedding Models

```toml
[embedding]
provider = "litellm"
base_model = "openai/text-embedding-3-small"
base_dimension = 512
batch_size = 1
concurrent_request_limit = 256
max_retries = 3
initial_backoff = 1.0
max_backoff = 64.0

[embedding.quantization_settings]
  quantization_type = "FP32"  # or "int8" for compression
```

**Supported Providers:**
- `litellm` - Universal LLM proxy (OpenAI, Anthropic, HuggingFace, etc.)
- `openai` - Direct OpenAI embeddings
- `ollama` - Local embeddings

**Common Models:**
| Model | Dimension | Use Case |
|-------|-----------|----------|
| `openai/text-embedding-3-small` | 512-1536 (default 1536) | General, cost-effective |
| `openai/text-embedding-3-large` | 256-3072 (default 3072) | High quality, expensive |
| `vertex_ai/text-embedding-004` | 768 | Google Cloud |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Local, fast |
| `BAAI/bge-small-en-v1.5` | 384 | Code optimized |

**Critical Rules:**
- `base_dimension` MUST match model's actual dimension
- Changing embedding model requires re-ingesting all documents
- `batch_size` affects memory usage (default: 1 for stability)
- Higher `batch_size` = faster ingestion but more memory

### [completion_embedding] - Completion Embeddings

```toml
[completion_embedding]
provider = "litellm"
base_model = "openai/text-embedding-3-small"
base_dimension = 512
batch_size = 1
concurrent_request_limit = 256
```

Usually mirrors `[embedding]` settings. Override only if completion requires different embedding model.

### [completion] - LLM Generation

```toml
[completion]
provider = "litellm"
concurrent_request_limit = 256
max_retries = 3
initial_backoff = 1.0
max_backoff = 64.0
request_timeout = 120.0

[completion.generation_config]
  model = "openai/gpt-4o-mini"
  temperature = 0.1
  top_p = 1.0
  max_tokens_to_sample = 4096
  stream = false
  add_generation_kwargs = {}  # Additional provider-specific params
```

**Popular Models:**
- `openai/gpt-4o` - Best quality (expensive)
- `openai/gpt-4o-mini` - Fast and cheap
- `anthropic/claude-3-opus-20240229` - Best reasoning
- `anthropic/claude-3-haiku-20240307` - Fastest Claude
- `vertex_ai/gemini-2.5-pro` - Google Cloud quality
- `vertex_ai/gemini-2.5-flash` - Google Cloud fast

### [ingestion] - Document Processing

```toml
[ingestion]
provider = "unstructured_local"  # or "r2r"
excluded_parsers = []
strategy = "auto"
chunking_strategy = "by_title"  # Override! Default is "recursive" which fails with Unstructured
chunk_size = 1024
chunk_overlap = 512
new_after_n_chars = 512
max_characters = 1500
combine_under_n_chars = 128
overlap = 64
automatic_extraction = true
skip_document_summary = false
document_summary_model = "openai/gpt-4o-mini"
document_summary_system_prompt = "system"
document_summary_task_prompt = "summary"
document_summary_max_length = 100000
chunks_for_document_summary = 128

# Vision/OCR settings
vlm_batch_size = 20
vlm_max_tokens_to_sample = 1024
max_concurrent_vlm_tasks = 20
vlm_ocr_one_page_per_chunk = true

# Audio settings
audio_transcription_model = "openai/whisper-1"

# Parser overrides
parser_overrides = {}

[ingestion.extra_parsers]
  pdf = ["zerox", "ocr"]  # Additional parsers for PDFs
```

**Providers:**
- `unstructured_local` - Uses Unstructured container for advanced parsing
- `r2r` - Built-in R2R parsers (simpler, faster)

**Chunking Strategies:**
- `by_title` - **RECOMMENDED** with Unstructured (uses document structure)
- `recursive` - ❌ NOT SUPPORTED by Unstructured provider
- `character` - Simple character-based splitting
- `token` - Token-aware splitting

**Common Issues:**
- "unrecognized chunking strategy" → Use `by_title` instead of `recursive`
- Large PDF fails → Increase `app.max_upload_size_by_type.pdf`
- Slow ingestion → Disable `automatic_extraction` or set `skip_document_summary = true`

**Chunk Enrichment:**
```toml
[ingestion.chunk_enrichment_settings]
  enable_chunk_enrichment = false  # Expensive LLM calls!
  strategies = ["neighborhood"]
  forward_chunks = 2
  backward_chunks = 2
  semantic_neighbors = 3
  semantic_similarity_threshold = 0.7
  generation_config = { model = "openai/gpt-4o-mini", max_tokens_to_sample = 4096, temperature = 0.1 }
```

### [database] - PostgreSQL Settings

```toml
[database]
provider = "postgres"
user = "postgres"
password = "YOUR_PASSWORD"
host = "postgres"
port = 5432
db_name = "r2r"
project_name = "r2r-project"
default_collection_name = "Default"
default_collection_description = "Your default collection."
batch_size = 512
disable_create_extension = false

# Collection summary settings
collection_summary_system_prompt = "system"
collection_summary_prompt = "collection_summary"
```

**Performance Tuning:**
```toml
[database.postgres_configuration_settings]
  max_connections = 256
  shared_buffers = 16384      # RAM for caching (increase for more memory)
  effective_cache_size = 524288
  work_mem = 4096             # Memory per query operation
  maintenance_work_mem = 65536
  wal_buffers = 512
  max_wal_size = 1024
  min_wal_size = 80
  checkpoint_completion_target = 0.9
  default_statistics_target = 100
  effective_io_concurrency = 1
  random_page_cost = 4.0      # Lower for SSD (1.1)
  max_parallel_workers_per_gather = 2
  max_parallel_workers = 8
  max_parallel_maintenance_workers = 2
  max_worker_processes = 8
  huge_pages = "try"
  statement_cache_size = 100
```

**Rate Limiting:**
```toml
[database.limits]
  global_per_min = 60
  route_per_min = 20
  monthly_limit = 10000

# Route-specific limits
[database.route_limits]
  "/v3/rag" = { route_per_min = 10 }
  "/v3/ingest_files" = { route_per_min = 5 }

# User-specific limits
[database.user_limits]
  # "user_uuid_here" = { global_per_min = 20, route_per_min = 5, monthly_limit = 2000 }
```

### [database.graph_creation_settings] - Knowledge Graphs

```toml
[database.graph_creation_settings]
  graph_entity_description_prompt = "graph_entity_description"
  graph_extraction_prompt = "graph_extraction"

  # Entity types to extract
  entity_types = [
    "Person",
    "Organization",
    "Location",
    "Technology",
    "Concept"
  ]

  # Relationship types
  relation_types = [
    "works_for",
    "located_in",
    "developed_by",
    "related_to",
    "part_of"
  ]

  fragment_merge_count = 4
  max_knowledge_relationships = 100
  max_description_input_length = 65536
  automatic_deduplication = true

  generation_config = {
    model = "openai/gpt-4o-mini",
    max_tokens_to_sample = 4096,
    temperature = 0.1
  }
```

**For Code Documentation:**
```toml
[database.graph_creation_settings]
  entity_types = [
    "CLASS",
    "FUNCTION",
    "METHOD",
    "MODULE",
    "IMPORT",
    "API_ENDPOINT",
    "INTERFACE",
    "TYPE",
    "CONSTANT",
    "DATABASE_TABLE"
  ]

  relation_types = [
    "CALLS",
    "INHERITS",
    "IMPORTS",
    "USES",
    "DEPENDS_ON",
    "IMPLEMENTS",
    "RETURNS",
    "CONTAINS",
    "QUERIES"
  ]
```

### [database.graph_enrichment_settings] - Graph Communities

```toml
[database.graph_enrichment_settings]
  graph_communities_prompt = "graph_communities"
  max_summary_input_length = 65536

  generation_config = {
    model = "openai/gpt-4o",
    max_tokens_to_sample = 8192,
    temperature = 0.1
  }

  leiden_params = {}  # Leiden algorithm parameters
```

### [database.graph_search_settings] - Graph-Enhanced Search

```toml
[database.graph_search_settings]
  generation_config = {
    model = "openai/gpt-4o-mini",
    max_tokens_to_sample = 4096,
    temperature = 0.1
  }
```

### [file] - Storage Provider

```toml
[file]
provider = "s3"  # or "postgres"
bucket_name = "r2r"
endpoint_url = "http://minio:9000"  # For MinIO
region_name = "us-east-1"  # For AWS S3
aws_access_key_id = "minio"
aws_secret_access_key = "YOUR_MINIO_PASSWORD"
```

**Providers:**
- `postgres` - Store files in database (simple, limited scale)
- `s3` - S3-compatible storage (MinIO, AWS S3, production)

**MinIO Setup:**
- Container: `r2r-deploy-minio-1`
- Credentials: `/home/laptop/r2r-deploy/env/minio.env`
- Console: http://localhost:9001
- Default credentials in env file: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`

**AWS S3 Setup:**
```toml
[file]
provider = "s3"
bucket_name = "my-r2r-bucket"
region_name = "us-east-1"
aws_access_key_id = "${AWS_ACCESS_KEY_ID}"  # From env
aws_secret_access_key = "${AWS_SECRET_ACCESS_KEY}"  # From env
```

### [auth] - Authentication

```toml
[auth]
provider = "r2r"
secret_key = ""  # Optional, auto-generated if empty
require_authentication = false  # Set true for production!
require_email_verification = false
access_token_lifetime_in_minutes = 60000
refresh_token_lifetime_in_days = 7
default_admin_email = "admin@example.com"
default_admin_password = "change_me_immediately"  # CHANGE THIS!
```

**Security Rules:**
- **ALWAYS** change default admin password in production
- **ALWAYS** set `require_authentication = true` in production
- Consider email verification for public deployments
- Use environment variables for `default_admin_password`

### [agent] - Agentic RAG

```toml
[agent]
rag_agent_static_prompt = "rag_agent"
rag_agent_dynamic_prompt = "dynamic_rag_agent"
tools = ["search_file_knowledge", "content"]

[agent.generation_config]
  model = "openai/gpt-4o"
  max_tokens_to_sample = 8192
  temperature = 0.1
  top_p = 1.0
```

**Available Tools:**
- `search_file_knowledge` - Search ingested documents
- `get_file_content` - Retrieve full document
- `web_search` - Search the web (requires API key)
- `web_scrape` - Scrape websites
- `reasoning` - Chain-of-thought reasoning
- `python_executor` - Execute Python code

### [orchestration] - Task Orchestration

```toml
[orchestration]
provider = "simple"  # or "hatchet"
max_runs = 2048
kg_creation_concurrency_limit = 32
ingestion_concurrency_limit = 16
kg_concurrency_limit = 4
```

**Providers:**
- `simple` - In-process orchestration (local/testing)
- `hatchet` - Distributed task engine (production)

### [crypto] - Password Hashing

```toml
[crypto]
provider = "bcrypt"
```

### [prompt] - Prompt Management

```toml
[prompt]
provider = "r2r"
```

### [email] - Email Notifications

```toml
[email]
provider = "console"  # or "smtp", "sendgrid", "mailersend"
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "user@example.com"
smtp_password = "YOUR_PASSWORD"
from_email = "noreply@example.com"
use_tls = true
sendgrid_api_key = ""
mailersend_api_key = ""
verify_email_template_id = ""
reset_password_template_id = ""
password_changed_template_id = ""
frontend_url = "https://app.example.com"
sender_name = "R2R System"
```

**Providers:**
- `console` - Print to console (testing)
- `console_mock` - Mock provider (no emails sent)
- `smtp` - Standard SMTP server
- `sendgrid` - SendGrid service
- `mailersend` - MailerSend service

## Configuration Workflow

1. **Edit Local Config**
   ```bash
   nano /Users/laptop/mcp/r2r-docker-full/docker/user_configs/r2r.toml
   ```

2. **Validate Syntax**
   ```bash
   python -c "import toml; toml.load('docker/user_configs/r2r.toml')"
   ```

3. **Upload to Server**
   ```bash
   gcloud compute scp docker/user_configs/r2r.toml \
     r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml --zone=us-central1-a
   ```

4. **Restart R2R**
   ```bash
   gcloud compute ssh r2r-vm-new --zone=us-central1-a \
     --command="cd /home/laptop/r2r-deploy && docker compose restart r2r"
   ```

5. **Verify**
   ```bash
   gcloud compute ssh r2r-vm-new --zone=us-central1-a \
     --command="docker logs r2r-deploy-r2r-1 --tail=50"
   ```

## Environment Variable Substitution

Use `${VAR_NAME}` syntax to reference environment variables:

```toml
[database]
password = "${POSTGRES_PASSWORD}"

[file]
aws_secret_access_key = "${MINIO_ROOT_PASSWORD}"

[auth]
default_admin_password = "${R2R_ADMIN_PASSWORD}"
```

Environment variables set in:
- Local: `.env` file in project root
- Server: `/home/laptop/r2r-deploy/env/r2r.env` and `minio.env`

## Best Practices

- **Start minimal** - Add features incrementally
- **Test locally** - Always test config changes locally first
- **Keep backups** - `cp r2r.toml r2r.toml.backup.$(date +%Y%m%d)`
- **Document changes** - Comment why you changed each setting
- **Monitor logs** - Check logs after every config change
- **Use env vars** - Never hardcode secrets in TOML
- **Match dimensions** - Embedding dimension must match model
- **Set rate limits** - Prevent abuse in production
- **Enable auth** - Always require authentication in production
- **Choose provider carefully** - `unstructured_local` for quality, `r2r` for speed

## Common Configuration Patterns

### Minimal (Testing)
```toml
[app]
project_name = "r2r-test"

[embedding]
provider = "litellm"
base_model = "openai/text-embedding-3-small"
base_dimension = 1536

[ingestion]
chunking_strategy = "by_title"
chunk_size = 512
automatic_extraction = false

[auth]
require_authentication = false
```

### Production (Code Documentation)
```toml
[app]
quality_llm = "anthropic/claude-3-opus-20240229"
fast_llm = "openai/gpt-4o-mini"

[embedding]
base_model = "openai/text-embedding-3-small"
base_dimension = 1536
batch_size = 128

[ingestion]
provider = "unstructured_local"
chunking_strategy = "by_title"
chunk_size = 512
automatic_extraction = false

[auth]
require_authentication = true
require_email_verification = true

[database.limits]
global_per_min = 60
route_per_min = 20

[file]
provider = "s3"
```

### Production (Research Papers)
```toml
[embedding]
base_model = "openai/text-embedding-3-large"
base_dimension = 3072

[ingestion]
chunking_strategy = "by_title"
chunk_size = 2048
chunk_overlap = 512
automatic_extraction = true

[database.graph_creation_settings]
  entity_types = ["Person", "Organization", "Technology", "Concept"]
  relation_types = ["works_for", "developed_by", "related_to"]
  max_knowledge_relationships = 100

[auth]
require_authentication = true
```
