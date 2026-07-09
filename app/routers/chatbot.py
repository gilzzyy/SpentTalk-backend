from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.controllers.chatbot_controller import ChatbotController
from app.schemas.chatbot import ChatMessage, ChatResponse, ConfirmTransactionRequest
from app.core.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/chatbot", tags=["Chatbot & AI Parser"])

@router.post("", response_model=ChatResponse)
def process_message(
    payload: ChatMessage,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    controller = ChatbotController(db)
    try:
        return controller.process_chat(current_user_id, payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memproses pesan: {str(e)}")

@router.post("/confirm")
def confirm_transaction(
    payload: ConfirmTransactionRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    controller = ChatbotController(db)
    try:
        message = controller.confirm_and_save_transaction(current_user_id, payload)
        return {"message": message}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menyimpan transaksi: {str(e)}")
