"""Serviços de LGPD: criptografia, masking e anonimização."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import get_settings


def _build_fernet() -> Fernet:
    settings = get_settings()
    digest = hashlib.sha256(settings.JWT_SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_value(value: str) -> str:
    return _build_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
    return _build_fernet().decrypt(token.encode("utf-8")).decode("utf-8")


def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_cpf(cpf: str) -> str:
    digits = "".join(ch for ch in cpf if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***.***.***-{digits[-2:]}"


def mask_generic(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def anonymized_email(identifier: str) -> str:
    return f"anon+{identifier}@anon.invalid"
