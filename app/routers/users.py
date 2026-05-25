import jwt
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import SECRET_KEY, ALGORITHM
from app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import User as UserSchema, UserCreate, RefreshTokenRequest
from app.models import User as UserModel
from sqlalchemy import select
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
      Регистрирует нового пользователя с ролью 'buyer' или 'seller'.
    """

    # Проверка уникальности email

    result = await db.scalars(select(UserModel).where(UserModel.email == user.email))
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered")

    # Создание объекта пользователя с хешированным паролем
    db_user = UserModel(
        email=user.email,
        role=user.role,
        hashed_password=hash_password(user.password.get_secret_value())
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_async_db)):
    """
     Аутентифицирует пользователя и возвращает access_token и refresh_token.
     """
    user = (await db.execute(
        select(UserModel).where(UserModel.email == form_data.username,
                                UserModel.is_active == True))).scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh-token")
async def refresh(
        body: RefreshTokenRequest,
        db: AsyncSession = Depends(get_async_db)
):
    """
    Обновляет refresh-токен, принимая старый refresh-токен в теле запроса.
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

        # Проверяем, что токен действительно refresh
        if email is None or token_type != "refresh":
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        # refresh-токен истёк
        raise credentials_exception
    except jwt.PyJWTError:
        # подпись неверна или токен повреждён
        raise credentials_exception

    result = await db.scalars(select(UserModel).where(UserModel.is_active == True, UserModel.email == email))

    user = result.first()

    if user is None:
        raise credentials_exception

    new_access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "id": user.id}
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"

    }
