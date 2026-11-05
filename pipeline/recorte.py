"""Recorta a Amazônia nas exportações do Redape e monta o pacote de dados do app TecAmazônia.

Entradas
  dados/<AAAA-MM>/{publicacoes,projetos,solucoes-tecnologicas}-da-embrapa-<AAAA-MM>.csv   (pipeline/redape.py)
  dados/enriquecimento/                       produtos, estados e biomas por documento (pipeline/observatorio.py)
  config/tipos_publicacao.csv                 tipo de publicação -> camada (tecnico | cientifico)
  curadoria/revisados.csv                     decisões da equipe sobre soluções e publicações técnicas

Critério da Amazônia: o documento entra se o Observatório marcou o bioma Amazônia (declarado na solução
tecnológica ou bioma predominante do município citado) OU se cita um estado da Amazônia Legal.
Com --so-bioma, entra só pelo bioma.

Camadas das publicações: pelo "Tipo de publicação" do Redape, segundo config/tipos_publicacao.csv. Tipo que
não está na tabela cai numa regra por palavras e fica marcado para revisão no relatório; sem regra, fica
"revisar" e não entra no app até alguém classificar. Checagem extra: PDF na Infoteca-e indica publicação
técnica editada pela Embrapa; PDF no Alice indica produção científica (só informada no relatório).

Saídas em saida/
  pacote.json              tudo o que o app usa (soluções, técnicas, científicas, projetos, produtos), para o
                           extensionista; o que ainda não foi revisado vai com rev vazio ("em revisão")
  pacote-produtor.json     só soluções e publicações técnicas APROVADAS pela curadoria, para o celular
  tipos_publicacao.csv     cada tipo encontrado, a camada usada, de onde veio e quantos há
  pendentes.csv            soluções e publicações técnicas da Amazônia ainda sem decisão da curadoria,
                           da mais amazônica para a menos (coluna prioridade)
  resumo.md                números do recorte, para o resumo do fluxo no GitHub

Uso:  python pipeline/recorte.py 2026-10 [--so-bioma]
"""
import json
import re
import sys
import unicodedata
from datetime import date
from urllib.parse import quote
from pathlib import Path

import pandas as pd

from apoio import confianca, sugerir_apoio

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "dados"
SAIDA = RAIZ / "saida"
UFS_AMAZONIA_LEGAL = {"AC", "AM", "AP", "PA", "RO", "RR", "TO", "MT", "MA"}
BIOMA = "Amazônia"
RESUMO_MAX = 700

# Regras de reserva para tipos que ainda não estão em config/tipos_publicacao.csv (texto sem acento).
REGRAS = [
    ("cientifico", r"artigo em periodico|anais|resumo|tese|dissert|livro cientifico|boletim de pesquisa|nota cientifica|evento"),
    ("tecnico", r"documentos|circular|comunicado|folder|folheto|cartilha|livro tecnico|orientac|guia|manual|colec|plantar|agroindustria|perguntas|divulgacao"),
]


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def limpo(t) -> str:
    return re.sub(r"\s+", " ", str(t)).strip() if isinstance(t, str) else ""


def curto(t: str, n: int) -> str:
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def ler(mes: str, nome: str) -> pd.DataFrame:
    return pd.read_csv(DADOS / mes / f"{nome}-da-embrapa-{mes}.csv", dtype=str)


def camadas(tipos: pd.Series) -> pd.DataFrame:
    """Para cada tipo de publicação: camada e origem (tabela, regra ou sem regra)."""
    tab = pd.read_csv(RAIZ / "config" / "tipos_publicacao.csv", dtype=str).fillna("")
    por_nome = {sem_acento(t.lower()).strip(): c for t, c in zip(tab.tipo, tab.camada)}
    linhas = []
    for t in sorted(set(tipos.fillna(""))):
        chave = sem_acento(t.lower()).strip()
        if chave in por_nome:
            linhas.append((t, por_nome[chave], "tabela"))
            continue
        for camada, rx in REGRAS:
            if re.search(rx, chave):
                linhas.append((t, camada, "regra"))
                break
        else:
            linhas.append((t, "revisar", "sem regra"))
    return pd.DataFrame(linhas, columns=["tipo", "camada", "origem"]).set_index("tipo")


PRIORIDADES = {1: "bioma Amazônia", 2: "só estado do núcleo amazônico (AC, AM, AP, PA, RO, RR)",
               3: "só MT, MA ou TO, que também têm Cerrado"}
UFS_NUCLEO = {"AC", "AM", "AP", "PA", "RO", "RR"}


