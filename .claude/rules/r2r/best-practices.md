# R2R Best Practices

## Configuration Management

### 1. Never Edit Directly on Server
```bash
# ❌ BAD - Editing on server
gcloud compute ssh r2r-vm-new --zone=us-central1-a
nano /home/laptop/r2r-deploy/user_configs/r2r.toml

# ✅ GOOD - Edit locally, upload
nano /Users/laptop/mcp/r2r-docker-full/docker/user_configs/r2r.toml
gcloud compute scp docker/user_configs/r2r.toml \
  r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml --zone=us-central1-a
```

### 2. Always Backup Before Changes
```bash
cp docker/user_configs/r2r.toml docker/user_configs/r2r.toml.backup.$(date +%Y%m%d)
```

### 3. Validate Before Upload
```bash
python -c "import toml; toml.load('docker/user_configs/r2r.toml')" || echo "Invalid TOML!"
```

### 4. Test Locally First
```bash
# Start local R2R with new config
docker compose -f compose.full.yaml --profile postgres --profile minio up -d
sleep 45
curl http://localhost:7272/v3/health
```

## Ingestion Best Practices

### Choose Right Ingestion Mode

```python
# Fast mode - Quick processing, lower quality
client.documents.create(
    file_path="document.pdf",
    ingestion_mode="fast"
)

# Hi-res mode - Better quality, slower (default)
client.documents.create(
    file_path="document.pdf",
    ingestion_mode="hi-res"  # Uses Unstructured with vision models
)
```

**When to use:**
- `fast` - Large batches, simple documents, testing
- `hi-res` - Complex PDFs, tables, images, production

### Batch Processing

```python
# ❌ BAD - Sequential processing
for file in files:
    client.documents.create(file_path=file)

# ✅ GOOD - Batch with error handling
import asyncio

async def ingest_batch(files):
    tasks = []
    for file in files:
        try:
            task = asyncio.create_task(
                client.documents.create_async(file_path=file)
            )
            tasks.append(task)
        except Exception as e:
            print(f"Failed {file}: {e}")

    return await asyncio.gather(*tasks, return_exceptions=True)

# Process in batches of 10
for i in range(0, len(files), 10):
    batch = files[i:i+10]
    results = asyncio.run(ingest_batch(batch))
```

### Optimize Chunk Settings

```toml
# For code documents
[ingestion]
chunk_size = 512      # Smaller chunks for code
chunk_overlap = 128   # Less overlap
chunking_strategy = "by_title"

# For research papers
[ingestion]
chunk_size = 2048     # Larger chunks for context
chunk_overlap = 512   # More overlap
chunking_strategy = "by_title"
```

## Search Best Practices

### Use Hybrid Search

```python
# ✅ GOOD - Hybrid search (semantic + full-text)
results = client.retrieval.search(
    query="machine learning algorithms",
    search_mode="advanced"  # Enables hybrid search
)

# Or custom weights
results = client.retrieval.search(
    query="machine learning algorithms",
    search_mode="custom",
    search_settings={
        "use_hybrid_search": True,
        "hybrid_settings": {
            "semantic_weight": 5.0,
            "full_text_weight": 1.0,
            "rrf_k": 50
        },
        "limit": 10
    }
)
```

### Filter by Metadata

```python
# Add metadata during ingestion
client.documents.create(
    file_path="paper.pdf",
    metadata={
        "category": "research",
        "year": 2024,
        "author": "John Doe"
    }
)

# Filter during search
results = client.retrieval.search(
    query="deep learning",
    search_settings={
        "filters": {
            "category": {"$eq": "research"},
            "year": {"$gte": 2023}
        }
    }
)
```

## RAG Best Practices

### Choose Right Model

```python
# For simple queries - use fast model
response = client.retrieval.rag(
    query="What is the capital of France?",
    rag_generation_config={
        "model": "openai/gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 200
    }
)

# For complex analysis - use quality model
response = client.retrieval.rag(
    query="Compare and contrast these three papers...",
    rag_generation_config={
        "model": "anthropic/claude-sonnet-4-20250514",  # Or claude-opus-4 for highest quality
        "temperature": 0.7,
        "max_tokens": 2000
    }
)
```

### Use Streaming for Better UX

```python
# ✅ GOOD - Stream responses
response = client.retrieval.rag(
    query="Explain quantum computing",
    rag_generation_config={
        "stream": True
    }
)

for chunk in response:
    print(chunk, end="", flush=True)
```

