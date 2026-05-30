from __future__ import annotations

import bcrypt

# bcrypt has a 72 byte password limit, so we truncate if necessary
MAX_PASSWORD_LENGTH = 72


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Truncate password if too long (bcrypt limit is 72 bytes)
    password_bytes = password.encode('utf-8')[:MAX_PASSWORD_LENGTH]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    # Truncate password if too long
    password_bytes = plain_password.encode('utf-8')[:MAX_PASSWORD_LENGTH]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
