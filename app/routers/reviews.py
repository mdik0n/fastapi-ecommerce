from fastapi import APIRouter, HTTPException, Depends, status

from app.db_depends import get_async_db
from app.models import Review as ReviewModel, User as UserModel, Product as ProductModel
from app.schemas import Review as ReviewSchema, ReviewCreate
from app.auth import get_current_user

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists

router = APIRouter(prefix="/reviews", tags=["reviews"])


async def calculate_grade(product: ProductModel, db: AsyncSession):
    stmt = select(func.avg(ReviewModel.grade)).where(ReviewModel.product_id == product.id, ReviewModel.is_active)

    rating = await db.scalar(stmt)

    product.rating = round(rating, 2) if rating else 0.0


@router.get("/", response_model=list[ReviewSchema])
async def read_reviews(db: AsyncSession = Depends(get_async_db)):
    stmt = select(ReviewModel).where(ReviewModel.is_active)
    reviews = (await db.scalars(stmt)).all()

    return reviews


@router.post("/", response_model=ReviewSchema)
async def create_review(review: ReviewCreate,
                        current_user: UserModel = Depends(get_current_user),
                        db: AsyncSession = Depends(get_async_db)):
    if current_user.role != 'buyer':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only buyers can create review")

    product_stmt = select(ProductModel).where(ProductModel.id == review.product_id, ProductModel.is_active)
    db_product = await db.scalar(product_stmt)

    if db_product is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found or is inactive")

    review_exists = await db.scalar(select(
        exists().where(ReviewModel.user_id == current_user.id, ReviewModel.product_id == db_product.id,
                       ReviewModel.is_active)
    ))

    if review_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already reviewed this product")

    new_review = ReviewModel(**review.model_dump(), user_id=current_user.id)

    db.add(new_review)

    await db.flush()  # чтобы new_review получил id, без полного коммита

    await calculate_grade(db_product, db)

    await db.commit()  # один коммит на всё: и отзыв, и рейтинг товара
    await db.refresh(new_review)

    return new_review


@router.delete("/{review_id}")
async def delete_review(review_id: int, db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_user)):
    review = await db.scalar(select(ReviewModel).where(ReviewModel.id == review_id, ReviewModel.is_active))

    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or inactive")

    if current_user.id != review.user_id and current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can delete your own review")

    review.is_active = False

    product_stmt = select(ProductModel).where(ProductModel.id == review.product_id)
    db_product = await db.scalar(product_stmt)

    await db.flush()  # чтобы is_active = False попало в БД до пересчёта среднего.

    await calculate_grade(db_product, db)

    await db.commit()

    return {"message": "Review deleted"}
