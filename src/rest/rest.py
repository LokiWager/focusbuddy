#!/usr/bin/env python
# -*- encoding=utf8 -*-
import datetime
import re
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, FastAPI, HTTPException, Response, status, Header
from src.api import (
    AddBlockListRequest,
    AnalyticsListResponse,
    EditBlockListResponse,
    ListBlockListResponse,
    ResponseStatus,
    GetUserAppTokenResponse,
    GetUserAppTokenRequest,
    UpdateUserStatusRequest,
    UpdateUserStatusResponse,
    FocusSessionModel,
    EditFocusSessionResponse,
    GetNextFocusSessionResponse,
    GetAllFocusSessionResponse
)
from src.config import Config, api_version
from src.rest.error import (
    BLOCKLIST_ALREADY_EXISTS,
    BLOCKLIST_ID_INVALID,
    BLOCKLIST_IS_INVALID,
    BLOCKLIST_NOT_FOUND,
    INVALID_TOKEN,
    FOCUSSESSION_CONFLICT,
    FOCUSSESSION_NOT_UPDATED,
    FOCUSSESSION_NOT_FOUND,
    USERSTATUS_NOT_UPDATED
)

from src.service.user import UserService
from src.service import BlockListService, FocusTimerService, AnalyticsListService


class BaseAPI:
    """Base API class to handle common functionality like token validation."""
    
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.user_service = UserService(cfg)
        self.router = APIRouter()

    def validate_token(self, token: str) -> (str, bool):
        """Validate the token."""
        if token is None:
            return "", False
        user = self.user_service.decode_user(token)
        if user.user_id == "":
            return "", False
        now = datetime.datetime.timestamp(datetime.datetime.utcnow())
        if float(user.exp) < now:
            return "", False
        return user.user_id, True

class BlockListAPI(BaseAPI):
    """class to encapsulate the blocklist API endpoints."""

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self.blocklist_service = BlockListService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/blocklist",
            endpoint=self.list_blocklist,
            methods=["GET"],
            response_model=ListBlockListResponse,
            summary="List all blocklist",
        )
        self.router.add_api_route(
            path="/blocklist",
            endpoint=self.add_blocklist,
            methods=["POST"],
            response_model=EditBlockListResponse,
            summary="Add a blocklist url",
        )
        self.router.add_api_route(
            path="/blocklist/{blocklist_id}",
            endpoint=self.delete_blocklist,
            methods=["DELETE"],
            response_model=EditBlockListResponse,
            summary="Delete a blocklist url",
        )

    async def list_blocklist(self, x_auth_token: Annotated[str, Header()] = None):
        """List all blocklist."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        response = self.blocklist_service.list_blocklist(user_id)
        return ListBlockListResponse(blocklist=response, status=ResponseStatus.SUCCESS)

    async def add_blocklist(self, request: AddBlockListRequest, x_auth_token: Annotated[str, Header()] = None):
        """Add an url to blocklist."""
        if not self.validate_domain(request.domain):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_IS_INVALID)
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        new_id, ok = self.blocklist_service.add_blocklist(user_id, request.domain, request.list_type)
        if not ok:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=BLOCKLIST_ALREADY_EXISTS)
        return EditBlockListResponse(user_id=user_id, domain=request.domain, list_type=request.list_type, status=ResponseStatus.SUCCESS, id=new_id)

    async def delete_blocklist(self, blocklist_id: str, x_auth_token: Annotated[str, Header()] = None):
        """Delete an url from blocklist."""
        if not ObjectId.is_valid(blocklist_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=BLOCKLIST_ID_INVALID)
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        ok = self.blocklist_service.delete_blocklist(user_id, blocklist_id)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=BLOCKLIST_NOT_FOUND
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def validate_domain(domain: str):
        """Validate the domain."""
        url_regex = re.compile(
            r"^(https?:\/\/)?"  # Optional http or https
            r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})"  # Domain (e.g., example.com)
            r"(:\d{1,5})?"  # Optional port (e.g., :8080)
            r"(\/[^\s]*)?$"  # Optional path (e.g., /path/to/page)
        )
        return url_regex.match(domain)


class UserAPI(BaseAPI):
    """class to encapsulate the user API endpoints."""

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/user/login",
            endpoint=self.get_user_app_token,
            methods=["POST"],
            response_model=GetUserAppTokenResponse,
            summary="Get user app token",
        )
        self.router.add_api_route(
            path="/user/status",
            endpoint=self.update_user_status,
            methods=["PUT"],
            summary="Modify user status",
        )

    async def get_user_app_token(self, request: GetUserAppTokenRequest):
        """Get user app token."""
        token = request.token
        if token is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_TOKEN)

        user = self.user_service.get_user_app_token(token)
        if user.jwt == "":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        return GetUserAppTokenResponse(jwt=user.jwt, email=user.email, picture=user.picture)
    
    async def update_user_status(self, request: UpdateUserStatusRequest, x_auth_token: Annotated[str, Header()] = None):
        """Update user status."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        ok = self.user_service.update_user_status(user_id, request.user_status)
        if not ok:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=USERSTATUS_NOT_UPDATED)
        return UpdateUserStatusResponse(user_id=user_id, user_status=request.user_status, status=ResponseStatus.SUCCESS)

