from app.database import Base

from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Numeric, DateTime, func


class OrderItem(Base):
    __tablename__ = "order_items"

    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    price : Mapped[Decimal] = mapped_column(Numeric(10,2))

    # Foreign Keys
    product_id: Mapped[int] = mapped_column(ForeignKey("app.products.id"))
    order_id: Mapped[int] = mapped_column(ForeignKey("app.orders.id",ondelete="CASCADE"))

    # relationships
    order: Mapped["Order"] = relationship(back_populates="order_items")
    product : Mapped["Product"] = relationship(back_populates="order_items")
