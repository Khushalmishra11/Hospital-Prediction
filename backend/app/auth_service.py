from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr
from firebase_admin import auth as firebase_auth, firestore

from .firebase_config import get_firestore_db, get_firebase_auth


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    uid: str
    email: str
    full_name: str
    created_at: str | None = None


class AuthService:
    """Service for handling user authentication."""

    @staticmethod
    def register_user(email: str, password: str, full_name: str) -> dict[str, Any]:
        """Register a new user."""
        auth_client = get_firebase_auth()
        try:
            # Create user in Firebase Auth
            user = auth_client.create_user(
                email=email,
                password=password,
                display_name=full_name
            )
        except firebase_auth.EmailAlreadyExistsError:
            # Frontend may have already created this user via Firebase client SDK.
            user = auth_client.get_user_by_email(email)
        except Exception as e:
            raise ValueError(f"Registration failed: {str(e)}")

        # Upsert user profile in Firestore.
        db = get_firestore_db()
        db.collection("users").document(user.uid).set(
            {
                "email": email,
                "full_name": full_name,
                "created_at": firestore.SERVER_TIMESTAMP,
                "predictions_count": 0,
            },
            merge=True,
        )

        return {
            "uid": user.uid,
            "email": user.email,
            "full_name": full_name,
        }

    @staticmethod
    def get_user_profile(uid: str) -> dict[str, Any]:
        """Get user profile from Firestore."""
        db = get_firestore_db()
        doc = db.collection("users").document(uid).get()
        
        if not doc.exists:
            raise ValueError("User not found")
        
        return doc.to_dict()

    @staticmethod
    def verify_token(token: str) -> dict[str, Any]:
        """Verify Firebase ID token."""
        try:
            auth_client = get_firebase_auth()
            decoded = auth_client.verify_id_token(token)
            return decoded
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")
