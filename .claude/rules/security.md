---
paths:
  - "**/*.env"
  - "**/*.env.*"
  - "**/credentials/**"
  - "docker/user_configs/gcp-key.json"
---

# Security Constraints

## Critical Security Rules

- **NEVER** commit files with secrets to git
- **NEVER** log credentials, API keys, or passwords
- **NEVER** expose MinIO credentials in plain text
- **NEVER** hardcode passwords in configuration files
- **ALWAYS** use environment variables for sensitive data
- **ALWAYS** check `.gitignore` before adding new credential files

## Sensitive Files

These files MUST NEVER be committed:

|  File Pattern  |  Contains  |  Protected By  |
| -------------- | ---------- | -------------- |
|  `*.env`  |  Environment variables  |  `.gitignore`  |
|  `.env copy`  |  Backup env vars  |  `.gitignore`  |
|  `docker/env/*.env`  |  Docker secrets  |  `.gitignore`  |
|  `credentials/**`  |  GCP/API keys  |  `.gitignore`  |
|  `docker/user_configs/gcp-key.json`  |  GCP service account  |  `.gitignore`  |

## When Handling Credentials

**Before editing config files with secrets:**

1. Check if file is in `.gitignore`
2. Use placeholders like `YOUR_PASSWORD_HERE` or `${ENV_VAR}` in examples
3. Store actual values in `.env` or server environment

**MinIO Credentials:**

- Location: `/home/laptop/r2r-deploy/env/minio.env` (server only)
- Access: `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD`
- Never include in local files or git commits

**GCP Credentials:**

- Use service account JSON key stored in `docker/user_configs/gcp-key.json`
- Never commit this file (already in `.gitignore`)
- Reference via `GOOGLE_APPLICATION_CREDENTIALS` env var

## API Keys & Tokens

When working with API keys:

1. Always use environment variables: `os.environ.get('API_KEY')`
2. Never log or print API keys
3. Use masked display in outputs: `hf_****...****` (first 3 + last 4 chars)
4. Revoke immediately if exposed in git history

## Verification Checklist

Before committing changes:

- [ ] Run `git status` to check staged files
- [ ] Verify no `.env` or credential files are staged
- [ ] Check diff for accidentally added secrets: `git diff --staged`
- [ ] Grep for common patterns: `git diff --staged | grep -i "password\|secret\|key"`

## Emergency Response

If secrets are committed:

1. **STOP** - Do not push to remote
2. Revoke the exposed credentials immediately
3. Remove from git history: `git reset --soft HEAD~1` (if not pushed)
4. Or use `git filter-branch` / BFG Repo-Cleaner (if already pushed)
5. Generate new credentials
6. Update `.gitignore` if needed
