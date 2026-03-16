"""Serviço inicial de mapeamento automático para classes documentais (US-004)."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable


RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "PCD-RH-Admissao",
        (
            "admissao",
            "admissão",
            "funcionario",
            "funcionário",
            "colaborador",
            "rh",
            "contratacao",
            "contratação",
        ),
    ),
    (
        "PCD-RH-Folha",
        (
            "folha",
            "salario",
            "salário",
            "beneficio",
            "benefício",
            "ponto",
        ),
    ),
    (
        "PCD-Juridico-Contratos",
        (
            "contrato",
            "aditivo",
            "fornecedor",
            "clausula",
            "cláusula",
            "juridico",
            "jurídico",
        ),
    ),
    (
        "PCD-Fiscal-Tributario",
        (
            "fiscal",
            "tributo",
            "tributário",
            "nota fiscal",
            "imposto",
            "icms",
            "pis",
            "cofins",
        ),
    ),
]

DEFAULT_CLASS = "PCD-Administrativo-Geral"


def _normalize_text(value: object) -> str:
    text = str(value or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _flatten_values(data: object) -> Iterable[str]:
    if isinstance(data, dict):
        for value in data.values():
            yield from _flatten_values(value)
        return

    if isinstance(data, list):
        for value in data:
            yield from _flatten_values(value)
        return

    yield _normalize_text(data)


def suggest_document_class(
    respostas: dict[str, object] | None,
    roteiro_titulo: str | None,
    roteiro_area: str | None,
) -> tuple[str, str]:
    corpus_parts = list(_flatten_values(respostas or {}))
    corpus_parts.append(_normalize_text(roteiro_titulo))
    corpus_parts.append(_normalize_text(roteiro_area))
    corpus = " ".join(part for part in corpus_parts if part)

    best_class = DEFAULT_CLASS
    best_hits: list[str] = []

    for class_code, keywords in RULES:
        hits = [kw for kw in keywords if _normalize_text(kw) in corpus]
        if len(hits) > len(best_hits):
            best_hits = hits
            best_class = class_code

    if best_hits:
        justificativa = (
            "Sugestão baseada em termos identificados na entrevista: "
            + ", ".join(sorted(set(best_hits)))
        )
    else:
        justificativa = (
            "Sugestão padrão aplicada por ausência de sinais fortes nas respostas."
        )

    return best_class, justificativa
