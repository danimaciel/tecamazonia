# Curadoria

Nada chega ao produtor sem passar por alguém da equipe.

1. Todo mês o fluxo publica `pendentes.csv` na release `pacote-AAAA-MM`: soluções tecnológicas e publicações
   técnicas da Amazônia que ainda não têm decisão.
2. Quem revisa preenche `decisao` (`aprovado` ou `reprovado`), `revisor`, `data` e, se quiser, `observacao`,
   e copia as linhas revisadas para `revisados.csv` nesta pasta.
3. No mês seguinte, os aprovados vão para o app como revisados, os reprovados saem do app e os que
   continuam sem decisão aparecem com o aviso "ainda não revisado".

`revisados.csv` é a memória da curadoria: uma linha por documento, pelo código do Redape (`TEC 123`, `PUB 456`).
