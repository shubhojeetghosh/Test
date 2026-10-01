from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.authentication.routes.auth import router as auth_router


app = FastAPI(
    title="Quiz Platform API",
    description="Backend API for Quiz Platform",
    version="1.0.0"
)


# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",

        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# AUTHENTICATION
# ==================================================

app.include_router(auth_router)


# ==================================================
# ROOT
# ==================================================

@app.get("/")
def root():
    return {
        "message": "Quiz Platform Backend is running",
        "status": "success"
    }


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
