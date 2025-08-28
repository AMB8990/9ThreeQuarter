from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Literal
from pydantic import UUID4
from app.service.service import (
    repo,
    ShowCreate, ShowOut,
    CommentCreate, CommentOut
)
import logging

router = APIRouter(prefix="/api", tags=["data"])

logging.config.fileConfig("./logging.conf", disable_existing_loggers=False)
logger = logging.getLogger("app")

@router.post("/shows", response_model=ShowOut)
def create_show(payload: ShowCreate):
    rec = repo.create_show(payload)
    logger.info(f"Created new show: {rec}")
    return ShowOut(**rec)

@router.get("/shows", response_model=List[ShowOut])
def list_shows():
    return [ShowOut(**s) for s in repo.list_shows()]

@router.get("/shows/search", response_model=List[ShowOut])
def search_shows(
    name: str = Query(..., description="搜尋的名字"),
    field: Literal["owner","tix"] = Query("owner", description="owner=擁有者, tix=票卷登記姓名"),
    exact: bool = True
):
    arr = repo.search_shows(name=name, field=field, exact=exact)
    logger.info(f"Search shows by {field}='{name}' (exact={exact}): found {len(arr)} records")
    return [ShowOut(**s) for s in arr]

@router.post("/shows/{show_id}/comments", response_model=CommentOut)
def add_comment(show_id: int, payload: CommentCreate):
    try:
        rec = repo.add_comment(show_id, payload)
        logger.info(f"Added comment to show {show_id}: {rec}")
        return CommentOut(**rec)
    except KeyError:
        logger.warning(f"Show not found for adding comment: {show_id}")
        raise HTTPException(status_code=404, detail="show_not_found")

@router.get("/shows/{show_id}/comments", response_model=List[CommentOut])
def api_list_comments(
    show_id: int,
    viewer_name: Optional[str] = Query(None),
    viewer_user_id: Optional[UUID4] = Query(None),
):
    try:
        uid = str(viewer_user_id) if viewer_user_id else None
        arr = repo.list_comments(show_id, viewer_name, uid)
        return [CommentOut(**c) for c in arr]
    except KeyError:
        raise HTTPException(status_code=404, detail="show_not_found")
    
@router.get("/healthz")
def healthz():
    return {"status": "ok"}
