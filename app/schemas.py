from pydantic import BaseModel, Field, ConfigDict, EmailStr, SecretStr
from decimal import Decimal
from datetime import datetime


class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=3, max_length=50,
                      description="Название категории (3-50 символов)")
    parent_id: int | None = Field(None, description="ID родительской категории, если есть")


class Category(BaseModel):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """
    id: int = Field(..., description="Уникальный идентификатор категории")
    name: str = Field(..., description="Название категории")
    parent_id: int | None = Field(None, description="ID родительской категории, если есть")
    is_active: bool = Field(..., description="Активность Категории")

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления продукта.
    Используется в POST и PUT запросах.
    """

    name: str = Field(..., min_length=3, max_length=100,
                      description="Название товара (3-100 символов)")
    description: str | None = Field(None, max_length=500,
                                    description="Описание товара (до 500 символов)")
    price: Decimal = Field(..., gt=0, description="Цена продукта", decimal_places=2)
    stock: int = Field(..., ge=0, description="Количество товара на складе (0 или больше)")

    image_url: str | None = Field(None, max_length=200, description="URL изображения товара")

    category_id: int = Field(..., description="ID категории, к которой относится товар")


class Product(BaseModel):
    """
    Модель для ответа с данными продукта.
    Используется в GET-запросах.
    """

    id: int = Field(..., description="Уникальный идентификатор продукта")
    name: str = Field(..., description="Название продукта")
    price: Decimal = Field(..., description="Цена продукта", gt=0, decimal_places=2)
    image_url: str | None = Field(None, description="URL изображения товара")
    stock: int = Field(..., description="Количество товара на складе")
    category_id: int = Field(..., description="ID категории, к которой относится товар")
    is_active: bool = Field(..., description="Активность продукта")

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str = Field(..., max_length=255, description="Email пользователя")
    password: SecretStr = Field(..., min_length=8, description="Пароль (минимум 8 символов)")
    role: str = Field(default="buyer", pattern="^(buyer|seller|admin)$", description="Роль: 'buyer','seller','admin'")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class Review(BaseModel):
    id: int
    user_id: int
    product_id: int
    comment: str
    comment_date: datetime
    grade: int
    is_active: bool


class ReviewCreate(BaseModel):
    product_id: int = Field(...,gt=0,description="product id ")
    comment: str | None = Field(None,description="product comment")
    grade : int = Field(...,ge=1,le=5,description="product grade")
