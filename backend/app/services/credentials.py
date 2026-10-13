from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.api.errors import ApiError
from app.config import get_settings


def _cipher() -> MultiFernet:
    configured = get_settings().connector_encryption_keys
    keys = (
        [key.strip() for key in configured.get_secret_value().split(",") if key.strip()]
        if configured is not None
        else []
    )
    if not keys:
        raise ApiError(
            503,
            "CONNECTOR_ENCRYPTION_NOT_CONFIGURED",
            "Connector credential encryption is not configured.",
        )
    try:
        return MultiFernet([Fernet(key.encode()) for key in keys])
    except ValueError:
        raise ApiError(
            503,
            "CONNECTOR_ENCRYPTION_NOT_CONFIGURED",
            "Connector credential encryption is not configured.",
        ) from None


def encrypt_credential(token: str) -> bytes:
    return _cipher().encrypt(token.encode())


def decrypt_credential(ciphertext: bytes) -> str:
    try:
        return _cipher().decrypt(ciphertext).decode()
    except InvalidToken:
        raise ApiError(
            409,
            "CONNECTOR_CREDENTIAL_UNREADABLE",
            "Stored credential cannot be decrypted; replace it.",
        ) from None
