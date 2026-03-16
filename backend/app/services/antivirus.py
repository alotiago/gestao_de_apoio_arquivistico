"""Integração com ClamAV (protocolo clamd INSTREAM)."""

from __future__ import annotations

import socket
import struct

from app.config import get_settings


class AntivirusUnavailableError(Exception):
    """Erro de comunicação/indisponibilidade do serviço de antivírus."""


def _parse_clamd_response(raw_response: str) -> tuple[bool, str | None]:
    normalized = raw_response.strip()
    if "FOUND" in normalized:
        prefix = normalized.split(":", 1)[-1].strip()
        signature = prefix.replace("FOUND", "").strip() or None
        return False, signature

    if normalized.endswith("OK"):
        return True, None

    raise AntivirusUnavailableError(f"Resposta inválida do ClamAV: {normalized}")


def scan_file_with_clamav(payload: bytes) -> tuple[bool, str | None]:
    """Escaneia bytes via ClamAV e retorna (arquivo_limpo, assinatura)."""
    settings = get_settings()

    if len(payload) == 0:
        return True, None

    try:
        with socket.create_connection(
            (settings.CLAMAV_HOST, settings.CLAMAV_PORT),
            timeout=settings.CLAMAV_TIMEOUT_SECONDS,
        ) as sock:
            sock.sendall(b"zINSTREAM\0")

            chunk_size = 1024 * 1024
            offset = 0
            while offset < len(payload):
                chunk = payload[offset : offset + chunk_size]
                sock.sendall(struct.pack("!I", len(chunk)))
                sock.sendall(chunk)
                offset += len(chunk)

            sock.sendall(struct.pack("!I", 0))
            response_bytes = sock.recv(4096)
    except OSError as exc:
        raise AntivirusUnavailableError("Falha ao conectar no ClamAV") from exc

    if not response_bytes:
        raise AntivirusUnavailableError("Sem resposta do ClamAV")

    response = response_bytes.decode("utf-8", errors="replace")
    return _parse_clamd_response(response)
