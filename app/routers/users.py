from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db_depends import get_async_db
from app.schemas import UserCreate, User as UserSchema
from app.models import User as UserModel
from app.auth import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"]
                   )


@router.post("/", status_code=201, response_model=UserSchema)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
        Registers a new user with the role buyer or seller
    """

    # Checking email uniqueness
    user_exists = (await db.scalars(select(UserModel).where(UserModel.email == user.email))).first()

    if user_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"User with the email {user.email} already exists")

    new_user = UserModel(email=user.email, role=user.role,
                         hashed_password=hash_password(user.password.get_secret_value()))

    db.add(new_user)
    await db.commit()

    return new_user