### Limit Search Results

```python
# ❌ BAD - Too many results = slow, expensive
response = client.retrieval.rag(
    query="...",
    search_settings={"limit": 100}  # Too many!
)

# ✅ GOOD - Reasonable limit
response = client.retrieval.rag(
    query="...",
    search_settings={"limit": 5}  # Usually sufficient
)
```

## Knowledge Graph Best Practices

### When to Use Knowledge Graphs

**Use for:**
- Complex documents with many entities (research papers, reports)
- Questions requiring relational understanding
- Multi-hop reasoning tasks

**Don't use for:**
- Simple Q&A
- Code documentation
- Short documents

### Configure Entity Types

```toml
[database.graph_creation_settings]
  # Define specific entity types for your domain
  entity_types = [
    "Person",
    "Organization",
    "Technology",
    "Concept",
    "Location"
  ]

  # Define relationship types
  relation_types = [
    "works_for",
    "developed_by",
    "related_to",
    "located_in",
    "part_of"
  ]

  # Limit triples to control costs
  max_knowledge_triples = 100
```

### Use Graph-Enhanced RAG

```python
# Standard RAG
response = client.retrieval.rag(
    query="Who works on AI safety?"
)

# Graph-enhanced RAG (better for entity questions)
response = client.retrieval.rag(
    query="Who works on AI safety?",
    graph_settings={"enabled": True}
)
```

## Security Best Practices

### 1. Always Require Authentication in Production

```toml
[auth]
require_authentication = true
require_email_verification = true
```

### 2. Change Default Credentials

```toml
[auth]
default_admin_email = "your-admin@company.com"
default_admin_password = "STRONG_RANDOM_PASSWORD"
```

### 3. Use Environment Variables for Secrets

```bash
# .env file (NOT committed!)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
POSTGRES_PASSWORD=...
MINIO_ROOT_PASSWORD=...
```

```toml
# r2r.toml - Reference env vars
[database]
password = "${POSTGRES_PASSWORD}"

[file]
aws_secret_access_key = "${MINIO_ROOT_PASSWORD}"
```

### 4. Set Rate Limits

```toml
[database.limits]
global_per_min = 60
route_per_min = 20
monthly_limit = 10000

# Per-route limits
[database.route_limits]
  "/v3/rag" = { route_per_min = 10 }
  "/v3/ingest_files" = { route_per_min = 5 }
```

## Performance Best Practices

### 1. Tune PostgreSQL

```toml
[database.postgres_configuration_settings]
  max_connections = 256
  shared_buffers = 16384       # Increase for more RAM
  effective_cache_size = 524288
  work_mem = 8192              # Increase for complex queries
  maintenance_work_mem = 131072
```

### 2. Use Batch Embeddings

```toml
[embedding]
batch_size = 128  # Higher = faster, more memory
concurrent_request_limit = 256
```

### 3. Enable Connection Pooling

```toml
[database]
max_connections = 256
```

### 4. Monitor Resource Usage

```bash
# Check container stats
docker stats

# Identify bottlenecks
docker stats r2r-deploy-r2r-1
docker stats r2r-deploy-postgres-1
docker stats r2r-deploy-unstructured-1
```

## Cost Optimization

### 1. Use Cheaper Embedding Models

```toml
# Expensive
[embedding]
base_model = "openai/text-embedding-3-large"
base_dimension = 3072

# Cost-effective
[embedding]
base_model = "openai/text-embedding-3-small"
base_dimension = 1536
```

### 2. Use Cheaper LLMs for Simple Tasks

```toml
[app]
quality_llm = "anthropic/claude-sonnet-4-20250514"  # Or claude-opus-4 for best quality
fast_llm = "openai/gpt-4o-mini"                     # Simple queries
```

### 3. Disable Expensive Features

```toml
[ingestion]
automatic_extraction = false        # Disable entity extraction
skip_document_summary = true        # Skip summaries to reduce LLM calls

[ingestion.chunk_enrichment_settings]
enable_chunk_enrichment = false     # Very expensive!
```

### 4. Cache Embeddings

R2R automatically caches embeddings in PostgreSQL - no action needed!

## Development Workflow

### Local Testing

```bash
# 1. Start local R2R
docker compose -f compose.full.yaml --profile postgres --profile minio up -d

# 2. Wait for startup
sleep 45

# 3. Health check
curl http://localhost:7272/v3/health

# 4. Test ingestion
curl -X POST http://localhost:7272/v3/ingest_files \
  -F "file=@test.pdf"

# 5. Test search
curl -X POST http://localhost:7272/v3/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 5}'
```

