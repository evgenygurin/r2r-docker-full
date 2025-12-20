# CI/CD Workflows

## Deploy to GCP Workflow

### MinIO Credential Substitution

**Problem:** Base64-encoded MinIO password contains `=` padding characters

**Solution:** Use `sed` instead of `cut` to extract password:

```bash
# ❌ WRONG - truncates = characters
MINIO_PASSWORD=$(grep MINIO_ROOT_PASSWORD file | cut -d= -f2)

# ✅ CORRECT - preserves full password
MINIO_PASSWORD=$(grep MINIO_ROOT_PASSWORD file | sed "s/^MINIO_ROOT_PASSWORD=//")
```

### Debug Output

The workflow includes verification:
- Password length (should be 45 chars)
- Masked final value in r2r.toml
