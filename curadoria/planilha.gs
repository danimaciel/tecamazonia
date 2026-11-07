/**
 * TecAmazônia: script da planilha de curadoria (Google Sheets → Extensões → Apps Script).
 *
 * Cole este arquivo no editor de Apps Script da planilha e salve. Aparece o menu "TecAmazônia" com:
 *   - Trazer novos pendentes: busca a fila do último recorte (pendentes.csv da release mais recente do
 *     repositório) e acrescenta só o que ainda não está na planilha. As decisões já feitas não mudam.
 *   - Aprovar / Reprovar linhas selecionadas: marca a decisão, quem revisou e a data nas linhas
 *     selecionadas. Use com um filtro (por unidade, produto, estado, prioridade) para decidir em lote.
 *     Funciona também nas abas Planos e Parceiros (a aba Etapas segue a decisão do plano).
 * Para trazer a fila sozinho todo mês: Apps Script → Acionadores → importarPendentes, mensal, dia 17.
 */
const REPO = 'danimaciel/tecamazonia';
const ABAS = {
  'Soluções': ['decisao', 'apoio_confirmado', 'observacao', 'revisor', 'data', 'prioridade', 'motivo', 'codigo',
               'titulo', 'unidade', 'ano', 'tipo', 'produtos', 'ufs', 'apoio_sugerido', 'apoio_titulos', 'link'],
  'Publicações técnicas': ['decisao', 'observacao', 'revisor', 'data', 'prioridade', 'motivo', 'codigo',
                           'titulo', 'unidade', 'ano', 'tipo', 'produtos', 'ufs', 'link'],
};

function onOpen() {
  SpreadsheetApp.getUi().createMenu('TecAmazônia')
    .addItem('Trazer novos pendentes', 'importarPendentes')
    .addSeparator()
    .addItem('Aprovar linhas selecionadas', 'aprovarSelecionadas')
    .addItem('Reprovar linhas selecionadas', 'reprovarSelecionadas')
    .addToUi();
}

function importarPendentes() {
  const url = `https://github.com/${REPO}/releases/latest/download/pendentes.csv`;
  const linhas = Utilities.parseCsv(UrlFetchApp.fetch(url, { followRedirects: true }).getContentText('UTF-8'));
  const cab = linhas.shift();
  const col = Object.fromEntries(cab.map((c, i) => [c, i]));
  const planilha = SpreadsheetApp.getActive();
  const novos = { 'Soluções': [], 'Publicações técnicas': [] };
  for (const l of linhas) {
    const aba = l[col.codigo].startsWith('TEC') ? 'Soluções' : 'Publicações técnicas';
    novos[aba].push(ABAS[aba].map(c => c === 'apoio_sugerido' ? l[col.apoio] : (c in col && !['decisao', 'revisor', 'data', 'observacao'].includes(c) ? l[col[c]] : '')));
  }
  let total = 0;
  for (const [nome, cols] of Object.entries(ABAS)) {
    const aba = planilha.getSheetByName(nome);
    const ic = cols.indexOf('codigo');
    const n = aba.getLastRow();
    const ja = new Set(n > 1 ? aba.getRange(2, ic + 1, n - 1, 1).getValues().map(r => r[0]) : []);
    const add = novos[nome].filter(r => !ja.has(r[ic]));
    if (add.length) aba.getRange(n + 1, 1, add.length, cols.length).setValues(add);
    total += add.length;
  }
  SpreadsheetApp.getActive().toast(`${total} itens novos na fila.`, 'TecAmazônia');
}

function marcar(decisao) {
  const aba = SpreadsheetApp.getActiveSheet();
  // Vale para qualquer aba com as colunas decisao, revisor e data (Soluções, Publicações técnicas, Planos, Parceiros)
  const cols = aba.getRange(1, 1, 1, aba.getLastColumn()).getValues()[0].map(String);
  if (!['decisao', 'revisor', 'data'].every(c => cols.includes(c))) {
    return SpreadsheetApp.getUi().alert('Use numa aba com as colunas decisao, revisor e data (Soluções, Publicações técnicas, Planos ou Parceiros).');
  }
  const quem = Session.getActiveUser().getEmail() || 'curadoria';
  const hoje = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyy-MM-dd');
  let n = 0;
  for (const faixa of aba.getActiveRangeList().getRanges()) {
    for (let r = faixa.getRow(); r < faixa.getRow() + faixa.getNumRows(); r++) {
      if (r === 1 || aba.isRowHiddenByFilter(r)) continue;   // pula o cabeçalho e o que o filtro escondeu
      aba.getRange(r, cols.indexOf('decisao') + 1).setValue(decisao);
      aba.getRange(r, cols.indexOf('revisor') + 1).setValue(quem);
      aba.getRange(r, cols.indexOf('data') + 1).setValue(hoje);
      n++;
    }
  }
  SpreadsheetApp.getActive().toast(`${n} linhas marcadas como ${decisao}.`, 'TecAmazônia');
}
function aprovarSelecionadas() { marcar('aprovado'); }
function reprovarSelecionadas() { marcar('reprovado'); }
