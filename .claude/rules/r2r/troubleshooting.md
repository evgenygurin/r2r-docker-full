# R2R Troubleshooting Guide

## Quick Diagnostics

### 1. Check R2R Health

```bash
# Local
curl http://localhost:7272/v3/health | jq

# Server
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="curl -s http://localhost:7272/v3/health | jq"
```

### 2. Check Container Status

```bash
# Local
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Server
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

### 3. View R2R Logs

```bash
# Local
docker logs r2r-deploy-r2r-1 --tail=100

# Server
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker logs r2r-deploy-r2r-1 --tail=100"
```

## Common Issues

### Issue: "unrecognized chunking strategy 'recursive'"

**Symptom:**
```text
ValueError: unrecognized chunking strategy 'recursive'
```

**Cause:** Unstructured provider doesn't support `recursive` strategy

**Solution:**
```toml
[ingestion]
chunking_strategy = "by_title"  # Use this instead
```

**Verification:**
```bash
# Restart and check logs
docker compose restart r2r && sleep 15
docker logs r2r-deploy-r2r-1 --tail=50 | grep -i chunking
```

---

### Issue: "S3 bucket name is required"

**Symptom:**
```text
ValueError: S3 bucket name is required when using S3 provider
```

**Cause:** Using `provider = "s3"` without bucket configuration

**Solution:**
```toml
[file]
provider = "s3"
bucket_name = "r2r"
endpoint_url = "http://minio:9000"
aws_access_key_id = "minio"
aws_secret_access_key = "YOUR_MINIO_PASSWORD"
```

**Get MinIO Credentials:**
```bash
# Server
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cat /home/laptop/r2r-deploy/env/minio.env"
```

---

### Issue: Upload Fails with "File too large"

**Symptom:**
```text
HTTP 413: Payload Too Large
```

**Diagnosis:**
```bash
# Check file size
ls -lh /path/to/file.pdf

# Check configured limit for PDF
grep -A5 "\\[app.max_upload_size_by_type\\]" docker/user_configs/r2r.toml
```

**Solution:**
```toml
[app]
default_max_upload_size = 2000000  # 2MB default

[app.max_upload_size_by_type]
  pdf = 50000000  # Increase to 50MB
```

---

### Issue: Embedding Dimension Mismatch

**Symptom:**
```text
RuntimeError: Embedding dimension 1536 doesn't match configured 512
```

**Cause:** Changed embedding model without updating `base_dimension`

**Solution:**
```toml
[embedding]
base_model = "openai/text-embedding-3-small"
base_dimension = 1536  # Must match model's actual dimension!
```

**Common Dimensions:**
- `text-embedding-3-small` → 1536
- `text-embedding-3-large` → 3072
- `all-MiniLM-L6-v2` → 384
- `bge-small-en-v1.5` → 384

**Important:** Changing embedding model requires re-ingesting all documents!

---

### Issue: R2R Container Crashes on Startup

**Symptom:**
```bash
docker ps | grep r2r
# No r2r container running
```

**Diagnosis:**
```bash
# Check exit code and logs
docker ps -a | grep r2r-deploy-r2r
docker logs r2r-deploy-r2r-1 --tail=200
```

**Common Causes:**

1. **Invalid TOML Syntax**
   ```bash
   # Validate locally
   python -c "import toml; toml.load('docker/user_configs/r2r.toml')"
   ```

2. **Missing Environment Variables**
   ```bash
   # Check required vars
   docker logs r2r-deploy-r2r-1 | grep -i "environment\\|api_key"
   ```

3. **Port Already in Use**
   ```bash
   lsof -i :7272
   # Kill conflicting process
   kill -9 <PID>
   ```

4. **PostgreSQL Not Ready**
   ```bash
   # Check postgres first
   docker logs r2r-deploy-postgres-1 --tail=50
   docker exec r2r-deploy-postgres-1 pg_isready -U postgres
   ```

**Solution:**
```bash
# Start dependencies first
docker compose up postgres minio -d
sleep 30

