from sqlalchemy.orm import Session
from app.models.user import User
from app.models.profile import FinancialProfile
from app.repositories.user_repository import UserRepository
from app.repositories.profile_repository import ProfileRepository
from app.schemas.user import UserCreate, UserLogin, UserUpdate
from app.core.security import security_manager
from app.core.exceptions import AuthError, ResourceNotFoundError

class AuthController:
    """
    AuthController handles register, login, session, profile updating.
    """
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.profile_repo = ProfileRepository(db)

    def register_user(self, payload: UserCreate) -> User:
        if payload.password != payload.password_confirm:
            raise AuthError("Password dan konfirmasi password tidak cocok.")
            
        existing_user = self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise AuthError("Email sudah terdaftar.")
            
        hashed_password = security_manager.hash_password(payload.password)
        new_user = User(nama=payload.nama, email=payload.email, password_hash=hashed_password)
        created_user = self.user_repo.create(new_user)
        
        # Proactively initialize an empty profile, so users can onboard/update it later
        new_profile = FinancialProfile(user_id=created_user.id)
        self.profile_repo.create(new_profile)
        
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

    def update_user_profile(self, user_id: int, payload: UserUpdate) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))

        if payload.nama:
            user.nama = payload.nama
        if payload.email:
            # Check email uniqueness
            if payload.email != user.email:
                existing = self.user_repo.get_by_email(payload.email)
                if existing:
                    raise AuthError("Email baru sudah digunakan.")
                user.email = payload.email

        if payload.new_password:
            if not payload.old_password:
                raise AuthError("Password lama diperlukan untuk mengganti password.")
            if not security_manager.verify_password(payload.old_password, user.password_hash):
                raise AuthError("Password lama salah.")
            user.password_hash = security_manager.hash_password(payload.new_password)

        return self.user_repo.update(user)

    def delete_user_account(self, user_id: int) -> bool:
        return self.user_repo.delete(user_id)
