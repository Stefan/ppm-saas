"""
Test Enhanced PMR Models
Validates the new AI-powered, collaborative PMR models
"""

import pytest
from datetime import datetime, date
from uuid import uuid4
from decimal import Decimal

from models.pmr import (
    # Enhanced models
    EnhancedPMRReport,
    AIInsightEngine,
    EnhancedAIInsight,
    CollaborationSession,
    CollaborationParticipant,
    Comment,
    ChangeEvent,
    MonteCarloResults,
    RealTimeMetrics,
    # Enums
    AIInsightType,
    AIInsightCategory,
    AIInsightPriority,
    ValidationStatus,
    SessionType,
    ParticipantRole,
    ChangeEventType,
    PMRStatus,
)


class TestAIInsightEngine:
    """Test AI Insight Engine model"""

    def test_create_ai_insight_engine_with_defaults(self):
        """Test creating AI insight engine with default values"""
        engine = AIInsightEngine()
        
        assert engine.model_version == "gpt-4"
        assert engine.temperature == Decimal("0.7")
        assert engine.confidence_threshold == Decimal("0.7")
        assert engine.enable_predictions is True
        assert engine.enable_recommendations is True
        assert engine.enable_alerts is True
        assert len(engine.insight_categories_enabled) == 5

    def test_create_ai_insight_engine_with_custom_values(self):
        """Test creating AI insight engine with custom values"""
        engine = AIInsightEngine(
            model_version="gpt-4-turbo",
            temperature=Decimal("0.5"),
            confidence_threshold=Decimal("0.8"),
            max_insights_per_category=10
        )
        
        assert engine.model_version == "gpt-4-turbo"
        assert engine.temperature == Decimal("0.5")
        assert engine.confidence_threshold == Decimal("0.8")
        assert engine.max_insights_per_category == 10

    def test_validate_temperature_range(self):
        """Test temperature validation"""
        with pytest.raises(ValueError, match="Temperature must be between"):
            AIInsightEngine(temperature=Decimal("3.0"))

    def test_validate_confidence_threshold_range(self):
        """Test confidence threshold validation"""
        with pytest.raises(ValueError, match="Confidence threshold must be between"):
            AIInsightEngine(confidence_threshold=Decimal("1.5"))


class TestEnhancedAIInsight:
    """Test Enhanced AI Insight model"""

    def test_create_enhanced_ai_insight(self):
        """Test creating an enhanced AI insight"""
        report_id = uuid4()
        insight = EnhancedAIInsight(
            report_id=report_id,
            insight_type=AIInsightType.prediction,
            category=AIInsightCategory.budget,
            title="Budget Variance Prediction",
            content="Project likely to finish 8% under budget",
            confidence_score=Decimal("0.87")
        )
        
        assert insight.report_id == report_id
        assert insight.insight_type == AIInsightType.prediction
        assert insight.category == AIInsightCategory.budget
        assert insight.confidence_score == Decimal("0.87")
        assert insight.validation_status == ValidationStatus.pending
        assert insight.validated is False

    def test_enhanced_ai_insight_with_validation(self):
        """Test AI insight with validation metadata"""
        user_id = uuid4()
        insight = EnhancedAIInsight(
            report_id=uuid4(),
            insight_type=AIInsightType.recommendation,
            category=AIInsightCategory.schedule,
            title="Schedule Optimization",
            content="Consider reallocating resources",
            confidence_score=Decimal("0.92"),
            validation_status=ValidationStatus.validated,
            validated_by=user_id,
            feedback_score=Decimal("4.5"),
            impact_score=Decimal("0.85")
        )
        
        assert insight.validation_status == ValidationStatus.validated
        assert insight.validated_by == user_id
        assert insight.feedback_score == Decimal("4.5")
        assert insight.impact_score == Decimal("0.85")


