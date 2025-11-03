import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

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

    # SAML-based admin emails (comma-separated: email:role)
    # Example: admin@example.com:superadmin,user@example.com:admin
    admin_emails: str = ""
    superadmin_emails: str = ""  # Comma-separated list of superadmin emails

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

    def get_admin_email_roles(self) -> dict[str, str]:
        """Parse admin emails with roles from configuration.

        Returns: {"email@example.com": "admin"|"superadmin", ...}
        """
        from ..models.admin_models import AdminRole

        email_roles = {}

        # First, add all superadmin emails
        if self.superadmin_emails:
            for email in self.superadmin_emails.split(","):
                email = email.strip()
                if email:
                    email_roles[email.lower()] = AdminRole.SUPERADMIN

        # Then add emails from admin_emails (format: email:role)
        if self.admin_emails:
            for entry in self.admin_emails.split(","):
                entry = entry.strip()
                if ":" in entry:
                    email, role = entry.split(":", 1)
                    email = email.strip().lower()
                    role = role.strip().lower()
                    if role in ["admin", "superadmin"]:
                        email_roles[email] = AdminRole.SUPERADMIN if role == "superadmin" else AdminRole.ADMIN
                elif entry:
                    # If no role specified, default to admin
                    email_roles[entry.lower()] = AdminRole.ADMIN

        return email_roles

    def is_admin_email(self, email: str) -> bool:
        """Check if an email is in the admin list."""
        if not email:
            return False
        email_roles = self.get_admin_email_roles()
        return email.lower() in email_roles

    def get_email_role(self, email: str) -> Optional[str]:
        """Get the role for a given email address."""
        if not email:
            return None
        email_roles = self.get_admin_email_roles()
        return email_roles.get(email.lower())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data path is absolute
        if not Path(self.data_path).is_absolute():
            self.data_path = str(Path.cwd() / self.data_path)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
