from datetime import datetime

from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, Text, Numeric, ForeignKey, Float, text, DateTime, func,Computed,Index
from decimal import Decimal
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.models.cart_items import CartItem


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_tsv_gin", "tsv", postgresql_using="gin"),
        {'schema': 'app'},
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0, server_default=text('0'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


    tsv: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
            """
            setweight(to_tsvector('english', coalesce(name, '')), 'A')
            || 
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
            """,
            persisted=True,
        ),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(ForeignKey("app.categories.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("app.users.id"), nullable=False)

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    seller: Mapped["User"] = relationship("User", back_populates="products")
    cart_items : Mapped[list["CartItem"]]  = relationship(back_populates="product")