def prioridade(d: dict) -> tuple:
    """Quão amazônico é o documento, para a curadoria revisar primeiro o que mais interessa à região."""
    if BIOMA in d["b"]:
        return 1, PRIORIDADES[1]
    if set(d["uf"]) & UFS_NUCLEO:
        return 2, PRIORIDADES[2]
    return 3, PRIORIDADES[3]


def ler_planilha() -> pd.DataFrame:
    """Decisões da planilha Google de curadoria (config/curadoria.txt), abas Soluções e Publicações técnicas.

    A planilha precisa estar compartilhada como "qualquer pessoa com o link pode ver". Sem planilha ou sem
    acesso, valem só as decisões de curadoria/revisados.csv."""
    arq = RAIZ / "config" / "curadoria.txt"
    m = re.search(r"/spreadsheets/d/([\w-]+)", arq.read_text(encoding="utf-8")) if arq.exists() else None
    vazio = pd.DataFrame(columns=["codigo", "decisao", "apoio"])
    if not m:
        return vazio
    partes = []
    for aba in ("Soluções", "Publicações técnicas"):
        url = f"https://docs.google.com/spreadsheets/d/{m.group(1)}/gviz/tq?tqx=out:csv&sheet={quote(aba)}"
        try:
            t = pd.read_csv(url, dtype=str).fillna("")
        except Exception as ex:
            print(f"Planilha de curadoria, aba {aba}: não consegui ler ({ex}).")
            continue
        t.columns = [sem_acento(c).strip().lower().replace(" ", "_") for c in t.columns]
        if "codigo" not in t or "decisao" not in t:
            continue
        t["apoio"] = t.get("apoio_confirmado", "")
        t = t[t.decisao.str.strip() != ""]
        t["decisao"] = t.decisao.map(lambda x: "aprovado" if sem_acento(x.lower()).startswith("aprov") else
                                     "reprovado" if sem_acento(x.lower()).startswith("reprov") else "")
        partes.append(t[t.decisao != ""][["codigo", "decisao", "apoio"]])
    return pd.concat(partes, ignore_index=True) if partes else vazio


def apoio_contagem(sol: list) -> dict:
    c = {"com apoio declarado": 0, "só com apoio sugerido": 0, "sem apoio": 0}
    for d in sol:
        origens = {a["origem"] for a in d["apoio"]}
        c["com apoio declarado" if origens - {"sugerido"} else "só com apoio sugerido" if origens else "sem apoio"] += 1
    return c


