# R2R Docker Full - Project Memory

> **For humans:** See @README.md for project overview and architecture
> **For reference:** See @.claude/rules/gcloud-reference.md for commands and container names

## Critical Rules

### Configuration Changes (MANDATORY)

**NEVER edit files on server directly. ALWAYS follow this protocol:**

1. **Backup:** `cp docker/user_configs/r2r.toml docker/user_configs/r2r.toml.backup.$(date +%Y%m%d)`
2. **Research:** Check `data/R2R/py/all_possible_config.toml` for available options
3. **Edit LOCAL:** Modify `docker/user_configs/r2r.toml`
4. **Validate:** `python -c "import toml; toml.load('docker/user_configs/r2r.toml')"`
5. **Test locally:** Start local R2R and verify change works
6. **Upload:**

   ```bash
   gcloud compute scp docker/user_configs/r2r.toml \
     r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml \
     --zone=us-central1-a
   ```

7. **Restart:**

   ```bash
   gcloud compute ssh r2r-vm-new --zone=us-central1-a \
     --command="cd /home/laptop/r2r-deploy && docker compose restart r2r"
   ```

8. **Verify logs:**

   ```bash
   gcloud compute ssh r2r-vm-new --zone=us-central1-a \
     --command="docker logs r2r-deploy-r2r-1 --tail=50"
   ```

**If restart fails:** Read full logs (`--tail=200`) and look for error messages.

### Security (CRITICAL)

- **NEVER** commit secrets to git (@.claude/rules/security.md)
- **NEVER** edit `.env` files on server
- **NEVER** log credentials in code
- **NEVER** use untrusted inputs directly in GitHub Actions `run:` - use `env:` (@.claude/rules/workflows/github-actions.md)
- **ALWAYS** use environment variables for sensitive data
- Before git commit: `git diff --staged | grep -i "password\|secret\|key"`

### R2R-Specific Constraints

**⚠️ КРИТИЧНО - см. @.claude/rules/deployment.md для полных правил!**

- **NEVER** use `chunking_strategy = "recursive"` - Unstructured doesn't support it
  - **ALWAYS** use `chunking_strategy = "by_title"` instead
- **NEVER** change `base_dimension` without re-ingesting all documents
  - **PRODUCTION DATABASE = 768 dim** (НЕ МЕНЯТЬ!)
- **ALWAYS** match `base_dimension` to embedding model:
  - `huggingface/BAAI/bge-base-en-v1.5` → 768 ✅ (текущая production модель)
  - `text-embedding-3-small` → 1536
  - `text-embedding-3-large` → 3072
  - `all-MiniLM-L6-v2` → 384
  - `huggingface/BAAI/bge-small-en-v1.5` → 384 ❌ (не использовать!)
- **NEVER** use `${ENV_VAR}` in r2r.toml for MinIO password - must be hardcoded
- **ALWAYS** run `setup-token` service if Hatchet auth fails

## Quick Diagnostics

### Is R2R healthy?

```bash
# Local
curl -s http://localhost:7272/v3/health | jq .status

# Production
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="curl -s http://localhost:7272/v3/health | jq .status"
```

**Expected:** `"healthy"`

### Are containers running?

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

**Expected:** All containers show "Up" status:

- `r2r-deploy-r2r-1`
- `r2r-deploy-postgres-1`
- `r2r-deploy-minio-1`
- `r2r-deploy-unstructured-1`

### Any errors in last 100 lines?

```bash
docker logs r2r-deploy-r2r-1 --tail=100 | grep -iE "error|exception|failed"
```

**Expected:** No output (or only known warnings)

### Are GitHub Actions workflows passing?

```bash
# Check workflow status
gh run list --limit 5

# View latest workflow run
gh run view

# Or via badge in README.md
```

**Expected:** All workflows passing (green checkmarks)

---

## Common R2R Errors & Fixes

### ❌ "unrecognized chunking strategy 'recursive'"

**Cause:** Unstructured provider doesn't support `recursive`

**Fix:**

```toml
[ingestion]
chunking_strategy = "by_title"  # NOT "recursive"
```

### ❌ "S3 bucket name is required"

**Cause:** Using `provider = "s3"` without complete configuration

**Fix:**

```toml
[file]
provider = "s3"
bucket_name = "r2r"
endpoint_url = "http://minio:9000"
aws_access_key_id = "minio"
aws_secret_access_key = "${MINIO_ROOT_PASSWORD}"
```

**Get credentials:**

```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cat /home/laptop/r2r-deploy/env/minio.env"
```

### ❌ "Embedding dimension 1536 doesn't match configured 512"

