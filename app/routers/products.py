from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, update, delete, exists, func
from sqlalchemy.orm import Session, selectinload

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.models import Review as ReviewModel
from app.db_depends import get_db
from app.schemas import Product as ProductSchema, ProductCreate, Review as ReviewSchema, ProductList, ProductsRequest,ProductSortField,SortDir

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db
from app.auth import get_current_seller
from app.models import User as UserModel



router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get(path='/', response_model=ProductList)
async def get_all_products(
        request:  Annotated[ProductsRequest, Query()],
        db: AsyncSession = Depends(get_async_db),
) -> dict[str, Sequence[ProductModel] | int]:
    """Возвращает список всех активных товаров."""

    if request.min_price is not None and request.max_price is not None and request.min_price > request.max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='min_price не может быть больше max_price',
        )

    filters = [ProductModel.is_active == True]
    if request.category_id is not None:
        filters.append(ProductModel.category_id == request.category_id)
    if request.min_price is not None:
        filters.append(ProductModel.price >= request.min_price)
    if request.max_price is not None:
        filters.append(ProductModel.price <= request.max_price)
    if request.in_stock is not None:
        filters.append(ProductModel.stock > 0 if request.in_stock else ProductModel.stock == 0)

    if request.seller_id is not None:
        filters.append(ProductModel.seller_id == request.seller_id)

    # Подсчёт общего количества с учётом фильтров
    total_stmt = select(func.count()).select_from(ProductModel).where(*filters)
    total = await db.scalar(total_stmt) or 0

    sort_mapping = {
        ProductSortField.id: ProductModel.id,
        ProductSortField.created_at: ProductModel.created_at,
    }  # new

    sort_col = sort_mapping[request.sort_by]  # new
    sort_expr = sort_col.desc() if request.sort_dir == SortDir.desc else sort_col.asc() # new

    # Выборка товаров с фильтрами и пагинацией
    products_stmt = (
        select(ProductModel)
        .where(*filters)
        .order_by(sort_expr)
        .offset((request.page - 1) * request.page_size)
        .limit(request.page_size)
    )
    items = (await db.scalars(products_stmt)).all()

    return {
        "items": items,
        "total": total,
        "page": request.page,
        "page_size": request.page_size,
    }


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
        Created a new product, linked to the current seller (only for 'seller').
    """
    db_category = await db.scalar(
        select(
            exists().where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
        )
    )

    if not db_category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    new_product = ProductModel(**product.model_dump(), seller_id=current_user.id)

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
        Returns list of all products by category_id
    """
    db_category = await db.scalar(
        select(
            exists().where(CategoryModel.id == category_id, CategoryModel.is_active == True)
        )
    )

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    product_stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True)
    result = await db.scalars(product_stmt)

    return result.all()


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
        Returns product details by id
    """

    stmt = select(ProductModel).join(CategoryModel).where(ProductModel.id == product_id, ProductModel.is_active == True,
                                                          CategoryModel.is_active == True)
    result = await db.scalars(stmt)
    product = result.first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found or category is inactive")

    # db_category = await db.scalar(
    #     select(
    #         exists().where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    #     )
    # )
    #
    # if not db_category:
    #     raise HTTPException(status_code=400, detail="Category not found or inactive")

    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
        Updates product if it belongs to the current seller (only for seller)
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)

    db_product = result.first()

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")

    db_category = await db.scalar(
        select(
            exists().where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
        )
    )

    if not db_category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    for k, v in product.model_dump().items():
        setattr(db_product, k, v)

    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_async_db),
                         current_user: UserModel = Depends(get_current_seller)):
    """
       Performs soft deletion if it belongs to the current seller
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    result = await db.scalars(stmt)

    db_product = result.first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")

    db_product.is_active = False

    await db.commit()

    await db.refresh(db_product)  # Для возврата is_active = False
    return db_product


@router.get("/{product_id}/reviews/", response_model=list[ReviewSchema])
async def read_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    db_product = await db.scalar(
        select(
            exists().where(ProductModel.id == product_id, ProductModel.is_active)
        )
    )
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    review_stmt = select(ReviewModel).options(selectinload(ReviewModel.user)).where(
        ReviewModel.product_id == product_id, ReviewModel.is_active)
    reviews = (await db.scalars(review_stmt)).all()

    return reviews
