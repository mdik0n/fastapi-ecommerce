from decimal import Decimal

from fastapi import APIRouter, Depends, status, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.schemas import Order as OrderSchema
from app.db_depends import get_async_db
from app.auth import get_current_user
from app.models import (
    User as UserModel,
    CartItem as CartItemModel,
    Order as OrderModel,
    OrderItem
)

router = APIRouter(prefix="/order", tags=["order"])


@router.post("/checkout", response_model=OrderSchema)
async def checkout(current_user: UserModel = Depends(get_current_user),
                   db: AsyncSession = Depends(get_async_db)
                   ):
    stmt = select(CartItemModel).options(selectinload(CartItemModel.product)).where(CartItemModel.user == current_user)
    cart_items = (await db.scalars(stmt)).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = OrderModel(user_id=current_user.id)
    db.add(order)

    total = Decimal('0')

    for cart_item in cart_items:
        product = cart_item.product
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {cart_item.product_id} is unavailable",
            )
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product {product.name}",
            )

        product.stock -= cart_item.quantity
        order_item = OrderItem(product_id=cart_item.product_id, quantity=cart_item.quantity,
                               price=cart_item.product.price, product=product)

        total += product.price * cart_item.quantity

        order.order_items.append(order_item)

        # await db.delete(cart_item)

    order.total = total
    await db.execute(delete(CartItemModel).where(CartItemModel.user_id == current_user.id))

    await db.commit()

    return order


@router.get("/", response_model=list[OrderSchema])
async def read_user_orders(
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)):
    stmt = (select(OrderModel).
            options(selectinload(OrderModel.order_items).selectinload(OrderItem.product))
            .where(OrderModel.user == current_user).order_by(OrderModel.created_at.desc())
            )
    orders = (await db.scalars(stmt)).all()

    return orders


@router.get("/{order_id}", response_model=OrderSchema)
async def read_user_order(
        order_id: int,
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)
):
    stmt = (select(OrderModel).
            options(selectinload(OrderModel.order_items).selectinload(OrderItem.product))
            .where(OrderModel.user == current_user, OrderModel.id == order_id)
            )
    order = await db.scalar(stmt)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
