from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK

from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategorySchema, CategoryCreate
from app.db_depends import get_db

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: Session = Depends(get_db)):
    """
        Returns list of all product categories
    """

    stmt = select(CategoryModel).where(CategoryModel.is_active == True)
    categories = db.scalars(stmt).all()

    return categories


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """
        Creates a new category
    """

    # Checking for the parent category existence

    if category.parent_id is not None:
        stmt = select(CategoryModel).where(CategoryModel.id == category.parent_id, CategoryModel.is_active == True)
        parent_category = db.scalars(stmt).first()

        if parent_category is None:
            raise HTTPException(status_code=400, detail="Parent category does not exist")

    new_category = CategoryModel(**category.model_dump())

    db.add(new_category)
    db.commit()

    db.refresh(new_category)

    return new_category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_db)):
    """
        Updates category by id
    """
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)

    category_db = db.scalars(stmt).first()

    #Checking for the category existence
    if category_db is None:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    # Checking for the parent category existence
    if category.parent_id is not None:
        stmt = select(CategoryModel).where(CategoryModel.id == category.parent_id, CategoryModel.is_active == True)
        parent_category = db.scalars(stmt).first()

        if parent_category is None:
            raise HTTPException(status_code=400, detail="Parent category does not exist")

    db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(**category.model_dump()))

    db.commit()
    db.refresh(category_db)

    return category_db


@router.delete("/{category_id}", status_code=HTTP_200_OK)
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
        Deletes category by id
    """

    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True)
    category = db.scalars(stmt).first()

    #Checking for the category existence

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(is_active=False))
    db.commit()

    return {"status": "success", "message": "Category marked as inactive"}