# Then start R2R
docker compose up r2r -d
```

---

### Issue: Search Returns No Results

**Symptom:** Search queries return empty results despite successful ingestion

**Diagnosis:**
```bash
# 1. Verify documents ingested
curl http://localhost:7272/v3/documents | jq

# 2. Check embeddings created
docker logs r2r-deploy-r2r-1 | grep -i "embedding\\|vector"

# 3. Test with simple query
curl -X POST http://localhost:7272/v3/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 10}' | jq
```

**Common Causes:**

1. **Embedding Service Not Configured**
   ```toml
   [embedding]
   provider = "litellm"
   base_model = "openai/text-embedding-3-small"
   ```
   ```bash
   # Check API key
   echo $OPENAI_API_KEY
   ```

2. **Documents Not Indexed**
   ```bash
   # Check PostgreSQL logs
   docker logs r2r-deploy-postgres-1 --tail=100
   ```

3. **Wrong Search Mode**
   ```json
   {
     "query": "test",
     "search_mode": "advanced",  // Try hybrid search
     "search_settings": {"limit": 10}
   }
   ```

---

### Issue: Slow Ingestion

**Symptom:** Document ingestion takes very long or times out

**Diagnosis:**
```bash
# Monitor ingestion in real-time
docker logs r2r-deploy-r2r-1 -f

# Check which step is slow
# - "Parsing..." - Unstructured service
# - "Embedding..." - Embedding API
# - "Storing..." - Database writes

# Check resource usage
docker stats
```

**Solutions:**

1. **Use Fast Mode**
   ```python
   client.documents.create(
       file_path="large.pdf",
       ingestion_mode="fast"  # Skip advanced parsing
   )
   ```

2. **Disable Expensive Features**
   ```toml
   [ingestion]
   automatic_extraction = false  # Disable entity extraction
   skip_document_summary = true   # Skip summarization

   [ingestion.chunk_enrichment_settings]
   enable_chunk_enrichment = false  # Disable chunk enrichment
   ```

3. **Reduce Chunk Size**
   ```toml
   [ingestion]
   chunk_size = 512  # Smaller chunks = faster processing
   chunk_overlap = 128
   ```

4. **Check Unstructured Service**
   ```bash
   docker logs r2r-deploy-unstructured-1 --tail=100
   docker stats r2r-deploy-unstructured-1
   ```

---

### Issue: MinIO Connection Errors

**Symptom:**
```text
Failed to connect to S3: Connection refused
```

**Diagnosis:**
```bash
# 1. Check MinIO running
docker ps | grep minio

# 2. Test MinIO health
curl http://localhost:9000/minio/health/live

# 3. Check credentials
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cat /home/laptop/r2r-deploy/env/minio.env"
```

**Solutions:**

1. **Verify MinIO Credentials**
   ```toml
   [file]
   provider = "s3"
   bucket_name = "r2r"
   endpoint_url = "http://minio:9000"
   aws_access_key_id = "MINIO_ROOT_USER from minio.env"
   aws_secret_access_key = "MINIO_ROOT_PASSWORD from minio.env"
   ```

2. **Create Bucket if Missing**
   ```bash
   docker exec r2r-deploy-minio-1 mc mb local/r2r
   ```

3. **Check MinIO Logs**
   ```bash
   docker logs r2r-deploy-minio-1 --tail=100
   ```

---

### Issue: Authentication Errors

**Symptom:**
```text
401 Unauthorized
```

**Diagnosis:**
```bash
# Check auth configuration
grep -A10 "\\[auth\\]" docker/user_configs/r2r.toml

