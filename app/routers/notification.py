from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationOut])
def get_my_notifications(
    limit: int = Query(50, ge=1, le=100),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retrieves the current user's notifications.
    """
    repo = NotificationRepository(db)
    return repo.get_user_notifications(current_user_id, limit=limit)

@router.put("/read-all", status_code=status.HTTP_200_OK)
def mark_all_as_read(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Marks all notifications for the current user as read.
    """
    repo = NotificationRepository(db)
    repo.mark_all_read(current_user_id)
    return {"message": "Semua notifikasi berhasil ditandai telah dibaca."}

@router.put("/{id}/read", response_model=NotificationOut)
def mark_as_read(
    id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Marks a specific notification as read.
    """
    repo = NotificationRepository(db)
    notif = repo.get_by_id(id)
    if not notif or notif.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notifikasi tidak ditemukan.")
    
    notif.is_read = True
    return repo.update(notif)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Deletes a notification record.
    """
    repo = NotificationRepository(db)
    notif = repo.get_by_id(id)
    if not notif or notif.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notifikasi tidak ditemukan.")
    
    repo.delete(id)
