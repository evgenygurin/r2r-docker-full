---
paths:
  - .github/workflows/**/*.yml
  - .github/workflows/**/*.yaml
---

# GitHub Actions Workflows

## Critical Security Rules

### Command Injection Prevention (MANDATORY)

**NEVER use untrusted inputs directly in `run:` commands:**

```yaml
# ❌ UNSAFE - Command injection vulnerability
run: echo "${{ github.event.issue.title }}"
run: git commit -m "${{ github.event.head_commit.message }}"
run: curl "${{ github.event.pull_request.head.ref }}"
```

**ALWAYS use environment variables for untrusted inputs:**

```yaml
# ✅ SAFE - Use env block
env:
  TITLE: ${{ github.event.issue.title }}
  MESSAGE: ${{ github.event.head_commit.message }}
  REF: ${{ github.event.pull_request.head.ref }}
run: |
  echo "$TITLE"
  git commit -m "$MESSAGE"
  curl "$REF"
```

**Untrusted inputs that MUST use env vars:**

- `github.event.issue.title/body`
- `github.event.pull_request.title/body/head.ref`
- `github.event.comment.body`
- `github.event.commits.*.message`
- `github.head_ref`
- `github.event.head_commit.author.name/email`
- Any user-controlled data from issues, PRs, comments

**Reference:** <https://github.blog/security/vulnerability-research/how-to-catch-github-actions-workflow-injections-before-attackers-do/>

---

## Cost Optimization (MANDATORY)

**ALWAYS apply these cost-saving measures:**

### 1. Use Path Filters

```yaml
on:
  pull_request:
    paths:
      - 'docker/**'           # Only trigger on relevant changes
      - 'src/**'
  push:
    branches: [main]
    paths:
      - 'docker/user_configs/**'
```

### 2. Set Timeouts

```yaml
jobs:
  build:
    timeout-minutes: 10     # ALWAYS set timeout (default is 360 min!)
```

### 3. Use Caching

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

### 4. Manual Triggers for Expensive Operations

```yaml
on:
  workflow_dispatch:        # Manual trigger only
  push:
    branches: [main]
    paths:
      - 'critical-file.yml' # Or only on specific changes
```

