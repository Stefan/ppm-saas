# Export Pipeline Service

## Overview

The Export Pipeline Service provides multi-format export capabilities for Enhanced PMR (Project Monthly Report) reports. It supports professional-grade exports in PDF, Excel, PowerPoint, and Word formats with customizable templates and branding.

## Features

- **Multi-Format Support**: PDF, Excel (.xlsx), PowerPoint (.pptx), Word (.docx)
- **Professional Templates**: Customizable templates with branding options
- **AI Insights Integration**: Includes AI-generated insights in exports
- **Branding Customization**: Logo, color schemes, company information
- **Structured Data Export**: Organized sections, metrics, and visualizations
- **File Management**: List, status check, and cleanup of export files

## Installation

### Production Dependencies

For full functionality, install the following libraries:

```bash
# PDF generation
pip install weasyprint

# Excel generation with charts
pip install openpyxl

# PowerPoint generation
pip install python-pptx

# Word document generation
pip install python-docx
```

### Current Implementation

The service currently works with placeholder implementations that don't require external dependencies. This allows the service to function immediately while providing a clear upgrade path for production use.

## Usage

### Basic Export

```python
from services.export_pipeline_service import ExportPipelineService
from models.pmr import PMRReport, ExportFormat

# Initialize service
export_service = ExportPipelineService(storage_path="/path/to/exports")

# Export report as PDF
result = await export_service.export_report(
    report=pmr_report,
    export_format=ExportFormat.pdf,
    insights=ai_insights
)

print(f"Exported to: {result['file_path']}")
print(f"File size: {result['file_size']} bytes")
```

### Export with Branding

```python
# Configure branding
template_config = {
    "branding": {
        "logo_url": "https://company.com/logo.png",
        "color_scheme": "corporate_blue",  # or "professional_gray", "modern_green"
        "company_name": "Acme Corporation"
    }
}

# Export with branding
result = await export_service.export_report(
    report=pmr_report,
    export_format=ExportFormat.pdf,
    template_config=template_config,
    insights=ai_insights
)
```

### Export Options

```python
export_options = {
    "include_charts": True,
    "include_raw_data": False,
    "include_ai_insights": True
}

result = await export_service.export_report(
    report=pmr_report,
    export_format=ExportFormat.excel,
    export_options=export_options,
    insights=ai_insights
)
```

## Supported Formats

### PDF Export

- Professional HTML-based templates
- Customizable color schemes
- Logo and branding integration
- AI insights with confidence scores
- Metrics visualization
- Section-based organization

**Production**: Uses WeasyPrint for high-quality PDF generation

### Excel Export

- Multiple worksheets:
  - Summary sheet with report metadata
  - Metrics sheet with key performance indicators
  - AI Insights sheet with detailed analysis
  - Report Sections sheet with content
- Chart integration (production)
- Data tables with formatting

**Production**: Uses openpyxl for full Excel functionality with charts

### PowerPoint Export

- Title slide with report information
- Executive summary slide
- Key metrics slide
- AI insights slides (grouped by category)
- Section content slides
- Professional layouts

**Production**: Uses python-pptx for full PowerPoint functionality

### Word Export

- Formatted document with:
  - Title page with metadata
  - Heading hierarchy
  - Tables for metrics
  - Bullet lists for recommendations
  - Professional styling

**Production**: Uses python-docx for full Word functionality

## File Management

### Check Export Status

```python
status = export_service.get_export_status(file_path)
print(f"File exists: {status['exists']}")
print(f"File size: {status['file_size']}")
print(f"Modified: {status['modified_at']}")
```

### List All Exports

```python
# List all exports
exports = export_service.list_exports()

# List exports for specific report
exports = export_service.list_exports(report_id="123e4567-e89b-12d3-a456-426614174000")

for export in exports:
    print(f"{export['filename']} - {export['format']} - {export['file_size']} bytes")
```

### Cleanup Exports

```python
# Delete specific export
success = export_service.cleanup_export(file_path)

# Cleanup old exports (implement custom logic)
exports = export_service.list_exports()
for export in exports:
    # Delete exports older than 30 days
    if is_older_than_30_days(export['modified_at']):
        export_service.cleanup_export(export['file_path'])
```

## Color Schemes

The service supports three built-in color schemes:

### Corporate Blue (Default)
- Primary: #0066cc
- Secondary: #004080
- Accent: #66b3ff

### Professional Gray
- Primary: #333333
- Secondary: #666666
- Accent: #999999

### Modern Green
- Primary: #00a86b
- Secondary: #008055
- Accent: #66d9a8

## Template Structure

### PDF Template

The PDF template includes:
- Header with logo and company information
- Report metadata (period, status, version)
- Executive summary section
- AI insights with confidence scores
- Key metrics display
- Report sections
- Footer with generation timestamp

### Excel Structure

Workbook contains multiple sheets:
1. **Summary**: Report overview and executive summary
2. **Metrics**: Key performance indicators
3. **AI Insights**: Detailed AI analysis with confidence scores
4. **Report Sections**: Full report content

### PowerPoint Structure

Presentation includes:
1. **Title Slide**: Report title and period
2. **Executive Summary**: High-level overview
3. **Key Metrics**: Performance indicators
4. **Category Insights**: AI insights grouped by category
5. **Section Slides**: Detailed content

### Word Structure

Document contains:
1. **Title Page**: Report information and metadata
2. **Executive Summary**: Overview section
3. **Key Metrics Table**: Performance data
4. **AI Insights**: Detailed analysis with recommendations
5. **Report Sections**: Full content with proper formatting

## Error Handling

The service includes comprehensive error handling:

```python
try:
    result = await export_service.export_report(
        report=pmr_report,
        export_format=ExportFormat.pdf
    )
except ValueError as e:
    print(f"Invalid format or configuration: {e}")
except Exception as e:
    print(f"Export failed: {e}")
```

## Performance Considerations

- **Async Operations**: All export operations are async for better performance
- **File Storage**: Exports are stored in the configured storage path
- **Cleanup**: Implement regular cleanup of old exports to manage disk space
- **Caching**: Consider caching frequently accessed reports

## Integration with Enhanced PMR

The Export Pipeline Service integrates seamlessly with:

- **PMR Models**: Uses standard PMR report models
- **AI Insights Engine**: Includes AI-generated insights
- **Template System**: Supports custom templates
- **Export Job Tracking**: Can be integrated with job queue systems

## Future Enhancements

When production libraries are installed:

1. **PDF**: High-quality rendering with WeasyPrint
2. **Excel**: Interactive charts and advanced formatting
3. **PowerPoint**: Custom layouts and animations
4. **Word**: Advanced styling and document properties
5. **Batch Export**: Export multiple reports simultaneously
6. **Cloud Storage**: Integration with S3, Azure Blob, etc.
7. **Email Integration**: Direct email delivery of exports
8. **Watermarking**: Security watermarks for sensitive reports

## Testing

Run the test suite:

```bash
cd backend
python3 -m pytest test_export_pipeline_service.py -v
```

All tests should pass, validating:
- Export functionality for all formats
- Branding customization
- File management operations
- Error handling
- Template generation

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review the API documentation
3. Consult the Enhanced PMR specification documents
