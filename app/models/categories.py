from app.database import Base
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=True)

    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")

    parent: Mapped["Category|None"] = relationship(back_populates="children", remote_side="Category.id")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")


# if __name__ == "__main__":
#     from sqlalchemy.schema import CreateTable
#     print(CreateTable(Category.__table__))



