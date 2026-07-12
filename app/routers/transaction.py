from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.user_repository import UserRepository
from app.repositories.notification_repository import NotificationRepository
from app.models.notification import Notification
from app.schemas.transaction import TransactionOut, DashboardSummary, HistorySummary
from app.services.finance_manager import FinanceManager
from app.services.excel_exporter import ExcelExporter
from app.services.nlp_parser import NLPParser
from decimal import Decimal


router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_model=HistorySummary)
def get_transactions(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_name: Optional[str] = Query(None),
    period: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    search: Optional[str] = Query(None),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    repo = TransactionRepository(db)
    tx_list = repo.get_by_user(
        current_user_id,
        start_date=start_date,
        end_date=end_date,
        category_name=category_name,
        period=period,
        search=search
    )


    
    total_pemasukan = Decimal("0.00")
    total_pengeluaran = Decimal("0.00")
    
    for tx in tx_list:
        tx.formatted_detail = tx.format_detail()
        if tx.type == "pemasukan":
            total_pemasukan += tx.amount
        elif tx.type == "pengeluaran":
            total_pengeluaran += tx.amount

    return HistorySummary(
        total_transaksi=len(tx_list),
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        transactions=tx_list
    )

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    tx_repo = TransactionRepository(db)
    budget_repo = BudgetRepository(db)
    cat_repo = CategoryRepository(db)
    user_repo = UserRepository(db)
    finance_mgr = FinanceManager()
    nlp_parser = NLPParser()
    
    # Load profile details
    user = user_repo.get_by_id(current_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    all_tx = tx_repo.get_by_user(current_user_id)
    
    # Compute dashboard metrics
    saldo_terkini = finance_mgr.calculate_current_balance(user.initial_balance, all_tx)
    monthly_sums = finance_mgr.calculate_monthly_summary(all_tx)
    
    # Load budgets and active categories
    period = date.today().strftime("%Y-%m")
    budgets = budget_repo.get_user_budgets(current_user_id, period)
    categories = cat_repo.get_user_categories(current_user_id)
    budget_progress = finance_mgr.track_budget_progress(budgets, categories, all_tx)
    
    # Map last 5 transactions
    recent_transactions = all_tx[:5]
    for tx in recent_transactions:
        tx.formatted_detail = tx.format_detail()
        
    # Generate AI financial insights
    summary_data = {
        "saldo_terkini": float(saldo_terkini),
        "total_pemasukan_bulan_ini": float(monthly_sums["income"]),
        "total_pengeluaran_bulan_ini": float(monthly_sums["expense"]),
        "budget_progress": [
            {
                "name": p["name"],
                "spent": float(p["spent"]),
                "limit": float(p["limit"]),
                "percentage": float(p["percentage"])
            }
            for p in budget_progress
        ]
    }
    # Generate or reuse cached AI financial insights to prevent Groq API 429 Rate Limits
    from app.models.ai_insight import AIInsight
    from datetime import datetime, timedelta

    
    # Check if a recent general insight exists (within last 5 minutes)
    cache_threshold = datetime.utcnow() - timedelta(minutes=5)
    cached_insight = db.query(AIInsight).filter(
        AIInsight.user_id == current_user_id,
        AIInsight.insight_type == "general",
        AIInsight.period == period,
        AIInsight.created_at >= cache_threshold
    ).order_by(AIInsight.created_at.desc()).first()
    
    if cached_insight:
        ai_insight = cached_insight.message
    else:
        # Call AI parser to generate new insight
        ai_insight = nlp_parser.generate_financial_insight(summary_data)
        
        # Save to cache
        new_insight = AIInsight(
            user_id=current_user_id,
            period=period,
            insight_type="general",
            message=ai_insight
        )
        db.add(new_insight)
        db.commit()
    
    # Update current_balance on User model
    if user.current_balance != saldo_terkini:
        user.current_balance = saldo_terkini
        user_repo.update(user)
    
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
    period: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
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
    
    # Generate Excel stream
    excel_stream = exporter.export_transactions(user.name, all_tx, budget_progress)
    
    # Format filename based on selected period
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


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    repo = TransactionRepository(db)
    user_repo = UserRepository(db)
    finance_mgr = FinanceManager()
    
    tx = repo.get_by_id(id)
    if not tx or tx.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        
    repo.delete(id)
    
    # Sync User current balance
    user = user_repo.get_by_id(current_user_id)
    if user:
        all_tx = repo.get_by_user(current_user_id)
        current_balance = finance_mgr.calculate_current_balance(user.initial_balance, all_tx)
        user.current_balance = current_balance
        user_repo.update(user)
