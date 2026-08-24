from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete, exists
from sqlalchemy.orm import Session

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.db_depends import get_db
from app.schemas import Product as ProductSchema, ProductCreate

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: Session = Depends(get_db)):
    """
        Returns list of all products
    """

    products = db.scalars(
        select(ProductModel).join(CategoryModel).where(ProductModel.is_active == True,
                                                       CategoryModel.is_active == True,
                                                       ProductModel.stock > 0)).all()
    return products


@router.post("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
        Creates a new product
    """
    db_category = db.scalar(
        select(
            exists().where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
        )
    )

    if not db_category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    new_product = ProductModel(**product.model_dump())

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
        Returns list of all products by category_id
    """
    db_category = db.scalar(
        select(
            exists().where(CategoryModel.id == category_id, CategoryModel.is_active == True)
        )
    )

    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    product_stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True)
    products = db.scalars(product_stmt).all()

    return products


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
        Returns product details by id
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    product = db.scalars(stmt).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    db_category = db.scalar(
        select(
            exists().where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
        )
    )

    if not db_category:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """
        Updates product by id
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    db_product = db.scalars(stmt).first()

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    db_category = db.scalar(
        select(
            exists().where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
        )
    )

    if db_category is None:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))

    db.commit()
    db.refresh(db_product)

    return db_product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
        Deletes product by id
    """
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    db_product = db.scalars(stmt).first()

    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found or inactive")

    db_product.is_active = False

    db.commit()

    return {"status": "success", "message": "Product marked as inactive"}
