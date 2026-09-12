from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Text, DateTime,Boolean,CheckConstraint

from app.database import Base

from datetime import datetime


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("grade >= 1 AND grade <= 5", name="ck_grade_range"),
        {"schema": "app"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    grade : Mapped[int] = mapped_column(Integer)
    is_active : Mapped[bool] = mapped_column(Boolean,default=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("app.users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("app.products.id"))


#   releationships
    user : Mapped["User"] = relationship(back_populates="reviews")

