from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import Category as CategorySchema, CategoryCreate
from app.models import Category as CategoryModel
from app.database import get_db, get_async_db

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, exists
from app.auth import get_current_admin
from app.models import User

# Создаём маршрутизатор с префиксом и тегом
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех категорий товаров.
    """
    result = await db.scalars(select(CategoryModel).where(CategoryModel.is_active == True))
    categories = result.all()
    return categories


@router.post("/", response_model=CategorySchema, status_code=201)
async def create_category(
        category: CategoryCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_admin)
):
    """
    Создаёт новую категорию.
    """
    if category.parent_id is not None:
        stmt = select(
            exists().where(
                CategoryModel.id == category.parent_id,
                CategoryModel.is_active.is_(True)
            )
        )
        parent_exists = await db.scalar(stmt)
        if not parent_exists:
            raise HTTPException(status_code=400, detail="Parent category not found")

    db_category = CategoryModel(**category.model_dump())

    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)

    return db_category


@router.put("/{category_id}", response_model=CategorySchema, status_code=201)
async def update_category(
        category_id: int, category: CategoryCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_admin)
):
    """
    Обновляет категорию по её ID.
    """

    stmt = select(CategoryModel).where(CategoryModel.is_active == True, CategoryModel.id == category_id)
    db_category = await db.scalar(stmt)

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.parent_id is not None:
        if category_id == category.parent_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category cannot be its own parent")

        parent_stmt = select(CategoryModel).where(CategoryModel.is_active, CategoryModel.id == category.parent_id)
        parent_result = await db.scalars(parent_stmt)
        parent_category = parent_result.first()

        if not parent_category:
            raise HTTPException(status_code=400, detail="Parent category not found")

    update_data = category.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_category, key, value)

    await db.commit()
    await db.refresh(db_category)

    return db_category


@router.delete("/{category_id}")
async def delete_category(category_id: int,
                          db: AsyncSession = Depends(get_async_db),
                          current_user: User = Depends(get_current_admin)
                          ):
    """
    Удаляет категорию по её ID.
    """
    stmt = select(CategoryModel).where(CategoryModel.is_active == True, CategoryModel.id == category_id)
    category = await db.scalar(stmt)

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = False
    await db.commit()

    return {"status": "success", "message": "Category marked as inactive"}