def main(mes: str, so_bioma: bool) -> None:
    pasta = DADOS / "enriquecimento"
    e = pd.read_csv(pasta / "enriquecimento.csv.gz", dtype=str).fillna("").set_index("doc_uid")
    reg = pd.read_csv(pasta / "registro_obra.csv.gz", dtype=str)
    obra = dict(zip(reg.registro.str[2:], reg.obra_id))
    tax = pd.read_csv(pasta / "produtos.csv", dtype=str).fillna("")
    release = (pasta / "release.txt").read_text(encoding="utf-8").strip() if (pasta / "release.txt").exists() else ""

    def marca(uid: str) -> dict:
        if uid not in e.index:
            return {"p": [], "uf": [], "b": []}
        r = e.loc[uid]
        sep = lambda s: [x for x in s.split(";") if x]
        return {"p": sep(r.produtos), "uf": sep(r.ufs), "b": sep(r.biomas)}

    def na_amazonia(m: dict) -> bool:
        return BIOMA in m["b"] or (not so_bioma and bool(set(m["uf"]) & UFS_AMAZONIA_LEGAL))

    # Soluções tecnológicas
    sol, textos = [], {}
    for r in ler(mes, "solucoes-tecnologicas").to_dict("records"):
        m = marca("T:" + r["ID"])
        if BIOMA in limpo(r.get("Bioma")):
            m["b"] = sorted(set(m["b"]) | {BIOMA})
        if not na_amazonia(m):
            continue
        textos["TEC " + r["ID"]] = " ".join(limpo(r.get(c)) for c in r if re.search(r"onde|descri|link|publica", c, re.I))
        sol.append({"c": "TEC " + r["ID"], "t": limpo(r["Nome"]), "d": curto(limpo(r["Descrição"]), RESUMO_MAX),
                    "a": limpo(r["Ano de lançamento"]),
                    "tipo": " - ".join(x for x in (limpo(r.get("Tipo")), limpo(r.get("Subtipo"))) if x),
                    "u": limpo(r["Unidade responsável"]), "w": curto(limpo(r["Onde encontrar"]), 400),
                    "l": limpo(r["Página da tecnologia no Portal Embrapa"]), **m})

    # Publicações: uma por obra (a mesma publicação depositada por várias unidades), resumo mais longo
    pub = ler(mes, "publicacoes")
    pub["obra"] = pub["ID"].map(lambda i: obra.get(i, "OB:" + i))
    pub["tam"] = pub["Resumo"].fillna("").str.len()
    pub = pub.sort_values("tam", ascending=False).drop_duplicates("obra")
    cam = camadas(pub["Tipo de publicação"])
    tec, cie = [], []
    contagem = []
    for r in pub.to_dict("records"):
        m = marca(r["obra"])
        dentro = na_amazonia(m)
        tipo = limpo(r["Tipo de publicação"])
        camada = cam.loc[tipo, "camada"] if tipo in cam.index else "revisar"
        pdf = limpo(r.get("URL do arquivo"))
        repo = "infoteca" if "infoteca" in pdf else "alice" if "alice" in pdf else ""
        contagem.append((tipo, camada, dentro, repo))
        if not dentro or camada == "revisar":
            continue
        base = {"c": "PUB " + r["ID"], "t": limpo(r["Título"]), "a": limpo(r["Ano de publicação"]), "tipo": tipo,
                "l": limpo(r["Página da publicação no Portal Embrapa"]), **m}
        if camada == "tecnico":
            tec.append({**base, "r": curto(limpo(r["Resumo"]), RESUMO_MAX), "u": limpo(r["Unidade"]), "pdf": pdf})
        else:
            cie.append(base)

    # Projetos (para extensionistas e gestores)
    prj = []
    for r in ler(mes, "projetos").to_dict("records"):
        m = marca("P:" + r["ID"])
        if na_amazonia(m):
            prj.append({"c": "PRJ " + r["ID"], "t": limpo(r["Título"]), "a": limpo(r["mês/ano de início"])[-4:],
                        "u": limpo(r["Unidade líder"]), "l": limpo(r["Página do projeto no Portal Embrapa"]), **m})

    # Material de apoio de cada solução (declarado na ficha ou sugerido pelo recorte)
    sugerir_apoio(sol, tec, textos)

    # Curadoria: reprovados saem de tudo; o produtor só recebe o que foi aprovado
    rev_arq = RAIZ / "curadoria" / "revisados.csv"
    rev = pd.read_csv(rev_arq, dtype=str).fillna("") if rev_arq.exists() else pd.DataFrame(columns=["codigo", "decisao"])
    rev = pd.concat([rev, ler_planilha()], ignore_index=True).drop_duplicates("codigo", keep="last")  # a planilha vale mais
    decisao = dict(zip(rev.codigo, rev.decisao.str.lower()))
    apoio_rev = dict(zip(rev.codigo, rev["apoio"])) if "apoio" in rev else {}
    por_codigo = {d["c"]: d for d in tec}
    for lst in (sol, tec):
        for d in lst:
            d["rev"] = decisao.get(d["c"], "")
    for d in sol:
        # A coluna apoio de revisados.csv (códigos PUB ou links, separados por ;) substitui a sugestão;
        # aprovado sem a coluna preenchida aceita o apoio sugerido que estava na fila
        conf = [x.strip() for x in apoio_rev.get(d["c"], "").split(";") if x.strip()]
        if conf:
            d["apoio"] = [{"c": x, "t": por_codigo[x]["t"], "pdf": por_codigo[x].get("pdf", ""), "origem": "curadoria", "nota": 100}
                          if x in por_codigo else {"c": "", "t": "", "pdf": x, "origem": "curadoria", "nota": 100} for x in conf]
    sol_app = [d for d in sol if d["rev"] != "reprovado"]
    tec_app = [d for d in tec if d["rev"] != "reprovado"]
    # Para o produtor, a solução vai junto com o material que ensina a usá-la
    sol_prod = [d for d in sol if d["rev"] == "aprovado" and d["apoio"]]
    sem_apoio = [d for d in sol if d["rev"] == "aprovado" and not d["apoio"]]
    tec_prod = [d for d in tec if d["rev"] == "aprovado"]

    def lista_produtos(docs: list) -> list:
        usados = {p for d in docs for p in d["p"]}
        return [{"id": r.produto_id, "nome": r.produto, "cat": r.categoria_ampla,
                 "n": sum(r.produto_id in d["p"] for d in docs)}
                for r in tax.itertuples() if r.produto_id in usados]
    meta = {"gerado_em": date.today().isoformat(), "redape": mes, "observatorio": release,
            "criterio": "bioma Amazônia" if so_bioma else "bioma Amazônia ou estado da Amazônia Legal"}

    SAIDA.mkdir(exist_ok=True)
    grava = lambda nome, obj: (SAIDA / nome).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    grava("pacote.json", {**meta, "produtos": lista_produtos(sol_app + tec_app + cie + prj), "solucoes": sol_app, "tecnicas": tec_app,
                          "cientificas": cie, "projetos": prj})
    grava("pacote-produtor.json", {**meta, "produtos": lista_produtos(sol_prod + tec_prod),
                                   "solucoes": sol_prod, "tecnicas": tec_prod})

    c = pd.DataFrame(contagem, columns=["tipo", "camada", "amazonia", "repositorio"])
    rel = (c.groupby(["tipo", "camada"])
             .agg(total=("amazonia", "size"), amazonia=("amazonia", "sum"),
                  pdf_infoteca=("repositorio", lambda s: int((s == "infoteca").sum())),
                  pdf_alice=("repositorio", lambda s: int((s == "alice").sum())))
             .reset_index())
    rel["origem"] = rel.tipo.map(lambda t: cam.loc[t, "origem"] if t in cam.index else "sem regra")
    rel.sort_values("amazonia", ascending=False).to_csv(SAIDA / "tipos_publicacao.csv", index=False)

    nome_prod = dict(zip(tax.produto_id, tax.produto))
    pend = [{"prioridade": prioridade(d)[0], "motivo": prioridade(d)[1],
             "codigo": d["c"], "tipo_doc": "solução" if d["c"].startswith("TEC") else "publicação técnica",
             "titulo": d["t"], "ano": d["a"], "unidade": d.get("u", ""), "tipo": d.get("tipo", ""),
             "apoio": ";".join(a["c"] or a["pdf"] for a in d.get("apoio", [])),
             "apoio_titulos": " | ".join(f"{a['t'] or a['pdf']} ({a['origem']}{', ' + confianca(a['nota']) if a['origem'] == 'sugerido' else ''})"
                                         for a in d.get("apoio", [])), "produtos": "; ".join(nome_prod.get(x, x) for x in d["p"]), "ufs": ";".join(d["uf"]), "link": d["l"],
             "decisao": "", "revisor": "", "data": "", "observacao": ""}
            for d in sol + tec if not d["rev"]]
    pend.sort(key=lambda x: (x["prioridade"], -int(x["ano"]) if x["ano"].isdigit() else 0))
    pd.DataFrame(pend, columns=["prioridade", "motivo", "codigo", "tipo_doc", "titulo", "ano", "unidade", "tipo", "apoio", "apoio_titulos", "produtos", "ufs", "link",
                                "decisao", "revisor", "data", "observacao"]).to_csv(SAIDA / "pendentes.csv", index=False)

    revisar = rel[rel.origem != "tabela"]
    txt = [f"# Recorte da Amazônia — Redape {mes}", "",
           f"Critério: {meta['criterio']}. Marcação: {release or 'sem release'}.", "",
           "| Conjunto | Documentos |", "|---|---|",
           f"| Soluções tecnológicas | {len(sol_app)} |",
           f"| Publicações técnicas | {len(tec_app)} |",
           f"| Publicações científicas | {len(cie)} |",
           f"| Projetos | {len(prj)} |",
           f"| Liberados para o produtor (aprovados) | {len(sol_prod) + len(tec_prod)} |",
           f"| Soluções aprovadas mas sem material de apoio (não vão ao produtor) | {len(sem_apoio)} |",
           f"| Aguardando curadoria (soluções e técnicas) | {len(pend)} |", "",
           "Material de apoio das soluções: " + ", ".join(f"{n} {o}" for o, n in apoio_contagem(sol).items()) + ".", "",
           "Fila de curadoria por prioridade: " + ", ".join(
               f"{n} = {PRIORIDADES[n]} ({sum(x['prioridade'] == n for x in pend)})" for n in sorted(PRIORIDADES)) + ".", ""]
    if len(revisar):
        txt += ["## Tipos de publicação para classificar em config/tipos_publicacao.csv", "",
                "| Tipo | Camada usada | Origem | Na Amazônia |", "|---|---|---|---|"]
        txt += [f"| {r.tipo or '(vazio)'} | {r.camada} | {r.origem} | {int(r.amazonia)} |" for r in revisar.itertuples()]
    (SAIDA / "resumo.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit("Uso: python pipeline/recorte.py AAAA-MM [--so-bioma]")
    main(args[0], "--so-bioma" in sys.argv)
