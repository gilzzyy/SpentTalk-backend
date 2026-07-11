from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.notification_repository import NotificationRepository
from app.models.category import Category
from app.models.budget import Budget
from app.models.notification import Notification
from app.schemas.category import CategoryCreate, CategoryOut
from app.schemas.budget import OnboardingRequest, BudgetCreate, BudgetOut
from app.services.finance_manager import FinanceManager
from app.services.excel_exporter import ExcelExporter
from typing import List, Optional



router = APIRouter(prefix="/profile", tags=["Profile & Onboarding"])

class BalanceUpdateRequest(BaseModel):
    initial_balance: Decimal = Field(..., ge=0)

@router.get("/categories", response_model=List[CategoryOut])
def get_categories(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    return repo.get_user_categories(current_user_id)

@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryCreate, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    budget_repo = BudgetRepository(db)
    
    # Check if category already exists
    existing = repo.get_by_name(current_user_id, payload.name)
    if existing:
        if not existing.is_active:
            existing.is_active = True
            if payload.icon:
                existing.icon = payload.icon
            repo.update(existing)
            cat = existing
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kategori sudah terdaftar.")
    else:
        cat = Category(user_id=current_user_id, name=payload.name, icon=payload.icon)
        cat = repo.create(cat)
        
    # If budget_amount is specified, register/create the budget record
    if payload.budget_amount is not None and payload.period:
        existing_budget = budget_repo.get_by_user_and_category(current_user_id, cat.id, payload.period)
        if existing_budget:
            existing_budget.amount = payload.budget_amount
            budget_repo.update(existing_budget)
        else:
            new_budget = Budget(user_id=current_user_id, category_id=cat.id, period=payload.period, amount=payload.budget_amount)
            budget_repo.create(new_budget)
            
    return cat

@router.delete("/categories/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(id: int, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = CategoryRepository(db)
    cat = repo.get_by_id(id)
    if not cat or cat.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori tidak ditemukan.")
    if cat.is_default:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kategori bawaan tidak dapat dihapus.")
    
    # Set to inactive instead of hard deleting to preserve referential integrity for old transactions
    cat.is_active = False
    repo.update(cat)

@router.put("/onboarding", status_code=status.HTTP_200_OK)
def complete_onboarding(payload: OnboardingRequest, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    budget_repo = BudgetRepository(db)
    cat_repo = CategoryRepository(db)
    
    user = user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    # 1. Access Control: Guard against double-onboarding
    if user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User sudah menyelesaikan onboarding."
        )
        
    # Save original commit method to allow single atomic transaction
    original_commit = db.commit
    db.commit = db.flush
    
    try:
        # 2. Update initial, current balance and monthly income
        user.initial_balance = payload.initial_balance
        user.current_balance = payload.initial_balance
        user.monthly_income = payload.monthly_income
        user.onboarding_completed = True
        user_repo.update(user)
        
        # 3. Deduplicate onboarding budgets to prevent duplicate database constraints
        unique_budgets = {}
        for b in payload.budgets:
            name_key = b.category_name.strip().lower() if b.category_name else ""
            key = (b.category_id, name_key, b.period)
            unique_budgets[key] = b
        
        # 4. Create or update budget goals
        for b in unique_budgets.values():
            target_category_id = b.category_id
            
            # Verify if category_id is valid and belongs to the user
            if target_category_id:
                cat = cat_repo.get_by_id(target_category_id)
                if not cat or cat.user_id != current_user_id:
                    target_category_id = None  # Fallback to name resolution
                    
            if not target_category_id and b.category_name:
                # Check if category exists by name
                existing_cat = cat_repo.get_by_name(current_user_id, b.category_name)
                if existing_cat:
                    target_category_id = existing_cat.id
                else:
                    # Create category dynamically with Capitalized Name
                    formatted_name = b.category_name.strip().title()
                    new_cat = Category(user_id=current_user_id, name=formatted_name, icon="folder")
                    new_cat = cat_repo.create(new_cat)
                    target_category_id = new_cat.id
                    
            if not target_category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Kategori tidak valid: ID '{b.category_id}' atau Nama '{b.category_name}' tidak ditemukan."
                )
                
            existing = budget_repo.get_by_user_and_category(current_user_id, target_category_id, b.period)
            if existing:
                existing.amount = b.amount
                budget_repo.update(existing)
            else:
                new_budget = Budget(user_id=current_user_id, category_id=target_category_id, period=b.period, amount=b.amount)
                budget_repo.create(new_budget)
                
        # Restore commit method and commit atomically
        db.commit = original_commit
        db.commit()
    except Exception as e:
        # Restore commit method and rollback
        db.commit = original_commit
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal memproses onboarding: {str(e)}"
        )
        
    return {"message": "Onboarding keuangan berhasil disimpan."}





