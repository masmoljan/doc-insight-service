import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import app_config
from app.utils.app_error import AppError, AppErrorType

KEY_LENGTH_BYTES = 32
GCM_NONCE_LENGTH_BYTES = 12
SEPARATOR = "."


def get_key_bytes() -> bytes:
    key_bytes = app_config.data_encryption_key.encode("utf-8")
    if len(key_bytes) != KEY_LENGTH_BYTES:
        raise AppError(
            AppErrorType.DATA_ENCRYPTION_KEY_INVALID,
            message="DATA_ENCRYPTION_KEY must be 32 bytes",
        )
    return key_bytes


def parse_payload(value: str) -> tuple[bytes, bytes] | None:
    if SEPARATOR not in value:
        return None
    cipher_hex, iv_hex = value.rsplit(SEPARATOR, 1)
    if not cipher_hex or not iv_hex:
        return None
    try:
        return bytes.fromhex(cipher_hex), bytes.fromhex(iv_hex)
    except ValueError:
        return None


def encrypt(value: str) -> str:
    if not value:
        return value
    key_bytes = get_key_bytes()
    nonce = secrets.token_bytes(GCM_NONCE_LENGTH_BYTES)
    try:
        ciphertext = AESGCM(key_bytes).encrypt(
            nonce, value.encode("utf-8"), None
        )
    except Exception as error:
        raise AppError(AppErrorType.DATA_ENCRYPTION_FAILED) from error
    return f"{ciphertext.hex()}{SEPARATOR}{nonce.hex()}"


def decrypt(value: str) -> str:
    if not value:
        return value
    payload = parse_payload(value)
    if payload is None:
        return value
    ciphertext, nonce = payload
    key_bytes = get_key_bytes()
    try:
        if len(nonce) != GCM_NONCE_LENGTH_BYTES:
            return value
        plaintext = AESGCM(key_bytes).decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as error:
        raise AppError(AppErrorType.DATA_DECRYPTION_FAILED) from error
