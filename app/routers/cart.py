from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from starlette.responses import Response

from app.schemas import (CartItem as CartItemSchema,
                         CartItemCreate,
                         CartItemUpdate,
                         Cart as CartSchema
                         )
from app.db_depends import get_async_db
from app.models import User as UserModel, Product as ProductModel, CartItem as CartItemModel
from app.auth import get_current_user

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

router = APIRouter(prefix="/cart", tags=["cart"])


async def _get_cart_item(db: AsyncSession, user_id: int, product_id: int):
    stmt = (
        select(CartItemModel).options(selectinload(CartItemModel.product)).
        where(CartItemModel.user_id == user_id,
              CartItemModel.product_id == product_id)
    )

    result = (await db.scalars(stmt)).first()

    return result


async def _ensure_product_available(db: AsyncSession, product_id: int):
    stmt = (
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active)
    )
    result = await db.scalar(stmt)

    if result is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")


@router.get("/", response_model=CartSchema)
async def get_cart(current_user: UserModel = Depends(get_current_user),
                   db: AsyncSession = Depends(get_async_db)):
    stmt = select(CartItemModel).options(selectinload(CartItemModel.product)).where(
        CartItemModel.user_id == current_user.id)
    items = list((await db.scalars(stmt)).all())

    total_quantity = sum(item.quantity for item in items)

    total_sum = sum((item.quantity * item.product.price for item in items), Decimal("0.00"))

    return CartSchema(
        user_id=current_user.id,
        cart_items=items,
        total_quantity=total_quantity,
        total_sum=total_sum
    )


@router.post("/items", response_model=CartItemSchema, status_code=201)
async def add_item_to_cart(payload: CartItemCreate,
                           current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_async_db)):
    await  _ensure_product_available(db, payload.product_id)

    cart_item = await _get_cart_item(db, current_user.id, product_id=payload.product_id)

    if cart_item is not None:
        cart_item.quantity += payload.quantity
    else:
        cart_item = CartItemModel(user_id=current_user.id, product_id=payload.product_id, quantity=payload.quantity)

        db.add(cart_item)

    await db.commit()
    user_cart = await _get_cart_item(db, current_user.id, product_id=payload.product_id)

    return user_cart


@router.put("/items/{product_id}", response_model=CartItemSchema)
async def update_cart_item(product_id: int, payload: CartItemUpdate,
                           current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_async_db)):
    await _ensure_product_available(db, product_id)

    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    cart_item.quantity = payload.quantity

    await db.commit()
    updated_item = await _get_cart_item(db, current_user.id, product_id)

    return updated_item


@router.delete("/items/{product_id}")
async def remove_item_from_cart(product_id: int,
                                current_user: UserModel = Depends(get_current_user),
                                db: AsyncSession = Depends(get_async_db)):
    cart_item = await _get_cart_item(db, current_user.id, product_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/")
async def remove_cart(current_user: UserModel = Depends(get_current_user),
                      db: AsyncSession = Depends(get_async_db)):
    await db.execute(delete(CartItemModel).where(CartItemModel.user_id == current_user.id))
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
