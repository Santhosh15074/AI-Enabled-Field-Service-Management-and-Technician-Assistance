import bcrypt

# bcrypt only reads the first 72 bytes of a password, so longer ones are rejected at registration.
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72


def password_problem(password: str) -> str | None:
    """Return why a password is unacceptable, or None if it is fine."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        return f"Password must be at most {MAX_PASSWORD_BYTES} bytes."
    return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# Checked against when the email is unknown, so a failed login takes the same time
# whether or not the account exists.
DUMMY_HASH = hash_password("timing-equaliser")
