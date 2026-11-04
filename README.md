# TecAmazônia

Soluções tecnológicas e publicações da Embrapa para quem produz na Amazônia, num app que funciona sem internet.
O produtor fala ou escreve o que está acontecendo na roça ou na criação, e o app mostra as soluções que se
aplicam, num mapa de rede com os produtos, e lê a resposta em voz alta.

Relançamento do aplicativo TecAmazônia (Embrapa, 2021), retirado das lojas por falta de atualização. Nesta versão
o conteúdo se atualiza sozinho todo mês a partir dos dados públicos da Embrapa, com curadoria da equipe antes de
chegar ao app. Não é um serviço oficial da Embrapa.

| Parte | O que é |
|---|---|
| `app/` | O app (uma página, roda sem internet), publicado em https://danimaciel.github.io/tecamazonia/. Dois modos: **produtor** (voz em destaque, só conteúdo revisado: painel de 2022 mais o que a curadoria aprovar) e **extensionista** (busca escrita ou falada no acervo todo da Amazônia, com filtros e envio pelo WhatsApp). `app/fonte/acervo.py` baixa o pacote mensal para `app/dados/acervo.json` |
| `pipeline/` | Recorte da Amazônia: Redape (exportação mensal) + marcação do Observatório (produtos, estados, biomas) |
| `config/tipos_publicacao.csv` | Qual tipo de publicação é material técnico e qual é científico |
| `curadoria/` | Decisões da equipe sobre o que entra no app |
| `.github/workflows/atualizar.yml` | Fluxo mensal que gera o pacote do app e a fila de curadoria |
| `android/`, `capacitor.config.json` | O mesmo app empacotado para Android com Capacitor; voz e leitura em voz alta pelo próprio celular |
| `.github/workflows/android.yml` | Gera o APK de teste e deixa na release `android-teste` |

## Como o conteúdo é escolhido

- **Amazônia:** entra o documento que o Observatório de Pesquisa da Embrapa marcou com o bioma Amazônia
  (declarado na solução tecnológica ou bioma predominante do município citado) ou que cita um estado da
  Amazônia Legal (AC, AM, AP, PA, RO, RR, TO, MT, MA). A opção `--so-bioma` deixa só o bioma.
- **Produtos:** taxonomia de 104 produtos do Observatório, com base no IBGE (PAM, PPM, PEVS).
- **Técnico e científico:** pelo campo "Tipo de publicação" do Redape, segundo `config/tipos_publicacao.csv`.
  Material técnico (séries editadas pela Embrapa: Documentos, Circular Técnica, Comunicado Técnico, folders,
  livros técnicos, cartilhas, coleções como Plantar e Agroindústria Familiar) vai para o produtor. Material
  científico (artigos, anais, resumos, livros científicos, teses) fica no "Para saber mais" do extensionista.
  Tipo novo que não está na tabela aparece no resumo do fluxo para alguém classificar. O relatório também conta
  quantos de cada tipo têm PDF na Infoteca-e (técnico) ou no Alice (científico), como checagem.
- **Material de apoio:** cada solução vai ao produtor junto com a publicação técnica que ensina a usá-la, como
  no painel de 2022. O recorte acha o apoio citado na ficha da solução ou sugere pelo produto e pelo título
  (`pipeline/apoio.py`); a curadoria confirma ou troca.
- **Curadoria:** o produtor só vê o que a equipe aprovou; a fila mensal vem ordenada do mais amazônico
  (bioma Amazônia) para o menos. Ver `curadoria/LEIAME.md`.

As mesmas fontes alimentam o [iAgro Embrapa](https://github.com/danimaciel/iagro-embrapa); `pipeline/redape.py`
foi copiado de lá.

## Rodar no próprio computador

```
pip install -r pipeline/requirements.txt
python pipeline/redape.py            # baixa a exportação mais recente do Redape para dados/AAAA-MM
python pipeline/observatorio.py      # baixa a marcação do Observatório para dados/enriquecimento
python pipeline/recorte.py 2026-10   # gera saida/pacote.json, pendentes.csv, tipos_publicacao.csv e resumo.md
python app/fonte/acervo.py           # baixa o pacote mensal mais recente para app/dados/acervo.json
python app/fonte/construir.py        # gera app/index.html a partir do modelo e do catálogo
npm ci && npm run android            # copia o app para o projeto Android (abrir android/ no Android Studio)
```

## Próximos passos

1. Rodar o fluxo uma vez e conferir em `tipos_publicacao.csv` a classificação dos tipos reais do Redape.
2. Busca por significado (multilingual-e5, como no iAgro) além das regras de produto, necessidade e palavras.
3. Testar o APK em celulares de campo e criar a conta na Google Play (pessoal ou da Embrapa) para publicar.
