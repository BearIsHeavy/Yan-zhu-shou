# security.py
from datetime import datetime, timedelta, timezone
import jwt
import hashlib
import bcrypt

# Security Constants (In production, load these from environment variables)
SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


def _pre_hash(password: str) -> bytes:
    """
    Bcrypt has a strict 72-byte limit.
    We pre-hash the password with SHA-256 to ensure it is always
    exactly 64 hex characters (converted to bytes for bcrypt).
    """
    hex_string = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hex_string.encode('utf-8')


def get_password_hash(password: str) -> str:
    """Hashes a plain text password using official bcrypt."""
    # 1. Generate salt and hash the pre-hashed password
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(_pre_hash(password), salt)

    # 2. Decode the bytes back to a string so it can be saved in MySQL
    return hashed_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against its hash safely."""
    # Bcrypt requires bytes for both the password and the stored hash
    return bcrypt.checkpw(
        _pre_hash(plain_password),
        hashed_password.encode('utf-8')
    )


def create_access_token(data: dict[str, str], expires_delta: timedelta | None = None) -> str:
    """Generates a JWT token containing user data."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt