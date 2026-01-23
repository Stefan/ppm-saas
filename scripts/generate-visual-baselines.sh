#!/bin/bash

# Visual Regression Baseline Generation Script
# Requirement 4.1: Generate baseline screenshots for all main pages
# Requirement 4.4: Support updating baseline screenshots

set -e

echo "🎨 Visual Regression Baseline Generation"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Playwright is installed
if ! command -v npx &> /dev/null; then
    echo -e "${RED}❌ Error: npx not found. Please install Node.js and npm.${NC}"
    exit 1
fi

# Check if Playwright browsers are installed
echo "📦 Checking Playwright browsers..."
if ! npx playwright --version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Playwright not found. Installing...${NC}"
    npm install -D @playwright/test
fi

# Install browsers if needed
echo "🌐 Installing Playwright browsers (if needed)..."
npx playwright install --with-deps chromium firefox webkit

echo ""
echo "🚀 Starting baseline generation..."
echo ""

# Parse command line arguments
PROJECT=""
PAGE=""
UPDATE_MODE="--update-snapshots"

while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --page)
            PAGE="$2"
            shift 2
            ;;
        --check)
            UPDATE_MODE=""
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project <name>   Generate baselines for specific project only"
            echo "  --page <name>      Generate baselines for specific page only"
            echo "  --check            Check baselines without updating"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Generate all baselines"
            echo "  $0 --project chromium-desktop         # Generate for desktop Chrome only"
            echo "  $0 --page dashboard                   # Generate for dashboard page only"
            echo "  $0 --check                            # Check without updating"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build the Playwright command
PLAYWRIGHT_CMD="npx playwright test --grep='@visual'"

if [ -n "$PROJECT" ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=$PROJECT"
    echo "📱 Generating baselines for project: $PROJECT"
fi

if [ -n "$PAGE" ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --grep='$PAGE'"
    echo "📄 Generating baselines for page: $PAGE"
fi

if [ -n "$UPDATE_MODE" ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD $UPDATE_MODE"
    echo "✏️  Update mode: ON"
else
    echo "🔍 Check mode: ON (no updates)"
fi

echo ""
echo "Running: $PLAYWRIGHT_CMD"
echo ""

# Run the command
if eval $PLAYWRIGHT_CMD; then
    echo ""
    echo -e "${GREEN}✅ Baseline generation completed successfully!${NC}"
    echo ""
    
    if [ -n "$UPDATE_MODE" ]; then
        echo "📸 Baseline screenshots have been saved to:"
        echo "   __tests__/e2e/visual-regression.spec.ts-snapshots/"
        echo ""
        echo "Next steps:"
        echo "1. Review the generated screenshots"
        echo "2. Run 'npm run test:visual' to verify"
        echo "3. Commit the screenshots to version control:"
        echo "   git add __tests__/e2e/visual-regression.spec.ts-snapshots/"
        echo "   git commit -m 'Add visual regression baselines'"
    else
        echo "✅ All visual regression tests passed!"
    fi
else
    echo ""
    echo -e "${RED}❌ Baseline generation failed!${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Ensure development server is running: npm run dev"
    echo "2. Check Playwright report: npm run test:e2e:report"
    echo "3. Review error messages above"
    exit 1
fi

echo ""
