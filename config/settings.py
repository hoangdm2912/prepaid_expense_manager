"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/expenses.db",
        description="Database connection URL"
    )
    
    # Google Drive Configuration
    google_drive_credentials_file: str = Field(
        default="credentials.json",
        description="Path to Google Drive Service Account credentials JSON file"
    )
    google_drive_client_secrets_file: str = Field(
        default="client_secrets.json",
        description="Path to Google Drive OAuth2 client secrets JSON file"
    )
    google_drive_token_file: str = Field(
        default="token.json",
        description="Path to Google Drive OAuth2 token JSON file"
    )
    google_drive_folder_name: str = Field(
        default="Ke_Toan_242",
        description="Default folder name in Google Drive"
    )
    google_drive_folder_id: Optional[str] = Field(
        default=None,
        description="Target Google Drive folder ID for uploads"
    )
    
    # Email Configuration
    smtp_server: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    email_from: Optional[str] = Field(default=None)
    
    # Zalo API Configuration
    zalo_app_id: Optional[str] = Field(default=None)
    zalo_secret_key: Optional[str] = Field(default=None)
    zalo_access_token: Optional[str] = Field(default=None)
    zalo_phone_number: Optional[str] = Field(default=None)
    
    # Application Settings
    app_title: str = Field(
        default="Quản Lý Chi Phí Trả Trước (TK 242)",
        description="Application title"
    )
    notification_days_before: int = Field(
        default=7,
        description="Days before quarter end to send notifications"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
