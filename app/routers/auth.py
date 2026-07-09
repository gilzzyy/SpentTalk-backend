from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.controllers.auth_controller import AuthController
from app.schemas.user import UserCreate, UserLogin, UserUpdate, UserOut, Token
from app.core.exceptions import AuthError, ResourceNotFoundError

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    controller = AuthController(db)
    try:
        return controller.register_user(payload)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    controller = AuthController(db)
    try:
        token = controller.authenticate_user(payload)
        return {"access_token": token, "token_type": "bearer"}
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT if "api" in str(e).lower() else status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me", response_model=UserOut)
def get_profile(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    controller = AuthController(db)
    try:
        return controller.get_current_user_profile(current_user_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/me", response_model=UserOut)
def update_profile(
    payload: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    controller = AuthController(db)
    try:
        return controller.update_user_profile(current_user_id, payload)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    controller = AuthController(db)
    success = controller.delete_user_account(current_user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
