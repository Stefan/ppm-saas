"""
Real-Time Collaboration Service for Enhanced PMR
Manages WebSocket connections, multi-user editing, and real-time synchronization
"""

import logging
import json
from typing import Dict, List, Optional, Set
from datetime import datetime
from uuid import UUID, uuid4
from fastapi import WebSocket, WebSocketDisconnect
from supabase import Client

# Import models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.pmr import (
    CollaborationSession, CollaborationParticipant, Comment, ChangeEvent,
    ChangeEventType, ParticipantRole, SessionType
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for a single collaboration session
    Handles message broadcasting and connection lifecycle
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.active_connections: Dict[str, WebSocket] = {}  # user_id -> WebSocket
        self.user_metadata: Dict[str, Dict] = {}  # user_id -> metadata
        
    async def connect(self, websocket: WebSocket, user_id: str, user_metadata: Dict) -> None:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_metadata[user_id] = user_metadata
        logger.info(f"User {user_id} connected to session {self.session_id}")
        
    def disconnect(self, user_id: str) -> None:
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_metadata:
            del self.user_metadata[user_id]
        logger.info(f"User {user_id} disconnected from session {self.session_id}")
        
    async def send_personal_message(self, message: Dict, user_id: str) -> None:
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)
                
    async def broadcast(self, message: Dict, exclude_user: Optional[str] = None) -> None:
        """Broadcast a message to all connected users except the sender"""
        disconnected_users = []
        
        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)
            
    def get_active_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


