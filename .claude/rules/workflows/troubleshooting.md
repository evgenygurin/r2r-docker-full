# Systematic Troubleshooting Guide

## Troubleshooting Framework

When something goes wrong, follow this systematic approach:

### 1. Define the Problem

**Ask:**
- What exactly is failing? (specific error, behavior)
- When did it start failing? (after what change?)
- Does it fail consistently or intermittently?
- Does it fail locally, on server, or both?

**Document:**
```text
Problem: [Specific description]
Started: [When/after what change]
Frequency: [Always/Sometimes/Rarely]
Location: [Local/Server/Both]
```

### 2. Check the Obvious

**Before deep investigation:**
- [ ] Is the service actually running? (`docker ps`)
- [ ] Are there recent errors in logs? (`docker logs --tail=100`)
- [ ] Was configuration recently changed?
- [ ] Is there enough disk space? (`df -h`)
- [ ] Is there enough memory? (`free -h` or `docker stats`)

### 3. Gather Information

**Collect diagnostic data:**

```bash
# Service status
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Recent logs (all services)
docker compose logs --tail=100 > all_logs.txt

# Specific service logs
docker logs r2r-deploy-r2r-1 --tail=200 > r2r_logs.txt

# System resources
docker stats --no-stream > docker_stats.txt

# Configuration
cat docker/user_configs/r2r.toml > current_config.txt
```

### 4. Isolate the Problem

**Narrow down the cause:**

**Is it a specific component?**
```bash
# Test each service individually
docker logs r2r-deploy-r2r-1 --tail=50        # R2R API
docker logs r2r-deploy-postgres-1 --tail=50   # Database
docker logs r2r-deploy-minio-1 --tail=50      # Storage
docker logs r2r-deploy-unstructured-1 --tail=50  # Parser
```

**Is it configuration-related?**
```bash
# Compare with known-good config
diff docker/user_configs/r2r.toml.backup docker/user_configs/r2r.toml
```

**Is it environment-related?**
```bash
# Check environment variables
docker exec r2r-deploy-r2r-1 env | grep -E "API|KEY|PASSWORD|URL"
```

### 5. Form Hypothesis

Based on gathered info, hypothesize what's wrong:

**Example hypotheses:**
- "PostgreSQL connection is failing because password changed"
- "MinIO is out of disk space"
- "Embedding model is incompatible with new config"
- "API rate limit exceeded"

### 6. Test Hypothesis

**Design targeted tests:**

```bash
# Hypothesis: Database connection failing
docker exec r2r-deploy-postgres-1 pg_isready -U postgres
# If fails -> hypothesis likely correct

# Hypothesis: Disk space issue
docker exec r2r-deploy-minio-1 df -h /data
# If <10% free -> hypothesis likely correct

# Hypothesis: Config validation error
docker logs r2r-deploy-r2r-1 | grep -i "config\|validation\|error"
# If validation errors -> hypothesis likely correct
```

### 7. Apply Fix

**Based on confirmed hypothesis:**

```bash
# Fix applied: [Description]
# Expected result: [What should happen]
# Verification: [How to verify]
```

### 8. Verify Fix

**Confirm problem is resolved:**

```bash
# Re-run original failing operation
# Check logs for errors
# Monitor for 15-30 minutes
```

## Common R2R Issues

### Issue: R2R Container Won't Start

**Symptoms:**
- Container exits immediately
- `docker ps` doesn't show r2r-deploy-r2r-1

**Diagnostic steps:**
```bash
# 1. Check exit status and error
docker ps -a | grep r2r-deploy-r2r-1
docker logs r2r-deploy-r2r-1 --tail=100

# 2. Common causes:
# - Config validation error (check for "ConfigError" in logs)
# - Missing environment variables (check env vars)
# - Port already in use (check: lsof -i :7272)
# - Dependency not ready (postgres, minio not up yet)
```

**Solutions:**
```bash
# If config error: Validate config syntax
python -c "import toml; toml.load('docker/user_configs/r2r.toml')"

# If port conflict: Find and stop conflicting service
lsof -i :7272
kill -9 <PID>

# If dependency not ready: Start in correct order
docker compose up postgres minio -d
sleep 30
docker compose up r2r -d
```

### Issue: Search Returns No Results

**Symptoms:**
- Search queries return empty results
- Documents were ingested successfully

**Diagnostic steps:**
```bash
# 1. Verify documents are ingested
curl http://localhost:7272/v3/documents

# 2. Check if embeddings were created
docker logs r2r-deploy-r2r-1 | grep -i "embedding"

# 3. Test with different query
curl -X POST http://localhost:7272/v3/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 10}'

# 4. Check vector search is enabled
cat docker/user_configs/r2r.toml | grep -A5 "\[embedding\]"
```

