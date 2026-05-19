from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import User as UserSchema, UserCreate
from app.models import User as UserModel
from sqlalchemy import select
from app.auth import hash_password, verify_password, create_access_token
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
    Аутентифицирует пользователя и возвращает JWT с email, role и id.
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
    return {"access_token": access_token, "token_type": "bearer"}