# Test login
curl -X POST http://localhost:7272/v3/users/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "change_me_immediately"}'
```

**Solutions:**

1. **Check Credentials**
   ```toml
   [auth]
   require_authentication = true
   default_admin_email = "admin@example.com"
   default_admin_password = "YOUR_SECURE_PASSWORD"
   ```

2. **Verify Email (if required)**
   ```python
   client.users.verify_email("admin@example.com", "verification_code")
   ```

3. **Refresh Token**
   ```python
   client.users.refresh_access_token("YOUR_REFRESH_TOKEN")
   ```

---

### Issue: LiteLLM Provider Errors

**Symptom:**
```text
Error: Failed to initialize LiteLLM provider
```

**Diagnosis:**
```bash
# Check LiteLLM configuration
grep -A10 "\\[embedding\\]" docker/user_configs/r2r.toml
grep -A10 "\\[completion\\]" docker/user_configs/r2r.toml

# Check API keys
docker logs r2r-deploy-r2r-1 | grep -i "api_key\\|litellm\\|openai"
```

**Solutions:**

1. **Set API Keys in Environment**
   ```bash
   # For OpenAI
   export OPENAI_API_KEY="sk-..."

   # For Anthropic
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

2. **Verify Model Names**
   ```toml
   [embedding]
   provider = "litellm"
   base_model = "openai/text-embedding-3-small"  # Must have provider prefix!

   [completion]
   provider = "r2r"

   [app]
   quality_llm = "anthropic/claude-3-opus-20240229"
   fast_llm = "openai/gpt-4o-mini"
   ```

3. **Test LiteLLM Directly**
   ```bash
   docker exec r2r-deploy-r2r-1 python -c "
   import litellm
   response = litellm.embedding(model='openai/text-embedding-3-small', input=['test'])
   print(response)
   "
   ```

---

### Issue: PostgreSQL Connection Refused

**Symptom:**
```text
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Diagnosis:**
```bash
# 1. Check PostgreSQL running
docker ps | grep postgres

# 2. Check PostgreSQL health
docker exec r2r-deploy-postgres-1 pg_isready -U postgres

# 3. Check logs
docker logs r2r-deploy-postgres-1 --tail=100
```

**Solutions:**

1. **Verify Database Configuration**
   ```toml
   [database]
   provider = "postgres"
   user = "postgres"
   password = "YOUR_PASSWORD"
   host = "postgres"  # Container name!
   port = 5432
   db_name = "r2r"
   ```

2. **Wait for PostgreSQL Startup**
   ```bash
   # PostgreSQL takes 10-15 seconds to start
   docker compose up postgres -d
   sleep 20
   docker logs r2r-deploy-postgres-1
   ```

3. **Check Network Connectivity**
   ```bash
   docker exec r2r-deploy-r2r-1 ping postgres
   docker exec r2r-deploy-r2r-1 nc -zv postgres 5432
   ```

---

### Issue: Hatchet Engine Errors

**Symptom:**
```text
Error: Failed to connect to Hatchet
```

**Diagnosis:**
```bash
# Check Hatchet containers
docker ps | grep hatchet

# Check Hatchet logs
docker logs r2r-deploy-hatchet-engine-1 --tail=100
docker logs r2r-deploy-hatchet-api-1 --tail=100
```

**Solutions:**

1. **Start All Hatchet Services**
   ```bash
   docker compose up hatchet-engine hatchet-api hatchet-setup-config -d
   sleep 30
   ```

2. **Check RabbitMQ**
   ```bash
   docker ps | grep rabbitmq
   docker logs r2r-deploy-rabbitmq-1 --tail=50
   ```

3. **Verify Hatchet Configuration**
   ```toml
   [orchestration]
   provider = "hatchet"
   ```

---

## Advanced Debugging

### Enable Debug Logging

```toml
# Add to r2r.toml
[logging]
level = "DEBUG"
```

```bash
# Restart and watch logs
docker compose restart r2r
docker logs r2r-deploy-r2r-1 -f
```

### Interactive Container Debugging

```bash
# Enter R2R container
docker exec -it r2r-deploy-r2r-1 /bin/bash

