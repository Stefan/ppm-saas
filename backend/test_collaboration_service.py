"""
Test suite for Real-Time Collaboration Service
Tests WebSocket connection management, session handling, and real-time events
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Import the service
from services.collaboration_service import CollaborationManager, ConnectionManager
from models.pmr import (
    CollaborationSession, CollaborationParticipant, Comment, ChangeEvent,
    SessionType, ParticipantRole, ChangeEventType
)


class TestConnectionManager:
    """Test ConnectionManager for WebSocket connection handling"""
    
    def test_connection_manager_initialization(self):
        """Test ConnectionManager initializes correctly"""
        session_id = "test-session-123"
        manager = ConnectionManager(session_id)
        
        assert manager.session_id == session_id
        assert len(manager.active_connections) == 0
        assert len(manager.user_metadata) == 0
    
    @pytest.mark.asyncio
    async def test_connect_user(self):
        """Test connecting a user via WebSocket"""
        manager = ConnectionManager("test-session")
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        user_id = "user-123"
        user_metadata = {"name": "Test User", "role": "editor"}
        
        await manager.connect(mock_websocket, user_id, user_metadata)
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        assert user_id in manager.active_connections
        assert manager.active_connections[user_id] == mock_websocket
        assert manager.user_metadata[user_id] == user_metadata
    
    def test_disconnect_user(self):
        """Test disconnecting a user"""
        manager = ConnectionManager("test-session")
        
        # Add a user
        user_id = "user-123"
        manager.active_connections[user_id] = Mock()
        manager.user_metadata[user_id] = {"name": "Test User"}
        
        # Disconnect
        manager.disconnect(user_id)
        
        assert user_id not in manager.active_connections
        assert user_id not in manager.user_metadata
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending a message to a specific user"""
        manager = ConnectionManager("test-session")
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        user_id = "user-123"
        manager.active_connections[user_id] = mock_websocket
        
        message = {"type": "test", "data": "hello"}
        await manager.send_personal_message(message, user_id)
        
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting a message to all users except sender"""
        manager = ConnectionManager("test-session")
        
        # Add multiple users
        user1_ws = AsyncMock()
        user2_ws = AsyncMock()
        user3_ws = AsyncMock()
        
        manager.active_connections["user-1"] = user1_ws
        manager.active_connections["user-2"] = user2_ws
        manager.active_connections["user-3"] = user3_ws
        
        message = {"type": "update", "data": "broadcast"}
        await manager.broadcast(message, exclude_user="user-1")
        
        # User 1 should not receive the message
        user1_ws.send_json.assert_not_called()
        
        # Users 2 and 3 should receive the message
        user2_ws.send_json.assert_called_once_with(message)
        user3_ws.send_json.assert_called_once_with(message)
    
    def test_get_active_users(self):
        """Test getting list of active users"""
        manager = ConnectionManager("test-session")
        
        manager.active_connections["user-1"] = Mock()
        manager.active_connections["user-2"] = Mock()
        manager.active_connections["user-3"] = Mock()
        
        active_users = manager.get_active_users()
        
        assert len(active_users) == 3
        assert "user-1" in active_users
        assert "user-2" in active_users
        assert "user-3" in active_users
    
    def test_get_connection_count(self):
        """Test getting connection count"""
        manager = ConnectionManager("test-session")
        
        assert manager.get_connection_count() == 0
        
        manager.active_connections["user-1"] = Mock()
        manager.active_connections["user-2"] = Mock()
        
        assert manager.get_connection_count() == 2


class TestCollaborationManager:
    """Test CollaborationManager for session and event management"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client"""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        return mock_client
    
    @pytest.fixture
    def collaboration_manager(self, mock_supabase):
        """Create a CollaborationManager instance with mocked Supabase"""
        return CollaborationManager(mock_supabase)
    
    def test_collaboration_manager_initialization(self, collaboration_manager):
        """Test CollaborationManager initializes correctly"""
        assert len(collaboration_manager.sessions) == 0
        assert len(collaboration_manager.session_data) == 0
        assert len(collaboration_manager.report_to_session) == 0
    
    @pytest.mark.asyncio
    async def test_create_session(self, collaboration_manager, mock_supabase):
        """Test creating a new collaboration session"""
        report_id = uuid4()
        
        # Mock database insert
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        session = await collaboration_manager.create_session(
            report_id=report_id,
            session_type=SessionType.collaborative,
            max_participants=10
        )
        
        assert session is not None
        assert session.report_id == report_id
        assert session.session_type == SessionType.collaborative
        assert session.max_participants == 10
        assert session.is_active is True
        
        # Verify session is stored
        assert session.session_id in collaboration_manager.session_data
        assert str(report_id) in collaboration_manager.report_to_session
        assert session.session_id in collaboration_manager.sessions
    
    @pytest.mark.asyncio
    async def test_add_participant(self, collaboration_manager, mock_supabase):
        """Test adding a participant to a session"""
        report_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        # Create session
        session = await collaboration_manager.create_session(report_id=report_id)
        
        # Add participant
        success = await collaboration_manager.add_participant(
            session_id=session.session_id,
            user_id=user_id,
            user_name="Test User",
            user_email="test@example.com",
            role=ParticipantRole.editor
        )
        
        assert success is True
        
        # Verify participant was added
        updated_session = await collaboration_manager.get_session(session.session_id)
        assert len(updated_session.participants) == 1
        assert updated_session.participants[0].user_id == user_id
        assert updated_session.participants[0].user_name == "Test User"
        assert updated_session.participants[0].role == ParticipantRole.editor
    
    @pytest.mark.asyncio
    async def test_remove_participant(self, collaboration_manager, mock_supabase):
        """Test removing a participant from a session"""
        report_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        # Create session and add participant
        session = await collaboration_manager.create_session(report_id=report_id)
        await collaboration_manager.add_participant(
            session_id=session.session_id,
            user_id=user_id,
            user_name="Test User",
            user_email="test@example.com"
        )
        
        # Remove participant
        success = await collaboration_manager.remove_participant(
            session_id=session.session_id,
            user_id=user_id
        )
        
        assert success is True
        
        # Verify participant was removed
        updated_session = await collaboration_manager.get_session(session.session_id)
        assert len(updated_session.participants) == 0
    
    @pytest.mark.asyncio
    async def test_end_session(self, collaboration_manager, mock_supabase):
        """Test ending a collaboration session"""
        report_id = uuid4()
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        # Create session
        session = await collaboration_manager.create_session(report_id=report_id)
        
        # End session
        success = await collaboration_manager.end_session(session.session_id)
        
        assert success is True
        
        # Verify session is inactive
        updated_session = await collaboration_manager.get_session(session.session_id)
        assert updated_session.is_active is False
    
    @pytest.mark.asyncio
    async def test_handle_section_update(self, collaboration_manager, mock_supabase):
        """Test handling a section update event"""
        report_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        # Create session and add participant
        session = await collaboration_manager.create_session(report_id=report_id)
        await collaboration_manager.add_participant(
            session_id=session.session_id,
            user_id=user_id,
            user_name="Test User",
            user_email="test@example.com"
        )
        
        # Handle section update
        await collaboration_manager.handle_section_update(
            session_id=session.session_id,
            user_id=user_id,
            section_id="executive_summary",
            changes={"content": "Updated content"}
        )
        
        # Verify change was logged
        updated_session = await collaboration_manager.get_session(session.session_id)
        assert len(updated_session.changes_log) == 1
        assert updated_session.changes_log[0].event_type == ChangeEventType.section_update
        assert updated_session.changes_log[0].section_id == "executive_summary"
        assert updated_session.changes_log[0].user_id == user_id
    
    @pytest.mark.asyncio
    async def test_handle_comment_added(self, collaboration_manager, mock_supabase):
        """Test handling a comment addition"""
        report_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        # Create session and add participant
        session = await collaboration_manager.create_session(report_id=report_id)
        await collaboration_manager.add_participant(
            session_id=session.session_id,
            user_id=user_id,
            user_name="Test User",
            user_email="test@example.com"
        )
        
        # Add comment
        comment = await collaboration_manager.handle_comment_added(
            session_id=session.session_id,
            user_id=user_id,
            section_id="budget_analysis",
            content="This needs more detail"
        )
        
        assert comment is not None
        assert comment.section_id == "budget_analysis"
        assert comment.content == "This needs more detail"
        assert comment.user_id == user_id
        
        # Verify comment was added to session
        updated_session = await collaboration_manager.get_session(session.session_id)
        assert len(updated_session.comments) == 1
        assert updated_session.comments[0].comment_id == comment.comment_id
    
    @pytest.mark.asyncio
    async def test_handle_comment_resolved(self, collaboration_manager, mock_supabase):
        """Test handling comment resolution"""
        report_id = uuid4()
        user_id = uuid4()
        
        # Mock database operations
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
        
        # Create session and add participant
        session = await collaboration_manager.create_session(report_id=report_id)
        await collaboration_manager.add_participant(
            session_id=session.session_id,
            user_id=user_id,
            user_name="Test User",
            user_email="test@example.com"
        )
        
        # Add comment
        comment = await collaboration_manager.handle_comment_added(
            session_id=session.session_id,
            user_id=user_id,
            section_id="budget_analysis",
            content="This needs more detail"
        )
        
        # Resolve comment
        success = await collaboration_manager.handle_comment_resolved(
            session_id=session.session_id,
            user_id=user_id,
            comment_id=comment.comment_id
        )
        
        assert success is True
        
        # Verify comment is resolved
        updated_session = await collaboration_manager.get_session(session.session_id)
        resolved_comment = next(
            (c for c in updated_session.comments if c.comment_id == comment.comment_id),
            None
        )
        assert resolved_comment is not None
        assert resolved_comment.resolved is True
        assert resolved_comment.resolved_by == user_id
    
    def test_get_active_session_count(self, collaboration_manager):
        """Test getting count of active sessions"""
        # Create some test sessions
        session1 = CollaborationSession(
            session_id="session-1",
            report_id=uuid4(),
            is_active=True
        )
        session2 = CollaborationSession(
            session_id="session-2",
            report_id=uuid4(),
            is_active=True
        )
        session3 = CollaborationSession(
            session_id="session-3",
            report_id=uuid4(),
            is_active=False
        )
        
        collaboration_manager.session_data["session-1"] = session1
        collaboration_manager.session_data["session-2"] = session2
        collaboration_manager.session_data["session-3"] = session3
        
        assert collaboration_manager.get_active_session_count() == 2
    
    def test_get_total_connections(self, collaboration_manager):
        """Test getting total connection count across all sessions"""
        # Create connection managers with different connection counts
        cm1 = ConnectionManager("session-1")
        cm1.active_connections["user-1"] = Mock()
        cm1.active_connections["user-2"] = Mock()
        
        cm2 = ConnectionManager("session-2")
        cm2.active_connections["user-3"] = Mock()
        
        collaboration_manager.sessions["session-1"] = cm1
        collaboration_manager.sessions["session-2"] = cm2
        
        assert collaboration_manager.get_total_connections() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
