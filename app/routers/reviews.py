from fastapi import APIRouter, Depends, status, HTTPException
from app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.models.products import Product as ProductModel
from sqlalchemy import select, exists, update
from app.auth import get_current_user
from app.schemas import ReviewCreate, Review as ReviewSchema

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)

from sqlalchemy.sql import func


async def update_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(rating=avg_rating))


@router.get("",response_model=list[ReviewSchema])
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    """
        Getting all active reviews
    """

    reviews = (await db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))).all()

    return reviews


@router.post("", response_model=ReviewSchema)
async def create_review(review: ReviewCreate,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_user)
                        ):
    """
        Create review
    """

    if current_user.role != "buyer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only buyers can create review")

    product_db = await db.scalar(select(ProductModel).where(
        ProductModel.id == review.product_id,
        ProductModel.is_active == True
    ))

    if not product_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")

    # Check if user already left comment
    stmt = select(
        exists().where(ReviewModel.product_id == review.product_id, ReviewModel.user_id == current_user.id)
    )

    review_exists = await db.scalar(stmt)

    if review_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already left comment")

    review_db = ReviewModel(**review.model_dump(), user_id=current_user.id)

    db.add(review_db)
    await db.flush()

    await update_product_rating(db, review.product_id)

    await db.commit()
    await db.refresh(review_db)
    return review_db


@router.delete("/{review_id}")
async def delete_review(review_id: int,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_user)
                        ):
    review = await db.scalar(select(ReviewModel).where(ReviewModel.id == review_id, ReviewModel.is_active == True))

    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or inactive")

    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can delete your own review")

    review.is_active = False

    await db.flush()

    await update_product_rating(db, review.product_id)

    await db.commit()

    return {"message": "Review deleted"}
