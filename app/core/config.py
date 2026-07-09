import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """
    Settings class encapsulating all configuration variables.
    Demonstrates Encapsulation by shielding access to raw os.environ.
    """
    def __init__(self):
        self._database_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/spendtalk_db")
        self._secret_key = os.getenv("SECRET_KEY", "super_secret_key")
        self._algorithm = os.getenv("ALGORITHM", "HS256")
        self._access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        self._gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    @property
    def database_url(self) -> str:
        return self._database_url

    @property
    def secret_key(self) -> str:
        return self._secret_key

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def access_token_expire_minutes(self) -> int:
        return self._access_token_expire_minutes

    @property
    def gemini_api_key(self) -> str:
        return self._gemini_api_key

settings = Settings()
