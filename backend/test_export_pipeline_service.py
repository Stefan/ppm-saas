"""
Test Export Pipeline Service
"""

import pytest
import os
import tempfile
from datetime import datetime, date
from uuid import uuid4
from decimal import Decimal

# Import service and models
from services.export_pipeline_service import ExportPipelineService
from models.pmr import (
    PMRReport, PMRStatus, ExportFormat,
    EnhancedAIInsight, AIInsightType, AIInsightCategory, AIInsightPriority
)


@pytest.fixture
def export_service():
    """Create export service with temp directory"""
    temp_dir = tempfile.mkdtemp()
    service = ExportPipelineService(storage_path=temp_dir)
    yield service
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_report():
    """Create sample PMR report"""
    report_id = uuid4()
    project_id = uuid4()
    
    return PMRReport(
        id=report_id,
        project_id=project_id,
        report_month=date(2024, 1, 1),
        report_year=2024,
        template_id=uuid4(),
        title="Test Project Monthly Report",
        executive_summary="This is a test executive summary for the project.",
        ai_generated_insights=[],
        sections=[
            {
                "title": "Budget Analysis",
                "content": "Budget is on track with 85% utilization."
            },
            {
                "title": "Schedule Performance",
                "content": "Project is 2 days ahead of schedule."
            }
        ],
        metrics={
            "budget_utilization": 0.85,
            "schedule_performance": 1.05,
            "risk_score": 0.23
        },
        visualizations=[],
        status=PMRStatus.approved,
        generated_by=uuid4(),
        approved_by=uuid4(),
        generated_at=datetime.utcnow(),
        last_modified=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        version=1,
        is_active=True
    )


@pytest.fixture
def sample_insights():
    """Create sample AI insights"""
    report_id = uuid4()
    
    return [
        EnhancedAIInsight(
            report_id=report_id,
            insight_type=AIInsightType.prediction,
            category=AIInsightCategory.budget,
            title="Budget Variance Prediction",
            content="Project is likely to finish 8% under budget based on current trends.",
            confidence_score=Decimal("0.87"),
            supporting_data={"historical_variance": [-0.02, 0.05, -0.03]},
            predicted_impact="Positive budget variance of approximately $50,000",
            recommended_actions=[
                "Consider reallocating surplus budget to quality improvements",
                "Evaluate opportunities for scope expansion"
            ],
            priority=AIInsightPriority.high,
            validated=True
        ),
        EnhancedAIInsight(
            report_id=report_id,
            insight_type=AIInsightType.recommendation,
            category=AIInsightCategory.schedule,
            title="Schedule Optimization Opportunity",
            content="Critical path can be optimized by parallelizing tasks A and B.",
            confidence_score=Decimal("0.92"),
            supporting_data={"task_dependencies": ["A", "B"]},
            predicted_impact="Potential 3-day schedule improvement",
            recommended_actions=[
                "Review task dependencies with project team",
                "Allocate additional resources to enable parallelization"
            ],
            priority=AIInsightPriority.medium,
            validated=False
        )
    ]


@pytest.mark.asyncio
async def test_export_pdf(export_service, sample_report, sample_insights):
    """Test PDF export functionality"""
    result = await export_service.export_report(
        report=sample_report,
        export_format=ExportFormat.pdf,
        insights=sample_insights
    )
    
    assert result["status"] == "completed"
    assert result["format"] == "pdf"
    assert os.path.exists(result["file_path"])
    assert result["file_size"] > 0
    assert result["filename"].endswith(".pdf")


@pytest.mark.asyncio
async def test_export_excel(export_service, sample_report, sample_insights):
    """Test Excel export functionality"""
    result = await export_service.export_report(
        report=sample_report,
        export_format=ExportFormat.excel,
        insights=sample_insights
    )
    
    assert result["status"] == "completed"
    assert result["format"] == "excel"
    assert os.path.exists(result["file_path"])
    assert result["file_size"] > 0
    assert result["filename"].endswith(".xlsx")


@pytest.mark.asyncio
async def test_export_powerpoint(export_service, sample_report, sample_insights):
    """Test PowerPoint export functionality"""
    result = await export_service.export_report(
        report=sample_report,
        export_format=ExportFormat.powerpoint,
        insights=sample_insights
    )
    
    assert result["status"] == "completed"
    assert result["format"] == "powerpoint"
    assert os.path.exists(result["file_path"])
    assert result["file_size"] > 0
    assert result["filename"].endswith(".pptx")


@pytest.mark.asyncio
async def test_export_word(export_service, sample_report, sample_insights):
    """Test Word export functionality"""
    result = await export_service.export_report(
        report=sample_report,
        export_format=ExportFormat.word,
        insights=sample_insights
    )
    
    assert result["status"] == "completed"
    assert result["format"] == "word"
    assert os.path.exists(result["file_path"])
    assert result["file_size"] > 0
    assert result["filename"].endswith(".docx")


