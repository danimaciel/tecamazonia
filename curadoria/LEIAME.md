# Curadoria

Nada chega ao produtor sem passar por alguém da equipe.

1. Todo mês o fluxo publica `pendentes.csv` na release `pacote-AAAA-MM`: soluções tecnológicas e publicações
   técnicas da Amazônia que ainda não têm decisão. A fila vem ordenada pela coluna `prioridade`, para revisar
   primeiro o que é mais da região:
   - 1: marcado com o bioma Amazônia;
   - 2: só cita estado do núcleo amazônico (AC, AM, AP, PA, RO, RR);
   - 3: só cita MT, MA ou TO, que também têm muito material de Cerrado.
2. Quem revisa preenche `decisao` (`aprovado` ou `reprovado`), `revisor`, `data` e, se quiser, `observacao`,
   e copia as linhas revisadas para `revisados.csv` nesta pasta.
3. No mês seguinte:
   - **produtor** (`pacote-produtor.json`): recebe só o que foi aprovado;
   - **extensionista** (`pacote.json`): vê também o que ainda não tem decisão, marcado como "em revisão";
   - reprovados saem dos dois.

`revisados.csv` é a memória da curadoria: uma linha por documento, pelo código do Redape (`TEC 123`, `PUB 456`).