class AnalyticsListAPI(object):
    """class to encapsulate the analytics API endpoint."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.analyticslist_service = AnalyticsListService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/analytics/{user_id}",
            endpoint=self.list_analytics,
            methods=["GET"],
            response_model=AnalyticsListResponse,
            summary="List all analytics for user",
        )

    async def list_analytics(self, user_id: str):
        """List all analytics for user."""
        response = self.analyticslist_service.get_analytics(user_id)
        return response

class FocusTimerAPI(BaseAPI):
    """class to encapsulate the focustimer API endpoints."""

    def __init__(self, cfg: Config):
        super().__init__(cfg)
        self.timer_service = FocusTimerService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/focustimer",
            endpoint=self.add_focus_session,
            methods=["POST"],
            summary="Add a focus session",
        )
        self.router.add_api_route(
            path="/focustimer/{session_id}",
            endpoint=self.modify_focus_session,
            methods=["PUT"],
            summary="Modify a focus session",
        )
        self.router.add_api_route(
            path="/focustimer/{session_id}",
            endpoint=self.delete_focus_session,
            methods=["DELETE"],
            summary="Delete a focus session",
        )
        self.router.add_api_route(
            path="/focustimer/nextSession",
            endpoint=self.get_next_focus_session,
            methods=["GET"],
            summary="Get next upcoming focus session",
        )
        self.router.add_api_route(
            path="/focustimer",
            endpoint=self.get_all_focus_session,
            methods=["GET"],
            summary="Get all focus sessions of specific status, fetch all by default",
        )

    async def add_focus_session(self, request: FocusSessionModel, x_auth_token: Annotated[str, Header()] = None):
        """Add a focus session."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        session_id, ok = self.timer_service.add_focus_session(user_id, request.session_status, request.start_date, request.start_time, request.duration, request.break_duration, request.session_type, request.remaining_focus_time, request.remaining_break_time)
        if not ok:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=FOCUSSESSION_CONFLICT)
        return EditFocusSessionResponse(user_id=user_id, id=session_id, status=ResponseStatus.SUCCESS)
    
    async def modify_focus_session(self, session_id: str, request: FocusSessionModel, x_auth_token: Annotated[str, Header()] = None):
        """Modify a focus session."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        
        updates = {k: v for k, v in request.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=FOCUSSESSION_NOT_UPDATED)
        
        result = self.timer_service.modify_focus_session(user_id, session_id, **updates)

        if result == "conflict":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=FOCUSSESSION_CONFLICT)
        if not result:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=FOCUSSESSION_NOT_UPDATED)
        return EditFocusSessionResponse(user_id=user_id, id=session_id, status=ResponseStatus.SUCCESS)
    
    async def delete_focus_session(self, session_id: str, x_auth_token: Annotated[str, Header()] = None):
        """Delete a focus session."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        ok = self.timer_service.delete_focus_session(user_id, session_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=FOCUSSESSION_NOT_FOUND)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    async def get_next_focus_session(self, x_auth_token: Annotated[str, Header()] = None):
        """Get next upcoming focus session."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        response = self.timer_service.get_next_focus_session(user_id)
        return GetNextFocusSessionResponse(focus_session=response, status=ResponseStatus.SUCCESS)
    
    async def get_all_focus_session(self, x_auth_token: Annotated[str, Header()] = None, session_status: int = None):
        """Get focus sessions of specific status, default is fetching all."""
        user_id, ok = self.validate_token(x_auth_token)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_TOKEN)
        response = self.timer_service.get_all_focus_session(user_id, session_status)
        return GetAllFocusSessionResponse(focus_sessions=response, status=ResponseStatus.SUCCESS)
        

def create_app(cfg: Config):
    _app = FastAPI()
    blocklist_api = BlockListAPI(cfg)
    focustimer_api = FocusTimerAPI(cfg)
    _app.include_router(focustimer_api.router, prefix=api_version)
    _app.include_router(blocklist_api.router, prefix=api_version)
    analyticslist_api = AnalyticsListAPI(cfg)
    _app.include_router(analyticslist_api.router, prefix=api_version)
    user_api = UserAPI(cfg)
    _app.include_router(user_api.router, prefix=api_version)
    return _app


app = create_app(Config())
