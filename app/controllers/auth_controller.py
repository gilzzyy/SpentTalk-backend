import os
import uuid
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.category import Category
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.user import UserCreate, UserLogin
from app.core.security import security_manager
from app.core.exceptions import AuthError, ResourceNotFoundError
from fastapi import UploadFile

class AuthController:
    """
    AuthController handles register, login, session, profile updating.
    """
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.category_repo = CategoryRepository(db)

    def register_user(self, payload: UserCreate) -> User:
        if payload.password != payload.password_confirm:
            raise AuthError("Password dan konfirmasi password tidak cocok.")
            
        existing_user = self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise AuthError("Email sudah terdaftar.")
            
        hashed_password = security_manager.hash_password(payload.password)
        new_user = User(name=payload.name, email=payload.email, password_hash=hashed_password)
        created_user = self.user_repo.create(new_user)
        
        # Populate Default Categories (Makan, Jajan, Transport, Lainnya)
        defaults = [
            ("Makan", "utensils"),
            ("Jajan", "cookie"),
            ("Transport", "car"),
            ("Lainnya", "ellipsis-h")
        ]
        for name, icon in defaults:
            default_cat = Category(user_id=created_user.id, name=name, icon=icon, is_default=True)
            self.category_repo.create(default_cat)
        
        return created_user

    def authenticate_user(self, payload: UserLogin) -> str:
        user = self.user_repo.get_by_email(payload.email)
        if not user or not security_manager.verify_password(payload.password, user.password_hash):
            raise AuthError("Email atau password salah.")
            
        access_token = security_manager.create_access_token(subject=user.id)
        return access_token

    def get_current_user_profile(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        return user

    def update_user_profile(
        self,
        user_id: int,
        name: str = None,
        email: str = None,
        old_password: str = None,
        new_password: str = None,
        profile_file: UploadFile = None
    ) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))

        if name:
            user.name = name
        if email:
            if email != user.email:
                existing = self.user_repo.get_by_email(email)
                if existing:
                    raise AuthError("Email baru sudah digunakan.")
                user.email = email



        if new_password:
            if not old_password:
                raise AuthError("Password lama diperlukan untuk mengganti password.")
            if not security_manager.verify_password(old_password, user.password_hash):
                raise AuthError("Password lama salah.")
            user.password_hash = security_manager.hash_password(new_password)

        if profile_file:
            # Save uploaded profile picture
            os.makedirs("uploads/profile_pics", exist_ok=True)
            file_extension = os.path.splitext(profile_file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join("uploads/profile_pics", unique_filename)
            
            with open(file_path, "wb") as buffer:
                buffer.write(profile_file.file.read())
                
            # Clean up the previous picture
            if user.profile_photo_url:
                old_filename = os.path.basename(user.profile_photo_url)
                old_path = os.path.join("uploads/profile_pics", old_filename)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
                        
            user.profile_photo_url = f"/uploads/profile_pics/{unique_filename}"

        return self.user_repo.update(user)

    def delete_user_account(self, user_id: int) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
            
        if user.profile_photo_url:
            old_filename = os.path.basename(user.profile_photo_url)
            old_path = os.path.join("uploads/profile_pics", old_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
                    
        return self.user_repo.delete(user_id)
