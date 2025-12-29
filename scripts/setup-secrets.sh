#!/bin/bash
# Setup Script for Secret Manager
# This script creates and updates secrets in Google Secret Manager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

print_info "Using GCP project: $PROJECT_ID"

# Check if required APIs are enabled
print_info "Checking if Secret Manager API is enabled..."
if ! gcloud services list --enabled --filter="name:secretmanager.googleapis.com" --format="value(name)" | grep -q secretmanager; then
    print_warn "Secret Manager API is not enabled. Enabling now..."
    gcloud services enable secretmanager.googleapis.com
    print_info "Secret Manager API enabled successfully"
else
    print_info "Secret Manager API is already enabled"
fi

# Function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2

    print_info "Processing secret: $secret_name"

    # Check if secret exists
    if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
        print_warn "Secret $secret_name already exists. Updating with new version..."
        echo -n "$secret_value" | gcloud secrets versions add "$secret_name" \
            --project="$PROJECT_ID" \
            --data-file=-
        print_info "Secret $secret_name updated successfully"
    else
        print_info "Creating new secret: $secret_name"
        echo -n "$secret_value" | gcloud secrets create "$secret_name" \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" \
            --data-file=-
        print_info "Secret $secret_name created successfully"
    fi
}

# Main setup
print_info "Starting Secret Manager setup for WBS Creation Service"
echo

# Prompt for Backlog API Key
read -p "Enter Backlog API Key: " -s BACKLOG_API_KEY
echo
if [ -z "$BACKLOG_API_KEY" ]; then
    print_error "Backlog API Key cannot be empty"
    exit 1
fi
create_or_update_secret "backlog-api-key" "$BACKLOG_API_KEY"
echo

# Prompt for Backlog Space URL
read -p "Enter Backlog Space URL (e.g., https://your-space.backlog.com): " BACKLOG_SPACE_URL
if [ -z "$BACKLOG_SPACE_URL" ]; then
    print_error "Backlog Space URL cannot be empty"
    exit 1
fi
create_or_update_secret "backlog-space-url" "$BACKLOG_SPACE_URL"
echo

# Prompt for Notion API Key
read -p "Enter Notion API Key (starts with secret_): " -s NOTION_API_KEY
echo
if [ -z "$NOTION_API_KEY" ]; then
    print_error "Notion API Key cannot be empty"
    exit 1
fi
create_or_update_secret "notion-api-key" "$NOTION_API_KEY"
echo

print_info "All secrets have been configured successfully!"
echo
print_info "To grant a service account access to these secrets, run:"
echo "  gcloud secrets add-iam-policy-binding SECRET_NAME \\"
echo "    --member='serviceAccount:SERVICE_ACCOUNT_EMAIL' \\"
echo "    --role='roles/secretmanager.secretAccessor'"
echo
print_info "Secret setup complete!"
