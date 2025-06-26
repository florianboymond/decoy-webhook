import os
from typing import Optional

class Config:
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./decoys.db")
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    MAILGUN_API_KEY: Optional[str] = os.getenv("MAILGUN_API_KEY")
    ALERT_SENDER: str = os.getenv("ALERT_SENDER", "canary@honeypotalerts.com")
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

config = Config()