"""Baixa a marcação de produtos, estados e biomas do Observatório de Pesquisa da Embrapa.

Usa a release pública mais recente "enriquecimento-AAAA-MM" de danimaciel/observatorio_embrapa, a mesma
fonte dos três iAgros. Só baixa os arquivos que o recorte usa. Funciona sem token; com GITHUB_TOKEN ou
GH_TOKEN no ambiente, o limite de consultas da API é maior.

Uso:  python pipeline/observatorio.py              (release mais recente)
      python pipeline/observatorio.py 2026-10
Grava em dados/enriquecimento/ e imprime o nome da release na última linha.
"""
import os
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
REPO = "danimaciel/observatorio_embrapa"
ARQUIVOS = ["enriquecimento.csv.gz", "registro_obra.csv.gz", "produtos.csv", "temas.csv"]


def cabecalho(binario: bool = False) -> dict:
    h = {"Accept": "application/octet-stream" if binario else "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def main():
    r = requests.get(f"https://api.github.com/repos/{REPO}/releases", params={"per_page": 50},
                     headers=cabecalho(), timeout=60)
    r.raise_for_status()
    rels = [x for x in r.json() if x["tag_name"].startswith("enriquecimento-")]
    if len(sys.argv) > 1:
        rels = [x for x in rels if x["tag_name"] == f"enriquecimento-{sys.argv[1]}"]
    if not rels:
        raise SystemExit("Nenhuma release de enriquecimento encontrada no Observatório.")
    rel = max(rels, key=lambda x: x["tag_name"])
    pasta = RAIZ / "dados" / "enriquecimento"
    pasta.mkdir(parents=True, exist_ok=True)
    anexos = {a["name"]: a for a in rel["assets"]}
    for nome in ARQUIVOS:
        if nome not in anexos:
            raise SystemExit(f"{rel['tag_name']} não tem {nome}.")
        with requests.get(anexos[nome]["url"], headers=cabecalho(True), stream=True, timeout=300) as d:
            d.raise_for_status()
            with open(pasta / nome, "wb") as fh:
                for bloco in d.iter_content(1 << 20):
                    fh.write(bloco)
        print(f"baixado {nome}")
    (pasta / "release.txt").write_text(rel["tag_name"], encoding="utf-8")
    print(rel["tag_name"])


if __name__ == "__main__":
    main()
