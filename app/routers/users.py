import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi.security import OAuth2PasswordRequestForm

from app.db_depends import get_async_db
from app.schemas import UserCreate, User as UserSchema, RefreshTokenRequest
from app.models import User as UserModel
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token
from app.config import SECRET_KEY, ALGORITHM

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


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_async_db)
                ):
    """
    Authenticates user and returns JWT с email, role и id.
    """
    email = form_data.username
    password = form_data.password

    user = (
        await db.execute(select(UserModel).where(UserModel.email == email, UserModel.is_active))).scalar_one_or_none()

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh-token")
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    """
    Updated refresh-token, accepting old refresh-токен in the body.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    old_refresh_token = body.refresh_token

    try:
        payload = jwt.decode(old_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")

        if email is None or token_type != "refresh":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        # refresh-token expired
        raise credentials_exception
    except jwt.PyJWTError:
        # invalid signature
        raise credentials_exception

    user: UserModel | None = (await db.execute(
        select(UserModel).where(UserModel.email == email, UserModel.is_active == True))).scalar_one_or_none()

    if user is None:
        raise credentials_exception

    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )
    new_access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})

    return {
        "refresh_token": new_refresh_token,
        "access_token": new_access_token,

        "token_type": "bearer",
    }
