# R2R Docker Full - Claude Code Instructions

## CRITICAL: Configuration Changes Workflow

**ALWAYS follow this workflow when troubleshooting R2R errors:**

1. **FIRST** - Look for solutions in `/Users/laptop/mcp/r2r-docker-full/data/R2R/`
   - `py/all_possible_config.toml` - all possible configuration options
   - `py/r2r/r2r.toml` - default R2R config
   - `deployment/k8s/manifests/examples/` - example configs
   - `llms.txt` - documentation

2. **THEN** - Edit local config: `/Users/laptop/mcp/r2r-docker-full/docker/user_configs/r2r.toml`

3. **THEN** - Upload to server:
   ```bash
   gcloud compute scp /Users/laptop/mcp/r2r-docker-full/docker/user_configs/r2r.toml \
     r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml --zone=us-central1-a
   ```

4. **THEN** - Restart R2R:
   ```bash
   gcloud compute ssh r2r-vm-new --zone=us-central1-a \
     --command="cd /home/laptop/r2r-deploy && docker compose restart r2r"
   ```

5. **THEN** - Check logs:
   ```bash
   gcloud compute ssh r2r-vm-new --zone=us-central1-a \
     --command="docker logs r2r-deploy-r2r-1 --tail=50"
   ```

## Key Configuration Files

| Location | Purpose |
|----------|---------|
| `docker/user_configs/r2r.toml` | Local R2R config (edit this) |
| `data/R2R/py/all_possible_config.toml` | Reference for all options |
| Server: `/home/laptop/r2r-deploy/user_configs/r2r.toml` | Server R2R config |
| Server: `/home/laptop/r2r-deploy/env/r2r.env` | Environment variables |
| Server: `/home/laptop/r2r-deploy/env/minio.env` | MinIO credentials |

## Common Issues & Solutions

### "unrecognized chunking strategy 'recursive'"
**Cause:** Unstructured doesn't support `recursive` strategy
**Solution:** Change `chunking_strategy = "by_title"` in `[ingestion]` section

### "S3 bucket name is required"
**Cause:** Using S3 provider without bucket config
**Solution:** Add to `[file]` section:
```toml
[file]
provider = "s3"
bucket_name = "r2r"
endpoint_url = "http://minio:9000"
aws_access_key_id = "minio"
aws_secret_access_key = "YOUR_MINIO_PASSWORD"
```

### MinIO Credentials
Located in `/home/laptop/r2r-deploy/env/minio.env`:
- `MINIO_ROOT_USER` = access key
- `MINIO_ROOT_PASSWORD` = secret key

## GCloud Commands

```bash
# SSH to VM
gcloud compute ssh r2r-vm-new --zone=us-central1-a

# Copy file to VM
gcloud compute scp LOCAL_PATH r2r-vm-new:REMOTE_PATH --zone=us-central1-a

# Run command on VM
gcloud compute ssh r2r-vm-new --zone=us-central1-a --command="COMMAND"

# View container logs
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker logs CONTAINER_NAME --tail=100"

# List containers
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

## Container Names

- `r2r-deploy-r2r-1` - Main R2R API
- `r2r-deploy-unstructured-1` - Document parsing
- `r2r-deploy-postgres-1` - Database
- `r2r-deploy-minio-1` - S3-compatible storage
- `r2r-deploy-hatchet-engine-1` - Task orchestration

docker compose -f compose.full.yaml --profile postgres up --profile minio -d
docker compose -f compose.full.yaml --profile postgres up --profile minio -d
docker compose -f compose.full.yaml --profile postgres up --profile minio -d
docker compose -f compose.full.yaml --profile postgres up --profile minio -d
