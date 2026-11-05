"""Gera app/dados/acervo.json, o acervo da Amazônia que o app carrega, a partir do pacote mensal.

O pacote vem da release pacote-AAAA-MM mais recente deste repositório (ou de um arquivo local) e é
enxugado para o celular: resumo curto, link sem o domínio, só os campos que a tela usa.

Uso:  python app/fonte/acervo.py                  # baixa o pacote.json.gz da release mais recente
      python app/fonte/acervo.py saida/pacote.json  # usa um pacote local

Sem pacote (sem internet ou sem release), o app segue só com o catálogo de 2022.
"""
import gzip
import json
import os
import sys
from pathlib import Path

import urllib.request

APP = Path(__file__).resolve().parent.parent
DESTINO = APP / "dados" / "acervo.json"
REPO = os.environ.get("GITHUB_REPOSITORY", "danimaciel/tecamazonia")
RESUMO = 320
DOMINIO = "https://www.embrapa.br"
# Começo do link de cada tipo; o app remonta o link com o número do código (TEC 15 -> .../produto-servico/15/)
PREFIXO = {"s": "/busca-de-solucoes-tecnologicas/-/produto-servico/", "t": "/busca-de-publicacoes/-/publicacao/",
           "c": "/busca-de-publicacoes/-/publicacao/", "p": "/busca-de-projetos/-/projeto/"}


def pedir(url: str, binario: bool = False) -> bytes:
    cab = {"Accept": "application/octet-stream" if binario else "application/vnd.github+json",
           "User-Agent": "tecamazonia-app"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        cab["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=cab), timeout=120) as r:
        return r.read()


def baixar() -> dict | None:
    rels = json.loads(pedir(f"https://api.github.com/repos/{REPO}/releases?per_page=30"))
    rels = sorted((r for r in rels if r["tag_name"].startswith("pacote-")), key=lambda r: r["tag_name"], reverse=True)
    for rel in rels:
        for a in rel["assets"]:
            if a["name"] == "pacote.json.gz":
                print(f"Pacote: {rel['tag_name']}")
                return json.loads(gzip.decompress(pedir(a["url"], binario=True)))
    return None


def curto(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def main() -> None:
    if len(sys.argv) > 1:
        caminho = Path(sys.argv[1])
        abrir = gzip.open if caminho.suffix == ".gz" else open
        with abrir(caminho, "rt", encoding="utf-8") as f:
            pac = json.load(f)
    else:
        try:
            pac = baixar()
        except Exception as ex:  # sem rede ou sem release: o app funciona só com o catálogo de 2022
            print(f"Não consegui baixar o pacote ({ex}); o app fica só com o catálogo de 2022.")
            pac = None
    if not pac:
        DESTINO.unlink(missing_ok=True)
        return

    itens, tipos = [], []
    for chave, k in (("solucoes", "s"), ("tecnicas", "t"), ("cientificas", "c"), ("projetos", "p")):
        for d in pac.get(chave, []):
            it = {"k": k, "c": d["c"], "t": d["t"], "a": d.get("a", ""), "p": d.get("p", []), "uf": d.get("uf", [])}
            if d.get("tipo"):  # tipos repetem muito: guarda o índice na lista de tipos
                if d["tipo"] not in tipos:
                    tipos.append(d["tipo"])
                it["tp"] = tipos.index(d["tipo"])
            resumo = d.get("d") or d.get("r")
            if resumo and k in "st":
                it["r"] = curto(resumo, RESUMO)
            for campo in ("u", "pdf", "rev"):
                if d.get(campo):
                    it[campo] = d[campo]
            if d.get("w") and k == "s":
                it["w"] = curto(d["w"], 200)
            if d.get("l"):
                base = DOMINIO + PREFIXO[k] + d["c"].split(" ")[1] + "/"
                it["l"] = d["l"][len(base):] if d["l"].startswith(base) else d["l"]
            if d.get("apoio"):  # material de apoio da solução: título, PDF e origem (d declarado, s sugerido, c curadoria)
                it["ap"] = [{"t": a.get("t", ""), "pdf": a.get("pdf", ""), "o": a.get("origem", "")[:1]} for a in d["apoio"]]
            if "Amazônia" in d.get("b", []):
                it["am"] = 1
            itens.append(it)

    acervo = {"gerado_em": pac.get("gerado_em"), "redape": pac.get("redape"), "criterio": pac.get("criterio"),
              "dominio": DOMINIO, "prefixo": PREFIXO, "tipos": tipos,
              "produtos": [{"id": p["id"], "nome": p["nome"]} for p in pac.get("produtos", [])], "itens": itens}
    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(json.dumps(acervo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{DESTINO.relative_to(APP.parent)}: {len(itens)} itens, {DESTINO.stat().st_size // 1024} kB")


if __name__ == "__main__":
    main()
