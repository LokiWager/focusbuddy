#!/usr/bin/env python
# -*- encoding=utf8 -*-

from fastapi import FastAPI, APIRouter

from src.api import ListBlockListResponse, BlockListType, EditBlockListResponse
from src.service import BlockListService
from src.config import api_version, Config


class BlockListAPI(object):
    """class to encapsulate the blocklist API endpoints."""

    def __init__(self, cfg: Config):
        self.router = APIRouter()
        self.blocklist_service = BlockListService(cfg)
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""
        self.router.add_api_route(
            path="/blocklist/{user_id}",
            endpoint=self.list_blocklist,
            methods=["GET"],
            response_model=ListBlockListResponse,
            summary="List all blocklist",
        )
        self.router.add_api_route(
            path="/blocklist/{user_id}",
            endpoint=self.add_blocklist,
            methods=["POST"],
            response_model=EditBlockListResponse,
            summary="Add a blocklist url",
        )

        self.router.add_api_route(
            path="/blocklist/{user_id}/{blocklist_id}",
            endpoint=self.delete_blocklist,
            methods=["DELETE"],
            response_model=EditBlockListResponse,
            summary="Delete a blocklist url",
        )



    async def list_blocklist(self, user_id: str, list_type: BlockListType = BlockListType.WORK):
        """List all blocklist."""
        return self.blocklist_service.list_blocklist(user_id, list_type)

    async def add_blocklist(self, user_id: str, domain: str, list_type: BlockListType):
        """Add an url to blocklist."""
        return self.blocklist_service.add_blocklist(user_id, domain, list_type)
       
    async def delete_blocklist(self, user_id: str, blocklist_id: str):
        """Delete an url from blocklist."""
        return self.blocklist_service.delete_blocklist(user_id, blocklist_id)

def create_app(cfg: Config):
    _app = FastAPI()
    blocklist_api = BlockListAPI(cfg)
    _app.include_router(blocklist_api.router, prefix=api_version)
    return _app

app = create_app(Config())
