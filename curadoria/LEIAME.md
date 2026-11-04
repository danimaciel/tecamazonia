# Curadoria

Nada chega ao produtor sem passar por alguém da equipe.

1. Todo mês o fluxo publica `pendentes.csv` na release `pacote-AAAA-MM`: soluções tecnológicas e publicações
   técnicas da Amazônia que ainda não têm decisão. A fila vem ordenada pela coluna `prioridade`, para revisar
   primeiro o que é mais da região:
   - 1: marcado com o bioma Amazônia;
   - 2: só cita estado do núcleo amazônico (AC, AM, AP, PA, RO, RR);
   - 3: só cita MT, MA ou TO, que também têm muito material de Cerrado.
2. Cada solução vem com o **material de apoio** (a publicação que ensina a usar a tecnologia), como no painel
   de 2022: produto -> tecnologia -> material de apoio. As colunas `apoio` (códigos) e `apoio_titulos` mostram
   o que foi achado e de onde veio: `declarado` (a ficha da solução no Redape cita o PDF) ou `sugerido` (mesmo
   produto e mesmas palavras no título, com confiança alta, média ou baixa). Aprovar a linha sem mexer em
   `apoio` aceita a sugestão; para trocar, escreva na coluna `apoio` os códigos (`PUB 123`) ou links certos,
   separados por `;`. **Solução sem material de apoio não chega ao produtor**, mesmo aprovada.
3. Quem revisa preenche `decisao` (`aprovado` ou `reprovado`), `revisor`, `data` e, se quiser, `observacao`,
   e copia as linhas revisadas para `revisados.csv` nesta pasta.
4. No mês seguinte:
   - **produtor** (`pacote-produtor.json`): recebe só o que foi aprovado;
   - **extensionista** (`pacote.json`): vê também o que ainda não tem decisão, marcado como "em revisão";
   - reprovados saem dos dois.

`revisados.csv` é a memória da curadoria: uma linha por documento, pelo código do Redape (`TEC 123`, `PUB 456`).
