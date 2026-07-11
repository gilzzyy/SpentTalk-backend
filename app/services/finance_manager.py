from decimal import Decimal
from typing import List, Dict, Any
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.category import Category

class FinanceManager:
    """
    FinanceManager encapsulates core calculations, balance updates, and budget tracking.
    """
    def __init__(self):
        pass

    def calculate_current_balance(self, initial_balance: Decimal, transactions: List[Transaction]) -> Decimal:
        """
        Calculates the net balance: initial_balance + total income - total expenses.
        Leverages PBO Polymorphism by calling tx.get_signed_amount().
        """
        total_delta = Decimal("0.00")
        for tx in transactions:
            total_delta += tx.get_signed_amount()
        return initial_balance + total_delta

    def calculate_monthly_summary(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """
        Calculates total income and total expense.
        """
        summary = {"income": Decimal("0.00"), "expense": Decimal("0.00")}
        for tx in transactions:
            if tx.type == "pemasukan":
                summary["income"] += tx.amount
            elif tx.type == "pengeluaran":
                summary["expense"] += tx.amount
        return summary

    def track_budget_progress(self, budgets: List[Budget], categories: List[Category], transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """
        Tracks spent totals per category against budget limits.
        """
        # Sum expenses by category_id
        spent = {}
        for tx in transactions:
            if tx.type == "pengeluaran":
                spent[tx.category_id] = spent.get(tx.category_id, Decimal("0.00")) + tx.amount

        # Map budget limits by category_id
        limits = {b.category_id: b.amount for b in budgets}

        # Build progress structures
        progress_list = []
        for cat in categories:
            # We skip category checking for active flag here or handle it in callers
            limit = limits.get(cat.id, Decimal("0.00"))
            used = spent.get(cat.id, Decimal("0.00"))
            percentage = Decimal("0.00")
            if limit > 0:
                percentage = (used / limit) * 100
                
            progress_list.append({
                "category_id": cat.id,
                "name": cat.name,
                "icon": cat.icon,
                "spent": used,
                "limit": limit,
                "percentage": round(percentage, 2)
            })
            
        return progress_list
