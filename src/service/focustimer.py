#!/usr/bin/env python
# -*- encoding=utf8 -*-

from src.api import SessionStatus, SessionType, GetFocusSessionResponse
from src.config import Config
from src.db import MongoDB
from bson import ObjectId 
from datetime import datetime

class FocusTimerService(object):
    """class to encapsulate the analytics service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db
    
    def _time_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM:SS to total seconds."""
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

    def add_focus_session(self, user_id: str, session_status: SessionStatus, start_date: str, start_time: str, duration: int, break_duration: int, session_type: SessionType, remaining_focus_time: int, remaining_break_time: int) -> (str, bool):
        """Add focus timer."""
        collection = self.db.get_collection("focus_timer")
        nextSession = self.get_next_focus_session(user_id)
        if nextSession:
            # Convert start times to seconds since midnight
            proposed_start_time_seconds = self._time_to_seconds(start_time)
            proposed_end_time_seconds = proposed_start_time_seconds + duration * 60 + break_duration * 60
            
            next_session_start_time_seconds = self._time_to_seconds(nextSession.start_time)
            next_session_end_time_seconds = next_session_start_time_seconds + nextSession.duration * 60 + nextSession.break_duration * 60
            
            # Check if there is a time conflict
            if (proposed_start_time_seconds < next_session_end_time_seconds) and (proposed_end_time_seconds > next_session_start_time_seconds):
                return "", False  # Conflict: the proposed session overlaps with the next session

        query = {
            "user_id": user_id,
            "session_status": session_status,
            "start_date": start_date,
            "start_time": start_time,
            "duration": duration,
            "break_duration": break_duration,
            "session_type": session_type,
            "remaining_focus_time": remaining_focus_time,
            "remaining_break_time": remaining_break_time
        }
        update = {"$setOnInsert": query}
        result = collection.update_one(query, update, upsert=True)
        return str(result.upserted_id), True
    
    def modify_focus_session(self, user_id: str, session_id: str, **updates) -> bool:
        """Modify focus timer with optional fields."""
        collection = self.db.get_collection("focus_timer")

        if not updates:
            return False
        
        if "session_status" in updates:
            updates["session_status"] = updates["session_status"].value
        if "session_type" in updates:
            updates["session_type"] = updates["session_type"].value
        

        result = collection.update_one({"user_id": user_id, "_id": ObjectId(session_id)}, {"$set": updates})
        return result.modified_count > 0
    
    def delete_focus_session(self, user_id: str, session_id: str) -> bool:
        """Delete focus timer."""
        collection = self.db.get_collection("focus_timer")
        result = collection.delete_one({"user_id": user_id, "_id": ObjectId(session_id)})
        return result.deleted_count > 0
    
    def get_next_focus_session(self, user_id: str) -> GetFocusSessionResponse:
        """Get next upcoming focus session."""
        collection = self.db.get_collection("focus_timer")

        session = collection.find_one(
            {"user_id": user_id, "session_status": 0},  # Filter: Only sessions with status 0
            sort=[("start_date", 1), ("start_time", 1)]  # Sort: First by date, then by time
        )
        
        return GetFocusSessionResponse(**session) if session else None
    
    def get_all_focus_session(self, user_id: str, session_status: int = None) -> list[GetFocusSessionResponse]:
        """Get focus sessions of specific status, default is fetching all."""
        collection = self.db.get_collection("focus_timer")

        query = {"user_id": user_id}
        if session_status is not None:
            query["session_status"] = session_status

        session_cursor = collection.find(query)

        focus_sessions = [
            GetFocusSessionResponse(
                session_id = str(doc["_id"]),
                session_status=SessionStatus(doc.get("session_status")),
                start_date=doc.get("start_date"),
                start_time=doc.get("start_time"),
                duration=doc.get("duration"),
                break_duration=doc.get("break_duration"),
                session_type=SessionType(doc.get("session_type")),
                remaining_focus_time=doc.get("remaining_focus_time"),
                remaining_break_time=doc.get("remaining_break_time"),
            )
            for doc in session_cursor
        ]

        return focus_sessions

