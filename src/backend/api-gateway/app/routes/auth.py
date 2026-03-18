"""Auth routes — registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import hash_password, verify_password, create_access_token
from shared.database import get_db
from shared.models import User, UserProfile
from shared.schemas import RegisterRequest, LoginRequest, AuthResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    exists = await db.execute(select(User).where(User.email == body.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        phone=body.phone,
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(
        user_id=user.id,
        skills=[],
        preferred_technologies=[],
        preferred_roles=[],
    )
    db.add(profile)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.email, user.full_name)
    return AuthResponse(
        token=token,
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name),
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = create_access_token(user.id, user.email, user.full_name)
    return AuthResponse(
        token=token,
        user=UserOut(id=user.id, email=user.email, full_name=user.full_name),
    )
