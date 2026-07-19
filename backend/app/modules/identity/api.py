from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id_for_demo, get_db
from app.core.config import Settings, get_settings
from app.modules.identity import avatar_storage
from app.modules.identity import service
from app.modules.identity.api_schemas import (
    UserCreateRequest,
    UserProfileUpdateRequest,
    UserResponse,
    user_response,
)
from app.modules.identity.exceptions import (
    UserAlreadyExistsError,
    UserContactRequiredError,
    UserNotFoundError,
)


router = APIRouter(prefix="/identity", tags=["identity"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)) -> UserResponse:
    try:
        user = service.create_user(
            db,
            email=payload.email,
            phone=payload.phone,
            nickname=payload.nickname,
            gender=payload.gender,
            birth_date=payload.birth_date,
        )
    except UserContactRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return user_response(user)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)) -> UserResponse:
    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user_response(user)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> UserResponse:
    user = service.get_user(db, current_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user_response(user)


@router.patch("/me/profile", response_model=UserResponse)
def update_me_profile(
    payload: UserProfileUpdateRequest,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
) -> UserResponse:
    try:
        user = service.update_profile(
            db,
            current_user_id,
            nickname=payload.nickname,
            avatar_url=payload.avatar_url,
            gender=payload.gender,
            birth_date=payload.birth_date,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found") from exc
    return user_response(user)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_me_avatar(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id_for_demo),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    try:
        user = service.upload_avatar(
            db,
            current_user_id,
            content=await request.body(),
            mime_type=request.headers.get("content-type"),
            settings=settings,
        )
    except (UserNotFoundError, avatar_storage.AvatarUploadError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user_response(user)


@router.get("/users/{user_id}/avatar")
def get_user_avatar(user_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    user = service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    try:
        file_path = avatar_storage.get_avatar_path(user_id=user_id, settings=get_settings())
    except avatar_storage.AvatarUploadError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FileResponse(file_path, media_type="image/*")