@router.get("/budgets", response_model=List[BudgetOut])
def get_budgets(period: str = Query(..., pattern=r"^\d{4}-\d{2}$"), current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = BudgetRepository(db)
    return repo.get_user_budgets(current_user_id, period)

@router.put("/budgets", response_model=BudgetOut)
def set_budget(payload: BudgetCreate, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = BudgetRepository(db)
    existing = repo.get_by_user_and_category(current_user_id, payload.category_id, payload.period)
    if existing:
        existing.amount = payload.amount
        return repo.update(existing)
    
    new_budget = Budget(user_id=current_user_id, category_id=payload.category_id, period=payload.period, amount=payload.amount)
    return repo.create(new_budget)

@router.put("/balance", status_code=status.HTTP_200_OK)
def update_balance(payload: BalanceUpdateRequest, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """
    Updates the user's initial balance at any time and automatically recalculates current balance.
    Fulfills budget tracker editing features (F-09).
    """
    user_repo = UserRepository(db)
    tx_repo = TransactionRepository(db)
    finance_mgr = FinanceManager()
    
    user = user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    user.initial_balance = payload.initial_balance
    
    # Recalculate balance
    all_tx = tx_repo.get_by_user(current_user_id)
    user.current_balance = finance_mgr.calculate_current_balance(payload.initial_balance, all_tx)
    
    user_repo.update(user)
    return {
        "message": "Saldo awal berhasil diperbarui.",
        "saldo_awal": user.initial_balance,
        "saldo_terkini": user.current_balance
    }

@router.get("/export")
def export_profile_excel(
    period: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Allows Excel export triggered from the profile view (F-13).
    """
    tx_repo = TransactionRepository(db)
    budget_repo = BudgetRepository(db)
    cat_repo = CategoryRepository(db)
    user_repo = UserRepository(db)
    finance_mgr = FinanceManager()
    exporter = ExcelExporter()
    
    user = user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    if period:
        all_tx = tx_repo.get_by_user(current_user_id, period=period)
        target_period = period
    else:
        all_tx = tx_repo.get_by_user(current_user_id)
        target_period = date.today().strftime("%Y-%m")
        
    budgets = budget_repo.get_user_budgets(current_user_id, target_period)
    categories = cat_repo.get_user_categories(current_user_id)
    budget_progress = finance_mgr.track_budget_progress(budgets, categories, all_tx)
    
    excel_stream = exporter.export_transactions(user.name, all_tx, budget_progress)
    period_suffix = target_period.replace("-", "")
    filename = f"SpendTalk_{user.name}_{period_suffix}.xlsx"
    
    # Create notification for Excel export
    notif_repo = NotificationRepository(db)
    notif_repo.create(Notification(
        user_id=current_user_id,
        title="Ekspor Laporan",
        message=f"Laporan keuangan periode {target_period} berhasil diekspor ke Excel!",
        type="export"
    ))
    
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}

    )


@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_all_data(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    tx_repo = TransactionRepository(db)
    budget_repo = BudgetRepository(db)
    cat_repo = CategoryRepository(db)
    
    user = user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    # Delete transactions
    transactions = tx_repo.get_by_user(current_user_id)
    for tx in transactions:
        tx_repo.delete(tx.id)
        
    # Delete budgets
    budgets = db.query(Budget).filter(Budget.user_id == current_user_id).all()
    for b in budgets:
        budget_repo.delete(b.id)
        
    # Delete custom categories
    categories = cat_repo.get_user_categories(current_user_id, only_active=False)
    for cat in categories:
        if not cat.is_default:
            cat_repo.delete(cat.id)
        else:
            cat.is_active = True # Restore defaults
            cat_repo.update(cat)
            
    # Reset user balance
    user.initial_balance = Decimal("0.00")
    user.current_balance = Decimal("0.00")
    user.onboarding_completed = False
    user_repo.update(user)
    
    return {"message": "Seluruh data transaksi dan alokasi anggaran berhasil di-reset ke kondisi awal."}