@pytest.mark.asyncio
async def test_export_with_branding(export_service, sample_report):
    """Test export with branding configuration"""
    template_config = {
        "branding": {
            "logo_url": "https://example.com/logo.png",
            "color_scheme": "corporate_blue",
            "company_name": "Test Company Inc."
        }
    }
    
    result = await export_service.export_report(
        report=sample_report,
        export_format=ExportFormat.pdf,
        template_config=template_config
    )
    
    assert result["status"] == "completed"
    assert os.path.exists(result["file_path"])


@pytest.mark.asyncio
async def test_export_without_insights(export_service, sample_report):
    """Test export without AI insights"""
    result = await export_service.export_report(
        report=sample_report,
        export_format=ExportFormat.pdf,
        insights=None
    )
    
    assert result["status"] == "completed"
    assert os.path.exists(result["file_path"])


def test_get_export_status(export_service, sample_report):
    """Test getting export status"""
    # Create a dummy file
    test_file = os.path.join(export_service.storage_path, "test_export.pdf")
    with open(test_file, 'wb') as f:
        f.write(b"test content")
    
    status = export_service.get_export_status(test_file)
    
    assert status["exists"] is True
    assert status["status"] == "completed"
    assert status["file_size"] > 0
    assert "modified_at" in status


def test_cleanup_export(export_service):
    """Test cleaning up export files"""
    # Create a dummy file
    test_file = os.path.join(export_service.storage_path, "test_export.pdf")
    with open(test_file, 'wb') as f:
        f.write(b"test content")
    
    assert os.path.exists(test_file)
    
    result = export_service.cleanup_export(test_file)
    
    assert result is True
    assert not os.path.exists(test_file)


def test_list_exports(export_service):
    """Test listing export files"""
    # Create some dummy files
    for i in range(3):
        filename = f"pmr_report_test{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path = os.path.join(export_service.storage_path, filename)
        with open(file_path, 'wb') as f:
            f.write(b"test content")
    
    exports = export_service.list_exports()
    
    assert len(exports) >= 3
    assert all("filename" in exp for exp in exports)
    assert all("file_size" in exp for exp in exports)
    assert all("format" in exp for exp in exports)


@pytest.mark.asyncio
async def test_unsupported_format(export_service, sample_report):
    """Test handling of unsupported export format"""
    # This should raise an error for unsupported format
    with pytest.raises(ValueError):
        await export_service.export_report(
            report=sample_report,
            export_format="unsupported_format",  # Invalid format
            insights=None
        )


def test_filename_generation(export_service):
    """Test filename generation"""
    report_id = str(uuid4())
    filename = export_service._generate_filename(report_id, "pdf")
    
    assert filename.startswith("pmr_report_")
    assert filename.endswith(".pdf")
    assert report_id[:8] in filename


@pytest.mark.asyncio
async def test_html_template_generation(export_service, sample_report, sample_insights):
    """Test HTML template generation for PDF"""
    export_data = export_service._prepare_export_data(
        report=sample_report,
        insights=sample_insights
    )
    
    html = export_service._generate_html_template(export_data)
    
    assert sample_report.title in html
    assert "Executive Summary" in html
    assert "AI-Powered Insights" in html
    assert sample_insights[0].title in html


def test_excel_structure_creation(export_service, sample_report, sample_insights):
    """Test Excel structure creation"""
    export_data = export_service._prepare_export_data(
        report=sample_report,
        insights=sample_insights
    )
    
    structure = export_service._create_excel_structure(export_data)
    
    assert "workbook_name" in structure
    assert "sheets" in structure
    assert len(structure["sheets"]) > 0
    assert any(sheet["name"] == "Summary" for sheet in structure["sheets"])
    assert any(sheet["name"] == "AI Insights" for sheet in structure["sheets"])


def test_powerpoint_structure_creation(export_service, sample_report, sample_insights):
    """Test PowerPoint structure creation"""
    export_data = export_service._prepare_export_data(
        report=sample_report,
        insights=sample_insights
    )
    
    structure = export_service._create_powerpoint_structure(export_data)
    
    assert "presentation_name" in structure
    assert "slides" in structure
    assert len(structure["slides"]) > 0
    assert structure["slides"][0]["type"] == "title"


def test_word_structure_creation(export_service, sample_report, sample_insights):
    """Test Word document structure creation"""
    export_data = export_service._prepare_export_data(
        report=sample_report,
        insights=sample_insights
    )
    
    structure = export_service._create_word_structure(export_data)
    
    assert "document_name" in structure
    assert "sections" in structure
    assert len(structure["sections"]) > 0
    assert structure["sections"][0]["type"] == "title"
