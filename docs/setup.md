# WBS Creation MCP Server - Setup Guide

## Prerequisites

- Python 3.11 or higher
- Google Cloud Platform account
- Backlog account with API access
- Notion account with Integration Token (optional)
- gcloud CLI installed

## GCP Project Setup

### 1. Create GCP Project

```bash
gcloud projects create your-project-id
gcloud config set project your-project-id
```

### 2. Enable Required APIs

```bash
# Enable required Google Cloud APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable documentai.googleapis.com
gcloud services enable logging.googleapis.com
```

### 3. Create GCS Bucket

```bash
gsutil mb -p your-project-id gs://your-wbs-data-bucket
```

### 4. Initialize Firestore

```bash
gcloud firestore databases create --region=asia-northeast1
```

### 5. Set up Document AI

1. Go to Document AI console
2. Create a processor (choose "Form Parser")
3. Note the Processor ID

### 6. Create Service Account

```bash
gcloud iam service-accounts create wbs-service-account \
  --display-name="WBS Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:wbs-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:wbs-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:wbs-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/documentai.apiUser"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:wbs-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

## Backlog Setup

### 1. Get API Key

1. Log in to Backlog
2. Go to Personal Settings > API
3. Generate API key
4. Note the API key and space URL

### 2. Create Test Project

1. Create a new project in Backlog
2. Note the project key (e.g., "PROJ")

## Notion Setup (Optional)

### 1. Create Integration

1. Go to https://www.notion.so/my-integrations
2. Create new integration
3. Note the Integration Token

### 2. Share Pages

1. Create template pages/databases in Notion
2. Share with your integration

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd mcp-wbs-add2
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values
```

Required environment variables:
```bash
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-wbs-data-bucket
DOCUMENT_AI_PROCESSOR_ID=your-processor-id
BACKLOG_SPACE_URL=https://your-space.backlog.com
BACKLOG_API_KEY=your-backlog-api-key
NOTION_API_KEY=your-notion-token  # Optional
```

### 5. Run Tests

```bash
# Run unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=src --cov-report=html

# Run integration tests
pytest tests/integration -v -m integration
```

## Deployment to Cloud Functions

### 1. Deploy Function

```bash
gcloud functions deploy wbs-create \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point wbs_create \
  --source . \
  --memory 512MB \
  --timeout 300s \
  --region asia-northeast1 \
  --service-account wbs-service-account@your-project-id.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=your-project-id,GCS_BUCKET_NAME=your-bucket,BACKLOG_SPACE_URL=https://your-space.backlog.com,BACKLOG_API_KEY=your-key,NOTION_API_KEY=your-notion-key,DOCUMENT_AI_PROCESSOR_ID=your-processor-id
```

### 2. Deploy Health Check

```bash
gcloud functions deploy health-check \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point health_check \
  --source . \
  --memory 128MB \
  --timeout 10s \
  --region asia-northeast1
```

### 3. Test Deployment

```bash
# Get function URL
gcloud functions describe wbs-create --region asia-northeast1 --format="value(httpsTrigger.url)"

# Test health check
curl https://your-function-url/health-check

# Test WBS creation
curl -X POST https://your-function-url/wbs-create \
  -H "Content-Type: application/json" \
  -d '{
    "template_url": "https://your-space.backlog.com/view/PROJ-1",
    "project_key": "PROJ"
  }'
```

## Monitoring

### View Logs

```bash
# View Cloud Functions logs
gcloud functions logs read wbs-create --region asia-northeast1 --limit 50

# Stream logs
gcloud functions logs read wbs-create --region asia-northeast1 --follow
```

### Check Metrics

```bash
# View function metrics in Cloud Console
https://console.cloud.google.com/functions/details/asia-northeast1/wbs-create
```

## Troubleshooting

### Common Issues

**Issue**: Permission denied errors
- Solution: Verify service account has required IAM roles
- Check: `gcloud projects get-iam-policy your-project-id`

**Issue**: Function timeout
- Solution: Increase timeout or optimize processing
- Check Document AI processor region matches function region

**Issue**: Import errors
- Solution: Ensure all dependencies in requirements.txt
- Redeploy with: `gcloud functions deploy ...`

**Issue**: Firestore/GCS errors
- Solution: Verify APIs are enabled and service account has access
- Check: `gcloud services list --enabled`

### Debug Mode

Set environment variable for verbose logging:
```bash
LOG_LEVEL=DEBUG
```

## Security Considerations

1. **API Keys**: Never commit .env file to version control
2. **IAM**: Use principle of least privilege for service accounts
3. **CORS**: Configure allowed origins in production
4. **Authentication**: Add authentication for production use
5. **Rate Limiting**: Implement rate limiting if needed

## Next Steps

1. Configure Backlog project with required categories
2. Create template tasks in Backlog or Notion
3. Test WBS creation workflow
4. Set up monitoring and alerts
5. Configure backup and disaster recovery

## Support

For issues and questions:
- Check logs in Cloud Logging
- Review API documentation in docs/api.md
- Verify configuration in .env matches requirements
