#!/bin/bash
# 完全自動セットアップ＆デプロイスクリプト
# GCPプロジェクトの設定からデプロイまでを一括実行

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

print_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}

# Banner
echo -e "${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   WBS Creation Service - GCP Setup & Deployment          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_success "gcloud CLI found!"
echo ""

# ============================================================================
# STEP 1: GCP Project Configuration
# ============================================================================
print_step "Step 1/7: GCP Project Configuration"
echo ""

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$CURRENT_PROJECT" ]; then
    print_warn "No GCP project is currently set."
    read -p "Enter your GCP Project ID: " PROJECT_ID

    # Check if project exists
    if gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        print_info "Project $PROJECT_ID found."
        gcloud config set project "$PROJECT_ID"
    else
        print_error "Project $PROJECT_ID not found."
        read -p "Do you want to create this project? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            gcloud projects create "$PROJECT_ID"
            gcloud config set project "$PROJECT_ID"
            print_success "Project created!"
            print_warn "Please enable billing for this project in the GCP Console:"
            echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
            read -p "Press Enter after enabling billing..."
        else
            print_error "Cannot proceed without a valid project."
            exit 1
        fi
    fi
else
    PROJECT_ID="$CURRENT_PROJECT"
    print_info "Using current project: $PROJECT_ID"
    read -p "Do you want to use this project? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your GCP Project ID: " PROJECT_ID
        gcloud config set project "$PROJECT_ID"
    fi
fi

print_success "GCP Project: $PROJECT_ID"
echo ""

# ============================================================================
# STEP 2: Collect API Keys and Configuration
# ============================================================================
print_step "Step 2/7: Collect API Keys and Configuration"
echo ""

# Backlog API Key
print_info "Backlog API Key is required."
echo "Get it from: https://your-space.backlog.com/PersonalSettings/userApiKeys"
read -sp "Enter Backlog API Key: " BACKLOG_API_KEY
echo ""
if [ -z "$BACKLOG_API_KEY" ]; then
    print_error "Backlog API Key is required."
    exit 1
fi

# Backlog Space URL
read -p "Enter Backlog Space URL (e.g., https://your-space.backlog.com): " BACKLOG_SPACE_URL
if [ -z "$BACKLOG_SPACE_URL" ]; then
    print_error "Backlog Space URL is required."
    exit 1
fi

# Notion API Key
print_info "Notion API Key is required."
echo "Get it from: https://www.notion.so/my-integrations"
read -sp "Enter Notion API Key: " NOTION_API_KEY
echo ""
if [ -z "$NOTION_API_KEY" ]; then
    print_error "Notion API Key is required."
    exit 1
fi

# CORS Settings
read -p "Enter allowed CORS origins (default: *): " ALLOWED_ORIGINS
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-*}"

# Region
read -p "Enter GCP region (default: asia-northeast1): " REGION
REGION="${REGION:-asia-northeast1}"

print_success "Configuration collected!"
echo ""

# ============================================================================
# STEP 3: Enable Required APIs
# ============================================================================
print_step "Step 3/7: Enable Required Google Cloud APIs"
echo ""

