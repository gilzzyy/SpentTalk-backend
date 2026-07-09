from decimal import Decimal
from typing import List, Dict, Any
from app.models.transaction import Transaction
from app.models.profile import FinancialProfile

class FinanceManager:
    """
    FinanceManager encapsulates core business logic for calculations, budget status tracking, and insights compilation.
    """
    def __init__(self):
        pass

    def calculate_current_balance(self, initial_balance: Decimal, transactions: List[Transaction]) -> Decimal:
        """
        Saldo terkini = saldo awal + total pemasukan - total pengeluaran.
        Utilizes polymorphism: get_signed_amount() handles positive/negative signs dynamically based on sub-class.
        """
        total_delta = Decimal("0.0")
        for tx in transactions:
            total_delta += tx.get_signed_amount()
        return initial_balance + total_delta

    def calculate_monthly_summary(self, transactions: List[Transaction]) -> Dict[str, Decimal]:
        """
        Calculates total income and total expense.
        """
        summary = {"income": Decimal("0.0"), "expense": Decimal("0.0")}
        for tx in transactions:
            amt = tx.amount
            if tx.type == "income":
                summary["income"] += amt
            elif tx.type == "expense":
                summary["expense"] += amt
        return summary

    def track_budget_progress(self, profile: FinancialProfile, transactions: List[Transaction]) -> Dict[str, Dict[str, Decimal]]:
        """
        Tracks spending per category compared to budget limits set in profile.
        Categories: makan, transport, jajan, lainnya
        Returns dict containing spent, budget limit, and percentage.
        """
        # Initialize spent tracking
        spent = {
            "makan": Decimal("0.0"),
            "transport": Decimal("0.0"),
            "jajan": Decimal("0.0"),
            "lainnya": Decimal("0.0")
        }
        
        # Aggregate expenses
        for tx in transactions:
            if tx.type == "expense":
                cat = tx.category.lower()
                if cat in spent:
                    spent[cat] += tx.amount
                else:
                    spent["lainnya"] += tx.amount

        # Map budget limits from profile
        limits = {
            "makan": profile.budget_makan if profile else Decimal("0.0"),
            "transport": profile.budget_transport if profile else Decimal("0.0"),
            "jajan": profile.budget_jajan if profile else Decimal("0.0"),
            "lainnya": profile.budget_lainnya if profile else Decimal("0.0")
        }

        # Calculate progress
        progress = {}
        for cat in spent:
            limit = limits[cat]
            used = spent[cat]
            percentage = Decimal("0.0")
            if limit > 0:
                percentage = (used / limit) * 100
            progress[cat] = {
                "spent": used,
                "limit": limit,
                "percentage": round(percentage, 2)
            }

        return progress
