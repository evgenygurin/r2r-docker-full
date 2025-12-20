# GitHub Actions Workflows

## Overview

This repository uses GitHub Actions for automated CI/CD.

## Workflows

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
- Pushes to `main` branch modifying `docker/**`

**What it does:**

1. Creates required env files for CI
2. Validates Docker Compose syntax

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

- Manual trigger via `workflow_dispatch` only

**What it does:**

1. Connects to GCP VM via SSH
2. Restarts R2R service
3. Verifies health endpoint
4. Shows recent error logs

**Required Secrets:**

- `GCP_VM_IP` - VM IP address
- `GCP_SSH_PRIVATE_KEY_BASE64` - SSH private key (base64 encoded)

---

### Release

**File:** `.github/workflows/release.yml`

**Triggers:**

- Push of version tags (e.g., `v1.0.0`)
- Manual trigger via `workflow_dispatch` with tag input

**What it does:**

1. Validates tag format (`v*.*.*`)
2. Generates changelog from git commits
3. Creates GitHub Release with changelog

**Badge:** ![Release](https://github.com/evgenygurin/r2r-docker-full/actions/workflows/release.yml/badge.svg)

**How to create a release:**

```bash
# 1. Create and push version tag
git tag v1.0.0
git push origin v1.0.0

# 2. Workflow automatically creates release with auto-generated changelog
```

---

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act

# Test security scan
act pull_request -W .github/workflows/security-scan.yml -j secret-scan

# Test Docker build
act pull_request -W .github/workflows/docker-build.yml
```

## Best Practices

1. **Always test locally before pushing** - Use `act` to verify workflows
2. **Keep secrets in GitHub Secrets** - Never commit secrets
3. **Monitor workflow runs** - Check Actions tab regularly
4. **Review Dependabot PRs** - Keep dependencies updated

## Troubleshooting

### Workflow fails with "permission denied"

Check that GitHub Actions has correct permissions:

- Settings → Actions → General → Workflow permissions
- Enable "Read and write permissions"

### GCP deployment fails with authentication error

1. Verify SSH key is correctly base64 encoded
2. Check VM IP is correct
3. Verify SSH access from GitHub Actions IP ranges

### Docker build times out

Increase timeout in workflow:

```yaml
jobs:
  build-test:
    timeout-minutes: 30  # Increase from default 20
```
