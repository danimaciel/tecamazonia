"""Liga cada solução tecnológica ao material de apoio para usá-la (lógica do painel TecAmazônia de 2022:
produto -> tecnologia -> publicação que ensina a usar).

Duas origens, que a curadoria confirma ou troca:
  declarado  a ficha da solução no Redape cita o PDF na Infoteca-e ou no Alice ("Onde encontrar", descrição)
  sugerido   publicação técnica do recorte com o mesmo produto e as mesmas palavras raras no título;
             a nota mede a confiança (alta >= 40, média >= 20, baixa abaixo disso)
"""
import math, re, unicodedata
from collections import Counter, defaultdict

PARADAS = set("""para como com sem sobre entre pelo pela pelos pelas uma umas uns dos das nos nas que sua seu suas seus este esta estes estas
isso essa esse cada mais menos muito pode podem deve ser sao foi tem ter tambem quando onde qual quais
embrapa sistema sistemas producao produtor produtores tecnologia tecnologias solucao uso usos utilizacao
estado estados regiao amazonia brasil brasileira brasileiro municipio area areas forma partir base meio
recomendacao recomendacoes informacoes documento documentos circular comunicado tecnico tecnica tecnicos
boas praticas avaliacao analise estudo""".split())

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def fichas(texto):
    t = sem_acento((texto or "").lower())
    t = re.sub(r"\bbrs\s+([a-z0-9]+)", r"brs_\1", t)      # nome de cultivar vira uma palavra só
    return {w for w in re.findall(r"[a-z0-9_]{4,}", t) if w not in PARADAS and not w.isdigit()}

PDF = re.compile(r"https?://(?:www\.)?(?:infoteca|alice)\.cnptia\.embrapa\.br/[^\s;,)\]]+")
DOC = re.compile(r"/doc/(\d+)")


def confianca(nota: float) -> str:
    return "alta" if nota >= 40 else "média" if nota >= 20 else "baixa"


def sugerir_apoio(sol, tec, textos_completos, maximo=3):
    """Preenche s["apoio"] em cada solução: lista de {c, t, pdf, origem, nota}.

    textos_completos: código da solução -> texto inteiro de "Onde encontrar" e da descrição, antes de cortar."""
    por_doc = {}
    for p in tec:
        m = DOC.search(p.get("pdf", ""))
        if m:
            por_doc[m.group(1)] = p
    pt = [(fichas(p["t"]), fichas(p.get("r", ""))) for p in tec]
    df = Counter(w for a, b in pt for w in a | b)
    n = len(tec)
    idf = lambda w: math.log(1 + n / (1 + df[w]))
    por_prod = defaultdict(list)
    for i, p in enumerate(tec):
        for x in p["p"]:
            por_prod[x].append(i)
    for s in sol:
        st, sd = fichas(s["t"]), fichas(s.get("d", "")[:400])
        cand = {i for x in s["p"] for i in por_prod[x]} if s["p"] else range(n)
        notas = []
        for i in cand:
            a, b = pt[i]
            nota = sum(3 * idf(w) for w in st & a) + sum(idf(w) for w in st & b) + sum(idf(w) for w in (sd - st) & a)
            if s.get("u") and s["u"] == tec[i].get("u"):
                nota *= 1.2
            notas.append((nota, i))
        notas.sort(reverse=True)
        top = notas[0][0] if notas else 0
        apoio = []
        for url in dict.fromkeys(PDF.findall(textos_completos.get(s["c"], ""))):
            m = DOC.search(url)
            p = por_doc.get(m.group(1)) if m else None
            apoio.append({"c": p["c"] if p else "", "t": p["t"] if p else "", "pdf": p["pdf"] if p else url,
                          "origem": "declarado", "nota": 100})
        vistos = {a["c"] for a in apoio if a["c"]}
        for nota, i in notas[:maximo]:
            if nota >= 12 and nota >= 0.5 * top and tec[i]["c"] not in vistos and len(apoio) < maximo:
                apoio.append({"c": tec[i]["c"], "t": tec[i]["t"], "pdf": tec[i].get("pdf", ""),
                              "origem": "sugerido", "nota": round(nota, 1)})
        s["apoio"] = apoio
