from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.user_repository import UserRepository
from app.repositories.notification_repository import NotificationRepository
from app.models.chat_message import ChatMessage
from app.models.transaction import IncomeTransaction, ExpenseTransaction
from app.models.notification import Notification
from app.services.nlp_parser import NLPParser
from app.services.finance_manager import FinanceManager
from app.schemas.chatbot import ChatMessage as ChatMessageSchema, ChatResponse, ParseResult, ParsedItem, ConfirmTransactionRequest
from app.core.exceptions import ResourceNotFoundError

class ChatbotController:
    """
    ChatbotController orchestrates natural language processing, caching,
    and bulk confirmation/saving of single and multi-item financial entries.
    """
    def __init__(self, db: Session):
        self.db = db
        self.tx_repo = TransactionRepository(db)
        self.cat_repo = CategoryRepository(db)
        self.chat_repo = ChatMessageRepository(db)
        self.budget_repo = BudgetRepository(db)
        self.user_repo = UserRepository(db)
        self.parser = NLPParser()
        self.finance_mgr = FinanceManager()

    def process_chat(self, user_id: int, payload: ChatMessageSchema) -> ChatResponse:
        """
        Parses text input for financial transactions. Supports single and multi-item extraction,
        caching each item separately, and returning a formatted summary list for confirmation.
        """
        message = payload.message.strip().lower()
        if not message:
            return ChatResponse(reply="Silakan masukkan pesan transaksi keuangan Anda.")

        # 1. Handling instant commands: "cek pemborosan" and "tips menabung" (Highest priority, matching substrings)
        if "pemborosan" in message or "boros" in message:
            user = self.user_repo.get_by_id(user_id)
            all_tx = self.tx_repo.get_by_user(user_id)
            current_balance = self.finance_mgr.calculate_current_balance(user.initial_balance, all_tx)
            
            period = date.today().strftime("%Y-%m")
            budgets = self.budget_repo.get_user_budgets(user_id, period)
            categories = self.cat_repo.get_user_categories(user_id)
            progress = self.finance_mgr.track_budget_progress(budgets, categories, all_tx)
            summary = self.finance_mgr.calculate_monthly_summary(all_tx)
            
            financial_summary = {
                "saldo_terkini": float(current_balance),
                "total_pemasukan_bulan_ini": float(summary["income"]),
                "total_pengeluaran_bulan_ini": float(summary["expense"]),
                "budget_progress": progress
            }
            
            reply = self.parser.generate_overspending_check(financial_summary)
            return ChatResponse(reply=reply)

        if "menabung" in message or "nabung" in message:
            user = self.user_repo.get_by_id(user_id)
            all_tx = self.tx_repo.get_by_user(user_id)
            current_balance = self.finance_mgr.calculate_current_balance(user.initial_balance, all_tx)
            
            period = date.today().strftime("%Y-%m")
            budgets = self.budget_repo.get_user_budgets(user_id, period)
            categories = self.cat_repo.get_user_categories(user_id)
            progress = self.finance_mgr.track_budget_progress(budgets, categories, all_tx)
            summary = self.finance_mgr.calculate_monthly_summary(all_tx)
            
            financial_summary = {
                "saldo_terkini": float(current_balance),
                "total_pemasukan_bulan_ini": float(summary["income"]),
                "total_pengeluaran_bulan_ini": float(summary["expense"]),
                "budget_progress": progress
            }
            
            reply = self.parser.generate_saving_tips(financial_summary)
            return ChatResponse(reply=reply)

        # 2. Check for simple general queries
        if message in ["halo", "hi", "p", "siapa kamu", "help"]:
            return ChatResponse(
                reply="Halo! Saya adalah chatbot asisten keuangan SpentTalk. Tulis transaksi Anda secara alami (Contoh: 'beli nasi padang 15rb dan teh manis 3k') untuk mencatat pengeluaran."
            )

        if "pengeluaran" in message:
            transactions = self.tx_repo.get_by_user(user_id)
            summary = self.finance_mgr.calculate_monthly_summary(transactions)
            return ChatResponse(
                reply=f"Total pengeluaran Anda keseluruhan adalah: **Rp {summary['expense']:,.2f}**."
            )



        # Process transaction parsing (API with fallback)
        # Fetch user's actual category names to guide AI categorization
        user_cats = self.cat_repo.get_user_categories(user_id)
        user_cat_names = [c.name for c in user_cats]
        
        parse_res = self.parser.parse_transaction(payload.message, user_cat_names)
        
        # If this is a general chat/question, not a transaction:
        if not parse_res.get("is_transaction", False):
            return ChatResponse(
                reply=parse_res.get("reply", "Halo! Ada yang bisa saya bantu?"),
                needs_confirmation=False
            )
            
        parsed_items = parse_res.get("items", [])
        if not parsed_items:
            return ChatResponse(
                reply="Maaf, saya tidak dapat mendeteksi transaksi dari kalimat tersebut. Coba ketik dengan format seperti: 'makan siang nasi padang 15rb'."
            )

        reply_lines = []
        parsed_items_schemas = []
        primary_chat_id = None

        for i, item in enumerate(parsed_items):

            raw_type = item["type"]
            db_type = "pemasukan" if raw_type in ["income", "pemasukan"] else "pengeluaran"
            
            # Smart category matching with fuzzy/partial fallback
            cat_name = item["category_name"]
            matched_cat = self._find_best_category(user_id, cat_name, user_cats)


            # Store in ChatMessage cache with status 'pending'
            chat_msg = ChatMessage(
                user_id=user_id,
                raw_text=payload.message,
                parsed_item_name=item["item_name"],
                parsed_amount=Decimal(str(item["amount"])),
                parsed_category_id=matched_cat.id,
                parsed_type=db_type,
                status="pending"
            )
            saved_chat = self.chat_repo.create(chat_msg)

            if i == 0:
                primary_chat_id = saved_chat.id

            sign = "+" if db_type == "pemasukan" else "-"
            reply_lines.append(f"- **{saved_chat.parsed_item_name}** ({matched_cat.name}): {sign}Rp {saved_chat.parsed_amount:,.0f}")


            
            parsed_items_schemas.append(ParsedItem(
                item_name=saved_chat.parsed_item_name,
                amount=saved_chat.parsed_amount,
                category_name=matched_cat.name,
                type=db_type
            ))

        # Formulate multi-item response
        reply_str = (
            f"Saya mendeteksi transaksi berikut:\n"
            + "\n".join(reply_lines)
            + "\n\nApakah data di atas sudah benar? (Ya/Tidak)"
        )

        return ChatResponse(
            reply=reply_str,
            parse_result=ParseResult(
                items=parsed_items_schemas,
                raw_message=payload.message,
                chat_message_id=primary_chat_id
            ),
            needs_confirmation=True
        )

    def confirm_and_save_transaction(self, user_id: int, payload: ConfirmTransactionRequest) -> str:
        """
        Confirms a transaction. Resolves all pending items associated with the same raw chat text
        to record them as separate transaction entries in a single confirmation step.
        """
        chat_msg = self.chat_repo.get_by_id(payload.chat_message_id)
        if not chat_msg or chat_msg.user_id != user_id:
            raise ResourceNotFoundError("ChatMessage", str(payload.chat_message_id))
            
        if chat_msg.status != "pending":
            return f"Transaksi ini sudah memiliki status: **{chat_msg.status}**."

        # Fetch all pending items parsed from the same message input
        related_msgs = self.chat_repo.get_pending_by_raw_text(user_id, chat_msg.raw_text)

        if not payload.confirmed:
            for msg in related_msgs:
                msg.status = "rejected"
                self.chat_repo.update(msg)
            return "Pencatatan transaksi dibatalkan."

        notif_repo = NotificationRepository(self.db)
        primary_tx_category_id = None
        involved_categories = set()

        for msg in related_msgs:
            # Apply overrides only on the primary message ID
            if msg.id == chat_msg.id:
                tx_item_name = payload.override_item_name if payload.override_item_name is not None else msg.parsed_item_name
                tx_amount = payload.override_amount if payload.override_amount is not None else msg.parsed_amount
                tx_category_id = payload.override_category_id if payload.override_category_id is not None else msg.parsed_category_id
                tx_type = payload.override_type if payload.override_type is not None else msg.parsed_type
                primary_tx_category_id = tx_category_id
            else:
                tx_item_name = msg.parsed_item_name
                tx_amount = msg.parsed_amount
                tx_category_id = msg.parsed_category_id
                tx_type = msg.parsed_type
            
            involved_categories.add(tx_category_id)

            # Instantiate concrete subclass polymorphic instances
            if tx_type == "pemasukan":
                tx = IncomeTransaction(
                    user_id=user_id,
                    category_id=tx_category_id,
                    chat_message_id=msg.id,
                    item_name=tx_item_name,
                    amount=tx_amount,
                    transaction_date=date.today()
                )
            else:
                tx = ExpenseTransaction(
                    user_id=user_id,
                    category_id=tx_category_id,
                    chat_message_id=msg.id,
                    item_name=tx_item_name,
                    amount=tx_amount,
                    transaction_date=date.today()
                )
                
            created_tx = self.tx_repo.create(tx)

            # Update cache message status & transaction link
            msg.status = "confirmed"
            msg.transaction_id = created_tx.id
            self.chat_repo.update(msg)

            # Create notification for new transaction
            sign = "+" if tx_type == "pemasukan" else "-"
            notif_repo.create(Notification(
                user_id=user_id,
                title="Transaksi Baru",
                message=f"Transaksi '{tx_item_name}' sebesar {sign}Rp {tx_amount:,.2f} berhasil dicatat!",
                type="transaction"
            ))

        # Sync user balance
        user = self.user_repo.get_by_id(user_id)
        if user:
            all_tx = self.tx_repo.get_by_user(user_id)
            current_balance = self.finance_mgr.calculate_current_balance(user.initial_balance, all_tx)
            user.current_balance = current_balance
            self.user_repo.update(user)

        # Check budget limit warnings
        period = date.today().strftime("%Y-%m")
        budgets = self.budget_repo.get_user_budgets(user_id, period)
        categories = self.cat_repo.get_user_categories(user_id)
        all_tx = self.tx_repo.get_by_user(user_id)
        
        # Monthly budget calculations
        progress = self.finance_mgr.track_budget_progress(budgets, categories, all_tx)
        
        warnings = []
        for p in progress:
            if p["category_id"] in involved_categories and p["limit"] > 0:
                percent = p["percentage"]
                if percent >= 100:
                    warn_text = f"Pengeluaran kategori {p['name']} sudah MELEBIHI budget bulanan ({percent}% terpakai)!"
                    warnings.append(f"⚠️ **Peringatan**: {warn_text}")
                    notif_repo.create(Notification(
                        user_id=user_id,
                        title="Batas Anggaran Terlewati",
                        message=warn_text,
                        type="alert"
                    ))
                elif percent >= 80:
                    warn_text = f"Pengeluaran kategori {p['name']} sudah mencapai {percent}% dari budget bulanan!"
                    warnings.append(f"⚠️ **Peringatan**: {warn_text}")
                    notif_repo.create(Notification(
                        user_id=user_id,
                        title="Anggaran Hampir Habis",
                        message=warn_text,
                        type="alert"
                    ))
                    
        warning_msg = "\n" + "\n".join(warnings) if warnings else ""



        return f"Berhasil menyimpan transaksi! 🎉{warning_msg}"

    def _find_best_category(self, user_id: int, ai_category_name: str, user_cats):
        """
        Finds the best matching user category for the AI-returned category name.
        Uses a 3-step matching strategy:
        1. Exact/case-insensitive match (e.g., "Makan" == "makan")
        2. Substring/partial match (e.g., "Makanan" contains "Makan")
        3. Fallback to "Lainnya"
        """
        ai_name_lower = ai_category_name.strip().lower()

        # Step 1: Exact case-insensitive match
        for cat in user_cats:
            if cat.name.lower() == ai_name_lower:
                return cat

        # Step 2: Substring/partial match (either direction)
        for cat in user_cats:
            cat_lower = cat.name.lower()
            if cat_lower in ai_name_lower or ai_name_lower in cat_lower:
                return cat

        # Step 3: Fallback to "Lainnya"
        fallback = self.cat_repo.get_by_name(user_id, "Lainnya")
        if not fallback:
            from app.models.category import Category
            fallback = self.cat_repo.create(Category(user_id=user_id, name="Lainnya", icon="ellipsis-h"))
        return fallback

