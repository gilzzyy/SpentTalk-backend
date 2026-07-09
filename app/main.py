from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import db_manager
from app.models.base import Base

# Import models to ensure they register on Base
from app.models.user import User
from app.models.profile import FinancialProfile
from app.models.transaction import Transaction

from app.routers import auth, profile, transaction, chatbot
from app.core.exceptions import SpendTalkException

# Attempt table generation during start-up (SQLite or MySQL)
try:
    Base.metadata.create_all(bind=db_manager.engine)
    print("Database tables initialized successfully.")
except Exception as e:
    print(f"Warning: Database connection failed during startup table generation: {e}")

app = FastAPI(
    title="SpendTalk API",
    description="AI-Powered Financial Chatbot Platform Backend",
    version="1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global custom exception handling
@app.exception_handler(SpendTalkException)
def handle_spendtalk_exceptions(request: Request, exc: SpendTalkException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message}
    )

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(transaction.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "app": "SpendTalk API",
        "status": "Running",
        "documentation": "/docs"
    }
