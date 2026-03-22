from datetime import datetime
from docx import Document
from docx.shared import Pt

OUT = r"c:\des\gestao_de_apoio_arquivistico\docs\MANUAL_EXECUTIVO_TREINAMENTO_ARQUIVISTAS.docx"


def title(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(20)


def bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def main() -> None:
    doc = Document()

    title(doc, "Manual Executivo de Treinamento - Arquivistas")
    doc.add_paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    doc.add_paragraph("Objetivo: capacitar rapidamente a equipe para operar o sistema no dia a dia.")

    doc.add_heading("1. Fluxo Diario (15 min)", level=1)
    bullets(doc, [
        "Acessar o dashboard e conferir status geral dos modulos.",
        "Validar health do backend e fila de jobs.",
        "Verificar entrevistas submetidas e devolvidas.",
        "Monitorar importacoes com erro e acionar reprocessamento.",
    ])

    doc.add_heading("2. Roteiro Operacional (30 min)", level=1)
    bullets(doc, [
        "Criar/ajustar roteiro de entrevista e perguntas.",
        "Atribuir entrevista para cliente quando necessario.",
        "Revisar respostas e evidencias anexadas.",
        "Concluir ou devolver com motivo objetivo.",
    ])

    doc.add_heading("3. Classificacao e Temporalidade (30 min)", level=1)
    bullets(doc, [
        "Manter arvore PCD atualizada (funcao ate tipo documental).",
        "Criar e revisar regras TTD por nivel.",
        "Aplicar hold quando houver impedimento legal.",
        "Emitir ordens de destinacao conforme politica.",
    ])

    doc.add_heading("4. Governanca e Auditoria (20 min)", level=1)
    bullets(doc, [
        "Atualizar matriz de rastreabilidade (norma x classe).",
        "Consultar logs de auditoria e integridade.",
        "Registrar evidencias de decisao em processos criticos.",
    ])

    doc.add_heading("5. Relatorios Essenciais (20 min)", level=1)
    bullets(doc, [
        "Gerar dashboard de temporalidade para visao executiva.",
        "Exportar PDF/CSV/Excel para reunioes e compliance.",
        "Emitir termo de eliminacao e relatorio de transferencia/recolhimento.",
    ])

    doc.add_heading("6. Atalhos de Suporte", level=1)
    bullets(doc, [
        "Se frontend estiver lento no primeiro acesso, aguarde compilacao inicial do Next.js.",
        "Health backend principal: /health.",
        "Logs locais: docker compose logs backend/frontend/celery-worker --tail 200.",
    ])

    doc.add_heading("7. Checklist de Encerramento (5 min)", level=1)
    bullets(doc, [
        "Pendencias de entrevistas tratadas.",
        "Jobs de retencao sem erro.",
        "Importacoes com falha registradas para acao.",
        "Relatorio diario exportado quando aplicavel.",
    ])

    doc.save(OUT)
    print(f"Manual executivo gerado em: {OUT}")


if __name__ == "__main__":
    main()
