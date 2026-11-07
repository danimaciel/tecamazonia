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

## Planos de adoção e parceiros

A jornada de adoção do app (necessidade → soluções no território → plano → acompanhamento) usa mais três listas,
com a mesma regra: **o produtor só vê o que foi aprovado**; o extensionista vê também o que está em revisão.

- `planos.csv`: um plano por linha (tecnologias ligadas, publicação de base, áudio, vídeo). A `necessidade` é
  uma de `aumentar`, `pragas`, `recuperar`, `diversificar`, `comercializar`. Plano sem etapas não aparece.
- `etapas.csv`: os passos de cada plano (`ordem`, `titulo`, `o_que_fazer`, `quando`, `fonte` com a página da
  publicação de onde saiu o passo). Os passos seguem a decisão do plano: aprovar o plano aprova as etapas dele.
- `parceiros.csv`: ATER, cooperativas, capacitações e unidades da Embrapa por estado e município.

As três listas ficam numa planilha Google própria, a da jornada (link em `config/jornada.txt`), gerada com
`python curadoria/montar_jornada.py jornada.xlsx`. O app lê as abas Planos, Etapas e Parceiros dela, que valem
mais que os arquivos daqui; sem `config/jornada.txt`, procura as abas na planilha de curadoria. O menu TecAmazônia → Aprovar linhas selecionadas
também funciona nelas.

Para testar as telas antes de ter plano aprovado, abra o app com `#teste` no fim do endereço, ou toque em
"Experimentar com o plano de teste" em Meu plano. O plano de teste (`app/fonte/plano-teste.json`) tem só texto de
exemplo e vem marcado como teste.
