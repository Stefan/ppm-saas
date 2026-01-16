# Automatic Documentation Detection and Updates

## The Problem

When new functionality is added to the application, the AI help chat won't automatically know about it. Someone needs to document the new feature and add it to the knowledge base. Without a systematic approach, documentation can quickly become outdated.

## The Solution

We've designed a multi-layered approach to keep documentation up-to-date:

### 1. **Automatic Feature Detection** (Tasks 25-25.1)

The system automatically scans your codebase to detect:
- New routes/pages in the Next.js app directory
- New API endpoints in FastAPI routers
- Changes to existing features

**How it works:**
```python
# Scans app directory for new routes
detected_routes = feature_detector.scan_nextjs_routes('app/')

# Scans backend for new API endpoints
detected_endpoints = feature_detector.scan_fastapi_routers('backend/routers/')

# Compares against knowledge base
gaps = gap_analyzer.find_undocumented_features(detected_routes, detected_endpoints)
```

### 2. **Documentation Gap Dashboard** (Tasks 26-26.1)

Admins get a dashboard showing:
- List of undocumented features
- Priority based on usage (how many users are accessing the feature)
- User queries about undocumented features
- Overall documentation coverage percentage

**Example:**
```
Documentation Coverage: 78% ⚠️

Undocumented Features:
┌─────────────────────────────┬──────────┬────────────┬─────────────────┐
│ Feature                     │ Priority │ Usage      │ User Queries    │
├─────────────────────────────┼──────────┼────────────┼─────────────────┤
│ /api/projects/export        │ HIGH     │ 150/day    │ 23 queries      │
│ /dashboards/custom-reports  │ MEDIUM   │ 45/day     │ 8 queries       │
│ /resources/bulk-assign      │ LOW      │ 12/day     │ 2 queries       │
└─────────────────────────────┴──────────┴────────────┴─────────────────┘
```

### 3. **Query-Based Gap Detection** (Tasks 27-27.1)

When users ask questions that the help chat can't answer well:
- The system logs these as potential documentation gaps
- Similar queries are clustered together
- Admins can see what users are asking about that isn't documented

**Example:**
```
Frequently Asked Questions (No Good Answer):
- "How do I export multiple projects at once?" (15 times)
- "Can I create custom dashboard widgets?" (12 times)
- "How to bulk assign resources to tasks?" (8 times)
```

### 4. **CI/CD Integration** (Tasks 28-28.1)

Add documentation checks to your deployment pipeline:

```yaml
# .github/workflows/check-docs.yml
name: Documentation Coverage Check

on: [pull_request]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check documentation coverage
        run: python backend/scripts/check_documentation_coverage.py --threshold 80
```

**Result:** Pull requests fail if documentation coverage drops below 80%

### 5. **Documentation Templates** (Tasks 29-29.1)

Speed up documentation creation with templates:

```typescript
// When you add a new CRUD feature
POST /admin/documentation/from-template
{
  "template": "crud_page",
  "variables": {
    "feature_name": "Project Templates",
    "route": "/templates",
    "actions": ["create", "edit", "delete", "duplicate"]
  }
}

// Generates a complete documentation page automatically
```

### 6. **Documentation-as-Code** (Tasks 30-30.1)

Write documentation directly in your code:

```typescript
/**
 * @feature Project Export
 * @category Projects
 * @description Allows users to export project data in multiple formats
 * 
 * ## How to Use
 * 1. Navigate to the project page
 * 2. Click the "Export" button in the top right
 * 3. Select your desired format (PDF, Excel, CSV)
 * 4. Click "Download"
 * 
 * ## Supported Formats
 * - PDF: Full project report with charts
 * - Excel: Detailed data with multiple sheets
 * - CSV: Raw data for analysis
 * 
 * @keywords export, download, report, pdf, excel, csv
 */
export function ProjectExportButton() {
  // Component code...
}
```

Or create adjacent markdown files:
```
app/
  projects/
    export/
      page.tsx
      page.docs.md  ← Documentation for this page
```

The system automatically extracts and indexes this documentation.

### 7. **Automatic Re-indexing** (Tasks 31-31.1)

Monitor a documentation directory for changes:

