from __future__ import annotations
from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, Literal, Dict, Any, Protocol
from itertools import count
from threading import Lock
from datetime import datetime
from uuid import uuid4

# Pydantic Schemas 

class UserCreate(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=100)

class UserOut(BaseModel):
    user_id: UUID4
    user_name: str

class ShowCreate(BaseModel):
    user_id: UUID4
    user_name: str = Field(..., min_length=1, max_length=100)  
    tix_name: str = Field(..., min_length=1, max_length=100)  
    show_name: str = Field(..., min_length=1, max_length=200)  
class ShowOut(ShowCreate):
    id: int
    created_at: str

# 留言保留，之後也能接 DB
class CommentCreate(BaseModel):
    author_user_id: Optional[UUID4] = None
    author_name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    visibility: Literal["public", "private"] = "public"

class CommentOut(CommentCreate):
    id: int
    show_id: int
    created_at: str

# Repository 介面（之後換成 DB）

class Repository(Protocol):
    # user
    def create_user(self, user_name: str) -> Dict[str, Any]: ...
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]: ...
    def find_users_by_name(self, user_name: str) -> List[Dict[str, Any]]: ...

    # show
    def create_show(self, data: ShowCreate) -> Dict[str, Any]: ...
    def list_shows(self) -> List[Dict[str, Any]]: ...
    def search_shows(
        self, *, name: str, field: Literal["owner", "tix"], exact: bool
    ) -> List[Dict[str, Any]]: ...
    def get_show(self, show_id: int) -> Optional[Dict[str, Any]]: ...

    # comment
    def add_comment(self, show_id: int, data: CommentCreate) -> Dict[str, Any]: ...
    def list_comments(self, show_id: int, viewer_name: Optional[str]) -> List[Dict[str, Any]]: ...

# In-memory

class InMemoryRepository:
    def __init__(self) -> None:
        self._users: Dict[str, Dict[str, Any]] = {}  # key=user_id(str)
        self._shows: List[Dict[str, Any]] = []
        self._comments: List[Dict[str, Any]] = []
        self._show_id = count(1)
        self._comment_id = count(1)
        self._lock = Lock()

    # ---------- helpers ----------
    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    # ---------- user ----------
    def create_user(self, user_name: str) -> Dict[str, Any]:
        uid = str(uuid4())
        rec = {"user_id": uid, "user_name": user_name.strip()}
        with self._lock:
            self._users[uid] = rec
        return rec

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(str(user_id))

    def find_users_by_name(self, user_name: str) -> List[Dict[str, Any]]:
        name = user_name.strip()
        return [u for u in self._users.values() if u["user_name"] == name]

    def create_show(self, data: ShowCreate) -> Dict[str, Any]:
        if str(data.user_id) not in self._users:
            self._users[str(data.user_id)] = {"user_id": str(data.user_id), "user_name": data.user_name}
        rec = data.model_dump()
        rec["id"] = next(self._show_id)
        rec["created_at"] = self._now()
        with self._lock:
            self._shows.append(rec)
        return rec

    def list_shows(self) -> List[Dict[str, Any]]:
        return sorted(self._shows, key=lambda x: x["id"], reverse=True)

    def search_shows(
        self, *, name: str, field: Literal["owner", "tix"], exact: bool
    ) -> List[Dict[str, Any]]:
        name = name.strip()
        if field == "owner":
            key = "user_name"
        else:
            key = "tix_name"

        def match(v: str) -> bool:
            return (v == name) if exact else (name in v)

        found = [s for s in self._shows if match(s[key])]
        return sorted(found, key=lambda x: x["id"], reverse=True)

    def get_show(self, show_id: int) -> Optional[Dict[str, Any]]:
        return next((s for s in self._shows if s["id"] == show_id), None)

    def add_comment(self, show_id: int, data: CommentCreate) -> Dict[str, Any]:
        if not self.get_show(show_id):
            raise KeyError("show_not_found")
        rec = data.model_dump()
        rec["id"] = next(self._comment_id)
        rec["show_id"] = show_id
        rec["created_at"] = self._now()
        with self._lock:
            self._comments.append(rec)
        return rec

    def list_comments(self, show_id: int, viewer_name: Optional[str]) -> List[Dict[str, Any]]:
        show = self.get_show(show_id)
        if not show:
            raise KeyError("show_not_found")

        if viewer_name and viewer_name.strip() == show["user_name"]:
            arr = [c for c in self._comments if c["show_id"] == show_id]
        else:
            arr = [c for c in self._comments if c["show_id"] == show_id and c["visibility"] == "public"]
        return sorted(arr, key=lambda x: x["id"], reverse=True)

# 單例 repository（之後要換 DB，就把這行改成 DB Repository）
repo: Repository = InMemoryRepository()
