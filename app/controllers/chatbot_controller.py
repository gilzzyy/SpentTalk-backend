from sqlalchemy.orm import Session
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.profile_repository import ProfileRepository
from app.models.transaction import IncomeTransaction, ExpenseTransaction
from app.services.nlp_parser import NLPParser
from app.services.finance_manager import FinanceManager
from app.schemas.chatbot import ChatMessage, ChatResponse, ParseResult, ParsedItem, ConfirmTransactionRequest
from app.core.exceptions import ResourceNotFoundError
from decimal import Decimal

class ChatbotController:
    """
    ChatbotController orchestrates dialogue, AI text parsing, and transaction saving.
    """
    def __init__(self, db: Session):
        self.db = db
        self.tx_repo = TransactionRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.parser = NLPParser()
        self.finance_mgr = FinanceManager()

    def process_chat(self, user_id: int, payload: ChatMessage) -> ChatResponse:
        message = payload.message.lower().strip()

        # Handle simple queries first
        if "saldo" in message:
            profile = self.profile_repo.get_by_user_id(user_id)
            initial_balance = profile.saldo_awal if profile else Decimal("0.0")
            transactions = self.tx_repo.get_by_user(user_id)
            current_balance = self.finance_mgr.calculate_current_balance(initial_balance, transactions)
            return ChatResponse(
                reply=f"Saldo Anda saat ini adalah: **Rp {current_balance:,.2f}**."
            )

        if "pengeluaran" in message:
            transactions = self.tx_repo.get_by_user(user_id)
            summary = self.finance_mgr.calculate_monthly_summary(transactions)
            return ChatResponse(
                reply=f"Total pengeluaran Anda bulan ini adalah: **Rp {summary['expense']:,.2f}**."
            )

        # Otherwise, process transaction parsing via AI
        parsed_items = self.parser.parse_transaction(payload.message)
        
        if not parsed_items:
            return ChatResponse(
                reply="Maaf, saya tidak dapat mendeteksi transaksi dari kalimat tersebut. Coba ketik dengan format seperti: 'makan siang nasi padang 15rb'."
            )

        # Standardize items into ParsedItem schemas
        items_list = []
        reply_items = []
        for item in parsed_items:
            parsed_item = ParsedItem(
                item_name=item["item_name"],
                amount=Decimal(str(item["amount"])),
                category=item["category"],
                type=item["type"]
            )
            items_list.append(parsed_item)
            sign = "+" if parsed_item.type == "income" else "-"
            reply_items.append(f"- {parsed_item.item_name} ({parsed_item.category}): {sign}Rp {parsed_item.amount:,.0f}")

        reply_str = "Saya mendeteksi transaksi berikut:\n" + "\n".join(reply_items) + "\n\nApakah data di atas sudah benar? (Ya/Tidak)"

        return ChatResponse(
            reply=reply_str,
            parse_result=ParseResult(items=items_list, raw_message=payload.message),
            needs_confirmation=True
        )

    def confirm_and_save_transaction(self, user_id: int, payload: ConfirmTransactionRequest) -> str:
        if not payload.confirmed:
            return "Pencatatan dibatalkan. Silakan ketik kembali transaksi Anda."

        profile = self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ResourceNotFoundError("FinancialProfile", f"user_id {user_id}")

        saved_count = 0
        for item in payload.items:
            # Instantiate correct subclass dynamically (Polymorphism / Factory pattern)
            if item.type == "income":
                tx = IncomeTransaction(
                    user_id=user_id,
                    item_name=item.item_name,
                    amount=item.amount,
                    category="pemasukan"
                )
            else:
                tx = ExpenseTransaction(
                    user_id=user_id,
                    item_name=item.item_name,
                    amount=item.amount,
                    category=item.category
                )
            self.tx_repo.create(tx)
            saved_count += 1

        # Retrieve updated budget status and check limits
        all_tx = self.tx_repo.get_by_user(user_id)
        progress = self.finance_mgr.track_budget_progress(profile, all_tx)
        
        warnings = []
        for cat, stat in progress.items():
            if stat["percentage"] >= 100:
                warnings.append(f"⚠️ Kategori **{cat.capitalize()}** telah MELEBIHI budget!")
            elif stat["percentage"] >= 80:
                warnings.append(f"⚠️ Kategori **{cat.capitalize()}** sudah terpakai {stat['percentage']}% (Hampir Habis)!")

        warning_msg = "\n" + "\n".join(warnings) if warnings else ""

        return f"Berhasil menyimpan {saved_count} transaksi! 🎉" + warning_msg
