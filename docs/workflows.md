# GitHub Actions Workflows

## Overview

This repository uses GitHub Actions for automated CI/CD.

## Workflows

### CI - Configuration Validation

**File:** `.github/workflows/ci-validation.yml`

**Triggers:**
- Pull requests modifying `docker/user_configs/**`
- Pushes to `main` branch

**What it does:**
1. Validates R2R TOML configuration syntax
2. Checks for hardcoded secrets
3. Ensures environment variable syntax is used

**Badge:** ![CI - Validation](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/ci-validation.yml/badge.svg)

---

### Security Scan

**File:** `.github/workflows/security-scan.yml`

**Triggers:**
- All pull requests
- Pushes to `main` branch
- Weekly on Mondays at 9am UTC

**What it does:**
1. Scans for leaked secrets with Gitleaks
2. Scans Docker configs with Trivy
3. Checks Python dependencies for vulnerabilities

**Badge:** ![Security Scan](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/security-scan.yml/badge.svg)

---

### Docker Build & Test

**File:** `.github/workflows/docker-build.yml`

**Triggers:**
- Pull requests modifying `docker/**`
- Pushes to `main` branch

**What it does:**
1. Validates Docker Compose syntax
2. Builds and starts R2R stack
3. Tests service health endpoints
4. Runs basic API tests

**Badge:** ![Docker Build](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/docker-build.yml/badge.svg)

---

### Lint & Code Quality

**File:** `.github/workflows/lint.yml`

**Triggers:**
- All pull requests
- Pushes to `main` branch

**What it does:**
1. Lints YAML files (workflows, compose)
2. Checks shell scripts with ShellCheck
3. Lints Python code (ruff, black, isort)
4. Lints Markdown files

**Badge:** ![Lint](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/lint.yml/badge.svg)

---

### Deploy to GCP

**File:** `.github/workflows/deploy-gcp.yml`

**Triggers:**
- Manual trigger via `workflow_dispatch`
- Pushes to `main` modifying `docker/user_configs/r2r.toml`

**What it does:**
1. Validates configuration
2. Creates backup on server
3. Uploads new configuration
4. Restarts R2R service
5. Verifies health
6. Automatic rollback on failure

**Required Secrets:**
- `GCP_SA_KEY` - Service account JSON key
- `GCP_PROJECT_ID` - GCP project ID

See `docs/github-secrets.md` for setup instructions.

---

### Release

**File:** `.github/workflows/release.yml`

**Triggers:**
- Push of version tags (e.g., `v1.0.0`)
- Manual trigger via `workflow_dispatch` with tag input

**What it does:**
1. Validates tag format (`v*.*.*`)
2. Generates changelog from git commits
3. Creates release artifacts:
   - `r2r.toml` - R2R configuration
   - `compose.full.yaml` - Docker Compose config
   - `DEPLOYMENT.md` - Deployment guide
4. Creates GitHub Release with artifacts

**Badge:** ![Release](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/release.yml/badge.svg)

**How to create a release:**

```bash
# 1. Create and push version tag
git tag v1.0.0
git push origin v1.0.0

# 2. Workflow automatically creates release with:
#    - Auto-generated changelog (grouped by commit type)
#    - Configuration files as attachments
#    - Deployment instructions
```

**Manual release:**

```bash
# Trigger workflow manually from GitHub Actions UI
# Actions → Release → Run workflow
# Enter tag: v1.0.0
```

---

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act

# Test validation workflow
act pull_request -W .github/workflows/ci-validation.yml

# Test security scan
act pull_request -W .github/workflows/security-scan.yml -j secret-scan

# Test Docker build (requires Docker)
act pull_request -W .github/workflows/docker-build.yml
```

## Best Practices

1. **Always test locally before pushing** - Use `act` to verify workflows
2. **Keep secrets in GitHub Secrets** - Never commit secrets
3. **Use environment-specific configurations** - Production vs staging
4. **Monitor workflow runs** - Check Actions tab regularly
5. **Review Dependabot PRs** - Keep dependencies updated

## Troubleshooting

### Workflow fails with "permission denied"

Check that GitHub Actions has correct permissions:
- Settings → Actions → General → Workflow permissions
- Enable "Read and write permissions"

### GCP deployment fails with authentication error

1. Verify `GCP_SA_KEY` secret is correct JSON
2. Check service account has required permissions
3. Verify `GCP_PROJECT_ID` matches your project

### Docker build times out

Increase timeout in workflow:

```yaml
jobs:
  build-test:
    timeout-minutes: 30  # Increase from default 20
```
