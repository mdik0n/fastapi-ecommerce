from fastapi import FastAPI
# from routers.categories import router as category_router
from app.routers import categories
from app.routers import products

app = FastAPI(
    title="FastAPI e-commerce",
    version="0.1.0"
)

app.include_router(categories.router)
app.include_router(products.router)


@app.get("/")
async def root():
    """
    Root endpoint which confirms that API is working.
    """
    return {"message": "Welcome to the API of e-commerce shop!"}
