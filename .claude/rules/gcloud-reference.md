# GCloud & Docker Reference

> **Note:** This is reference material. For behavioral rules, see `CLAUDE.md`.

## GCloud Commands

### SSH Access
```bash
# Connect to VM
gcloud compute ssh r2r-vm-new --zone=us-central1-a

# Run remote command
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="COMMAND"
```

### File Transfer
```bash
# Copy file to VM
gcloud compute scp LOCAL_PATH r2r-vm-new:REMOTE_PATH --zone=us-central1-a

# Copy from VM
gcloud compute scp r2r-vm-new:REMOTE_PATH LOCAL_PATH --zone=us-central1-a
```

### Container Management
```bash
# View logs
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker logs CONTAINER_NAME --tail=100"

# Follow logs (real-time)
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker logs -f CONTAINER_NAME"

# List running containers
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker ps --format 'table {{.Names}}\t{{.Status}}'"

# Restart specific container
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cd /home/laptop/r2r-deploy && docker compose restart CONTAINER_NAME"
```

## Container Names

| Container | Purpose |
|-----------|---------|
| `r2r-deploy-r2r-1` | Main R2R API server |
| `r2r-deploy-unstructured-1` | Document parsing service |
| `r2r-deploy-postgres-1` | PostgreSQL database |
| `r2r-deploy-minio-1` | S3-compatible object storage |
| `r2r-deploy-hatchet-engine-1` | Task orchestration engine |

## Docker Compose Profiles

```bash
# Start with PostgreSQL and MinIO
docker compose -f compose.full.yaml --profile postgres --profile minio up -d

# Stop all services
docker compose -f compose.full.yaml down

# View service status
docker compose -f compose.full.yaml ps
```

## Troubleshooting Commands

### Check R2R API Health
```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="curl -s http://localhost:7272/v3/health | jq"
```

### Check MinIO Status
```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker exec r2r-deploy-minio-1 mc admin info local"
```

### Check PostgreSQL Connection
```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker exec r2r-deploy-postgres-1 pg_isready -U postgres"
```

### View All Logs (Last Hour)
```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker compose -f /home/laptop/r2r-deploy/compose.yaml logs --since 1h"
```
