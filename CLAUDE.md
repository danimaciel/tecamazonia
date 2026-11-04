# TecAmazônia: notas para quem trabalha no código

- Tudo em português: código, comentários, mensagens e documentação.
- O app tem de funcionar sem internet: nada de biblioteca carregada de CDN em `app/`; dados vão dentro da página
  ou no pacote baixado quando houver sinal.
- Recomendação só a partir do catálogo e das publicações; nada de texto técnico gerado por IA chegando ao
  produtor sem curadoria.
- Material técnico e científico ficam separados (`config/tipos_publicacao.csv`); o produtor vê só o técnico.
- Fontes de dados: Redape (exportação mensal) e releases `enriquecimento-AAAA-MM` de
  danimaciel/observatorio_embrapa, as mesmas dos iAgros.
- `dados/` e `saida/` não vão para o repositório; o fluxo publica as saídas na release `pacote-AAAA-MM`.