```
docs/
  features/
    projects.md          ← Edit this file
    resources.md
    financials.md
```

When you save changes, the system:
1. Detects the file modification
2. Re-parses the document
3. Regenerates embeddings
4. Updates the vector store
5. Help chat immediately knows about the changes

### 8. **Workflow Automation** (Tasks 32-32.1)

When a new feature is detected:

1. **Notification sent** to Slack/email:
   ```
   🆕 New feature detected: /api/projects/bulk-update
   📊 Usage: 45 requests in the last 24 hours
   📝 Action needed: Document this feature
   🔗 Create documentation: [Click here]
   ```

2. **GitHub issue created automatically**:
   ```
   Title: Document new feature: Bulk Project Update API
   
   A new API endpoint was detected that needs documentation:
   - Endpoint: POST /api/projects/bulk-update
   - Detected: 2026-01-16
   - Usage: 45 requests/day
   - Priority: HIGH
   
   Please create documentation covering:
   - What the feature does
   - How to use it
   - Required permissions
   - Example requests/responses
   ```

3. **Documentation workflow**:
   - Developer creates documentation (draft)
   - Tech writer reviews (review)
   - Admin approves (published)
   - System automatically indexes

## Recommended Workflow

### For New Features

1. **Developer adds feature** to the codebase
2. **Include JSDoc/docstring** with basic documentation
3. **CI/CD check runs** on pull request
4. **If coverage drops**, PR is blocked until documentation is added
5. **Developer adds documentation** using template or writes custom docs
6. **System auto-indexes** the new documentation
7. **Help chat immediately knows** about the new feature

### For Existing Features

1. **System detects undocumented feature** through usage analysis
2. **Notification sent** to documentation team
3. **GitHub issue created** automatically
4. **Documentation team prioritizes** based on usage and user queries
5. **Documentation created** using templates or from scratch
6. **System auto-indexes** and help chat is updated

## Configuration

```python
# backend/config/documentation.py

DOCUMENTATION_CONFIG = {
    # Feature detection
    "scan_interval": "1 hour",  # How often to scan for new features
    "scan_paths": ["app/", "backend/routers/"],
    
    # Coverage thresholds
    "minimum_coverage": 0.80,  # 80% of features must be documented
    "warning_coverage": 0.85,  # Warn when below 85%
    
    # Documentation sources
    "docs_directory": "docs/features/",
    "watch_for_changes": True,
    "extract_from_code": True,
    
    # Notifications
    "slack_webhook": "https://hooks.slack.com/...",
    "email_recipients": ["docs-team@company.com"],
    "create_github_issues": True,
    
    # Gap detection
    "low_confidence_threshold": 0.6,  # Log queries with confidence < 60%
    "min_queries_for_gap": 5,  # Flag as gap after 5 similar queries
}
```

## Benefits

✅ **Never miss documenting a feature** - Automatic detection catches everything
✅ **Prioritize what matters** - Focus on high-usage, frequently-asked-about features
✅ **Fast documentation creation** - Templates and code extraction speed up the process
✅ **Always up-to-date** - Automatic re-indexing keeps help chat current
✅ **Quality gates** - CI/CD checks prevent deploying undocumented features
✅ **Data-driven** - Know what users are asking about and can't find answers for

## Implementation Priority

**Phase 1 (Essential):**
- Tasks 25-27: Feature detection and gap analysis
- Provides visibility into what's undocumented

**Phase 2 (High Value):**
- Tasks 28-29: CI/CD integration and templates
- Prevents new undocumented features and speeds up documentation

**Phase 3 (Automation):**
- Tasks 30-31: Documentation-as-code and auto re-indexing
- Enables the most automated workflow

**Phase 4 (Polish):**
- Tasks 32-33: Workflow automation and notifications
- Makes the process seamless for the team

## Summary

While the AI help chat won't **automatically** know about new features, this system makes it **very easy** to keep documentation up-to-date by:

1. Automatically detecting what's undocumented
2. Showing you what users are asking about
3. Providing templates to speed up documentation
4. Allowing documentation in code comments
5. Auto-indexing when documentation changes
6. Blocking deployments if documentation is missing

The result: Your help chat stays current with minimal manual effort.
