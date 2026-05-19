from app.database import Base
from sqlalchemy.orm import  mapped_column, Mapped,relationship
from sqlalchemy import String, ForeignKey, Text, Numeric
from decimal import Decimal



class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column()
    image_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)


    category_id : Mapped[int] = mapped_column(ForeignKey("categories.id"),nullable=False)
    seller_id : Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)

    category : Mapped["Category"] = relationship(back_populates="products")
    seller : Mapped["User"] = relationship(back_populates="products")