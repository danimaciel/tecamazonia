"""Gera app/index.html a partir de app/fonte/template.html, do catálogo e dos dados da jornada de adoção.

Tudo vai dentro da página, para ela funcionar aberta direto do celular, sem internet e sem servidor:
  - catálogo de 2022 (app/dados/catalogo-2022.json);
  - planos de adoção, etapas e parceiros (curadoria/planos.csv, etapas.csv, parceiros.csv). Quando a planilha
    Google da jornada (config/jornada.txt, ou a da curadoria em config/curadoria.txt) tem as abas Planos, Etapas ou Parceiros, elas valem mais que os
    arquivos do repositório;
  - municípios da Amazônia Legal com coordenadas (app/dados/municipios.json), para achar o município pelo GPS;
  - um plano de teste (app/fonte/plano-teste.json), que só aparece abrindo a página com #teste.

O que foi reprovado não entra. O que ainda não tem decisão entra marcado e só aparece no modo extensionista.

Uso:  python app/fonte/construir.py
"""
import csv
import io
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote

APP = Path(__file__).resolve().parents[1]
RAIZ = APP.parent
COLUNA_DA_ABA = {"Planos": "plano", "Etapas": "ordem", "Parceiros": "o_que_faz"}


def ler_aba(aba: str) -> list[dict] | None:
    """Lê uma aba da planilha de curadoria como CSV; None se não houver planilha, aba ou internet."""
    cfg = next((c for c in (RAIZ / "config" / "jornada.txt", RAIZ / "config" / "curadoria.txt") if c.exists()), None)
    if not cfg:
        return None
    m = re.search(r"/spreadsheets/d/([\w-]+)", cfg.read_text(encoding="utf-8"))
    if not m:
        return None
    url = f"https://docs.google.com/spreadsheets/d/{m.group(1)}/gviz/tq?tqx=out:csv&sheet={quote(aba)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            texto = r.read().decode("utf-8")
    except Exception:
        return None
    linhas = list(csv.DictReader(io.StringIO(texto)))
    # Aba que não existe: o Google devolve a primeira aba; confere por uma coluna que só esta aba tem
    if not linhas or COLUNA_DA_ABA[aba] not in linhas[0]:
        return None
    print(f"Planilha: aba {aba} ({len(linhas)} linhas)")
    return linhas


def ler(nome: str, aba: str) -> list[dict]:
    linhas = ler_aba(aba)
    if linhas is None:
        with open(RAIZ / "curadoria" / f"{nome}.csv", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
    return [{k.strip(): (v or "").strip() for k, v in l.items() if k} for l in linhas]


def situacao(l: dict) -> str:
    d = l.get("decisao", "").lower()
    return "aprovado" if d.startswith("aprov") else ("reprovado" if d.startswith("reprov") else "")


def jornada() -> dict:
    etapas = {}
    for e in ler("etapas", "Etapas"):
        if e.get("plano") and e.get("titulo"):
            etapas.setdefault(e["plano"], []).append(e)
    planos = []
    for p in ler("planos", "Planos"):
        rev = situacao(p)
        if not p.get("plano") or rev == "reprovado":
            continue
        ets = sorted(etapas.get(p["plano"], []), key=lambda e: float(e.get("ordem") or 0))
        planos.append({
            "id": p["plano"], "t": p.get("titulo", ""), "prod": p.get("produto", ""), "nec": p.get("necessidade", ""),
            "tec": [c.strip() for c in p.get("tecnologias", "").split(";") if c.strip()],
            "pub": p.get("publicacao", ""), "pubt": p.get("publicacao_titulo", ""), "audio": p.get("audio", ""),
            "video": p.get("video", ""), "r": p.get("resumo", ""), "rev": rev,
            "etapas": [{"t": e["titulo"], "f": e.get("o_que_fazer", ""), "q": e.get("quando", ""), "fonte": e.get("fonte", "")}
                       for e in ets],
        })
    parceiros = []
    for p in ler("parceiros", "Parceiros"):
        rev = situacao(p)
        if not p.get("nome") or rev == "reprovado":
            continue
        parceiros.append({"n": p["nome"], "tipo": p.get("tipo", ""), "uf": p.get("uf", ""), "mun": p.get("municipio", ""),
                          "o": p.get("o_que_faz", ""), "contato": p.get("contato", ""), "site": p.get("site", ""), "rev": rev})
    teste = json.loads((APP / "fonte" / "plano-teste.json").read_text(encoding="utf-8"))
    municipios = json.loads((APP / "dados" / "municipios.json").read_text(encoding="utf-8"))
    return {"planos": planos, "parceiros": parceiros, "teste": teste, "municipios": municipios}


def embutir(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


modelo = (APP / "fonte" / "template.html").read_text(encoding="utf-8")
catalogo = (APP / "dados" / "catalogo-2022.json").read_text(encoding="utf-8").replace("</", "<\\/")
j = jornada()
pagina = modelo.replace("__DATA__", catalogo).replace("__JORNADA__", embutir(j))
(APP / "index.html").write_text(pagina, encoding="utf-8")
prontos = sum(1 for p in j["planos"] if p["rev"] == "aprovado" and p["etapas"])
print(f"app/index.html gerado ({(APP / 'index.html').stat().st_size / 1e3:.0f} kB); "
      f"{len(j['planos'])} planos ({prontos} aprovados com etapas), {len(j['parceiros'])} parceiros")
