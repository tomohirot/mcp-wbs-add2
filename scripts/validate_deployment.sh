#!/bin/bash
# Deployment validation script

set -e

echo "=== WBS Creation MCP Server - Deployment Validation ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if venv exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "${RED}✗ Virtual environment not found${NC}"
    echo "  Run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check dependencies
echo ""
echo "Checking dependencies..."
pip install -q -r requirements.txt
echo "✓ All dependencies installed"

# Run unit tests
echo ""
echo "Running unit tests..."
if pytest tests/unit -v --tb=short -q; then
    echo "${GREEN}✓ Unit tests passed${NC}"
else
    echo "${RED}✗ Unit tests failed${NC}"
    exit 1
fi

# Check test coverage
echo ""
echo "Checking test coverage..."
if pytest tests/unit --cov=src --cov-report=term --cov-fail-under=80 -q; then
    echo "${GREEN}✓ Test coverage >= 80%${NC}"
else
    echo "${RED}✗ Test coverage < 80%${NC}"
    exit 1
fi

# Check configuration files
echo ""
echo "Checking configuration files..."
required_files=(
    "config/categories.yaml"
    "config/issue_types.yaml"
    "config/settings.yaml"
    "requirements.txt"
    ".env.example"
    ".gcloudignore"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "${RED}✗ $file missing${NC}"
        exit 1
    fi
done

# Check .env file
echo ""
if [ -f ".env" ]; then
    echo "✓ .env file exists"

    # Check required environment variables
    required_vars=(
        "GCP_PROJECT_ID"
        "GCS_BUCKET_NAME"
        "BACKLOG_SPACE_URL"
        "BACKLOG_API_KEY"
    )

    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo "✓ $var is set"
        else
            echo "${RED}✗ $var not set in .env${NC}"
            exit 1
        fi
    done
else
    echo "${RED}✗ .env file not found${NC}"
    echo "  Copy .env.example to .env and fill in values"
    exit 1
fi

# Check source structure
echo ""
echo "Checking source structure..."
required_dirs=(
    "src/models"
    "src/utils"
    "src/storage"
    "src/processors"
    "src/integrations"
    "src/services"
    "src/mcp"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir exists"
    else
        echo "${RED}✗ $dir missing${NC}"
        exit 1
    fi
done

# Validate Python syntax
echo ""
echo "Validating Python syntax..."
if python3 -m py_compile src/**/*.py 2>/dev/null; then
    echo "✓ All Python files have valid syntax"
else
    echo "${RED}✗ Python syntax errors found${NC}"
    exit 1
fi

# Final summary
echo ""
echo "${GREEN}========================================${NC}"
echo "${GREEN}✓ All validation checks passed!${NC}"
echo "${GREEN}========================================${NC}"
echo ""
echo "Ready for deployment to Cloud Functions."
echo ""
echo "Next steps:"
echo "1. Review deployment configuration"
echo "2. Deploy with: gcloud functions deploy wbs-create ..."
echo "3. Test deployed function"
echo "4. Monitor logs and metrics"