class TestCollaborationModels:
    """Test Collaboration models"""

    def test_create_collaboration_participant(self):
        """Test creating a collaboration participant"""
        user_id = uuid4()
        participant = CollaborationParticipant(
            user_id=user_id,
            user_name="John Doe",
            user_email="john@example.com",
            role=ParticipantRole.editor
        )
        
        assert participant.user_id == user_id
        assert participant.user_name == "John Doe"
        assert participant.role == ParticipantRole.editor
        assert participant.is_online is True

    def test_create_comment(self):
        """Test creating a comment"""
        user_id = uuid4()
        comment = Comment(
            section_id="executive_summary",
            user_id=user_id,
            user_name="Jane Smith",
            content="Consider adding more detail"
        )
        
        assert comment.section_id == "executive_summary"
        assert comment.user_id == user_id
        assert comment.content == "Consider adding more detail"
        assert comment.resolved is False

    def test_comment_content_validation(self):
        """Test comment content validation"""
        with pytest.raises(ValueError, match="Comment content cannot be empty"):
            Comment(
                section_id="test",
                user_id=uuid4(),
                user_name="Test User",
                content="   "
            )

    def test_create_change_event(self):
        """Test creating a change event"""
        user_id = uuid4()
        event = ChangeEvent(
            event_type=ChangeEventType.section_update,
            user_id=user_id,
            user_name="John Doe",
            section_id="budget_analysis",
            changes={"content": "Updated budget forecast"}
        )
        
        assert event.event_type == ChangeEventType.section_update
        assert event.user_id == user_id
        assert event.section_id == "budget_analysis"

    def test_create_collaboration_session(self):
        """Test creating a collaboration session"""
        report_id = uuid4()
        session = CollaborationSession(
            report_id=report_id,
            session_type=SessionType.collaborative,
            max_participants=10
        )
        
        assert session.report_id == report_id
        assert session.session_type == SessionType.collaborative
        assert session.max_participants == 10
        assert session.is_active is True
        assert len(session.participants) == 0

    def test_add_participant_to_session(self):
        """Test adding a participant to a collaboration session"""
        session = CollaborationSession(
            report_id=uuid4(),
            max_participants=5
        )
        
        participant = CollaborationParticipant(
            user_id=uuid4(),
            user_name="John Doe",
            user_email="john@example.com",
            role=ParticipantRole.editor
        )
        
        result = session.add_participant(participant)
        assert result is True
        assert len(session.participants) == 1

    def test_add_duplicate_participant(self):
        """Test adding duplicate participant fails"""
        session = CollaborationSession(report_id=uuid4())
        user_id = uuid4()
        
        participant1 = CollaborationParticipant(
            user_id=user_id,
            user_name="John Doe",
            user_email="john@example.com",
            role=ParticipantRole.editor
        )
        
        participant2 = CollaborationParticipant(
            user_id=user_id,
            user_name="John Doe",
            user_email="john@example.com",
            role=ParticipantRole.editor
        )
        
        session.add_participant(participant1)
        result = session.add_participant(participant2)
        
        assert result is False
        assert len(session.participants) == 1

    def test_remove_participant_from_session(self):
        """Test removing a participant from a collaboration session"""
        session = CollaborationSession(report_id=uuid4())
        user_id = uuid4()
        
        participant = CollaborationParticipant(
            user_id=user_id,
            user_name="John Doe",
            user_email="john@example.com",
            role=ParticipantRole.editor
        )
        
        session.add_participant(participant)
        result = session.remove_participant(user_id)
        
        assert result is True
        assert len(session.participants) == 0


class TestMonteCarloResults:
    """Test Monte Carlo Results model"""

    def test_create_monte_carlo_results(self):
        """Test creating Monte Carlo results"""
        results = MonteCarloResults(
            analysis_type="budget_variance",
            iterations=10000,
            budget_completion={
                "p50": Decimal("0.92"),
                "p80": Decimal("0.96"),
                "p95": Decimal("1.02")
            }
        )
        
        assert results.analysis_type == "budget_variance"
        assert results.iterations == 10000
        assert results.budget_completion["p50"] == Decimal("0.92")


