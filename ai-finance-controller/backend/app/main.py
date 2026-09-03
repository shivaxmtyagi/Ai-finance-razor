from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import review_routes

app = FastAPI(title="AI Finance Controller API")

# Allow the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_routes.router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "online", "message": "Finance Controller Backend is running."}