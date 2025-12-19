# R2R Docker Full - Project Memory

## Tech Stack
- R2R v3.x (RAG framework)
- Docker Compose
- GCloud (VM: r2r-vm-new, zone: us-central1-a)
- MinIO (S3-compatible storage)
- PostgreSQL, Unstructured, Hatchet

## Critical Constraints

- **NEVER** edit configuration files directly on the server
- **NEVER** skip the 5-step troubleshooting workflow
- **NEVER** restart R2R without checking logs afterward
- **NEVER** commit secrets or credentials to git
- **ALWAYS** edit local config first, then upload to server

## R2R Configuration Workflow

When troubleshooting R2R errors or making config changes, follow this exact sequence:

**Step 1: Research** - Check reference files first:
- `data/R2R/py/all_possible_config.toml` - all available options
- `data/R2R/py/r2r/r2r.toml` - default config
- `data/R2R/llms.txt` - documentation
- `data/R2R/deployment/k8s/manifests/examples/` - examples

**Step 2: Edit Local** - Modify `docker/user_configs/r2r.toml`

**Step 3: Upload** - Use gcloud scp to deploy:
```bash
gcloud compute scp docker/user_configs/r2r.toml \
  r2r-vm-new:/home/laptop/r2r-deploy/user_configs/r2r.toml \
  --zone=us-central1-a
```

**Step 4: Restart** - Restart the R2R container:
```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="cd /home/laptop/r2r-deploy && docker compose restart r2r"
```

**Step 5: Verify** - ALWAYS check logs for errors:
```bash
gcloud compute ssh r2r-vm-new --zone=us-central1-a \
  --command="docker logs r2r-deploy-r2r-1 --tail=50"
```

**If restart fails:** Read full logs with `--tail=200` and look for error messages.

## Common R2R Issues

### "unrecognized chunking strategy 'recursive'"
- **Cause:** Unstructured doesn't support `recursive` strategy
- **Fix:** Set `chunking_strategy = "by_title"` in `[ingestion]` section

### "S3 bucket name is required"
- **Cause:** S3 provider configured without bucket
- **Fix:** Add complete `[file]` configuration:
  ```toml
  [file]
  provider = "s3"
  bucket_name = "r2r"
  endpoint_url = "http://minio:9000"
  aws_access_key_id = "minio"
  aws_secret_access_key = "YOUR_MINIO_PASSWORD"
  ```
- **Note:** MinIO credentials are in `/home/laptop/r2r-deploy/env/minio.env` on server

## File Structure

| Local Path | Purpose |
|------------|---------|
| `docker/user_configs/r2r.toml` | **EDIT THIS** - your R2R config |
| `data/R2R/py/all_possible_config.toml` | Reference: all config options |
| `.env` | Local environment variables |

| Server Path | Purpose |
|-------------|---------|
| `/home/laptop/r2r-deploy/user_configs/r2r.toml` | Deployed R2R config |
| `/home/laptop/r2r-deploy/env/r2r.env` | Server environment vars |
| `/home/laptop/r2r-deploy/env/minio.env` | MinIO credentials |

## Local Development

To run R2R locally:
```bash
docker compose -f compose.full.yaml --profile postgres --profile minio up -d
```

## Workflows

Development workflows and best practices:
@.claude/rules/workflows/testing.md
@.claude/rules/workflows/troubleshooting.md
@.claude/rules/workflows/git-workflow.md

## R2R Framework

R2R v3.x-specific rules and references:
@.claude/rules/r2r/configuration.md
@.claude/rules/r2r/api-reference.md
@.claude/rules/r2r/troubleshooting.md
@.claude/rules/r2r/best-practices.md

## Additional Rules

Security constraints and deployment procedures:
@.claude/rules/security.md
@.claude/rules/deployment.md

## Reference Documentation

For GCloud commands, container names, and other reference info:
@.claude/rules/gcloud-reference.md

## Personal Overrides

Copy `CLAUDE.local.md.template` to `CLAUDE.local.md` for personal preferences.
@CLAUDE.local.md