### 5. Weekly Schedules, Not Daily

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'     # Monday 9am, not daily
```

---

## Workflow Development Rules

### When to Edit Workflows

**Before editing ANY workflow:**

1. Test changes locally with `act` if possible
2. Review security implications (especially for untrusted inputs)
3. Check for cost impact (new jobs, longer timeouts)
4. Validate YAML syntax: `yamllint .github/workflows/*.yml`

### Keep Workflows Simple

**Each workflow should be self-contained with minimal dependencies.**

### Job Structure

**Each job MUST have:**

- `timeout-minutes` - prevent runaway jobs
- Clear `name` - describes what it does
- Minimal steps - only what's necessary

```yaml
jobs:
  validate:
    name: Validate Configuration
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Validate TOML
        run: python -c "import toml; toml.load('config.toml')"
```

---

## Workflow Best Practices

### 1. Use Latest Stable Actions

```yaml
# ✅ Pin to major version
- uses: actions/checkout@v4
- uses: actions/setup-python@v5

# ❌ Don't pin to commit SHA (hard to audit)
- uses: actions/checkout@a81bbbf8298c0fa03ea29cdc473d45769f953675
```

### 2. Fail Fast

```yaml
# ✅ Exit immediately on first error
run: |
  set -e  # Exit on error
  command1
  command2
```

### 3. Meaningful Output

```yaml
# ✅ Clear success/failure messages
run: |
  if validate_config; then
    echo "✅ Configuration valid"
  else
    echo "❌ Configuration validation failed"
    exit 1
  fi
```

### 4. Use GitHub Step Summary

```yaml
# ✅ Add to job summary for visibility
run: |
  echo "## Test Results" >> $GITHUB_STEP_SUMMARY
  echo "✅ All tests passed" >> $GITHUB_STEP_SUMMARY
```

---

## Project-Specific Workflows

### Security Scan (security-scan.yml)

**Triggers:** All PRs, pushes to main, weekly Monday 9am
**Purpose:** Gitleaks, Trivy, Python dependency scanning
**Cost:** ~3-5 min, runs weekly to save costs

### Docker Build (docker-build.yml)

**Triggers:** PRs touching `docker/**`, pushes to main
**Purpose:** Validate Docker Compose syntax
**Note:** Creates test env files for CI (gitignored in repo)

### Lint (lint.yml)

**Triggers:** All PRs, pushes to main
**Purpose:** YAML, Shell, Python, Markdown linting
**Note:** Python linting in advisory mode (`|| true`)

### Deploy to GCP (deploy-gcp.yml)

**Triggers:** Manual (`workflow_dispatch`) only
**Purpose:** Restart R2R service on production server
**Secrets:** `GCP_VM_IP`, `GCP_SSH_PRIVATE_KEY_BASE64`

### Release (release.yml)

**Triggers:** Version tags (`v*.*.*`), manual
**Purpose:** Create GitHub release with changelog
**Note:** Auto-generates changelog grouped by commit type

---

## Troubleshooting Workflows

### Workflow Fails to Start

**Check:**

1. YAML syntax: `yamllint .github/workflows/failing.yml`
2. GitHub Actions permissions: Settings → Actions → General
3. Workflow file location: Must be in `.github/workflows/`

### Workflow Runs Too Long

**Fix:**

1. Add/reduce `timeout-minutes`
2. Check for infinite loops or hanging commands
3. Review logs for slow steps

### Secrets Not Working

**Fix:**

1. Verify secret exists: Settings → Secrets → Actions
2. Check secret name matches exactly
3. For GCP_SA_KEY, verify it's valid JSON

### Cache Not Working

**Debug:**

```yaml
- name: Check cache
  uses: actions/cache@v4
  id: cache
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

- name: Cache status
  run: echo "Cache hit: ${{ steps.cache.outputs.cache-hit }}"
```

### Manual Trigger Not Showing

**Fix:**

1. Workflow must be on default branch (main)
2. Add `workflow_dispatch` to `on:` section
3. Push workflow file to main first

---

## Testing Workflows Locally

### Using act

```bash
# Install act
brew install act

# Test specific workflow
act pull_request -W .github/workflows/docker-build.yml

# Test with secrets
act -s GITHUB_TOKEN=your_token

# Test specific job
act -j validate-compose
```

### Limitations of act

- Some GitHub-specific features don't work
- Large Docker images may be slow
- GCP deployment workflows can't be fully tested

---

## Workflow File Organization

```text
.github/
└── workflows/
    ├── security-scan.yml           # Security: Gitleaks, Trivy
    ├── docker-build.yml            # Build: Compose validation
    ├── lint.yml                    # Quality: Code linting
    ├── deploy-gcp.yml              # Deploy: Production restart
    └── release.yml                 # Release: Version tagging
```

**Naming convention:**

- `<purpose>-<target>.yml` - e.g., `deploy-gcp.yml`

---

## Common Workflow Patterns

### Conditional Steps

```yaml
- name: Run only on main
  if: github.ref == 'refs/heads/main'
  run: echo "Main branch only"

- name: Run only on PRs
  if: github.event_name == 'pull_request'
  run: echo "PR only"
```

### Matrix Builds

```yaml
# Only if truly needed for cost optimization
strategy:
  matrix:
    python-version: ['3.11']  # Single version only
```

### Artifact Upload

```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: results/
    retention-days: 7  # Don't keep forever
```

---

## Pre-Commit Checklist

Before committing workflow changes:

- [ ] Validated YAML syntax
- [ ] All untrusted inputs use `env:` block
- [ ] `timeout-minutes` set on all jobs
- [ ] Path filters added where applicable
- [ ] Tested locally with `act` (if possible)
- [ ] Documented purpose in workflow file
- [ ] No hardcoded secrets or credentials
- [ ] Uses reusable workflows where applicable

---

## Emergency Procedures

### Disable Failing Workflow

1. Go to Actions tab
2. Select failing workflow
3. Click "..." → Disable workflow
4. Fix and re-enable

### Cancel Running Workflow

```bash
# Via GitHub CLI
gh run cancel <run-id>

# Or via UI
Actions → Select run → Cancel run
```

### Force Re-run

```bash
# Via GitHub CLI
gh run rerun <run-id>

# Or via UI
Actions → Select run → Re-run jobs
```
