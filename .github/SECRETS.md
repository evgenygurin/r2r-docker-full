# GitHub Secrets Configuration

This document describes the GitHub Secrets configured for this repository's CI/CD workflows.

## Configured Secrets

### GCP_PROJECT_ID

- **Used by:** `deploy-gcp.yml`
- **Purpose:** Google Cloud Project ID for deployment
- **Value:** `r2r-full-deployment`
- **Last updated:** 2025-12-19

### GCP_SA_KEY

- **Used by:** `deploy-gcp.yml`
- **Purpose:** Google Cloud Service Account Key (JSON) for authentication
- **Source:** `docker/user_configs/gcp-key.json` (gitignored)
- **Last updated:** 2025-12-19

## How to Update Secrets

### Using GitHub CLI (gh)

```bash
# Update GCP_PROJECT_ID
echo "r2r-full-deployment" | gh secret set GCP_PROJECT_ID

# Update GCP_SA_KEY from file
gh secret set GCP_SA_KEY < docker/user_configs/gcp-key.json
```

### Using GitHub Web UI

1. Go to repository Settings
2. Navigate to Secrets and variables → Actions
3. Click "New repository secret" or edit existing
4. Enter secret name and value
5. Click "Add secret" or "Update secret"

## Verifying Secrets

```bash
# List all configured secrets
gh secret list

# Output:
# GCP_PROJECT_ID  2025-12-19T22:16:58Z
# GCP_SA_KEY      2025-12-19T22:17:04Z
```

## Security Best Practices

1. **Never commit secrets to git**
   - `gcp-key.json` is in `.gitignore`
   - Use environment variables or GitHub Secrets

2. **Rotate secrets regularly**
   - Update GCP service account keys every 90 days
   - Revoke old keys after rotation

3. **Least privilege principle**
   - Service account should have minimum required permissions
   - Only roles needed for deployment

4. **Audit secret access**
   - Check workflow logs for unauthorized access attempts
   - Monitor GCP IAM audit logs

## Required GCP Service Account Permissions

The service account key (`GCP_SA_KEY`) needs these IAM roles:

- `roles/compute.instanceAdmin.v1` - Manage VM instances
- `roles/iam.serviceAccountUser` - Act as service account
- `compute.instances.get` - Describe VM status
- `compute.sshKeys.get` - SSH access to VMs

## Workflow-Specific Secret Usage

### deploy-gcp.yml

```yaml
env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}

steps:
  - name: Set up Cloud SDK
    uses: google-github-actions/setup-gcloud@v3
    with:
      service_account_key: ${{ secrets.GCP_SA_KEY }}
      project_id: ${{ secrets.GCP_PROJECT_ID }}
```

## Adding New Secrets

When adding new secrets:

1. Update this document with secret details
2. Add secret via `gh secret set` or GitHub UI
3. Update workflows to use the secret
4. Test workflow to verify secret works
5. Document in `.claude/rules/workflows/github-actions.md` if needed

## Troubleshooting

### "Secret not found" error

```bash
# Verify secret exists
gh secret list | grep SECRET_NAME

# Re-add secret if missing
gh secret set SECRET_NAME
```

### "Invalid credentials" error

1. Check GCP service account key is valid JSON:
   ```bash
   cat docker/user_configs/gcp-key.json | jq .
   ```

2. Verify service account has required permissions:
   ```bash
   gcloud projects get-iam-policy r2r-full-deployment \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:*"
   ```

3. Re-upload the secret:
   ```bash
   gh secret set GCP_SA_KEY < docker/user_configs/gcp-key.json
   ```

## Secret Rotation Schedule

| Secret | Rotation Frequency | Last Rotated | Next Rotation |
|--------|-------------------|--------------|---------------|
| GCP_SA_KEY | 90 days | 2025-12-19 | 2026-03-19 |
| GCP_PROJECT_ID | Never (project ID is static) | N/A | N/A |