class TestRealTimeMetrics:
    """Test Real-Time Metrics model"""

    def test_create_real_time_metrics(self):
        """Test creating real-time metrics"""
        metrics = RealTimeMetrics(
            budget_utilization=Decimal("0.78"),
            schedule_performance_index=Decimal("1.12"),
            risk_score=Decimal("0.23"),
            active_issues_count=5
        )
        
        assert metrics.budget_utilization == Decimal("0.78")
        assert metrics.schedule_performance_index == Decimal("1.12")
        assert metrics.risk_score == Decimal("0.23")
        assert metrics.active_issues_count == 5

    def test_validate_risk_score_range(self):
        """Test risk score validation"""
        with pytest.raises(ValueError, match="Score must be between"):
            RealTimeMetrics(risk_score=Decimal("1.5"))


class TestEnhancedPMRReport:
    """Test Enhanced PMR Report model"""

    def test_create_enhanced_pmr_report(self):
        """Test creating an enhanced PMR report"""
        project_id = uuid4()
        template_id = uuid4()
        generated_by = uuid4()
        
        report = EnhancedPMRReport(
            project_id=project_id,
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=template_id,
            title="Project Alpha Monthly Report",
            generated_by=generated_by,
            collaboration_enabled=True,
            monte_carlo_enabled=True
        )
        
        assert report.project_id == project_id
        assert report.title == "Project Alpha Monthly Report"
        assert report.collaboration_enabled is True
        assert report.monte_carlo_enabled is True
        assert report.status == PMRStatus.draft
        assert len(report.ai_insights) == 0

    def test_add_ai_insight_to_report(self):
        """Test adding an AI insight to a report"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        insight = EnhancedAIInsight(
            report_id=report.id,
            insight_type=AIInsightType.prediction,
            category=AIInsightCategory.budget,
            title="Test Insight",
            content="Test content",
            confidence_score=Decimal("0.85")
        )
        
        report.add_ai_insight(insight)
        
        assert len(report.ai_insights) == 1
        assert report.last_ai_update is not None

    def test_update_real_time_metrics(self):
        """Test updating real-time metrics"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        metrics = RealTimeMetrics(
            budget_utilization=Decimal("0.75"),
            risk_score=Decimal("0.30")
        )
        
        report.update_real_time_metrics(metrics)
        
        assert report.real_time_metrics is not None
        assert report.real_time_metrics.budget_utilization == Decimal("0.75")

    def test_start_collaboration_session(self):
        """Test starting a collaboration session"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        session = CollaborationSession(
            report_id=report.id,
            session_type=SessionType.collaborative
        )
        
        report.start_collaboration_session(session)
        
        assert report.collaboration_session is not None
        assert report.collaboration_enabled is True
        assert report.last_collaboration_activity is not None

    def test_end_collaboration_session(self):
        """Test ending a collaboration session"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        session = CollaborationSession(
            report_id=report.id,
            session_type=SessionType.collaborative
        )
        
        report.start_collaboration_session(session)
        report.end_collaboration_session()
        
        assert report.collaboration_session.is_active is False
        assert report.collaboration_enabled is False

    def test_add_export_record(self):
        """Test adding an export record"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        report.add_export_record("pdf", "https://example.com/report.pdf", 1024000)
        
        assert len(report.export_history) == 1
        assert report.export_history[0]["format"] == "pdf"
        assert report.export_history[0]["file_size"] == 1024000

    def test_increment_edit_count(self):
        """Test incrementing edit count"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        initial_count = report.total_edits
        report.increment_edit_count()
        
        assert report.total_edits == initial_count + 1

    def test_add_audit_entry(self):
        """Test adding an audit entry"""
        report = EnhancedPMRReport(
            project_id=uuid4(),
            report_month=date(2024, 1, 1),
            report_year=2024,
            template_id=uuid4(),
            title="Test Report",
            generated_by=uuid4()
        )
        
        user_id = uuid4()
        report.add_audit_entry(
            "section_updated",
            user_id,
            {"section": "executive_summary", "change": "content update"}
        )
        
        assert len(report.audit_log) == 1
        assert report.audit_log[0]["action"] == "section_updated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
