#!/usr/bin/env python
# -*- encoding=utf8 -*-

from enum import Enum, IntEnum
from pydantic import BaseModel
from typing import List


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class BlockListType(IntEnum):
    WORK: int = 0
    STUDY: int = 1
    PERSONAL: int = 2
    OTHER: int = 3
    PERMANENT: int = 4


class BlockListModel(BaseModel):
    domain: str
    list_type: BlockListType


class BlockListResponse(BaseModel):
    id: str
    domain: str
    icon: str = None


class ListBlockListResponse(BaseModel):
    blocklist: List[BlockListResponse]
    status: ResponseStatus = ResponseStatus.SUCCESS

class EditBlockListResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.SUCCESS
    user_id: str
    domain: str
    list_type: BlockListType