### Configuration Changes

```bash
# 1. Edit local config
nano docker/user_configs/r2r.toml

# 2. Validate
python -c "import toml; toml.load('docker/user_configs/r2r.toml')"

# 3. Test locally
docker compose restart r2r
sleep 15
docker logs r2r-deploy-r2r-1 --tail=50

# 4. Upload to server
gcloud compute scp docker/user_configs/r2r.toml \
  r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml --zone=us-central1-a

# 5. Deploy
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cd /home/laptop/r2r-deploy && docker compose restart r2r"

# 6. Verify
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker logs r2r-deploy-r2r-1 --tail=50"
```

## Monitoring

### Health Checks

```bash
# Automated health monitoring
#!/bin/bash
while true; do
  if curl -sf http://localhost:7272/v3/health > /dev/null; then
    echo "$(date): R2R healthy"
  else
    echo "$(date): R2R UNHEALTHY!" | tee -a r2r_alerts.log
  fi
  sleep 300  # Every 5 minutes
done
```

### Log Monitoring

```bash
# Watch for errors
docker logs r2r-deploy-r2r-1 -f | grep -i "error\|exception\|failed"
```

### Performance Monitoring

```bash
# Track query performance
docker logs r2r-deploy-r2r-1 | grep -i "query_time" | tail -100
```

## Backup & Recovery

### Backup PostgreSQL

```bash
# Backup database
docker exec r2r-deploy-postgres-1 pg_dump -U postgres r2r > backup_$(date +%Y%m%d).sql

# Backup to GCloud Storage
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker exec r2r-deploy-postgres-1 pg_dump -U postgres r2r > /tmp/r2r_backup.sql
"
gcloud compute scp r2r-vm-new:/tmp/r2r_backup.sql . --zone=us-central1-a
```

### Backup MinIO

```bash
# Backup MinIO data
docker exec r2r-deploy-minio-1 mc mirror local/r2r /backup/r2r
```

### Restore

```bash
# Restore PostgreSQL
cat backup_20241219.sql | docker exec -i r2r-deploy-postgres-1 psql -U postgres r2r
```

## Common Anti-Patterns

### ❌ Don't: Use `recursive` chunking with Unstructured

```toml
# BAD
[ingestion]
chunking_strategy = "recursive"  # Fails with Unstructured!
```

### ❌ Don't: Hardcode credentials

```toml
# BAD
[database]
password = "mypassword123"  # Never hardcode!
```

### ❌ Don't: Disable authentication

```toml
# BAD in production
[auth]
require_authentication = false  # Dangerous!
```

### ❌ Don't: Use default admin password

```toml
# BAD
[auth]
default_admin_password = "change_me_immediately"  # Change this!
```

### ❌ Don't: Set unreasonably high limits

```toml
# BAD - wastes tokens and money
[ingestion]
chunk_size = 10000  # Too large!
```

## Recommended Configurations

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
project_name = "r2r-code-docs"
quality_llm = "anthropic/claude-sonnet-4-20250514"
fast_llm = "openai/gpt-4o-mini"

[embedding]
provider = "litellm"
base_model = "openai/text-embedding-3-small"
base_dimension = 1536
batch_size = 128

[ingestion]
chunking_strategy = "by_title"
chunk_size = 512
chunk_overlap = 128
automatic_extraction = false
skip_document_summary = false

[auth]
require_authentication = true
require_email_verification = true
default_admin_email = "admin@company.com"
default_admin_password = "STRONG_PASSWORD"

[database.limits]
global_per_min = 60
route_per_min = 20
```

### Production (Research Papers)

```toml
[app]
project_name = "r2r-research"
quality_llm = "anthropic/claude-sonnet-4-20250514"

[embedding]
provider = "litellm"
base_model = "openai/text-embedding-3-small"
base_dimension = 1536

[ingestion]
chunking_strategy = "by_title"
chunk_size = 2048
chunk_overlap = 512
automatic_extraction = true  # Enable entity extraction

[database.graph_creation_settings]
  entity_types = ["Person", "Organization", "Technology", "Concept"]
  relation_types = ["works_for", "developed_by", "related_to"]
  max_knowledge_triples = 100
  automatic_deduplication = true

[auth]
require_authentication = true
```
