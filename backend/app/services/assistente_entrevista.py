"""Heurísticas leves para prévia assistida de PCD/TTD na entrevista."""


def suggest_retention_preview(respostas: dict[str, object], sugestao_classe: str) -> tuple[str, str]:
    texto_base = " ".join(str(valor).lower() for valor in respostas.values())
    classe = sugestao_classe.lower()

    if any(termo in texto_base for termo in ["contrato", "fornecedor", "licitação"]) or "contrato" in classe:
        return (
            "Fim do contrato + 5 anos · eliminação",
            "Indícios contratuais nas respostas sugerem regra típica de retenção contratual com descarte após prazo legal.",
        )

    if any(termo in texto_base for termo in ["nota fiscal", "fiscal", "tribut", "pagamento"]):
        return (
            "Exercício fiscal + 10 anos · eliminação",
            "Presença de termos fiscais/financeiros indica retenção ampliada para auditoria e fiscalização.",
        )

    if any(termo in texto_base for termo in ["histórico", "memória", "institucional", "governança"]) or "governança" in classe:
        return (
            "Guarda permanente",
            "As respostas apontam valor secundário e potencial histórico, justificando preservação permanente.",
        )

    return (
        "Validar TTD setorial",
        "As respostas ainda não delimitam evento de guarda com segurança; revisar base legal e evento de início.",
    )
