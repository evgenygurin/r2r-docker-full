# Deployment Procedures

## Pre-Deployment Checklist

Before deploying any changes to production:

- [ ] Test configuration changes locally first
- [ ] Backup current production config
- [ ] Review changes with `git diff`
- [ ] Verify no secrets in staged files
- [ ] Have rollback plan ready

## Local Testing

**Test R2R config changes locally:**

```bash
# 1. Start local R2R stack
docker compose -f compose.full.yaml --profile postgres --profile minio up -d

# 2. Wait for services to be ready (30-60 seconds)
sleep 30

# 3. Check health
curl http://localhost:7272/v3/health

# 4. Test your changes
# (run your specific tests here)

# 5. Check logs for errors
docker logs r2r-deploy-r2r-1 --tail=100

# 6. Stop when done
docker compose -f compose.full.yaml down
```

**If local test fails:**

- Fix the issue locally
- Re-test until working
- Only then deploy to server

## Production Deployment

**Standard deployment workflow** (same as CLAUDE.md 5-step process):

### Step 1: Backup Current Config

```bash
# Backup server config before changes
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cp /home/laptop/r2r-deploy/user_configs/r2r.toml \
     /home/laptop/r2r-deploy/user_configs/r2r.toml.backup-\$(date +%Y%m%d-%H%M%S)
"
```

### Step 2: Upload New Config

```bash
gcloud compute scp docker/user_configs/r2r.toml \
  r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml \
  --zone=us-central1-a
```

### Step 3: Verify Upload

```bash
# Check file was uploaded correctly
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  ls -lh /home/laptop/r2r-deploy/user_configs/r2r.toml
"
```

### Step 4: Restart Service

```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cd /home/laptop/r2r-deploy && docker compose restart r2r
"
```

### Step 5: Verify Deployment

```bash
# Check R2R started successfully
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker logs r2r-deploy-r2r-1 --tail=50
"

# Check health endpoint
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  curl -s http://localhost:7272/v3/health
"
```

## Rollback Procedure

If deployment fails:

**Option A: Restore from backup (recommended)**

```bash
# List available backups
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  ls -lht /home/laptop/r2r-deploy/user_configs/r2r.toml.backup-*
"

# Restore specific backup (replace TIMESTAMP)
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cp /home/laptop/r2r-deploy/user_configs/r2r.toml.backup-TIMESTAMP \
     /home/laptop/r2r-deploy/user_configs/r2r.toml
"

# Restart R2R
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cd /home/laptop/r2r-deploy && docker compose restart r2r
"
```

**Option B: Re-upload known good config**

```bash
# Upload previous working version from git
git checkout <previous-commit> docker/user_configs/r2r.toml
gcloud compute scp docker/user_configs/r2r.toml \
  r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml \
  --zone=us-central1-a

# Restart
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cd /home/laptop/r2r-deploy && docker compose restart r2r
"
```

## Emergency Procedures

### Complete Service Restart

If R2R is stuck or unresponsive:

```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  cd /home/laptop/r2r-deploy
  docker compose down
  docker compose up -d
"

# Wait for startup (2-3 minutes)
sleep 120

# Verify all services
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker ps --format 'table {{.Names}}\t{{.Status}}'
"
```

### Database Issues

If PostgreSQL has problems:

```bash
# Check PostgreSQL status
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker exec r2r-deploy-postgres-1 pg_isready -U postgres
"

# View PostgreSQL logs
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker logs r2r-deploy-postgres-1 --tail=100
"
```

### MinIO Issues

If MinIO storage has problems:

```bash
# Check MinIO health
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker exec r2r-deploy-minio-1 mc admin info local
"

# View MinIO logs
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker logs r2r-deploy-minio-1 --tail=100
"
```

## Post-Deployment Monitoring

After successful deployment, monitor for 15-30 minutes:

```bash
# Follow R2R logs in real-time
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="
  docker logs -f r2r-deploy-r2r-1
"
```

Watch for:

- ERROR level messages
- Python exceptions/tracebacks
- Configuration validation errors
- Database connection issues
- Memory/performance warnings

## Deployment Best Practices

1. **Deploy during low-traffic periods** (if applicable)
2. **Test locally first** - always verify changes work locally
3. **Keep backups** - automatically create timestamped backups
4. **Monitor after deploy** - watch logs for 15-30 minutes
5. **Document changes** - commit with clear message explaining what changed
6. **One change at a time** - don't combine multiple config changes in one deploy
7. **Have rollback ready** - know how to quickly revert if needed
