from app.database import Base

from decimal import Decimal
from enum import Enum
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Numeric, DateTime, func,Enum as SAEnum



class OrderStatus(str,Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus),default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    #  Foreign keys
    user_id: Mapped[int] = mapped_column(ForeignKey("app.users.id"))

    user: Mapped["User"] = relationship(back_populates="orders")
    order_items : Mapped[list["OrderItem"]] = relationship(back_populates="order")