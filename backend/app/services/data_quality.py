"""Serviços de avaliação de qualidade de dados para inventários migrados."""

import re
from collections import Counter
from collections.abc import Iterable

REQUIRED_FIELDS = ("codigo", "titulo", "classe_codigo")
CODIGO_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._/-]{1,31}$")
CLASSE_PATTERN = re.compile(r"^[A-Z0-9._-]{2,20}$")
DEFAULT_RULES = [
    {"nome": "Trim global", "tipo": "trim", "campo": None, "configuracao": {}},
    {"nome": "Colapsar espaços", "tipo": "collapse_spaces", "campo": None, "configuracao": {}},
    {"nome": "Normalizar código", "tipo": "upper", "campo": "codigo", "configuracao": {}},
    {"nome": "Normalizar classe", "tipo": "upper", "campo": "classe_codigo", "configuracao": {}},
]


def _round(value: float) -> float:
    return round(value, 2)


def _normalize_text(value: object | None) -> str:
    if value is None:
        return ""
    return str(value)


def _rule_descriptor(rule: dict) -> dict:
    return {
        "nome": rule.get("nome") or rule.get("tipo") or "regra",
        "tipo": rule.get("tipo"),
        "campo": rule.get("campo"),
        "configuracao": rule.get("configuracao") or {},
    }


def apply_cleansing_rules(record: dict, rules: Iterable[dict]) -> tuple[dict, list[dict]]:
    cleaned = dict(record)
    transformations: list[dict] = []

    for raw_rule in rules:
        rule = _rule_descriptor(raw_rule)
        fields = [rule["campo"]] if rule.get("campo") else list(cleaned.keys())
        for field in fields:
            if field not in cleaned:
                continue
            original = cleaned.get(field)
            if original is None:
                continue
            value = str(original)
            updated = value

            if rule["tipo"] == "trim":
                updated = value.strip()
            elif rule["tipo"] == "collapse_spaces":
                updated = re.sub(r"\s+", " ", value).strip()
            elif rule["tipo"] == "upper":
                updated = value.upper()
            elif rule["tipo"] == "title_case":
                updated = value.title()

            if updated != value:
                cleaned[field] = updated
                transformations.append(
                    {
                        "campo": field,
                        "antes": value,
                        "depois": updated,
                        "regra": rule["nome"],
                    }
                )

    return cleaned, transformations


