"""
Basic unit tests for AuditService

These tests verify the core functionality of the audit service including
logging import start/complete events and graceful degradation on failures.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json

from services.audit_service import AuditService


class TestAuditService:
    """Test suite for AuditService"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database client"""
        db = Mock()
        db.table = Mock(return_value=Mock())
        return db
    
    @pytest.fixture
    def audit_service(self, mock_db):
        """Create an AuditService instance with mock database"""
        return AuditService(db_session=mock_db)
    
    @pytest.mark.asyncio
    async def test_log_import_start_success(self, audit_service, mock_db):
        """Test successful logging of import start"""
        # Arrange
        user_id = "user-123"
        import_method = "json"
        record_count = 5
        
        mock_response = Mock()
        mock_response.data = [{"id": "audit-123"}]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Act
        audit_id = await audit_service.log_import_start(user_id, import_method, record_count)
        
        # Assert
        assert audit_id is not None
        assert isinstance(audit_id, str)
        mock_db.table.assert_called_with("admin_audit_log")
        mock_db.table.return_value.insert.assert_called_once()
        
        # Verify the inserted data structure
        call_args = mock_db.table.return_value.insert.call_args[0][0]
        assert call_args["user_id"] == user_id
        assert call_args["action"] == "project_import"
        assert call_args["entity_type"] == "project"
        
        action_details = json.loads(call_args["action_details"])
        assert action_details["import_method"] == import_method
        assert action_details["record_count"] == record_count
    
    @pytest.mark.asyncio
    async def test_log_import_complete_success(self, audit_service, mock_db):
        """Test successful logging of import completion"""
        # Arrange
        audit_id = "audit-123"
        success = True
        imported_count = 5
        
        # Mock existing entry fetch
        mock_existing = Mock()
        mock_existing.data = [{
            "action_details": json.dumps({
                "import_method": "json",
                "record_count": 5
            })
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_existing
        
        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{"id": audit_id}]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        # Act
        await audit_service.log_import_complete(audit_id, success, imported_count)
        
        # Assert
        mock_db.table.return_value.update.assert_called_once()
        
        # Verify the update data structure
        call_args = mock_db.table.return_value.update.call_args[0][0]
        assert call_args["success"] == success
        assert "completed_at" in call_args
        
        action_details = json.loads(call_args["action_details"])
        assert action_details["imported_count"] == imported_count
        assert action_details["success"] == success
    
    @pytest.mark.asyncio
    async def test_log_import_complete_with_error(self, audit_service, mock_db):
        """Test logging import completion with error message"""
        # Arrange
        audit_id = "audit-123"
        success = False
        imported_count = 0
        error_message = "Validation failed for 3 records"
        
        # Mock existing entry fetch
        mock_existing = Mock()
        mock_existing.data = [{
            "action_details": json.dumps({
                "import_method": "csv",
                "record_count": 10
            })
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_existing
        
        # Mock update
        mock_update_response = Mock()
        mock_update_response.data = [{"id": audit_id}]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        # Act
        await audit_service.log_import_complete(audit_id, success, imported_count, error_message)
        
        # Assert
        call_args = mock_db.table.return_value.update.call_args[0][0]
        assert call_args["success"] == success
        assert call_args["error_message"] == error_message
        
        action_details = json.loads(call_args["action_details"])
        assert action_details["error_message"] == error_message
    
    @pytest.mark.asyncio
    async def test_log_import_start_graceful_failure(self, audit_service, mock_db):
        """Test graceful degradation when logging fails (Requirement 5.5)"""
        # Arrange
        user_id = "user-123"
        import_method = "json"
        record_count = 5
        
        # Make database insert fail
        mock_db.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")
        
        # Act - should not raise exception
        audit_id = await audit_service.log_import_start(user_id, import_method, record_count)
        
        # Assert - returns audit_id even on failure
        assert audit_id is not None
        assert isinstance(audit_id, str)
    
    @pytest.mark.asyncio
    async def test_log_import_complete_graceful_failure(self, audit_service, mock_db):
        """Test graceful degradation when completion logging fails (Requirement 5.5)"""
        # Arrange
        audit_id = "audit-123"
        success = True
        imported_count = 5
        
        # Make database update fail
        mock_db.table.return_value.select.return_value.eq.return_value.execute.side_effect = Exception("Database error")
        
        # Act - should not raise exception
        await audit_service.log_import_complete(audit_id, success, imported_count)
        
        # Assert - no exception raised (graceful degradation)
        # Test passes if no exception is raised
    
    @pytest.mark.asyncio
    async def test_log_import_start_no_database(self):
        """Test behavior when database client is not available"""
        # Arrange
        audit_service = AuditService(db_session=None)
        user_id = "user-123"
        import_method = "json"
        record_count = 5
        
        # Act
        audit_id = await audit_service.log_import_start(user_id, import_method, record_count)
        
        # Assert - returns audit_id even without database
        assert audit_id is not None
        assert isinstance(audit_id, str)
    
    @pytest.mark.asyncio
    async def test_log_import_complete_no_database(self):
        """Test behavior when database client is not available"""
        # Arrange
        audit_service = AuditService(db_session=None)
        audit_id = "audit-123"
        success = True
        imported_count = 5
        
        # Act - should not raise exception
        await audit_service.log_import_complete(audit_id, success, imported_count)
        
        # Assert - no exception raised
        # Test passes if no exception is raised
