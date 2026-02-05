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
    
    # Application Settings
    app_title: str = Field(
        default="Quản Lý Chi Phí Trả Trước (TK 242)",
        description="Application title"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
