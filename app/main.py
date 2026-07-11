import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import db_manager
from app.models.base import Base

# Import all models to ensure they register on Base
from app.models.user import User
from app.models.category import Category
from app.models.budget import Budget
from app.models.transaction import Transaction, IncomeTransaction, ExpenseTransaction
from app.models.chat_message import ChatMessage
from app.models.ai_insight import AIInsight
from app.models.export_log import ExportLog
from app.models.notification import Notification

from app.routers import auth, profile, transaction, chatbot, notification
from app.core.exceptions import SpendTalkException

# Ensure profile pics directory exists
os.makedirs("uploads/profile_pics", exist_ok=True)

# Attempt table generation during start-up (SQLite or Aiven MySQL)
try:
    Base.metadata.create_all(bind=db_manager.engine)
    print("Database tables verified/initialized successfully.")
except Exception as e:
    print(f"Warning: Database connection failed during startup table generation: {e}")

app = FastAPI(
    title="SpendTalk API",
    description="AI-Powered Financial Chatbot Platform Backend (MySQL Connected)",
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

# Mount static files directory to serve user uploaded profile photos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
app.include_router(notification.router, prefix="/api")


@app.get("/")
def read_root():
    return {
        "app": "SpendTalk API",
        "status": "Running",
        "documentation": "/docs"
    }
