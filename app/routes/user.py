from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import UUID4
from app.service.service import repo, UserCreate, UserOut
import logging

router = APIRouter(prefix="/api/users", tags=["users"])

logging.config.fileConfig("./logging.conf", disable_existing_loggers=False)
logger = logging.getLogger("app")

@router.post("/register", response_model=UserOut)
def register_user(payload: UserCreate):
    rec = repo.create_user(payload.user_name)
    logger.info(f"Registered new user: {rec}")
    return UserOut(user_id=rec["user_id"], user_name=rec["user_name"])

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: UUID4):
    rec = repo.get_user(str(user_id))
    if not rec:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(status_code=404, detail="user_not_found")
    logger.info(f"Retrieved user: {rec}")
    return UserOut(user_id=rec["user_id"], user_name=rec["user_name"])

@router.get("/by-name", response_model=List[UserOut])
def get_users_by_name(user_name: str = Query(...)):
    arr = repo.find_users_by_name(user_name)
    logger.info(f"Found {len(arr)} users with name '{user_name}'")
    return [UserOut(user_id=a["user_id"], user_name=a["user_name"]) for a in arr]
