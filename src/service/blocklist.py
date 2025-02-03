#!/usr/bin/env python
# -*- encoding=utf8 -*-

from src.config import Config
from src.api import ListBlockListResponse, BlockListType, ResponseStatus, BlockListResponse, EditBlockListResponse
from src.db import MongoDB
import re
from bson import ObjectId


URL_REGEX = re.compile(
    r"^(https?:\/\/)?"  # Optional http or https
    r"(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})"  # Domain (e.g., example.com)
    r"(:\d{1,5})?"  # Optional port (e.g., :8080)
    r"(\/[^\s]*)?$"  # Optional path (e.g., /path/to/page)
)

class BlockListService(object):
    """class to encapsulate the blocklist service."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.db = MongoDB().db

    def list_blocklist(self, user_id: str, list_type: BlockListType) -> ListBlockListResponse:
        """List all blocklist."""
        collection = self.db.get_collection("blocklist")
        query = {"user_id": user_id, "list_type": list_type}
        blocklist_cursor = collection.find(query)
        blocklist = [
            BlockListResponse(id=str(doc["_id"]), domain=doc["domain"])
            for doc in blocklist_cursor
        ]

        return ListBlockListResponse(blocklist=blocklist, status=ResponseStatus.SUCCESS)

    def add_blocklist(self, user_id: str, domain: str, list_type: BlockListType) -> EditBlockListResponse:
        """Add an url to blocklist."""
        collection = self.db.get_collection("blocklist")

        # Validate the website URL
        if not URL_REGEX.match(domain):
            return EditBlockListResponse(
                status=ResponseStatus.FAILED,
                user_id=user_id,
                domain=domain,
                list_type=list_type
            )
        
        query = {
            "user_id": user_id,
            "domain": domain,
            "list_type": list_type
        }
        update = {"$setOnInsert": query}
        result = collection.update_one(query, update, upsert=True)

        # if it already exists, update nothing and return failed
        if result.matched_count > 0:
            return EditBlockListResponse(
                status=ResponseStatus.FAILED, 
                user_id=user_id,
                domain=domain,
                list_type=list_type
            )

        return EditBlockListResponse(
            status=ResponseStatus.SUCCESS,
            user_id=user_id,
            domain=domain,
            list_type=list_type
        )
    
    def delete_blocklist(self, user_id:str, blocklist_id: str) -> EditBlockListResponse:
        """Delete an url from blocklist."""
        collection = self.db.get_collection("blocklist")

        if not ObjectId.is_valid(blocklist_id):
            return EditBlockListResponse(
                status=ResponseStatus.FAILED, 
                user_id="", 
                domain="", 
                list_type=0
            )
        
        entry = collection.find_one({"_id": ObjectId(blocklist_id), "user_id": user_id})
        result = collection.delete_one({"_id": ObjectId(blocklist_id), "user_id": user_id})
        # if nothing was deleted, return a failed response
        if result.deleted_count == 0:
            return EditBlockListResponse(
                status=ResponseStatus.FAILED,
                user_id=user_id,
                domain="",
                list_type=0
            )
        return EditBlockListResponse(
            status=ResponseStatus.SUCCESS,
            user_id=user_id,
            domain=entry["domain"],
            list_type=entry["list_type"]
        )