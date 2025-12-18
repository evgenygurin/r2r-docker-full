"""Authentication module for API access"""
import hashlib
import jwt
from datetime import datetime, timedelta

class AuthenticationManager:
    """Manages user authentication and token generation"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = 3600  # 1 hour

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        # In production, this would query a database
        hashed = self.hash_password(password)
        return self._verify_credentials(username, hashed)

    def generate_token(self, user_id: str) -> str:
        """Generate JWT access token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=self.token_expiry),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def validate_token(self, token: str) -> dict:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def _verify_credentials(self, username: str, hashed_password: str) -> bool:
        """Internal method to verify credentials against database"""
        # Placeholder for database lookup
        return True
