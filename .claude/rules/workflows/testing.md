# Testing Guidelines

## Testing Philosophy

- **Test locally before deploying** - Always verify changes work on your machine first
- **Test one thing at a time** - Don't combine multiple config changes
- **Document test results** - Keep notes on what works and what doesn't
- **Automate when possible** - Create scripts for repeated testing workflows

## Local R2R Testing Workflow

### Quick Health Check

```bash
# 1. Start R2R locally
docker compose -f compose.full.yaml --profile postgres --profile minio up -d

# 2. Wait for startup (30-60 seconds)
echo "Waiting for R2R to start..."
sleep 45

# 3. Test health endpoint
curl -s http://localhost:7272/v3/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "services": { ... }
# }
```

### Configuration Change Testing

When changing `r2r.toml`:

**Step 1: Backup current config**
```bash
cp docker/user_configs/r2r.toml docker/user_configs/r2r.toml.backup
```

**Step 2: Make changes**
- Edit `docker/user_configs/r2r.toml`
- Change only ONE setting at a time

**Step 3: Test locally**
```bash
# Restart with new config
docker compose -f compose.full.yaml restart r2r

# Wait for restart
sleep 15

# Check logs for errors
docker logs r2r-deploy-r2r-1 --tail=100 | grep -i error

# Test health
curl http://localhost:7272/v3/health
```

**Step 4: Verify the change worked**
- Test the specific feature you changed
- Check relevant logs
- Verify no new errors appeared

**Step 5: Document results**
```bash
# If test passed:
echo "✓ Config change successful: [describe what you changed]" >> test_log.txt

# If test failed:
echo "✗ Config change failed: [describe what failed]" >> test_log.txt
git checkout docker/user_configs/r2r.toml  # Restore backup
```

## Testing Common Changes

### Testing Embedding Model Changes

```bash
# After changing embedding model in r2r.toml:

# 1. Restart R2R
docker compose restart r2r && sleep 15

# 2. Upload a test document
curl -X POST http://localhost:7272/v3/ingest_files \
  -F "file=@test_document.txt"

# 3. Check embedding was created (look for dimension in logs)
docker logs r2r-deploy-r2r-1 --tail=50 | grep -i "embedding\|dimension"

# 4. Test search
curl -X POST http://localhost:7272/v3/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "limit": 5}'
```

### Testing Ingestion Configuration

```bash
# After changing chunking strategy or chunk size:

# 1. Clear previous data (optional, for clean test)
docker compose down -v
docker compose up -d

# 2. Ingest test document
curl -X POST http://localhost:7272/v3/ingest_files \
  -F "file=@sample.pdf"

# 3. Check chunk sizes in logs
docker logs r2r-deploy-r2r-1 --tail=100 | grep -i "chunk"

# 4. Verify chunks via API
curl http://localhost:7272/v3/documents/<doc_id>/chunks
```

### Testing LLM Configuration

```bash
# After changing completion model:

# 1. Restart R2R
docker compose restart r2r && sleep 20

# 2. Test RAG query
curl -X POST http://localhost:7272/v3/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "search_limit": 5
  }'

# 3. Check for LLM errors in logs
docker logs r2r-deploy-r2r-1 --tail=50 | grep -i "llm\|completion\|error"
```

## Production Testing

### Pre-Production Verification

Before deploying to production:

- [ ] Local tests pass for the specific change
- [ ] No errors in local R2R logs
- [ ] Health endpoint returns healthy
- [ ] Backup of production config created
- [ ] Rollback plan documented

### Post-Production Testing

After deploying to production:

```bash
# 1. Verify service is running
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker ps | grep r2r-deploy-r2r-1
"

# 2. Check health endpoint
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  curl -s http://localhost:7272/v3/health
"

# 3. Monitor logs for 5 minutes
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker logs -f r2r-deploy-r2r-1
" &

# Let it run for 5 minutes, watch for errors
sleep 300
kill %1  # Stop log following
```

## Test Data

### Creating Test Documents

Keep test files for repeatable testing:

```bash
# Create test directory
mkdir -p test_data/

# Simple text file
echo "This is a test document about machine learning." > test_data/simple.txt

# Python code file
cat > test_data/code_sample.py << 'EOF'
def factorial(n):
    """Calculate factorial of n"""
    if n <= 1:
        return 1
    return n * factorial(n-1)
EOF

# Markdown file
cat > test_data/markdown.md << 'EOF'
# Test Document
This is a test document with **markdown** formatting.
EOF
```

### Test Queries

Keep a list of test queries for search/RAG testing:

```bash
# test_queries.txt
echo "What is machine learning?" > test_queries.txt
echo "How does factorial work?" >> test_queries.txt
echo "Explain the code" >> test_queries.txt
```

## Troubleshooting Failed Tests

### If local R2R won't start:

```bash
# 1. Check what's using the ports
lsof -i :7272  # R2R API port
lsof -i :5432  # PostgreSQL port
lsof -i :9000  # MinIO port

# 2. Check Docker status
docker ps -a | grep r2r

# 3. View all container logs
docker compose -f compose.full.yaml logs --tail=100

# 4. Complete cleanup and restart
docker compose -f compose.full.yaml down -v
docker compose -f compose.full.yaml up -d
```

### If config changes don't take effect:

```bash
# 1. Verify config file was actually changed
cat docker/user_configs/r2r.toml | grep [setting_you_changed]

# 2. Hard restart (not just restart)
docker compose down
docker compose up -d

# 3. Check if config was loaded
docker logs r2r-deploy-r2r-1 | grep -i "config\|loaded"
```

### If tests pass locally but fail on production:

Common causes:
1. **Environment differences** - Check env vars on server
2. **File paths** - Verify paths exist on server
3. **Permissions** - Check file/directory permissions
4. **Resources** - Server might have different CPU/RAM
5. **Network** - Firewall or network config differences

## Test Automation Scripts

### Create reusable test script:

```bash
# test_r2r.sh
#!/bin/bash

echo "=== R2R Local Test Suite ==="

# Start services
echo "1. Starting R2R..."
docker compose -f compose.full.yaml up -d
sleep 45

# Health check
echo "2. Health check..."
HEALTH=$(curl -s http://localhost:7272/v3/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test ingestion
echo "3. Test document ingestion..."
INGEST=$(curl -s -X POST http://localhost:7272/v3/ingest_files \
    -F "file=@test_data/simple.txt")
if echo "$INGEST" | grep -q "document_id"; then
    echo "✓ Ingestion test passed"
else
    echo "✗ Ingestion test failed"
    exit 1
fi

# Test search
echo "4. Test search..."
SEARCH=$(curl -s -X POST http://localhost:7272/v3/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 5}')
if echo "$SEARCH" | grep -q "results"; then
    echo "✓ Search test passed"
else
    echo "✗ Search test failed"
    exit 1
fi

echo ""
echo "=== All tests passed! ==="
```

Make it executable:
```bash
chmod +x test_r2r.sh
./test_r2r.sh
```

## Best Practices

1. **Test incrementally** - One change at a time
2. **Keep test data** - Reuse same test files for consistency
3. **Document failures** - Note what didn't work and why
4. **Automate repetitive tests** - Create scripts for common test scenarios
5. **Clean state** - Start with fresh state when needed (`docker compose down -v`)
6. **Monitor resources** - Check CPU/memory during tests
7. **Compare with baseline** - Keep known-good config for comparison