REQUIRED_APIS=(
    "cloudfunctions.googleapis.com"
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "firestore.googleapis.com"
    "storage.googleapis.com"
    "documentai.googleapis.com"
    "logging.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        print_info "API $api is already enabled"
    else
        print_warn "Enabling API: $api"
        gcloud services enable "$api" --project="$PROJECT_ID"
    fi
done

print_success "All required APIs enabled!"
echo ""

# ============================================================================
# STEP 4: Create Firestore Database
# ============================================================================
print_step "Step 4/7: Create Firestore Database"
echo ""

# Check if Firestore database already exists
if gcloud firestore databases list --project="$PROJECT_ID" --format="value(name)" 2>/dev/null | grep -q "(default)"; then
    print_info "Firestore database already exists"
else
    print_warn "Creating Firestore database in region: $REGION"

    # Create Firestore database
    if gcloud firestore databases create \
        --location="$REGION" \
        --type=firestore-native \
        --project="$PROJECT_ID"; then
        print_success "Firestore database created!"
    else
        print_error "Failed to create Firestore database."
        print_warn "You may need to create it manually in the GCP Console:"
        echo "https://console.cloud.google.com/firestore?project=$PROJECT_ID"
        read -p "Press Enter to continue (assuming Firestore is ready)..."
    fi
fi

echo ""

# ============================================================================
# STEP 5: Create Secrets in Secret Manager
# ============================================================================
print_step "Step 5/7: Create Secrets in Secret Manager"
echo ""

# Backlog API Key secret
if gcloud secrets describe backlog-api-key --project="$PROJECT_ID" &>/dev/null; then
    print_warn "Secret 'backlog-api-key' already exists. Updating..."
    echo -n "$BACKLOG_API_KEY" | gcloud secrets versions add backlog-api-key \
        --data-file=- \
        --project="$PROJECT_ID"
else
    print_info "Creating secret: backlog-api-key"
    echo -n "$BACKLOG_API_KEY" | gcloud secrets create backlog-api-key \
        --replication-policy="automatic" \
        --data-file=- \
        --project="$PROJECT_ID"
fi

# Notion API Key secret
if gcloud secrets describe notion-api-key --project="$PROJECT_ID" &>/dev/null; then
    print_warn "Secret 'notion-api-key' already exists. Updating..."
    echo -n "$NOTION_API_KEY" | gcloud secrets versions add notion-api-key \
        --data-file=- \
        --project="$PROJECT_ID"
else
    print_info "Creating secret: notion-api-key"
    echo -n "$NOTION_API_KEY" | gcloud secrets create notion-api-key \
        --replication-policy="automatic" \
        --data-file=- \
        --project="$PROJECT_ID"
fi

print_success "Secrets created in Secret Manager!"
echo ""

# ============================================================================
# STEP 6: Create GCS Bucket
# ============================================================================
print_step "Step 6/7: Create GCS Bucket for Data Storage"
echo ""

BUCKET_NAME="${PROJECT_ID}-wbs-data"

if gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null; then
    print_info "Bucket $BUCKET_NAME already exists"
else
    print_warn "Creating bucket: $BUCKET_NAME"
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$BUCKET_NAME"
    print_success "Bucket created!"
fi

echo ""

# ============================================================================
# STEP 7: Run Tests Before Deployment
# ============================================================================
print_step "Step 7/7: Run Tests Before Deployment"
echo ""

print_info "Running unit tests with coverage check..."

if python -m pytest tests/unit -v --cov=src --cov-fail-under=80; then
    print_success "All tests passed with sufficient coverage!"
else
    print_error "Tests failed or coverage below 80%."
    read -p "Do you want to continue deployment anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled."
        exit 1
    fi
fi

echo ""

# ============================================================================
# FINAL CONFIRMATION
# ============================================================================
print_step "Ready to Deploy!"
echo ""
echo "Configuration Summary:"
echo "  Project ID:     $PROJECT_ID"
echo "  Region:         $REGION"
echo "  Backlog URL:    $BACKLOG_SPACE_URL"
echo "  CORS Origins:   $ALLOWED_ORIGINS"
echo "  GCS Bucket:     $BUCKET_NAME"
echo ""

read -p "Deploy Cloud Function now? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warn "Deployment cancelled by user."
    exit 0
fi

# ============================================================================
# DEPLOYMENT
# ============================================================================
print_step "Deploying to Cloud Functions..."
echo ""

FUNCTION_NAME="wbs-creation-service"
RUNTIME="python311"
ENTRY_POINT="wbs_create"
MEMORY="512Mi"
TIMEOUT="540"
MAX_INSTANCES="10"

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
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,BACKLOG_SPACE_URL=$BACKLOG_SPACE_URL,ALLOWED_ORIGINS=$ALLOWED_ORIGINS,ENVIRONMENT=production,GCS_BUCKET=$BUCKET_NAME" \
    --set-secrets="BACKLOG_API_KEY=backlog-api-key:latest,NOTION_API_KEY=notion-api-key:latest" \
    --project="$PROJECT_ID"

# Get function URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --gen2 \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(serviceConfig.uri)")

echo ""
print_success "Deployment completed successfully!"
echo ""

# ============================================================================
# POST-DEPLOYMENT VERIFICATION
# ============================================================================
print_step "Post-Deployment Verification"
echo ""

print_info "Testing health check endpoint..."
if curl -s "$FUNCTION_URL/health" | grep -q "healthy"; then
    print_success "Health check passed!"
else
    print_warn "Health check may have failed. Check logs for details."
fi

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                           ║${NC}"
echo -e "${CYAN}║              🎉 DEPLOYMENT SUCCESSFUL! 🎉                 ║${NC}"
echo -e "${CYAN}║                                                           ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Function URL:${NC}"
echo "  $FUNCTION_URL"
echo ""
echo -e "${GREEN}Quick Test:${NC}"
echo "  # Health Check"
echo "  curl $FUNCTION_URL/health"
echo ""
echo "  # WBS Creation (replace with your actual Backlog issue)"
echo "  curl -X POST $FUNCTION_URL/wbs-create \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{"
echo "      \"template_url\": \"$BACKLOG_SPACE_URL/view/PROJ-1\","
echo "      \"project_key\": \"PROJ\""
echo "    }'"
echo ""
echo -e "${GREEN}View Logs:${NC}"
echo "  gcloud functions logs read $FUNCTION_NAME --gen2 --region=$REGION --limit=50"
echo ""
echo -e "${GREEN}GCP Console:${NC}"
echo "  https://console.cloud.google.com/functions/details/$REGION/$FUNCTION_NAME?project=$PROJECT_ID"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NOTES:${NC}"
echo "  - Current MCP SDK integration is placeholder (uses await asyncio.sleep)"
echo "  - For production use, implement actual Backlog/Notion MCP SDK calls"
echo "  - Update ALLOWED_ORIGINS for production (currently: $ALLOWED_ORIGINS)"
echo ""
