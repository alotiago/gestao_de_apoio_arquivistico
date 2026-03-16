"""Motor condicional para execução de perguntas dinâmicas (US-002)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def _to_dict(condition_value: Any) -> dict[str, Any]:
    if isinstance(condition_value, Mapping):
        return dict(condition_value)
    return {}


def _read_attr(data: Any, key: str, default: Any = None) -> Any:
    if isinstance(data, Mapping):
        return data.get(key, default)
    return getattr(data, key, default)


def _is_filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) > 0
    return True


def _to_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def evaluate_condition(operador: str, valor: dict[str, Any], respostas: dict[str, Any]) -> bool:
    operator = operador.upper()
    payload = _to_dict(valor)

    if operator in {"AND", "OR", "NOT"}:
        raw_children = payload.get("condicoes", [])
        children = [
            item
            for item in raw_children
            if isinstance(item, Mapping) and "operador" in item and "valor" in item
        ]
        if not children:
            return False

        evaluations = [
            evaluate_condition(str(item["operador"]), _to_dict(item["valor"]), respostas)
            for item in children
        ]
        if operator == "AND":
            return all(evaluations)
        if operator == "OR":
            return any(evaluations)
        return not evaluations[0]

    question_id = payload.get("pergunta_id") or payload.get("question_id") or payload.get("campo")
    expected = payload.get("valor")
    current = respostas.get(str(question_id)) if question_id is not None else payload.get("atual")

    if operator == "EXISTS":
        return _is_filled(current)
    if operator == "EQ":
        return current == expected
    if operator == "NEQ":
        return current != expected
    if operator == "IN":
        return isinstance(expected, Sequence) and not isinstance(expected, (str, bytes, bytearray)) and current in expected
    if operator == "NOT_IN":
        return isinstance(expected, Sequence) and not isinstance(expected, (str, bytes, bytearray)) and current not in expected

    current_number = _to_number(current)
    expected_number = _to_number(expected)
    if current_number is None or expected_number is None:
        return False

    if operator == "GT":
        return current_number > expected_number
    if operator == "LT":
        return current_number < expected_number
    if operator == "GTE":
        return current_number >= expected_number
    if operator == "LTE":
        return current_number <= expected_number
    return False


def compute_question_state(
    question: Any,
    respostas: dict[str, Any],
) -> tuple[bool, bool]:
    visible = True
    required = bool(_read_attr(question, "obrigatoria", True))
    raw_conditions = _read_attr(question, "condicoes", [])

    for condicao in raw_conditions:
        operador = str(_read_attr(condicao, "operador", ""))
        valor = _to_dict(_read_attr(condicao, "valor", {}))
        acao = str(_read_attr(condicao, "acao", "")).lower()

        if not operador or not acao:
            continue

        if evaluate_condition(operador, valor, respostas):
            if acao == "ocultar":
                visible = False
            elif acao == "mostrar":
                visible = True
            elif acao == "obrigar":
                required = True

    return visible, required


def list_missing_required(
    questions: Sequence[Any],
    respostas: dict[str, Any],
) -> list[str]:
    missing: list[str] = []
    for question in questions:
        visible, required = compute_question_state(question, respostas)
        if not visible or not required:
            continue

        question_id = str(_read_attr(question, "id", ""))
        value = respostas.get(question_id)
        if not _is_filled(value):
            text = str(_read_attr(question, "texto", question_id))
            missing.append(text)

    return missing
