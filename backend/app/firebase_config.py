from __future__ import annotations

import json
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""
    firebase_api_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
BASE_DIR = Path(__file__).resolve().parents[1]


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        return  # Already initialized

    try:
        # Try to load from JSON file first (for production)
        cred_path = settings.firebase_credentials_path
        if cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
        else:
            # Fallback: use environment variable
            cred_json = settings.firebase_credentials_json
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                raise ValueError("Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON")

        firebase_admin.initialize_app(cred)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Firebase: {str(e)}") from e


def get_firestore_db():
    """Get Firestore client."""
    initialize_firebase()
    return firestore.client()


def get_firebase_auth():
    """Get Firebase Auth."""
    initialize_firebase()
    return firebase_auth
