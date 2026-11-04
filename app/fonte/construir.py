"""Gera app/index.html a partir de app/fonte/template.html e do catálogo em app/dados/.

O catálogo vai dentro da página, para ela funcionar aberta direto do celular, sem internet e sem servidor.

Uso:  python app/fonte/construir.py
"""
from pathlib import Path

APP = Path(__file__).resolve().parents[1]

modelo = (APP / "fonte" / "template.html").read_text(encoding="utf-8")
dados = (APP / "dados" / "catalogo-2022.json").read_text(encoding="utf-8").replace("</", "<\\/")
(APP / "index.html").write_text(modelo.replace("__DATA__", dados), encoding="utf-8")
print(f"app/index.html gerado ({(APP / 'index.html').stat().st_size / 1e3:.0f} kB)")
