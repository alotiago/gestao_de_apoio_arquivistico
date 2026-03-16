from app.services.condicional import (
    compute_question_state,
    evaluate_condition,
    list_missing_required,
)


class FakeCondicao:
    def __init__(self, operador: str, valor: dict, acao: str) -> None:
        self.operador = operador
        self.valor = valor
        self.acao = acao


class FakePergunta:
    def __init__(
        self,
        question_id: str,
        texto: str,
        obrigatoria: bool,
        condicoes: list[FakeCondicao] | None = None,
    ) -> None:
        self.id = question_id
        self.texto = texto
        self.obrigatoria = obrigatoria
        self.condicoes = condicoes or []


def test_evaluate_condition_eq_true() -> None:
    respostas = {"q1": "Sim"}
    assert evaluate_condition("EQ", {"pergunta_id": "q1", "valor": "Sim"}, respostas)


def test_evaluate_condition_gt_true() -> None:
    respostas = {"q1": 12}
    assert evaluate_condition("GT", {"pergunta_id": "q1", "valor": 10}, respostas)


def test_evaluate_condition_and_true() -> None:
    respostas = {"q1": "Sim", "q2": 5}
    condition = {
        "condicoes": [
            {"operador": "EQ", "valor": {"pergunta_id": "q1", "valor": "Sim"}},
            {"operador": "GTE", "valor": {"pergunta_id": "q2", "valor": 5}},
        ]
    }
    assert evaluate_condition("AND", condition, respostas)


def test_compute_question_state_hides_question() -> None:
    pergunta = FakePergunta(
        question_id="q2",
        texto="Pergunta condicional",
        obrigatoria=True,
        condicoes=[
            FakeCondicao(
                operador="EQ",
                valor={"pergunta_id": "q1", "valor": "Não"},
                acao="ocultar",
            )
        ],
    )
    visible, required = compute_question_state(pergunta, {"q1": "Não"})
    assert not visible
    assert required


def test_list_missing_required_returns_question_text() -> None:
    perguntas = [
        FakePergunta(question_id="q1", texto="Nome do processo", obrigatoria=True),
        FakePergunta(question_id="q2", texto="Prazo contratual", obrigatoria=False),
    ]
    pendencias = list_missing_required(perguntas, {"q2": 12})
    assert pendencias == ["Nome do processo"]