# Inside container:
python --version
python -c "import r2r; print(r2r.__version__)"
cat /app/config/r2r.toml
ping postgres
ping minio
```

### Network Debugging

```bash
# Check container network
docker network inspect r2r-deploy_default

# Test connectivity
docker exec r2r-deploy-r2r-1 ping postgres
docker exec r2r-deploy-r2r-1 ping minio

# Check port bindings
docker port r2r-deploy-r2r-1
```

### Database Debugging

```bash
# Connect to PostgreSQL
docker exec -it r2r-deploy-postgres-1 psql -U postgres -d r2r

# Inside psql:
\dt                           # List tables
SELECT COUNT(*) FROM documents;
SELECT * FROM chunks LIMIT 5;
\q
```

### Check Document Processing Pipeline

```bash
# Monitor full pipeline
docker logs r2r-deploy-r2r-1 -f &
docker logs r2r-deploy-unstructured-1 -f &
docker logs r2r-deploy-postgres-1 -f &

# Ingest test document
curl -X POST http://localhost:7272/v3/ingest_files \
  -F "file=@test.pdf"

# Watch all logs simultaneously
```

---

## Emergency Procedures

### Complete Restart

```bash
# Local
docker compose down
docker compose up -d
sleep 45
curl http://localhost:7272/v3/health

# Server
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cd /home/laptop/r2r-deploy &&
  docker compose down &&
  docker compose up -d &&
  sleep 45 &&
  docker logs r2r-deploy-r2r-1 --tail=50
"
```

### Reset Database (DANGER!)

```bash
# CAUTION: Deletes ALL data!
docker compose down -v
docker compose up -d
```

### Rollback Configuration

```bash
# Local
cp docker/user_configs/r2r.toml.backup docker/user_configs/r2r.toml

# Upload and restart
gcloud compute scp docker/user_configs/r2r.toml \
  r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml --zone=us-central1-a

gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cd /home/laptop/r2r-deploy && docker compose restart r2r"
```

### Force Rebuild Containers

```bash
# Local
docker compose down
docker compose build --no-cache
docker compose up -d

# Server
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cd /home/laptop/r2r-deploy &&
  docker compose down &&
  docker compose pull &&
  docker compose up -d
"
```

---

## Escalation Checklist

Before asking for help, collect:

- [ ] R2R version: `docker exec r2r-deploy-r2r-1 python -c "import r2r; print(r2r.__version__)"`
- [ ] Full logs: `docker logs r2r-deploy-r2r-1 > r2r_logs.txt`
- [ ] Configuration (REDACTED): `cat docker/user_configs/r2r.toml | grep -v password`
- [ ] Health status: `curl http://localhost:7272/v3/health | jq`
- [ ] Container status: `docker ps -a`
- [ ] Steps to reproduce
- [ ] What you've already tried

---

## Monitoring Best Practices

### 1. Regular Health Checks

```bash
# Add to cron
*/5 * * * * curl -sf http://localhost:7272/v3/health || echo "R2R unhealthy!"
```

### 2. Log Monitoring

```bash
# Watch for errors
docker logs r2r-deploy-r2r-1 -f | grep -i "error\\|exception"
```

### 3. Resource Monitoring

```bash
docker stats --no-stream
```

### 4. Database Monitoring

```bash
docker exec r2r-deploy-postgres-1 psql -U postgres -d r2r -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### 5. API Endpoint Monitoring

```bash
# Monitor endpoint performance
curl -w "\nTime: %{time_total}s\n" -X POST http://localhost:7272/v3/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### 6. Storage Monitoring

```bash
# Check MinIO bucket size
docker exec r2r-deploy-minio-1 mc du local/r2r

# Check PostgreSQL database size
docker exec r2r-deploy-postgres-1 psql -U postgres -c "
  SELECT pg_size_pretty(pg_database_size('r2r'));
"
```