**Solutions:**
```bash
# If no embeddings: Check embedding config
# Verify base_model is correct
# Check embedding provider API key

# If embeddings exist but no results: Check search settings
# Try different search_limit
# Verify index is built (postgres)
```

### Issue: High Memory Usage

**Symptoms:**
- Docker containers using excessive RAM
- System becoming slow
- OOM (Out of Memory) errors

**Diagnostic steps:**
```bash
# 1. Check which container uses most memory
docker stats --no-stream | sort -k4 -h

# 2. Check R2R memory usage over time
docker stats r2r-deploy-r2r-1

# 3. Check for memory leaks in logs
docker logs r2r-deploy-r2r-1 | grep -i "memory\|oom"
```

**Solutions:**
```bash
# Limit container memory in docker-compose.yaml:
services:
  r2r:
    mem_limit: 4g
    memswap_limit: 4g

# Restart services to free memory
docker compose restart

# If persistent: Check for memory leaks, update R2R version
```

### Issue: Slow Ingestion

**Symptoms:**
- Document ingestion takes very long
- Timeouts during upload

**Diagnostic steps:**
```bash
# 1. Check which step is slow
docker logs r2r-deploy-r2r-1 -f
# Watch logs during ingestion, note slow steps

# 2. Check unstructured service
docker logs r2r-deploy-unstructured-1 --tail=100

# 3. Check system resources during ingestion
docker stats

# 4. Test with small file first
curl -X POST http://localhost:7272/v3/ingest_files \
  -F "file=@small_test.txt"
```

**Solutions:**
```bash
# If parsing is slow: Adjust chunk size
# In r2r.toml:
chunk_size = 256  # Smaller chunks = faster processing

# If embedding is slow: Check embedding service
# Verify embedding API is responding
# Consider batch_size adjustment

# If database writes slow: Check postgres performance
docker exec r2r-deploy-postgres-1 pg_stat_statements
```

### Issue: MinIO Connection Errors

**Symptoms:**
- "Failed to connect to S3"
- "Bucket not found"
- File upload errors

**Diagnostic steps:**
```bash
# 1. Check MinIO is running
docker ps | grep minio

# 2. Check MinIO health
docker exec r2r-deploy-minio-1 mc admin info local

# 3. Verify credentials
cat /home/laptop/r2r-deploy/env/minio.env

# 4. Test connection
curl http://localhost:9000/minio/health/live
```

**Solutions:**
```bash
# If bucket doesn't exist: Create it
docker exec r2r-deploy-minio-1 mc mb local/r2r

# If credentials wrong: Update r2r.toml with correct credentials
# Check [file] section matches minio.env

# If MinIO won't start: Check data directory permissions
docker exec r2r-deploy-minio-1 ls -la /data
```

## Advanced Debugging

### Enable Debug Logging

```toml
# In r2r.toml, add:
[logging]
level = "DEBUG"
```

Restart R2R and check logs for detailed output.

### Interactive Debugging

```bash
# Enter R2R container
docker exec -it r2r-deploy-r2r-1 /bin/bash

# Inside container:
# - Check Python environment: python --version
# - Test imports: python -c "import r2r"
# - Check config: cat /app/config/r2r.toml
# - Test connections: ping postgres, ping minio
```

### Network Debugging

```bash
# Check container network
docker network inspect r2r-deploy_default

# Test connectivity between containers
docker exec r2r-deploy-r2r-1 ping postgres
docker exec r2r-deploy-r2r-1 ping minio

# Check port bindings
docker port r2r-deploy-r2r-1
```

## Escalation Checklist

Before asking for help, gather:

- [ ] Exact error message (copy from logs)
- [ ] R2R version: `docker exec r2r-deploy-r2r-1 pip show r2r`
- [ ] Full logs: `docker logs r2r-deploy-r2r-1 > full_logs.txt`
- [ ] Configuration (with secrets redacted)
- [ ] Steps to reproduce
- [ ] What you've already tried
- [ ] System info: OS, Docker version, available resources

## Prevention

**Avoid future issues:**

1. **Version control configs** - Git track r2r.toml changes
2. **Test before deploy** - Always test locally first
3. **Keep backups** - Auto-backup configs before changes
4. **Monitor logs** - Regular log review catches issues early
5. **Document changes** - Note what you changed and why
6. **Update regularly** - Keep R2R and dependencies current
7. **Resource monitoring** - Set up alerts for disk/memory
