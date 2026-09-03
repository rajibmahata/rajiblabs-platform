"""Password hashing utilities (bcrypt directly — passlib 1.7.4 is
incompatible with bcrypt>=4.1 and raises on its own wrap-bug probe)."""
import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except Exception:
        return False
