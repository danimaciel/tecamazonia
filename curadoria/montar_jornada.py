"""Monta as abas Planos, Etapas e Parceiros para acrescentar à planilha Google da curadoria.

Lê curadoria/planos.csv, etapas.csv e parceiros.csv e gera um Excel com as três abas. Na planilha Google:
Arquivo → Importar → Enviar o arquivo → "Inserir nova(s) página(s)". Depois disso, o app passa a ler as abas
da planilha (app/fonte/construir.py), que valem mais que os arquivos do repositório.

Uso:  python curadoria/montar_jornada.py jornada.xlsx
"""
import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

PASTA = Path(__file__).resolve().parent
ABAS = {"Planos": "planos", "Etapas": "etapas", "Parceiros": "parceiros"}
EDITAVEIS = {"decisao", "revisor", "data", "observacao", "titulo", "o_que_fazer", "quando", "fonte", "resumo",
             "video", "audio", "contato", "site", "o_que_faz", "municipio", "ordem"}
LARGO = {"titulo": 40, "o_que_fazer": 70, "resumo": 50, "publicacao": 40, "publicacao_titulo": 45, "o_que_faz": 50,
         "observacao": 35, "nome": 32, "tecnologias": 24, "fonte": 30}


def main(destino: str) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    amarelo, cinza = PatternFill("solid", fgColor="FFF4CC"), PatternFill("solid", fgColor="E8EEEA")
    for aba, arq in ABAS.items():
        with open(PASTA / f"{arq}.csv", encoding="utf-8") as f:
            leitor = csv.reader(f)
            cab = next(leitor)
            linhas = list(leitor)
        ws = wb.create_sheet(aba)
        ws.append(cab)
        for j, c in enumerate(cab, 1):
            cel = ws.cell(row=1, column=j)
            cel.font = Font(bold=True)
            cel.fill = amarelo if c in EDITAVEIS else cinza
            ws.column_dimensions[cel.column_letter].width = LARGO.get(c, 14)
        for l in linhas:
            ws.append(l)
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(vertical="top", wrap_text=True)
        ws.freeze_panes = "A2"
        if "decisao" in cab:
            col = ws.cell(row=1, column=cab.index("decisao") + 1).column_letter
            dv = DataValidation(type="list", formula1='"aprovado,reprovado"', allow_blank=True)
            ws.add_data_validation(dv)
            dv.add(f"{col}2:{col}2000")
        print(f"{aba}: {len(linhas)} linhas")
    wb.save(destino)


if __name__ == "__main__":
    main(sys.argv[1])