**Cause:** Changed `base_model` without updating `base_dimension`

**Fix:** Update dimension AND re-ingest all documents

```toml
[embedding]
base_model = "openai/text-embedding-3-small"
base_dimension = 1536  # MUST match model
```

### ❌ Container won't start

**Diagnosis:**

```bash
docker ps -a | grep r2r-deploy-r2r-1
docker logs r2r-deploy-r2r-1 --tail=100
```

**Common causes:**

- Invalid TOML → Validate: `python -c "import toml; toml.load('r2r.toml')"`
- Port 7272 in use → Check: `lsof -i :7272` → Kill process
- PostgreSQL not ready → Wait 30 seconds after `docker compose up`

### ❌ Search returns no results

**Diagnosis:**

```bash
# Check documents exist
curl http://localhost:7272/v3/documents | jq

# Check embeddings were created
docker logs r2r-deploy-r2r-1 | grep -i "embedding"
```

**Fix:** Verify `[embedding]` config and `OPENAI_API_KEY` is set

### ❌ Upload fails "File too large"

**Fix:**

```toml
[app.max_upload_size_by_type]
pdf = 50000000  # 50MB (default is 30MB)
```

## File Locations

| What | Local Path | Server Path |
| ------ | ----------- | ------------- |
| **Config to edit** | `docker/user_configs/r2r.toml` | `/home/laptop/r2r-deploy/user_configs/r2r.toml` |
| Reference configs | `data/R2R/py/all_possible_config.toml` | N/A |
| Local env vars | `.env` | `/home/laptop/r2r-deploy/env/r2r.env` |
| MinIO credentials | N/A | `/home/laptop/r2r-deploy/env/minio.env` |

## Environment Variables

**Required for R2R:**

```bash
OPENAI_API_KEY=sk-...           # For embeddings and LLM
ANTHROPIC_API_KEY=sk-ant-...    # Optional, for Claude models
POSTGRES_PASSWORD=...           # Database password
```

**MinIO (server only):**

```bash
MINIO_ROOT_USER=...
MINIO_ROOT_PASSWORD=...
```

## Local Development

```bash
# Start R2R locally
docker compose -f compose.full.yaml --profile postgres --profile minio up -d
sleep 45
curl http://localhost:7272/v3/health

# Stop
docker compose -f compose.full.yaml down

# Reset (DELETES ALL DATA)
docker compose -f compose.full.yaml down -v
```

## Project-Specific Details

### Tech Stack (R2R v3.x specifics)

- **Vector DB:** PostgreSQL with pgvector extension
- **Storage:** MinIO (S3-compatible) at `http://minio:9000`
- **Parsing:** Unstructured with vision models for tables/images
- **LLM Proxy:** LiteLLM (supports OpenAI, Anthropic, HuggingFace, etc.)
- **Orchestration:** Hatchet for distributed task execution

### Ports

- R2R API: `7272` (<http://localhost:7272>)
- MinIO: `9000` (storage), `9001` (console)
- PostgreSQL: `5432`

### Production Server

- **VM:** `r2r-vm-new`
- **Zone:** `us-central1-a`
- **Access:** `gcloud compute ssh r2r-vm-new --zone=us-central1-a`

## Advanced Debugging

### Access PostgreSQL

```bash
docker exec -it r2r-deploy-postgres-1 psql -U postgres -d r2r

# Inside psql:
\dt                           # List tables
SELECT COUNT(*) FROM documents;
SELECT COUNT(*) FROM chunks;
```

### Watch logs in real-time

```bash
docker logs -f r2r-deploy-r2r-1
```

### Check resource usage

```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Detailed Documentation

Comprehensive guides and references:

### Workflows & CI/CD

- @.claude/rules/workflows/github-actions.md - GitHub Actions security & best practices
- @.claude/rules/workflows/testing.md - Testing procedures
- @.claude/rules/workflows/troubleshooting.md - Systematic debugging framework
- @.claude/rules/workflows/git-workflow.md - Commit conventions
- @docs/workflows.md - Complete workflows documentation (for reference)

### R2R Framework

- @.claude/rules/r2r/configuration.md - Complete config reference
- @.claude/rules/r2r/api-reference.md - API endpoints with curl/Python examples
- @.claude/rules/r2r/troubleshooting.md - Extended troubleshooting guide
- @.claude/rules/r2r/best-practices.md - Production best practices

### Operations

- @.claude/rules/security.md - Security constraints
- @.claude/rules/deployment.md - Production deployment workflow
- @.claude/rules/gcloud-reference.md - GCloud commands and container names

## Personal Overrides

@CLAUDE.local.md (gitignored, for personal preferences)
