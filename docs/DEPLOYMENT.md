# Deployment Guide

Complete guide for deploying the WBS Creation Service to Google Cloud Platform.

## Prerequisites

### Required Tools
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Terraform](https://www.terraform.io/downloads) (optional, for infrastructure as code)
- Python 3.11+ installed locally
- Git for version control

### Required Accounts & APIs
- Google Cloud Platform account with billing enabled
- Backlog API key from your Backlog space
- Notion Integration token

## Deployment Methods

Choose one of the following deployment methods:

### Method 1: Quick Deployment (Recommended for Getting Started)

Use the deployment script for a quick, automated deployment.

#### Step 1: Authenticate with GCloud
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### Step 2: Set Up Secrets
```bash
./scripts/setup-secrets.sh
```

This will prompt you for:
- Backlog API Key
- Backlog Space URL
- Notion API Key

#### Step 3: Configure Environment Variables
```bash
# Set required environment variables
export BACKLOG_SPACE_URL="https://your-space.backlog.com"
export ALLOWED_ORIGINS="https://yourdomain.com"  # Or "*" for development
export ENVIRONMENT="production"
```

#### Step 4: Deploy
```bash
./scripts/deploy.sh
```

The script will:
1. Run tests (must have 80%+ coverage)
2. Enable required Google Cloud APIs
3. Create GCS bucket for data storage
4. Deploy the Cloud Function

#### Step 5: Test Deployment
```bash
# Get function URL (shown in deployment output)
FUNCTION_URL=$(gcloud functions describe wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --format="value(serviceConfig.uri)")

# Test health check
curl $FUNCTION_URL/health

# Test WBS creation
curl -X POST $FUNCTION_URL/wbs-create \
    -H 'Content-Type: application/json' \
    -d '{
        "template_url": "https://your-space.backlog.com/view/PROJ-1",
        "project_key": "PROJ"
    }'
```

---

### Method 2: Infrastructure as Code (Terraform)

Use Terraform for reproducible, version-controlled infrastructure.

#### Step 1: Configure Terraform Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:
```hcl
project_id     = "your-gcp-project-id"
region         = "asia-northeast1"
environment    = "production"

backlog_api_key   = "your-backlog-api-key"
backlog_space_url = "https://your-space.backlog.com"
notion_api_key    = "secret_xxxxxxxxxxxxx"

allowed_origins = "https://yourdomain.com"
```

#### Step 2: Initialize Terraform
```bash
terraform init
```

#### Step 3: Plan Infrastructure
```bash
terraform plan
```

Review the planned changes carefully.

#### Step 4: Apply Infrastructure
```bash
terraform apply
```

Type `yes` when prompted.

#### Step 5: Deploy Function Code
```bash
cd ..
./scripts/deploy.sh
```

---

### Method 3: Manual Deployment

For complete control over each step.

#### Step 1: Enable APIs
```bash
gcloud services enable \
    cloudfunctions.googleapis.com \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com
```

#### Step 2: Create Secrets
```bash
# Backlog API Key
echo -n "your-backlog-api-key" | gcloud secrets create backlog-api-key \
    --replication-policy="automatic" \
    --data-file=-

# Notion API Key
echo -n "secret_xxxxxxxxxxxxx" | gcloud secrets create notion-api-key \
    --replication-policy="automatic" \
    --data-file=-
```

#### Step 3: Create Service Account
```bash
gcloud iam service-accounts create wbs-creation-service-sa \
    --display-name="WBS Creation Service Account"

# Grant permissions
gcloud secrets add-iam-policy-binding backlog-api-key \
    --member="serviceAccount:wbs-creation-service-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding notion-api-key \
    --member="serviceAccount:wbs-creation-service-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

#### Step 4: Create GCS Bucket
```bash
gsutil mb -p YOUR_PROJECT_ID -c STANDARD -l asia-northeast1 gs://YOUR_PROJECT_ID-wbs-data
```

#### Step 5: Deploy Cloud Function
```bash
gcloud functions deploy wbs-creation-service \
    --gen2 \
    --runtime=python311 \
    --region=asia-northeast1 \
    --source=. \
    --entry-point=wbs_create \
    --trigger-http \
    --allow-unauthenticated \
    --memory=512Mi \
    --timeout=540 \
    --max-instances=10 \
    --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT_ID,BACKLOG_SPACE_URL=https://your-space.backlog.com,ALLOWED_ORIGINS=*,ENVIRONMENT=production,GCS_BUCKET_NAME=YOUR_PROJECT_ID-wbs-data" \
    --set-secrets="BACKLOG_API_KEY=backlog-api-key:latest,NOTION_API_KEY=notion-api-key:latest" \
    --service-account=wbs-creation-service-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## Post-Deployment

### 1. Verify Deployment
```bash
# Check function status
gcloud functions describe wbs-creation-service --gen2 --region=asia-northeast1

# View logs
gcloud functions logs read wbs-creation-service --gen2 --region=asia-northeast1 --limit=50
```

### 2. Set Up Monitoring
```bash
# Create uptime check (optional)
# Via GCP Console: Monitoring > Uptime checks

# Create alert policies (optional)
# Via GCP Console: Monitoring > Alerting
```

### 3. Configure CORS (Production)
Update `ALLOWED_ORIGINS` to restrict access:
```bash
gcloud functions deploy wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --update-env-vars="ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com"
```

### 4. Set Up CI/CD (Optional)
See [CI/CD Setup Guide](./CI_CD_SETUP.md) for GitHub Actions integration.

---

## Troubleshooting

### Deployment Fails

**Error: "Permission denied"**
```bash
# Ensure you're authenticated
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**Error: "API not enabled"**
```bash
# Enable the required API
gcloud services enable SERVICE_NAME.googleapis.com
```

### Function Returns 500 Error

**Check logs:**
```bash
gcloud functions logs read wbs-creation-service --gen2 --region=asia-northeast1 --limit=100
```

**Common issues:**
- Missing environment variables
- Secret not accessible
- Firestore not initialized

### Secrets Not Accessible

**Grant access to service account:**
```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

---

## Updating the Deployment

### Update Function Code
```bash
# Run tests first
pytest tests/unit -v --cov=src --cov-fail-under=80

# Deploy update
./scripts/deploy.sh
```

### Update Secrets
```bash
# Add new version
echo -n "new-secret-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Update Environment Variables
```bash
gcloud functions deploy wbs-creation-service \
    --gen2 \
    --region=asia-northeast1 \
    --update-env-vars="KEY=VALUE"
```

---

## Rollback

### Rollback to Previous Version
```bash
# List revisions
gcloud functions describe wbs-creation-service --gen2 --region=asia-northeast1

# Rollback (redeploy previous version from git)
git checkout PREVIOUS_COMMIT
./scripts/deploy.sh
git checkout main
```

---

## Cost Estimation

Estimated monthly costs (based on moderate usage):

- Cloud Functions: $0-10/month (first 2M invocations free)
- Firestore: $0-5/month (free tier: 1GB storage, 50K reads/day)
- Cloud Storage: $0-2/month (first 5GB free)
- Secret Manager: $0.06/secret/month
- **Total: ~$1-20/month** (depending on usage)

For high-traffic scenarios, consider:
- Setting min instances > 0 (reduces cold starts, increases cost)
- Using Cloud Run instead (better control over scaling)

---

## Security Best Practices

1. **Restrict CORS origins** in production
2. **Enable Cloud Armor** for DDoS protection (optional)
3. **Use least-privilege IAM** for service accounts
4. **Regularly rotate API keys**
5. **Enable audit logging** for compliance
6. **Use VPC Service Controls** for data governance (enterprise)

---

## Next Steps

- Set up [monitoring and alerting](./MONITORING.md)
- Configure [CI/CD pipeline](./CI_CD_SETUP.md)
- Review [API documentation](./API.md)
- Implement [backup strategy](./BACKUP.md)
