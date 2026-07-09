from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.profile_repository import ProfileRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.profile import ProfileUpdate, ProfileOut
from app.core.exceptions import ResourceNotFoundError
from decimal import Decimal

router = APIRouter(prefix="/profile", tags=["Financial Profile"])

@router.get("", response_model=ProfileOut)
def get_user_profile(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    repo = ProfileRepository(db)
    profile = repo.get_by_user_id(current_user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial profile not found")
    return profile

@router.put("", response_model=ProfileOut)
def update_user_profile(
    payload: ProfileUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    repo = ProfileRepository(db)
    profile = repo.get_by_user_id(current_user_id)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial profile not found")
        
    profile.saldo_awal = payload.saldo_awal
    profile.penghasilan_bulanan = payload.penghasilan_bulanan
    profile.budget_makan = payload.budget_makan
    profile.budget_transport = payload.budget_transport
    profile.budget_jajan = payload.budget_jajan
    profile.budget_lainnya = payload.budget_lainnya
    
    return repo.update(profile)

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_all_data(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """
    Resets all financial data (transactions and profile values) for the current user.
    Required by F-13 (riset semua data).
    """
    profile_repo = ProfileRepository(db)
    tx_repo = TransactionRepository(db)
    
    # Delete all transactions
    transactions = tx_repo.get_by_user(current_user_id)
    for tx in transactions:
        tx_repo.delete(tx.id)
        
    # Reset profile metrics
    profile = profile_repo.get_by_user_id(current_user_id)
    if profile:
        profile.saldo_awal = Decimal("0.0")
        profile.penghasilan_bulanan = Decimal("0.0")
        profile.budget_makan = Decimal("0.0")
        profile.budget_transport = Decimal("0.0")
        profile.budget_jajan = Decimal("0.0")
        profile.budget_lainnya = Decimal("0.0")
        profile_repo.update(profile)
        
    return {"message": "Seluruh data transaksi dan konfigurasi profil keuangan berhasil di-reset."}
