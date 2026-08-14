from fastapi import APIRouter

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/")
async def get_all_products():
    """
        Returns list of all products
    """
    return {"message": "List of all products (mock)"}


@router.post("/")
async def create_product():
    """
        Creates a new product
    """

    return {"message": "Product was created"}


@router.get("/category/{category_id}")
async def get_products_by_category(category_id: int):
    """
        Returns list of all products by category_id
    """
    return {"message": f"Products in category {category_id}"}


@router.get("/{product_id}")
async def get_product(product_id: int):
    """
        Returns product details by id
    """
    return {"message": f"Product details {product_id}"}


@router.put("/")
async def update_product(product_id: int):
    """
        Updates product by id
    """

    return {"message": f"Product with ID {product_id} was updated"}


@router.delete("/")
async def delete_product(product_id):
    """
        Deletes product by id
    """

    return {"message": f"Product with ID {product_id} was deleted"}