def summarize_quality(resultados: list[dict], regras: list[dict], previous: dict | None = None) -> dict:
    total_registros = len(resultados)
    if total_registros == 0:
        return {
            "total_registros": 0,
            "score_geral": 0.0,
            "score_completude": 0.0,
            "score_unicidade": 0.0,
            "score_conformidade": 0.0,
            "status_qualidade": "critico",
            "indicadores": {
                "campos_nulos": {field: 0 for field in REQUIRED_FIELDS},
                "invalidos_formato": {"codigo": 0, "titulo": 0, "classe_codigo": 0},
                "duplicidades_codigo": [],
                "registros_conformes": 0,
                "registros_com_erro": 0,
                "transformacoes_aplicadas": 0,
                "amostra_transformacoes": [],
            },
            "inconsistencias": [],
            "recomendacoes": ["Importe ao menos um acervo válido para gerar o inventário de qualidade."],
            "comparativo_anterior": None,
            "regras_aplicadas": [_rule_descriptor(rule) for rule in regras],
        }

    null_counts = {field: 0 for field in REQUIRED_FIELDS}
    invalid_counts = {"codigo": 0, "titulo": 0, "classe_codigo": 0}
    inconsistencias: list[dict] = []
    amostra_transformacoes: list[dict] = []
    codes: list[str] = []
    registros_conformes = 0
    registros_com_erro = 0
    transformations_total = 0

    for index, raw_item in enumerate(resultados, start=1):
        item = {field: _normalize_text(raw_item.get(field)).strip() for field in REQUIRED_FIELDS}
        cleaned_item, transformations = apply_cleansing_rules(item, regras)
        if transformations and len(amostra_transformacoes) < 8:
            amostra_transformacoes.extend(transformations[: max(0, 8 - len(amostra_transformacoes))])
        transformations_total += len(transformations)

        erros_item: list[str] = list(raw_item.get("erros") or [])
        linha = raw_item.get("linha") or index

        for field in REQUIRED_FIELDS:
            if not _normalize_text(cleaned_item.get(field)).strip():
                null_counts[field] += 1

        codigo = _normalize_text(cleaned_item.get("codigo")).strip()
        titulo = _normalize_text(cleaned_item.get("titulo")).strip()
        classe_codigo = _normalize_text(cleaned_item.get("classe_codigo")).strip()

        codigo_valido = not codigo or bool(CODIGO_PATTERN.match(codigo))
        titulo_valido = not titulo or len(titulo) >= 3
        classe_valido = not classe_codigo or bool(CLASSE_PATTERN.match(classe_codigo))

        if not codigo_valido:
            invalid_counts["codigo"] += 1
            erros_item.append("codigo em formato inválido")
        if not titulo_valido:
            invalid_counts["titulo"] += 1
            erros_item.append("titulo em formato inválido")
        if not classe_valido:
            invalid_counts["classe_codigo"] += 1
            erros_item.append("classe_codigo em formato inválido")

        if codigo:
            codes.append(codigo)

        if erros_item:
            registros_com_erro += 1
            inconsistencias.append(
                {
                    "linha": linha,
                    "codigo": codigo or None,
                    "titulo": titulo or None,
                    "classe_codigo": classe_codigo or None,
                    "erros": sorted(set(erros_item)),
                }
            )
        else:
            registros_conformes += 1

    expected_fields = total_registros * len(REQUIRED_FIELDS)
    filled_fields = expected_fields - sum(null_counts.values())
    score_completude = _round((filled_fields / expected_fields) * 100 if expected_fields else 0)

    distinct_codes = len(set(codes))
    score_unicidade = _round((distinct_codes / len(codes)) * 100 if codes else 100)
    duplicate_codes = sorted([code for code, count in Counter(codes).items() if count > 1])

    score_conformidade = _round((registros_conformes / total_registros) * 100 if total_registros else 0)
    score_geral = _round((score_completude * 0.4) + (score_unicidade * 0.3) + (score_conformidade * 0.3))

    if score_geral >= 95:
        status_qualidade = "excelente"
    elif score_geral >= 85:
        status_qualidade = "saudavel"
    elif score_geral >= 70:
        status_qualidade = "atencao"
    else:
        status_qualidade = "critico"

    recomendacoes: list[str] = []
    if score_completude < 90:
        recomendacoes.append("Priorize saneamento de campos obrigatórios antes da próxima onda de migração.")
    if duplicate_codes:
        recomendacoes.append("Execute deduplicação por código documental para evitar conflitos de carga.")
    if score_conformidade < 95:
        recomendacoes.append("Corrija formatos inválidos e registros com referência de classe inconsistente.")
    if transformations_total > 0:
        recomendacoes.append("Aplique as regras de cleansing também na origem para reduzir retrabalho nas próximas cargas.")
    if not recomendacoes:
        recomendacoes.append("Qualidade aderente ao corte proposto; manter monitoramento por histórico de score.")

    comparativo_anterior = None
    if previous:
        comparativo_anterior = {
            "score_geral_delta": _round(score_geral - float(previous.get("score_geral", 0))),
            "completude_delta": _round(score_completude - float(previous.get("score_completude", 0))),
            "unicidade_delta": _round(score_unicidade - float(previous.get("score_unicidade", 0))),
            "conformidade_delta": _round(score_conformidade - float(previous.get("score_conformidade", 0))),
        }

    return {
        "total_registros": total_registros,
        "score_geral": score_geral,
        "score_completude": score_completude,
        "score_unicidade": score_unicidade,
        "score_conformidade": score_conformidade,
        "status_qualidade": status_qualidade,
        "indicadores": {
            "campos_nulos": null_counts,
            "invalidos_formato": invalid_counts,
            "duplicidades_codigo": duplicate_codes,
            "registros_conformes": registros_conformes,
            "registros_com_erro": registros_com_erro,
            "transformacoes_aplicadas": transformations_total,
            "amostra_transformacoes": amostra_transformacoes,
        },
        "inconsistencias": inconsistencias[:100],
        "recomendacoes": recomendacoes,
        "comparativo_anterior": comparativo_anterior,
        "regras_aplicadas": [_rule_descriptor(rule) for rule in regras],
    }