class CollaborationManager:
    """
    Main collaboration manager for Enhanced PMR
    Manages multiple collaboration sessions and WebSocket connections
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.sessions: Dict[str, ConnectionManager] = {}  # session_id -> ConnectionManager
        self.session_data: Dict[str, CollaborationSession] = {}  # session_id -> CollaborationSession
        self.report_to_session: Dict[str, str] = {}  # report_id -> session_id
        
        logger.info("Collaboration Manager initialized")
    
    # Session Management
    
    async def create_session(
        self,
        report_id: UUID,
        session_type: SessionType = SessionType.collaborative,
        max_participants: int = 10,
        conflict_resolution_strategy: str = "last_write_wins",
        session_timeout_minutes: int = 60
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        try:
            session_id = str(uuid4())
            
            # Create session data
            session = CollaborationSession(
                session_id=session_id,
                report_id=report_id,
                session_type=session_type,
                max_participants=max_participants,
                conflict_resolution_strategy=conflict_resolution_strategy,
                session_timeout_minutes=session_timeout_minutes,
                is_active=True
            )
            
            # Store session
            self.session_data[session_id] = session
            self.report_to_session[str(report_id)] = session_id
            
            # Create connection manager
            self.sessions[session_id] = ConnectionManager(session_id)
            
            # Persist to database
            await self._persist_session(session)
            
            logger.info(f"Created collaboration session {session_id} for report {report_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create collaboration session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get a collaboration session by ID"""
        if session_id in self.session_data:
            return self.session_data[session_id]
        
        # Try to load from database
        try:
            response = self.supabase.table("collaboration_sessions").select(
                "*"
            ).eq("session_id", session_id).execute()
            
            if response.data:
                session_dict = response.data[0]
                session = CollaborationSession(**session_dict)
                self.session_data[session_id] = session
                return session
        except Exception as e:
            logger.error(f"Failed to load session from database: {e}")
        
        return None
    
    async def get_session_by_report(self, report_id: UUID) -> Optional[CollaborationSession]:
        """Get active collaboration session for a report"""
        report_id_str = str(report_id)
        
        if report_id_str in self.report_to_session:
            session_id = self.report_to_session[report_id_str]
            return await self.get_session(session_id)
        
        # Try to load from database
        try:
            response = self.supabase.table("collaboration_sessions").select(
                "*"
            ).eq("report_id", report_id_str).eq("is_active", True).execute()
            
            if response.data:
                session_dict = response.data[0]
                session = CollaborationSession(**session_dict)
                self.session_data[session.session_id] = session
                self.report_to_session[report_id_str] = session.session_id
                return session
        except Exception as e:
            logger.error(f"Failed to load session by report from database: {e}")
        
        return None
    
    async def end_session(self, session_id: str) -> bool:
        """End a collaboration session"""
        try:
            if session_id not in self.session_data:
                return False
            
            session = self.session_data[session_id]
            session.is_active = False
            
            # Disconnect all users
            if session_id in self.sessions:
                connection_manager = self.sessions[session_id]
                
                # Notify all users that session is ending
                await connection_manager.broadcast({
                    "type": "session_ended",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Clean up connections
                del self.sessions[session_id]
            
            # Update database
            await self._persist_session(session)
            
            # Clean up mappings
            report_id_str = str(session.report_id)
            if report_id_str in self.report_to_session:
                del self.report_to_session[report_id_str]
            
            logger.info(f"Ended collaboration session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return False
    
    # Participant Management
    
    async def add_participant(
        self,
        session_id: str,
        user_id: UUID,
        user_name: str,
        user_email: str,
        role: ParticipantRole = ParticipantRole.editor
    ) -> bool:
        """Add a participant to a collaboration session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            # Create participant
            participant = CollaborationParticipant(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                role=role
            )
            
            # Add to session
            if not session.add_participant(participant):
                logger.warning(f"Failed to add participant {user_id} to session {session_id}")
                return False
            
            # Update database
            await self._persist_session(session)
            
            # Notify other participants
            if session_id in self.sessions:
                await self.sessions[session_id].broadcast({
                    "type": "participant_joined",
                    "session_id": session_id,
                    "participant": {
                        "user_id": str(user_id),
                        "user_name": user_name,
                        "role": role.value
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"Added participant {user_id} to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add participant: {e}")
            return False
    
    async def remove_participant(self, session_id: str, user_id: UUID) -> bool:
        """Remove a participant from a collaboration session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Remove from session
            if not session.remove_participant(user_id):
                return False
            
            # Update database
            await self._persist_session(session)
            
            # Disconnect WebSocket if active
            if session_id in self.sessions:
                connection_manager = self.sessions[session_id]
                user_id_str = str(user_id)
                
                # Notify other participants
                await connection_manager.broadcast({
                    "type": "participant_left",
                    "session_id": session_id,
                    "user_id": user_id_str,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                connection_manager.disconnect(user_id_str)
            
            logger.info(f"Removed participant {user_id} from session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove participant: {e}")
            return False
    
    # WebSocket Connection Management
    
    async def connect_user(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: UUID,
        user_name: str
    ) -> bool:
        """Connect a user to a collaboration session via WebSocket"""
        try:
            session = await self.get_session(session_id)
            if not session or not session.is_active:
                logger.error(f"Session {session_id} not found or inactive")
                return False
            
            # Check if user is a participant
            user_id_str = str(user_id)
            participant = next(
                (p for p in session.participants if str(p.user_id) == user_id_str),
                None
            )
            
            if not participant:
                logger.error(f"User {user_id} is not a participant in session {session_id}")
                return False
            
            # Create connection manager if needed
            if session_id not in self.sessions:
                self.sessions[session_id] = ConnectionManager(session_id)
            
            connection_manager = self.sessions[session_id]
            
            # Connect user
            user_metadata = {
                "user_name": user_name,
                "role": participant.role.value,
                "joined_at": datetime.utcnow().isoformat()
            }
            
            await connection_manager.connect(websocket, user_id_str, user_metadata)
            
            # Update participant status
            participant.is_online = True
            participant.last_active = datetime.utcnow()
            
            # Send current session state to the new user
            await connection_manager.send_personal_message({
                "type": "session_state",
                "session_id": session_id,
                "participants": [
                    {
                        "user_id": str(p.user_id),
                        "user_name": p.user_name,
                        "role": p.role.value,
                        "is_online": p.is_online,
                        "current_section": p.current_section
                    }
                    for p in session.participants
                ],
                "active_editors": session.active_editors,
                "locked_sections": {k: str(v) for k, v in session.locked_sections.items()},
                "timestamp": datetime.utcnow().isoformat()
            }, user_id_str)
            
            # Notify other participants
            await connection_manager.broadcast({
                "type": "user_online",
                "session_id": session_id,
                "user_id": user_id_str,
                "user_name": user_name,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_user=user_id_str)
            
            logger.info(f"User {user_id} connected to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect user: {e}")
            return False
    
    async def disconnect_user(self, session_id: str, user_id: UUID) -> None:
        """Disconnect a user from a collaboration session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return
            
            user_id_str = str(user_id)
            
            # Update participant status
            participant = next(
                (p for p in session.participants if str(p.user_id) == user_id_str),
                None
            )
            
            if participant:
                participant.is_online = False
                participant.last_active = datetime.utcnow()
            
            # Remove from active editors
            if user_id_str in session.active_editors:
                session.active_editors.remove(user_id_str)
            
            # Unlock any sections locked by this user
            sections_to_unlock = [
                section_id for section_id, locked_user_id in session.locked_sections.items()
                if str(locked_user_id) == user_id_str
            ]
            for section_id in sections_to_unlock:
                del session.locked_sections[section_id]
            
            # Disconnect WebSocket
            if session_id in self.sessions:
                connection_manager = self.sessions[session_id]
                connection_manager.disconnect(user_id_str)
                
                # Notify other participants
                await connection_manager.broadcast({
                    "type": "user_offline",
                    "session_id": session_id,
                    "user_id": user_id_str,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Update database
            await self._persist_session(session)
            
            logger.info(f"User {user_id} disconnected from session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to disconnect user: {e}")
    
    # Real-Time Event Handling
    
    async def handle_section_update(
        self,
        session_id: str,
        user_id: UUID,
        section_id: str,
        changes: Dict
    ) -> None:
        """Handle a section update event"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return
            
            user_id_str = str(user_id)
            
            # Get user name
            participant = next(
                (p for p in session.participants if str(p.user_id) == user_id_str),
                None
            )
            user_name = participant.user_name if participant else "Unknown"
            
            # Create change event
            event = ChangeEvent(
                event_type=ChangeEventType.section_update,
                user_id=user_id,
                user_name=user_name,
                section_id=section_id,
                changes=changes
            )
            
            # Add to session log
            session.add_change_event(event)
            
            # Update database
            await self._persist_session(session)
            
            # Broadcast to other participants
            if session_id in self.sessions:
                await self.sessions[session_id].broadcast({
                    "type": "section_update",
                    "session_id": session_id,
                    "section_id": section_id,
                    "user_id": user_id_str,
                    "user_name": user_name,
                    "changes": changes,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user_id_str)
            
            logger.info(f"Section {section_id} updated by user {user_id} in session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle section update: {e}")
    
    async def handle_cursor_position(
        self,
        session_id: str,
        user_id: UUID,
        section_id: str,
        position: int
    ) -> None:
        """Handle cursor position update"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return
            
            user_id_str = str(user_id)
            
            # Update participant cursor position
            participant = next(
                (p for p in session.participants if str(p.user_id) == user_id_str),
                None
            )
            
            if participant:
                participant.current_section = section_id
                participant.cursor_position = position
                participant.last_active = datetime.utcnow()
            
            # Broadcast to other participants
            if session_id in self.sessions:
                await self.sessions[session_id].broadcast({
                    "type": "cursor_position",
                    "session_id": session_id,
                    "user_id": user_id_str,
                    "section_id": section_id,
                    "position": position,
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude_user=user_id_str)
            
        except Exception as e:
            logger.error(f"Failed to handle cursor position: {e}")
    
    async def handle_comment_added(
        self,
        session_id: str,
        user_id: UUID,
        section_id: str,
        content: str,
        parent_comment_id: Optional[UUID] = None
    ) -> Optional[Comment]:
        """Handle comment addition"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return None
            
            user_id_str = str(user_id)
            
            # Get user name
            participant = next(
                (p for p in session.participants if str(p.user_id) == user_id_str),
                None
            )
            user_name = participant.user_name if participant else "Unknown"
            
            # Create comment
            comment = Comment(
                section_id=section_id,
                user_id=user_id,
                user_name=user_name,
                content=content,
                parent_comment_id=parent_comment_id
            )
            
            # Add to session
            session.add_comment(comment)
            
            # Update database
            await self._persist_session(session)
            
            # Broadcast to other participants
            if session_id in self.sessions:
                await self.sessions[session_id].broadcast({
                    "type": "comment_added",
                    "session_id": session_id,
                    "comment": {
                        "comment_id": str(comment.comment_id),
                        "section_id": section_id,
                        "user_id": user_id_str,
                        "user_name": user_name,
                        "content": content,
                        "created_at": comment.created_at.isoformat(),
                        "parent_comment_id": str(parent_comment_id) if parent_comment_id else None
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"Comment added by user {user_id} in session {session_id}")
            return comment
            
        except Exception as e:
            logger.error(f"Failed to handle comment addition: {e}")
            return None
    
    async def handle_comment_resolved(
        self,
        session_id: str,
        user_id: UUID,
        comment_id: UUID
    ) -> bool:
        """Handle comment resolution"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Find and resolve comment
            comment = next(
                (c for c in session.comments if c.comment_id == comment_id),
                None
            )
            
            if not comment:
                return False
            
            comment.resolved = True
            comment.resolved_by = user_id
            comment.resolved_at = datetime.utcnow()
            
            # Update database
            await self._persist_session(session)
            
            # Broadcast to other participants
            if session_id in self.sessions:
                await self.sessions[session_id].broadcast({
                    "type": "comment_resolved",
                    "session_id": session_id,
                    "comment_id": str(comment_id),
                    "resolved_by": str(user_id),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            logger.info(f"Comment {comment_id} resolved by user {user_id} in session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle comment resolution: {e}")
            return False
    
    # Helper Methods
    
    async def _persist_session(self, session: CollaborationSession) -> None:
        """Persist collaboration session to database"""
        try:
            session_data = {
                "session_id": session.session_id,
                "report_id": str(session.report_id),
                "session_type": session.session_type.value,
                "participants": [
                    {
                        "user_id": str(p.user_id),
                        "user_name": p.user_name,
                        "user_email": p.user_email,
                        "role": p.role.value,
                        "joined_at": p.joined_at.isoformat(),
                        "last_active": p.last_active.isoformat(),
                        "is_online": p.is_online,
                        "current_section": p.current_section,
                        "cursor_position": p.cursor_position
                    }
                    for p in session.participants
                ],
                "active_editors": session.active_editors,
                "started_at": session.started_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "changes_log": [
                    {
                        "event_id": str(e.event_id),
                        "event_type": e.event_type.value,
                        "user_id": str(e.user_id),
                        "user_name": e.user_name,
                        "section_id": e.section_id,
                        "timestamp": e.timestamp.isoformat(),
                        "changes": e.changes
                    }
                    for e in session.changes_log
                ],
                "comments": [
                    {
                        "comment_id": str(c.comment_id),
                        "section_id": c.section_id,
                        "user_id": str(c.user_id),
                        "user_name": c.user_name,
                        "content": c.content,
                        "created_at": c.created_at.isoformat(),
                        "resolved": c.resolved,
                        "parent_comment_id": str(c.parent_comment_id) if c.parent_comment_id else None
                    }
                    for c in session.comments
                ],
                "locked_sections": {k: str(v) for k, v in session.locked_sections.items()},
                "conflict_resolution_strategy": session.conflict_resolution_strategy,
                "max_participants": session.max_participants,
                "session_timeout_minutes": session.session_timeout_minutes,
                "is_active": session.is_active
            }
            
            # Upsert to database
            self.supabase.table("collaboration_sessions").upsert(
                session_data,
                on_conflict="session_id"
            ).execute()
            
        except Exception as e:
            logger.error(f"Failed to persist session: {e}")
    
    def get_active_session_count(self) -> int:
        """Get number of active collaboration sessions"""
        return len([s for s in self.session_data.values() if s.is_active])
    
    def get_total_connections(self) -> int:
        """Get total number of active WebSocket connections"""
        return sum(cm.get_connection_count() for cm in self.sessions.values())
