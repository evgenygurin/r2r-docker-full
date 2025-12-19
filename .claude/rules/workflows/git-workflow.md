# Git Workflow

## Commit Message Format

Use conventional commits format:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring without behavior change
- `docs`: Documentation only
- `chore`: Maintenance tasks
- `test`: Adding or updating tests
- `config`: Configuration changes

### Examples

```bash
# Good commit messages:
git commit -m "feat(r2r): add MinIO storage configuration"
git commit -m "fix(deployment): correct gcloud zone parameter"
git commit -m "config(embedding): switch to CodeBERT model"
git commit -m "docs(claude): improve troubleshooting guide"

# Bad commit messages:
git commit -m "updates"
git commit -m "fix"
git commit -m "WIP"
```

## Branching Strategy

### Main Branches

- `main` - Production-ready code
- `dev` - Development integration (if needed)

### Feature Branches

```bash
# Create feature branch
git checkout -b feature/new-embedding-model

# Work on feature
# ... make changes ...

# Commit frequently
git add docker/user_configs/r2r.toml
git commit -m "config(r2r): update embedding model to CodeBERT"

# When complete, merge to main
git checkout main
git merge feature/new-embedding-model

# Delete feature branch
git branch -d feature/new-embedding-model
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `config/` - Configuration changes
- `docs/` - Documentation updates

Examples:
- `feature/add-minio-storage`
- `fix/postgres-connection`
- `config/update-chunking-strategy`
- `docs/deployment-guide`

## Before Committing

**Pre-commit checklist:**

```bash
# 1. Check what's staged
git status

# 2. Review changes
git diff --staged

# 3. Verify no secrets
git diff --staged | grep -iE "password|secret|key|token"

# 4. Check .gitignore is working
git status --ignored

# 5. If secrets found: Unstage immediately
git restore --staged <file>
```

## Configuration Changes

### Committing r2r.toml Changes

```bash
# 1. Make changes
# Edit docker/user_configs/r2r.toml

# 2. Test locally first
docker compose restart r2r
# Verify it works

# 3. Review diff carefully
git diff docker/user_configs/r2r.toml

# 4. Commit with descriptive message
git add docker/user_configs/r2r.toml
git commit -m "config(r2r): change chunking_strategy to by_title

Reason: Unstructured doesn't support recursive strategy
Impact: Improves document parsing reliability
Testing: Verified locally with sample.pdf ingestion"

# 5. Deploy to server after commit
# (follow deployment.md workflow)
```

## Handling Sensitive Files

### Files to NEVER commit

```bash
# Already in .gitignore:
.env
.env copy
docker/env/*.env
credentials/
docker/user_configs/gcp-key.json
CLAUDE.local.md
```

### If you accidentally stage sensitive file:

```bash
# Unstage immediately
git restore --staged <file>

# Verify it's not staged
git status

# Double-check .gitignore
cat .gitignore | grep <file-pattern>
```

### If you accidentally commit sensitive file:

```bash
# If NOT pushed yet:
git reset --soft HEAD~1  # Undo commit, keep changes
# Remove sensitive content
# Re-commit

# If already pushed:
# 1. IMMEDIATELY revoke exposed credentials
# 2. Use git filter-branch or BFG Repo-Cleaner
# 3. Force push (coordinate with team)
```

## Working with Remote

### Before pushing to GitHub

```bash
# 1. Verify commits are clean
git log -3 --oneline

# 2. Check no secrets in recent commits
git log -p -3 | grep -iE "password|secret|token|key"

# 3. Push
git push origin main
```

### Syncing with remote

```bash
# Fetch latest changes
git fetch origin

# Check what's new
git log HEAD..origin/main --oneline

# Pull changes
git pull origin main

# If conflicts:
# 1. Resolve conflicts in files
# 2. git add <resolved-files>
# 3. git commit -m "merge: resolve conflicts from origin/main"
```

## Useful Git Commands

### Viewing History

```bash
# Recent commits
git log --oneline -10

# Changes in specific file
git log -p docker/user_configs/r2r.toml

# Who changed what
git blame docker/user_configs/r2r.toml

# Search commit messages
git log --grep="embedding"
```

### Undoing Changes

```bash
# Discard unstaged changes in file
git checkout -- <file>

# Unstage file
git restore --staged <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - DANGEROUS
git reset --hard HEAD~1

# Revert a commit (creates new commit)
git revert <commit-hash>
```

### Stashing

```bash
# Save work-in-progress
git stash save "WIP: testing new config"

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{1}
```

## R2R-Specific Git Workflows

### Workflow: Update R2R Configuration

```bash
# 1. Create config branch
git checkout -b config/update-embedding-model

# 2. Backup current config
cp docker/user_configs/r2r.toml docker/user_configs/r2r.toml.backup

# 3. Make changes
nano docker/user_configs/r2r.toml

# 4. Test locally
docker compose restart r2r
docker logs r2r-deploy-r2r-1 --tail=50

# 5. Commit if test passes
git add docker/user_configs/r2r.toml
git commit -m "config(r2r): update embedding model to CodeBERT

- Changed base_model to huggingface/microsoft/codebert-base
- Updated base_dimension from 512 to 768
- Tested locally: embeddings working correctly"

# 6. Merge to main
git checkout main
git merge config/update-embedding-model

# 7. Deploy to server
# (follow deployment workflow)

# 8. Clean up
git branch -d config/update-embedding-model
```

### Workflow: Emergency Rollback

```bash
# If production is broken and you need to revert quickly:

# 1. Find last working commit
git log --oneline -10

# 2. Create emergency rollback branch
git checkout -b emergency/rollback-config

# 3. Revert to specific commit
git revert <bad-commit-hash>

# OR restore specific file from good commit
git checkout <good-commit-hash> -- docker/user_configs/r2r.toml

# 4. Commit rollback
git commit -m "fix(emergency): rollback to working config

Reason: Production R2R failing after config change
Reverted: commit <hash>
Verified: Local test passes"

# 5. Merge to main
git checkout main
git merge emergency/rollback-config

# 6. Deploy immediately
# (fast-track deployment)

# 7. Investigate root cause later
```

## Best Practices

1. **Commit frequently** - Small, focused commits
2. **Descriptive messages** - Explain why, not just what
3. **Test before commit** - Verify changes work
4. **Review before push** - Check commits don't contain secrets
5. **Pull before push** - Avoid conflicts
6. **Branch for features** - Keep main stable
7. **Clean history** - Use meaningful commit messages
8. **Backup before major changes** - Easy rollback if needed
