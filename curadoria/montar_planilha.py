"""Monta o arquivo Excel da planilha de curadoria a partir da fila do recorte (pendentes.csv).

O arquivo é importado na planilha Google (Arquivo → Importar → Substituir planilha). Depois disso a fila
de cada mês entra pelo menu TecAmazônia → Trazer novos pendentes (curadoria/planilha.gs).

Uso:  python curadoria/montar_planilha.py saida/pendentes.csv curadoria.xlsx
"""
import csv
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ABAS = {
    "Soluções": ["decisao", "apoio_confirmado", "observacao", "revisor", "data", "prioridade", "motivo", "codigo",
                 "titulo", "unidade", "ano", "tipo", "produtos", "ufs", "apoio_sugerido", "apoio_titulos", "link"],
    "Publicações técnicas": ["decisao", "observacao", "revisor", "data", "prioridade", "motivo", "codigo",
                             "titulo", "unidade", "ano", "tipo", "produtos", "ufs", "link"],
}
LARGURA = {"decisao": 13, "apoio_confirmado": 22, "observacao": 28, "revisor": 18, "data": 11, "prioridade": 10,
           "motivo": 22, "codigo": 13, "titulo": 60, "unidade": 26, "ano": 7, "tipo": 24, "produtos": 24,
           "ufs": 12, "apoio_sugerido": 22, "apoio_titulos": 70, "link": 30}
EDITAVEIS = {"decisao", "apoio_confirmado", "observacao", "revisor", "data"}
COMO_USAR = [
    "TecAmazônia: curadoria antes de publicar",
    "",
    "Nada chega ao produtor sem passar por aqui. Cada linha é uma solução tecnológica ou publicação técnica da Amazônia.",
    "As colunas amarelas são da equipe; as outras vêm do recorte e não devem ser mudadas.",
    "",
    "Como decidir",
    "1. Na coluna decisao, escolha aprovado ou reprovado. Linha sem decisão continua na fila e não vai ao produtor.",
    "2. Soluções: confira o material de apoio sugerido (apoio_titulos). Ele é a publicação que ensina a usar a tecnologia.",
    "   Se a sugestão estiver certa, só aprove. Se não, escreva em apoio_confirmado os códigos certos (PUB 123) ou links, separados por ;.",
    "   Solução sem material de apoio não chega ao produtor, mesmo aprovada.",
    "3. Em lote: use o filtro (por unidade, produto, estado, prioridade), selecione as linhas e use o menu",
    "   TecAmazônia → Aprovar linhas selecionadas (ou Reprovar). O menu preenche revisor e data.",
    "",
    "Prioridade: 1 = bioma Amazônia; 2 = só estado do núcleo amazônico (AC, AM, AP, PA, RO, RR); 3 = só MT, MA ou TO.",
    "Origem do apoio: declarado = a ficha da solução cita o PDF; sugerido = mesmo produto e palavras do título (confiança alta, média ou baixa).",
    "",
    "Todo mês",
    "O recorte roda no dia 16 e lê as decisões desta planilha. No dia 17, o menu TecAmazônia → Trazer novos pendentes",
    "acrescenta o que é novo, sem mexer no que já foi decidido (dá para deixar automático em Apps Script → Acionadores).",
    "",
    "Para funcionar, a planilha precisa estar compartilhada como \"qualquer pessoa com o link pode ver\" e ter o script",
    "curadoria/planilha.gs do repositório colado em Extensões → Apps Script.",
]


def main(origem: str, destino: str) -> None:
    with open(origem, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    wb = Workbook()
    ws = wb.active
    ws.title = "Como usar"
    for i, t in enumerate(COMO_USAR, 1):
        c = ws.cell(row=i, column=1, value=t)
        if i == 1:
            c.font = Font(bold=True, size=16)
        elif t in ("Como decidir", "Todo mês"):
            c.font = Font(bold=True, size=12)
    ws.column_dimensions["A"].width = 130

    amarelo = PatternFill("solid", fgColor="FFF4CC")
    cinza = PatternFill("solid", fgColor="E8EEEA")
    for nome, cols in ABAS.items():
        ws = wb.create_sheet(nome)
        ws.append(cols)
        for j, c in enumerate(cols, 1):
            cel = ws.cell(row=1, column=j)
            cel.font = Font(bold=True)
            cel.fill = amarelo if c in EDITAVEIS else cinza
            ws.column_dimensions[cel.column_letter].width = LARGURA.get(c, 15)
        sol = nome == "Soluções"
        for l in linhas:
            if l["codigo"].startswith("TEC") != sol:
                continue
            ws.append([l.get("apoio", "") if c == "apoio_sugerido" else ("" if c in EDITAVEIS else l.get(c, "")) for c in cols])
        n = ws.max_row
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(cols)).column_letter}{n}"
        dv = DataValidation(type="list", formula1='"aprovado,reprovado"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"A2:A{max(n, 2) + 2000}")
        ws.conditional_formatting.add(f"A2:A{n + 2000}", FormulaRule(formula=['$A2="aprovado"'], fill=PatternFill("solid", fgColor="D5EFDD")))
        ws.conditional_formatting.add(f"A2:A{n + 2000}", FormulaRule(formula=['$A2="reprovado"'], fill=PatternFill("solid", fgColor="F6D6D6")))
        for row in ws.iter_rows(min_row=2, max_row=n):
            for c in row:
                c.alignment = Alignment(vertical="top", wrap_text=cols[c.column - 1] in ("titulo", "apoio_titulos"))
        print(f"{nome}: {n - 1} linhas")
    wb.save(destino)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
