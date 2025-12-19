     STDIN
   1 # GitHub Secrets Configuration
   2 
   3 ## Required Secrets
   4 
   5 Add these secrets in GitHub repository settings:
   6 
   7 ### GCP Authentication
   8 
   9 - **GCP_SA_KEY**: Service account JSON key with permissions:
  10   - Compute Instance Admin
  11   - Service Account User
  12 
  13 - **GCP_PROJECT_ID**: GCP project ID (e.g., `my-r2r-project`)
  14 
  15 ## How to Create GCP Service Account
  16 
  17 ```bash
  18 # Create service account
  19 gcloud iam service-accounts create github-actions \
  20   --display-name="GitHub Actions Deployer"
  21 
  22 # Grant permissions
  23 gcloud projects add-iam-policy-binding PROJECT_ID \
  24   --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  25   --role="roles/compute.instanceAdmin.v1"
  26 
  27 # Create and download key
  28 gcloud iam service-accounts keys create key.json \
  29   --iam-account=github-actions@PROJECT_ID.iam.gserviceaccount.com
  30 
  31 # Copy contents of key.json to GitHub secret GCP_SA_KEY
  32 cat key.json
  33 ```
