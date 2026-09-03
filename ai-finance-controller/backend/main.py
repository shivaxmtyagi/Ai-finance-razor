from fastapi import FastAPI
from app.api import review_routes

app = FastAPI(title="AI Finance Controller API")

app.include_router(review_routes.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "online", "message": "Finance Controller Backend is running."}