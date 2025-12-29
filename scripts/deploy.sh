#!/bin/bash
# Deployment Script for WBS Creation Service to Google Cloud Functions
# This script deploys the application to Cloud Functions (Gen 2)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    print_error "No GCP project is set. Run 'gcloud config set project PROJECT_ID'"
    exit 1
fi

# Configuration
REGION="${REGION:-asia-northeast1}"
FUNCTION_NAME="${FUNCTION_NAME:-wbs-creation-service}"
RUNTIME="python311"
ENTRY_POINT="wbs_create"
MEMORY="${MEMORY:-512Mi}"
TIMEOUT="${TIMEOUT:-540}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"

print_info "Deployment Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Function Name: $FUNCTION_NAME"
echo "  Runtime: $RUNTIME"
echo "  Memory: $MEMORY"
echo "  Timeout: ${TIMEOUT}s"
echo "  Max Instances: $MAX_INSTANCES"
echo

# Confirm deployment
read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warn "Deployment cancelled by user"
    exit 0
fi

# Step 1: Run tests
print_step "Running tests..."
if ! python -m pytest tests/unit -v --cov=src --cov-fail-under=80; then
    print_error "Tests failed or coverage below 80%. Please fix before deploying."
    exit 1
fi
print_info "All tests passed!"
echo

# Step 2: Check required environment variables
print_step "Checking environment variables..."

# These will be set via Secret Manager or environment variables
REQUIRED_SECRETS=(
    "backlog-api-key"
    "notion-api-key"
)

for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
        print_warn "Secret $secret does not exist. Run scripts/setup-secrets.sh first."
    else
        print_info "Secret $secret found"
    fi
done
echo

# Step 3: Enable required APIs
print_step "Enabling required Google Cloud APIs..."
REQUIRED_APIS=(
    "cloudfunctions.googleapis.com"
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        print_info "API $api is already enabled"
    else
        print_warn "Enabling API: $api"
        gcloud services enable "$api" --project="$PROJECT_ID"
    fi
done
echo

# Step 4: Create GCS bucket for data (if it doesn't exist)
print_step "Checking GCS bucket..."
BUCKET_NAME="${PROJECT_ID}-wbs-data"
if gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null; then
    print_info "Bucket $BUCKET_NAME already exists"
else
    print_warn "Creating bucket: $BUCKET_NAME"
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$BUCKET_NAME"
fi
echo

# Step 5: Deploy to Cloud Functions
print_step "Deploying to Cloud Functions..."

# Get environment variables
BACKLOG_SPACE_URL="${BACKLOG_SPACE_URL:-}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-*}"
ENVIRONMENT="${ENVIRONMENT:-production}"

if [ -z "$BACKLOG_SPACE_URL" ]; then
    print_warn "BACKLOG_SPACE_URL not set. Using placeholder."
    BACKLOG_SPACE_URL="https://your-space.backlog.com"
fi

# Deploy function
gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime="$RUNTIME" \
    --region="$REGION" \
    --source=. \
    --entry-point="$ENTRY_POINT" \
    --trigger-http \
    --allow-unauthenticated \
    --memory="$MEMORY" \
    --timeout="$TIMEOUT" \
    --max-instances="$MAX_INSTANCES" \
    --min-instances="$MIN_INSTANCES" \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,BACKLOG_SPACE_URL=$BACKLOG_SPACE_URL,ALLOWED_ORIGINS=$ALLOWED_ORIGINS,ENVIRONMENT=$ENVIRONMENT,GCS_BUCKET_NAME=$BUCKET_NAME" \
    --set-secrets="BACKLOG_API_KEY=backlog-api-key:latest,NOTION_API_KEY=notion-api-key:latest" \
    --project="$PROJECT_ID"

# Get function URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --gen2 \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(serviceConfig.uri)")

echo
print_info "Deployment completed successfully!"
print_info "Function URL: $FUNCTION_URL"
echo
print_info "To test the function, run:"
echo "  curl -X POST $FUNCTION_URL/wbs-create \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"template_url\": \"https://example.backlog.com/view/PROJ-1\", \"project_key\": \"PROJ\"}'"
echo
print_info "To view logs, run:"
echo "  gcloud functions logs read $FUNCTION_NAME --gen2 --region=$REGION --limit=50"
