import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    api_title: str = "Slurm Usage History API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api"

    # Security (comma-separated string)
    api_keys: str = ""

    # Admin (comma-separated: username:hashed_password)
    admin_users: str = ""
    admin_secret_key: str = "change-this-to-a-random-secret-key-in-production"

    # Data
    data_path: str = "data"
    auto_refresh_interval: int = 600

    # CORS (comma-separated string)
    cors_origins: str = "http://localhost:3100"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_api_keys(self) -> list[str]:
        """Parse API keys from comma-separated string."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def get_admin_users(self) -> dict[str, str]:
        """Parse admin users from comma-separated string.

        Format: username:hashed_password,username2:hashed_password2
        Returns: {"username": "hashed_password", ...}
        """
        if not self.admin_users:
            return {}

        users = {}
        for user_entry in self.admin_users.split(","):
            user_entry = user_entry.strip()
            if ":" in user_entry:
                username, password_hash = user_entry.split(":", 1)
                users[username.strip()] = password_hash.strip()

        return users

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data path is absolute
        if not Path(self.data_path).is_absolute():
            self.data_path = str(Path.cwd() / self.data_path)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
