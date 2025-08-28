from __future__ import annotations

from datetime import datetime
from itertools import count
from threading import Lock
from typing import Any, Dict, List, Literal, Optional, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field, UUID4

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

# 留言
class CommentCreate(BaseModel):
    author_user_id: Optional[UUID4] = None
    author_name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=2000)
    visibility: Literal["public", "private"] = "public"

class CommentOut(CommentCreate):
    id: int
    show_id: int
    created_at: str

class Repository(Protocol):
    # user
    def create_user(self, user_name: str) -> Dict[str, Any]: ...
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]: ...
    def find_users_by_name(self, user_name: str) -> List[Dict[str, Any]]: ...

    # show
    def create_show(self, data: ShowCreate) -> Dict[str, Any]: ...
    def list_shows(self) -> List[Dict[str, Any]]: ...
    def search_shows(self, *, name: str, field: Literal["owner", "tix"], exact: bool) -> List[Dict[str, Any]]: ...
    def get_show(self, show_id: int) -> Optional[Dict[str, Any]]: ...

    # comment
    def add_comment(self, show_id: int, data: CommentCreate) -> Dict[str, Any]: ...
    def list_comments(self, show_id: int, viewer_name: Optional[str], viewer_user_id: Optional[str]) -> List[Dict[str, Any]]: ...

class InMemoryRepository:
    def __init__(self) -> None:
        self._users: Dict[str, Dict[str, Any]] = {} 
        self._shows: List[Dict[str, Any]] = []
        self._comments: List[Dict[str, Any]] = []
        self._show_id = count(1)
        self._comment_id = count(1)
        self._lock = Lock()

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def _as_str(v: Any) -> Optional[str]:
        return str(v) if v is not None else None

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
        # 若 user_id 尚未存在，容錯建立（未來接 DB 可做 FK 檢查）
        uid = str(data.user_id)
        if uid not in self._users:
            self._users[uid] = {"user_id": uid, "user_name": data.user_name}

        rec = data.model_dump()
        rec["user_id"] = uid  
        rec["id"] = next(self._show_id)
        rec["created_at"] = self._now()
        with self._lock:
            self._shows.append(rec)
        return rec

    def list_shows(self) -> List[Dict[str, Any]]:
        return sorted(self._shows, key=lambda x: x["id"], reverse=True)

    def search_shows(self, *, name: str, field: Literal["owner", "tix"], exact: bool) -> List[Dict[str, Any]]:
        key = "user_name" if field == "owner" else "tix_name"
        name = name.strip()

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
        # 統一成字串，便於之後比對
        rec["author_user_id"] = self._as_str(rec.get("author_user_id"))

        with self._lock:
            self._comments.append(rec)
        return rec

    def list_comments(self, show_id: int, viewer_name: Optional[str], viewer_user_id: Optional[str]) -> List[Dict[str, Any]]:
        show = self.get_show(show_id)
        if not show:
            raise KeyError("show_not_found")

        owner_name = show["user_name"]
        owner_uid = self._as_str(show.get("user_id"))
        vu = self._as_str(viewer_user_id)

        is_owner = (viewer_name and viewer_name == owner_name) or (vu and owner_uid and vu == owner_uid)

        def is_author(c: Dict[str, Any]) -> bool:
            # 作者可見：user_id 相等 或 名稱相等（未登入時）
            if vu and c.get("author_user_id") and self._as_str(c["author_user_id"]) == vu:
                return True
            if viewer_name and c.get("author_name") == viewer_name:
                return True
            return False

        if is_owner:
            visible = [c for c in self._comments if c["show_id"] == show_id]
        else:
            visible = [
                c for c in self._comments
                if c["show_id"] == show_id and (c["visibility"] == "public" or is_author(c))
            ]

        return sorted(visible, key=lambda x: x["id"], reverse=True)

#之後換 DB，把這行換成對應的 SqlAlchemyRepository 
repo: Repository = InMemoryRepository()
