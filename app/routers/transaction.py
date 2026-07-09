from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.transaction import TransactionOut, DashboardSummary
from app.services.finance_manager import FinanceManager
from app.services.excel_exporter import ExcelExporter
from app.services.nlp_parser import NLPParser

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_model=List[TransactionOut])
def get_transactions(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    repo = TransactionRepository(db)
    tx_list = repo.get_by_user(current_user_id, start_date=start_date, end_date=end_date, category=category)
    
    # Map polymorphic details if needed
    for tx in tx_list:
        tx.formatted_detail = tx.format_detail()
        
    return tx_list

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    tx_repo = TransactionRepository(db)
    profile_repo = ProfileRepository(db)
    finance_mgr = FinanceManager()
    nlp_parser = NLPParser()
    
    # Load profile and transactions
    profile = profile_repo.get_by_user_id(current_user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial profile not found")
        
    all_tx = tx_repo.get_by_user(current_user_id)
    
    # Compute dashboard metrics
    saldo_terkini = finance_mgr.calculate_current_balance(profile.saldo_awal, all_tx)
    monthly_sums = finance_mgr.calculate_monthly_summary(all_tx)
    budget_progress = finance_mgr.track_budget_progress(profile, all_tx)
    
    # Map last 5 transactions
    recent_transactions = all_tx[:5]
    for tx in recent_transactions:
        tx.formatted_detail = tx.format_detail()
        
    # Generate AI financial insights
    summary_data = {
        "saldo_terkini": float(saldo_terkini),
        "total_pemasukan_bulan_ini": float(monthly_sums["income"]),
        "total_pengeluaran_bulan_ini": float(monthly_sums["expense"]),
        "budget_progress": {
            k: {"spent": float(v["spent"]), "limit": float(v["limit"]), "percentage": float(v["percentage"])}
            for k, v in budget_progress.items()
        }
    }
    ai_insight = nlp_parser.generate_financial_insight(summary_data)
    
    return DashboardSummary(
        saldo_terkini=saldo_terkini,
        total_pemasukan_bulan_ini=monthly_sums["income"],
        total_pengeluaran_bulan_ini=monthly_sums["expense"],
        budget_progress=budget_progress,
        recent_transactions=recent_transactions,
        ai_insight=ai_insight
    )

@router.get("/export")
def export_excel(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    tx_repo = TransactionRepository(db)
    profile_repo = ProfileRepository(db)
    user_repo = UserRepository(db)
    finance_mgr = FinanceManager()
    exporter = ExcelExporter()
    
    user = user_repo.get_by_id(current_user_id)
    profile = profile_repo.get_by_user_id(current_user_id)
    
    if not user or not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
        
    all_tx = tx_repo.get_by_user(current_user_id)
    budget_progress = finance_mgr.track_budget_progress(profile, all_tx)
    
    # Generate Excel in-memory stream
    excel_stream = exporter.export_transactions(user.nama, all_tx, budget_progress)
    
    filename = f"SpendTalk_{user.nama}_{date.today().strftime('%m%Y')}.xlsx"
    
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    repo = TransactionRepository(db)
    tx = repo.get_by_id(id)
    if not tx or tx.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    repo.delete(id)