### 7. Automated Alerting

```bash
#!/bin/bash
# Save as monitor_r2r.sh

SLACK_WEBHOOK="YOUR_WEBHOOK_URL"

while true; do
  # Health check
  if ! curl -sf http://localhost:7272/v3/health > /dev/null; then
    curl -X POST $SLACK_WEBHOOK -d '{"text":"R2R is DOWN!"}'
  fi

  # Check disk space
  DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
  if [ $DISK_USAGE -gt 80 ]; then
    curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"Disk usage at ${DISK_USAGE}%\"}"
  fi

  sleep 300  # Every 5 minutes
done
```

---

## Performance Troubleshooting

### Issue: Slow Search Queries

**Diagnosis:**
```bash
# Enable query logging
docker logs r2r-deploy-postgres-1 -f | grep -i "duration"

# Check for missing indexes
docker exec r2r-deploy-postgres-1 psql -U postgres -d r2r -c "
  SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
"
```

**Solutions:**

1. **Use Hybrid Search**
   ```python
   results = client.retrieval.search(
       query="...",
       search_mode="advanced"  # Faster than semantic-only
   )
   ```

2. **Reduce Limit**
   ```python
   results = client.retrieval.search(
       query="...",
       search_settings={"limit": 5}  # Instead of 20
   )
   ```

3. **Add PostgreSQL Indexes** (if missing)
   ```sql
   CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding);
   ```

### Issue: High Memory Usage

**Diagnosis:**
```bash
docker stats --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

**Solutions:**

1. **Reduce Batch Size**
   ```toml
   [embedding]
   batch_size = 1  # Lower memory usage
   ```

2. **Limit PostgreSQL Memory**
   ```toml
   [database.postgres_configuration_settings]
   shared_buffers = 8192  # Reduce from default
   work_mem = 2048
   ```

3. **Restart Containers Periodically**
   ```bash
   # Add to cron - restart daily at 3am
   0 3 * * * cd /home/laptop/r2r-deploy && docker compose restart r2r
   ```

---

## Common Error Messages Reference

| Error | Likely Cause | Fix |
|-------|--------------|-----|
| `ValueError: unrecognized chunking strategy` | Using `recursive` with Unstructured | Change to `by_title` |
| `S3 bucket name is required` | Missing S3 config | Add `bucket_name` in `[file]` |
| `Embedding dimension mismatch` | Changed model without updating dimension | Update `base_dimension` |
| `Connection refused` (PostgreSQL) | PostgreSQL not ready | Wait 20 seconds after startup |
| `401 Unauthorized` | Missing/invalid token | Re-login to get new token |
| `413 Payload Too Large` | File exceeds upload limit | Increase `max_upload_size_by_type` |
| `Failed to initialize LiteLLM` | Missing API key | Set `OPENAI_API_KEY` env var |
| `No module named 'r2r'` | Container not built correctly | Rebuild: `docker compose build` |
| `Port already in use` | Another service on 7272 | Kill conflicting process |
| `No such file or directory: r2r.toml` | Missing config file | Check volume mount in compose |

---

## Debug Workflow Checklist

When troubleshooting ANY issue:

1. [ ] Check R2R health endpoint
2. [ ] Verify all containers running: `docker ps`
3. [ ] Read last 100 lines of R2R logs
4. [ ] Check configuration syntax: `python -c "import toml; toml.load('r2r.toml')"`
5. [ ] Test PostgreSQL: `docker exec r2r-deploy-postgres-1 pg_isready`
6. [ ] Test MinIO: `curl http://localhost:9000/minio/health/live`
7. [ ] Check environment variables: `docker logs r2r-deploy-r2r-1 | grep -i env`
8. [ ] Review recent configuration changes
9. [ ] Try minimal reproduction (simple test document)
10. [ ] Check resource usage: `docker stats`
