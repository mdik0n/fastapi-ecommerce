from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Annotated
from decimal import Decimal


class CategoryCreate(BaseModel):
    """
        Model for the category creation and update
        Used in POST/PUT requests
    """

    name: Annotated[str, Field(min_length=3, max_length=50, description="Category name (3-50)")]
    parent_id: Annotated[int | None, Field(description="ID of the parent category if exists")] = None


class Category(CategoryCreate):
    """
        Model for the category response
        Used in GET request
    """

    id: Annotated[int, Field(description="Category ID")]
    is_active: Annotated[bool, Field(description="Activity of category")]

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
        Model for the product creation and update
        Used in POST/PUT requests
    """

    name: Annotated[str, Field(min_length=3, max_length=100, description="Product name (3-100)")]
    description: Annotated[str | None, Field(max_length=500, description="Product description (0-500)")] = None
    price: Annotated[Decimal, Field(gt=0, description="Product price (greater than 0)", decimal_places=2)]
    image_url: Annotated[str | None, Field(max_length=200, description="URL image of the product")] = None
    stock: Annotated[int, Field(ge=0, description="Product quantity in the stock (0 or more)")]
    category_id: Annotated[int, Field(gt=0, description="ID of the product category")]


class Product(ProductCreate):
    """
        Model for the product response
        Used in GET request
    """

    id: Annotated[int, Field(description="Product ID")]
    is_active: Annotated[bool, Field(description="Activity of product")]

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: Annotated[EmailStr, Field(default="user email")]
    password: Annotated[str, Field(min_length=9, description="User password (minimum 8 chars)")]
    role: Annotated[str, Field(default="buyer", pattern="^(buyer|seller)$", description="Role : 'buyer' or 'seller'")]


class User(BaseModel):
    id: int
    email: EmailStr
    is_active : bool
    role: str


    model_config = ConfigDict(from_attributes=True)
