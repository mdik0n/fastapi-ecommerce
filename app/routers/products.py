from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import Product as ProductSchema, ProductCreate
from app.models import Product as ProductModel, Category as CategoryModel
from sqlalchemy import select, exists, update

from app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_seller
from app.models.users import User as UserModel
from app.models.reviews import Review as ReviewModel
from app.schemas import Review as ReviewSchema

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров.
    """
    products = (await db.scalars(select(ProductModel).where(ProductModel.is_active))).all()
    return products


@router.post("/", response_model=ProductSchema, status_code=201)
async def create_product(
        product: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)
):
    """
    Создаёт новый товар.
    """
    stmt = select(
        exists().where(CategoryModel.is_active == True, CategoryModel.id == product.category_id)
    )

    category_exists = await db.scalar(stmt)
    if not category_exists:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.is_active == True, CategoryModel.id == category_id))
    category = category_result.first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    product_result = await db.scalars(
        select(ProductModel).where(ProductModel.is_active == True, ProductModel.category_id == category_id))
    products = product_result.all()
    return products


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Получает продукт по id
    """
    product = await db.scalar(select(ProductModel).where(ProductModel.is_active, ProductModel.id == product_id))

    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    category_stmt = select(
        exists().where(CategoryModel.is_active, CategoryModel.id == product.category_id)
    )
    category_exists = await db.scalar(category_stmt)

    if not category_exists:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
        product_id: int,
        product: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)

):
    """
    Обновляет продукт по её ID.
    """
    db_product = await db.scalar(
        select(ProductModel).where(ProductModel.is_active == True, ProductModel.id == product_id))

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")

    category_exists = await db.scalar(
        select(
            exists().where(
                CategoryModel.is_active == True,
                CategoryModel.id == product.category_id)
        )
    )

    if not category_exists:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    for key, value in product.model_dump().items():
        setattr(db_product, key, value)

    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(
        product_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)

):
    """
    Удаляет продукт по её ID.
    """
    db_product = await  db.scalar(
        select(ProductModel).where(ProductModel.is_active == True, ProductModel.id == product_id))

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")

    db_product.is_active = False
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.get("/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_reviews_by_product_id(product_id: int, db: AsyncSession = Depends(get_async_db)):
    product = await db.scalar(select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True))

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    stmt = select(ReviewModel).where(ReviewModel.product_id == product_id, ReviewModel.is_active == True)
    result = await db.scalars(stmt)
    reviews = result.all()

    return reviews
