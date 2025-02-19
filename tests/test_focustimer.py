#!/usr/bin/env python
# -*- encoding=utf8 -*-
import unittest
from bson import ObjectId

from src.config import Config
from src.service.user import UserService
from tests.test_utils import get_test_app
from src.api import ResponseStatus, SessionStatus, SessionType
from src.db import MongoDB  # Import the MongoDB singleton
from src.service.focustimer import FocusTimerService

# import logging

# logging.basicConfig(level=logging.DEBUG)

class TestFocusTimer(unittest.TestCase):
    app = get_test_app()
    db = MongoDB().db
    user_service = UserService(cfg=Config())
    user_id = "focusbuddy_test"
    jwt_token = user_service._generate_jwt("focusbuddy_test", "focusbuddy.test@gmail.com")

    def test_get_all_focustimer(self):
        response = self.app.get("/api/v1/focustimer", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        assert response.json() == {
            "focus_sessions": [],
            "status": ResponseStatus.SUCCESS,
        }

    def test_get_all_focustimer_non_empty(self):
        collection = self.db.get_collection("focus_timer")
        collection.delete_many({})
        # Insert a test entry
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:16:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        inserted_id = collection.insert_one(test_entry).inserted_id
        response = self.app.get("/api/v1/focustimer", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 200
        # logging.debug(f"Response: {response.json()}")
        assert response.json() == {
            "focus_sessions": [
                {
                    "session_id": str(inserted_id),
                    "session_status": 0, 
                    "start_date": "02/22/2025", 
                    "start_time": "23:16:15", 
                    "duration": 1, 
                    "break_duration": 1, 
                    "session_type": 0, 
                    "remaining_focus_time": 60, 
                    "remaining_break_time": 60
                }
            ],
            "status": ResponseStatus.SUCCESS,
        }


    """Test add_focustimer."""

    def setUp(self):
        """Setup mock database before each test."""
        self.db = MongoDB().db
        self.service = FocusTimerService(cfg=None)
        self.service.db = self.db

        # Clear the collection before each test to prevent interference
        self.db.get_collection("focus_timer").delete_many({})

    
    def test_add_focus_timer(self):
        response = self.service.add_focus_session(
            user_id="test_user",
            session_status=SessionStatus.UPCOMING,
            start_date="02/22/2025",
            start_time="23:16:15",
            duration=1,
            break_duration=1,
            session_type=SessionType.WORK,
            remaining_focus_time=60,
            remaining_break_time=60
        )
        assert response[0] != ""  # Should return a valid ObjectId
        assert response[1] is True  # Should return True

    def test_add_conflic_session(self):
        collection = self.db.get_collection("focus_timer")
        collection.delete_many({})
        # Insert a test entry
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:16:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        response = self.app.post("/api/v1/focustimer", json=test_entry, headers={"x-auth-token": self.jwt_token})

        # logging.debug(f"Document count after insertion: {collection.count_documents({})}")
        # logging.debug(f"Response in adding: {response.json()}")
        assert response.status_code == 200

        test_entry2 = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:15:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        response = self.app.post("/api/v1/focustimer", json=test_entry2, headers={"x-auth-token": self.jwt_token})
        # logging.debug(f"Document count after insertion: {collection.count_documents({})}")
        assert response.status_code == 409
        

    """Test update_focustimer."""

    def test_update_focus_timer(self):
        collection = self.db.get_collection("focus_timer")

        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:00:00",
            "duration": 30,
            "break_duration": 5,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 1800,
            "remaining_break_time": 300
        }
        inserted_id = collection.insert_one(test_entry).inserted_id

        # Case 1: 400 Bad Request
        response = self.app.put(f"/api/v1/focustimer/{str(inserted_id)}", json={}, headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 400

        # Case 2: 200 OK
        response = self.app.put(
            f"/api/v1/focustimer/{str(inserted_id)}",
            json={"session_type": SessionType.PERSONAL},
            headers={"x-auth-token": self.jwt_token}
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": self.user_id,
            "id": str(inserted_id),
            "status": ResponseStatus.SUCCESS,
        }

        # Case 3: 409 Conflict
        conflict_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:25:00",
            "duration": 30,
            "break_duration": 5,
            "session_type": SessionType.STUDY,
            "remaining_focus_time": 1800,
            "remaining_break_time": 300
        }
        conflict_id = collection.insert_one(conflict_entry).inserted_id

        response = self.app.put(
            f"/api/v1/focustimer/{str(conflict_id)}",
            json={"start_time": "23:10:00"},
            headers={"x-auth-token": self.jwt_token}
        )
        assert response.status_code == 409  

        # Case 4: 200 OK
        response = self.app.put(
            f"/api/v1/focustimer/{str(inserted_id)}",
            json={"start_time": "22:00:00"},
            headers={"x-auth-token": self.jwt_token}
        )
        assert response.status_code == 200
        assert response.json() == {
            "user_id": self.user_id,
            "id": str(inserted_id),
            "status": ResponseStatus.SUCCESS,
        }


    """Test delete_focustimer."""

    def test_delete_valid_entry(self):
        """Test deleting an existing session."""
        collection = self.db.get_collection("focus_timer")

        # Insert a test entry
        test_entry = {
            "user_id": self.user_id,
            "session_status": SessionStatus.UPCOMING,
            "start_date": "02/22/2025",
            "start_time": "23:16:15",
            "duration": 1,
            "break_duration": 1,
            "session_type": SessionType.WORK,
            "remaining_focus_time": 60,
            "remaining_break_time": 60
        }
        inserted_id = collection.insert_one(test_entry).inserted_id

        # Delete the entry
        response = self.app.delete(f"/api/v1/focustimer/{str(inserted_id)}", headers={"x-auth-token": self.jwt_token})
        assert response.status_code == 204
        # Verify the entry is actually removed
        assert collection.count_documents({"_id": inserted_id}) == 0

    def test_delete_non_existent_entry(self):
        """Test deleting a non-existent blocklist entry."""
        response = self.app.delete(f"/api/v1/focustimer/{str(ObjectId())}", headers={"x-auth-token": self.jwt_token}) # Random ObjectId
        assert response.status_code == 404