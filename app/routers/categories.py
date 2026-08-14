from fastapi import APIRouter

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.get("/")
async def get_all_categories():
    """
        Returns list of all product categories
    """

    return {"message": "List of all categories (mock)"}


@router.post("/")
async def create_category():
    """
        Creates a new category
    """

    return {"message": "Category was created"}


@router.put("/")
async def update_category(category_id: int):
    """
        Updates category by id
    """

    return {"message": f"Category with ID {category_id} was updated"}


@router.delete("/")
async def delete_category(category_id):
    """
        Deletes category by id
    """

    return {"message": f"Category with ID {category_id} was deleted"}
