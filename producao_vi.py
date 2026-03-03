<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vi Lingerie — Sistema de Produção</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #F7F5F2;
    --surface: #FFFFFF;
    --surface2: #F0EDE8;
    --border: #E8E3DC;
    --text: #1A1714;
    --text-muted: #8C8480;
    --accent: #C8566A;
    --accent-light: #F5E8EB;
    --accent2: #3D3530;
    --green: #4A7C59;
    --green-light: #E8F2EC;
    --amber: #C47B2A;
    --amber-light: #FBF2E6;
    --shadow: 0 2px 20px rgba(0,0,0,0.06);
    --shadow-lg: 0 8px 40px rgba(0,0,0,0.10);
    --radius: 16px;
    --radius-sm: 10px;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  /* ── SCREENS ── */
  .screen { display: none; width: 100%; max-width: 680px; padding: 24px 20px; }
  .screen.active { display: flex; flex-direction: column; align-items: center; }

  /* ── HEADER ── */
  .logo-wrap { margin-bottom: 36px; }
  .logo-wrap img { height: 60px; object-fit: contain; }

  /* ── OPERATOR GRID ── */
  .ops-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    width: 100%;
    margin-top: 8px;
  }
  .op-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 12px 16px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    transition: all .2s ease;
    box-shadow: var(--shadow);
  }
  .op-card:hover {
    border-color: var(--accent);
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(200,86,106,0.12);
  }
  .op-avatar {
    width: 52px; height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), #9E3F52);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 700; color: #fff;
    letter-spacing: -0.5px;
    flex-shrink: 0;
  }
  .op-name {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text);
    text-align: center;
    letter-spacing: 0.2px;
  }

  /* ── SECTION TITLE ── */
  .section-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 20px;
  }

  /* ── CARD ── */
  .card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    width: 100%;
    box-shadow: var(--shadow);
  }

  /* ── STEPPER ── */
  .stepper {
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 28px;
    width: 100%;
  }
  .step {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    position: relative;
  }
  .step-dot {
    width: 28px; height: 28px;
    border-radius: 50%;
    border: 2px solid var(--border);
    background: var(--surface2);
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
    color: var(--text-muted);
    z-index: 1;
    transition: all .3s;
  }
  .step.active .step-dot {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
    box-shadow: 0 0 0 4px rgba(200,86,106,0.15);
  }
  .step.done .step-dot {
    background: var(--green);
    border-color: var(--green);
    color: #fff;
  }
  .step-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--text-muted);
  }
  .step.active .step-label { color: var(--accent); }
  .step.done .step-label { color: var(--green); }
  .step-line {
    flex: 1;
    height: 2px;
    background: var(--border);
    margin-top: -17px;
    transition: background .3s;
  }
  .step-line.done { background: var(--green); }

  /* ── BADGE ── */
  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px;
    border-radius: 100px;
    font-size: 12px; font-weight: 600;
    margin-bottom: 20px;
  }
  .badge.info { background: var(--accent-light); color: var(--accent); }
  .badge.green { background: var(--green-light); color: var(--green); }

  /* ── INPUT ── */
  .input-label {
    font-size: 12px; font-weight: 600;
    color: var(--text-muted); letter-spacing: 0.5px;
    margin-bottom: 8px; display: block;
  }
  .input-field {
    width: 100%;
    padding: 14px 16px;
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px; font-weight: 500;
    color: var(--text);
    background: var(--bg);
    outline: none;
    transition: border-color .2s;
  }
  .input-field:focus { border-color: var(--accent); }

  /* ── BUTTONS ── */
  .btn {
    padding: 14px 28px;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-size: 14px; font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    border: none;
    transition: all .2s ease;
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  }
  .btn-primary {
    background: var(--accent);
    color: #fff;
    width: 100%;
    font-size: 15px;
    padding: 16px;
    box-shadow: 0 4px 16px rgba(200,86,106,0.25);
  }
  .btn-primary:hover { background: #b04560; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(200,86,106,0.30); }
  .btn-primary:disabled { background: #ccc; box-shadow: none; cursor: not-allowed; transform: none; }
  .btn-secondary {
    background: var(--surface2);
    color: var(--text);
    border: 1.5px solid var(--border);
  }
  .btn-secondary:hover { background: var(--border); }
  .btn-danger {
    background: var(--text);
    color: #fff;
    width: 100%;
    font-size: 15px;
    padding: 16px;
  }
  .btn-danger:hover { background: #333; }
  .btn-green {
    background: var(--green);
    color: #fff;
  }
  .btn-green:hover { background: #3a6347; }
  .btn-outline {
    background: transparent;
    border: 1.5px solid var(--border);
    color: var(--text);
  }
  .btn-outline:hover { border-color: var(--accent); color: var(--accent); }

  /* ── TIMER ── */
  .timer-display {
    font-family: 'DM Mono', monospace;
    font-size: 52px;
    font-weight: 500;
    color: var(--text);
    letter-spacing: -2px;
    text-align: center;
    padding: 20px 0;
    line-height: 1;
  }
  .timer-display.running { color: var(--accent); }
  .pedido-badge {
    font-size: 13px; font-weight: 600;
    color: var(--text-muted);
    text-align: center;
    margin-bottom: 4px;
  }
  .pedido-num {
    font-family: 'DM Mono', monospace;
    font-size: 22px; font-weight: 500;
    color: var(--text);
    text-align: center;
    margin-bottom: 20px;
  }

  /* ── MODAL ── */
  .modal-overlay {
    position: fixed; inset: 0;
    background: rgba(26,23,20,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
    padding: 20px;
    backdrop-filter: blur(4px);
  }
  .modal-overlay.hidden { display: none; }
  .modal {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 32px;
    max-width: 400px;
    width: 100%;
    box-shadow: var(--shadow-lg);
    text-align: center;
  }
  .modal-icon { font-size: 40px; margin-bottom: 16px; }
  .modal h3 { font-size: 18px; font-weight: 700; margin-bottom: 8px; }
  .modal p { font-size: 14px; color: var(--text-muted); margin-bottom: 24px; line-height: 1.6; }
  .modal-btns { display: flex; gap: 12px; flex-direction: column; }
  .modal-btns .btn { width: 100%; }

  /* ── ADMIN PANEL ── */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    width: 100%;
    margin-bottom: 20px;
  }
  .stat-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 16px;
    text-align: center;
  }
  .stat-num {
    font-family: 'DM Mono', monospace;
    font-size: 28px; font-weight: 500;
    color: var(--accent);
  }
  .stat-label { font-size: 11px; font-weight: 600; color: var(--text-muted); letter-spacing: 0.5px; margin-top: 4px; }

  .table-wrap { width: 100%; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    text-align: left; padding: 10px 12px;
    font-size: 10px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; color: var(--text-muted);
    border-bottom: 1.5px solid var(--border);
  }
  tbody td {
    padding: 12px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: middle;
  }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: var(--bg); }

  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 100px;
    font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
  }
  .tag-sep { background: #EBF0FB; color: #3B5EC6; }
  .tag-conf { background: var(--amber-light); color: var(--amber); }
  .tag-emb { background: var(--green-light); color: var(--green); }

  .op-row { display: flex; align-items: center; gap: 8px; }
  .op-mini {
    width: 26px; height: 26px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), #9E3F52);
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; color: #fff;
    flex-shrink: 0;
  }

  /* ── FOOTER ── */
  .footer-admin {
    position: fixed; bottom: 20px;
    font-size: 11px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    color: var(--text-muted);
    cursor: pointer;
    padding: 6px 14px;
    border-radius: 100px;
    border: 1px solid var(--border);
    background: var(--surface);
    transition: all .2s;
    opacity: 0.6;
  }
  .footer-admin:hover { opacity: 1; border-color: var(--accent); color: var(--accent); }

  /* ── DIVIDER ── */
  .divider { width: 100%; height: 1px; background: var(--border); margin: 20px 0; }

  .row { display: flex; gap: 12px; width: 100%; }
  .row .btn { flex: 1; }

  .empty-state {
    text-align: center; padding: 32px;
    color: var(--text-muted); font-size: 14px;
  }

  @media (max-width: 480px) {
    .ops-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .timer-display { font-size: 40px; }
    .stepper { display: none; }
  }
</style>
</head>
<body>

<!-- ═══════════════ SCREEN: HOME ═══════════════ -->
<div class="screen active" id="screen-home">
  <div class="logo-wrap">
    <img src="data:image/png;base64,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" alt="Vi Lingerie" onerror="this.style.display='none';document.getElementById('logo-fallback').style.display='block'">
    <div id="logo-fallback" style="display:none;font-size:24px;font-weight:700;color:var(--accent);letter-spacing:-1px;">Vi Lingerie</div>
  </div>
  <div class="section-label">Selecione o Operador</div>
  <div class="ops-grid" id="ops-grid"></div>
</div>

<!-- ═══════════════ SCREEN: PRODUCTION ═══════════════ -->
<div class="screen" id="screen-prod">
  <div class="logo-wrap">
    <img src="data:image/png;base64,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" alt="Vi Lingerie" style="height:44px" onerror="this.style.display='none'">
  </div>

  <!-- Stepper -->
  <div class="stepper" id="stepper">
    <div class="step" id="step-0">
      <div class="step-dot">1</div>
      <div class="step-label">Separação</div>
    </div>
    <div class="step-line" id="line-0"></div>
    <div class="step" id="step-1">
      <div class="step-dot">2</div>
      <div class="step-label">Conferência</div>
    </div>
    <div class="step-line" id="line-1"></div>
    <div class="step" id="step-2">
      <div class="step-dot">3</div>
      <div class="step-label">Embalagem</div>
    </div>
  </div>

  <!-- State: input -->
  <div class="card" id="state-input" style="display:block">
    <div class="badge info" id="op-badge">● Operador</div>
    <div style="margin-bottom:20px">
      <label class="input-label">NÚMERO DO PEDIDO</label>
      <input class="input-field" id="pedido-input" type="text" placeholder="Ex: #00123" autocomplete="off">
    </div>
    <button class="btn btn-primary" onclick="iniciar()">▶ INICIAR</button>
  </div>

  <!-- State: running -->
  <div class="card" id="state-running" style="display:none">
    <div class="badge info" id="op-badge2">● Operador</div>
    <div class="pedido-badge">PEDIDO</div>
    <div class="pedido-num" id="pedido-display">—</div>
    <div class="timer-display running" id="timer">00:00:00</div>
    <div style="font-size:12px;color:var(--text-muted);text-align:center;margin-bottom:24px;" id="etapa-label">Etapa: Separação</div>
    <button class="btn btn-danger" onclick="finalizar()">■ FINALIZAR</button>
  </div>
</div>

<!-- ═══════════════ SCREEN: ADMIN ═══════════════ -->
<div class="screen" id="screen-admin">
  <div style="display:flex;align-items:center;justify-content:space-between;width:100%;margin-bottom:24px;">
    <div>
      <div class="section-label" style="margin-bottom:2px">Painel Administrativo</div>
      <div style="font-size:20px;font-weight:700;">Visão Geral</div>
    </div>
    <button class="btn btn-outline" onclick="voltarHome()" style="padding:10px 18px;font-size:13px;">← Voltar</button>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-num" id="admin-total">0</div>
      <div class="stat-label">Pedidos Concluídos</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="admin-ops">0</div>
      <div class="stat-label">Operadores Ativos</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="admin-avg">0m</div>
      <div class="stat-label">Tempo Médio</div>
    </div>
  </div>

  <div class="card" style="margin-bottom:16px">
    <div style="font-size:13px;font-weight:700;margin-bottom:16px;letter-spacing:0.3px;">Desempenho por Operador</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Operador</th>
            <th>Pedidos</th>
            <th>Separação</th>
            <th>Conferência</th>
            <th>Embalagem</th>
          </tr>
        </thead>
        <tbody id="admin-ops-table"></tbody>
      </table>
    </div>
  </div>

  <div class="card" style="margin-bottom:80px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
      <div style="font-size:13px;font-weight:700;">Histórico de Pedidos</div>
      <button class="btn btn-outline" onclick="limparDados()" style="padding:7px 14px;font-size:11px;color:var(--accent);border-color:var(--accent)">Limpar</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Pedido</th>
            <th>Operador</th>
            <th>Etapa</th>
            <th>Tempo</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody id="admin-hist-table"></tbody>
      </table>
    </div>
    <div class="divider"></div>
    <button class="btn btn-primary" onclick="gerarPDF()" style="font-size:13px;padding:13px;">⬇ Gerar Relatório PDF</button>
  </div>
</div>

<!-- ═══════════════ MODALS ═══════════════ -->

<!-- Modal: Próxima etapa? -->
<div class="modal-overlay hidden" id="modal-next">
  <div class="modal">
    <div class="modal-icon">✅</div>
    <h3>Etapa Concluída!</h3>
    <p id="modal-next-msg">Deseja ir para a próxima etapa?</p>
    <div class="modal-btns">
      <button class="btn btn-primary" onclick="simProxima()">Sim, ir para a próxima →</button>
      <button class="btn btn-secondary" onclick="naoProxima()">Não, encerrar pedido</button>
    </div>
  </div>
</div>

<!-- Modal: Quem faz? -->
<div class="modal-overlay hidden" id="modal-quem">
  <div class="modal">
    <div class="modal-icon">👤</div>
    <h3>Quem faz a próxima etapa?</h3>
    <p id="modal-quem-label">Separação → <strong>Conferência</strong></p>
    <div class="modal-btns">
      <button class="btn btn-primary" onclick="euMesmo()">Eu mesmo</button>
      <button class="btn btn-secondary" onclick="outroOp()">Outro operador</button>
    </div>
  </div>
</div>

<!-- Admin password -->
<div class="modal-overlay hidden" id="modal-pwd">
  <div class="modal">
    <div class="modal-icon">🔐</div>
    <h3>Área Administrativa</h3>
    <p>Digite a senha para acessar</p>
    <input class="input-field" id="pwd-input" type="password" placeholder="Senha" style="margin-bottom:16px" onkeydown="if(event.key==='Enter')checkPwd()">
    <div class="row">
      <button class="btn btn-secondary" onclick="fecharModal('modal-pwd')">Cancelar</button>
      <button class="btn btn-primary" onclick="checkPwd()" style="width:auto">Entrar</button>
    </div>
  </div>
</div>

<!-- Footer -->
<button class="footer-admin" onclick="abrirAdmin()">⚙ Admin</button>

<script>
// ══════════════════════════════════════
//  DATA & STATE
// ══════════════════════════════════════
const OPERADORES = ["Lucivanio","Enagio","Daniel","Italo","Cildenir","Samya","Neide","Eduardo","Talyson"];
const ETAPAS = ["Separação","Conferência","Embalagem"];
const ADMIN_PWD = "vi2025";

let state = {
  operador: null,
  pedido: null,
  etapaIdx: 0,
  timerInterval: null,
  startTime: null,
  elapsed: 0,    // seconds this run
  registros: JSON.parse(localStorage.getItem('vi_registros') || '[]')
};

// ══════════════════════════════════════
//  INIT
// ══════════════════════════════════════
function init() {
  renderOps();
  showScreen('screen-home');
}

function renderOps() {
  const grid = document.getElementById('ops-grid');
  grid.innerHTML = OPERADORES.map(op => `
    <div class="op-card" onclick="selecionarOp('${op}')">
      <div class="op-avatar">${op[0]}</div>
      <div class="op-name">${op}</div>
    </div>
  `).join('');
}

// ══════════════════════════════════════
//  NAVIGATION
// ══════════════════════════════════════
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function voltarHome() {
  pararTimer();
  showScreen('screen-home');
}

// ══════════════════════════════════════
//  OPERATOR SELECTION
// ══════════════════════════════════════
function selecionarOp(op) {
  state.operador = op;
  state.etapaIdx = 0;
  mostrarInputEtapa();
  showScreen('screen-prod');
}

function mostrarInputEtapa() {
  pararTimer();
  state.elapsed = 0;
  atualizarTimer();

  document.getElementById('state-input').style.display = 'block';
  document.getElementById('state-running').style.display = 'none';

  document.getElementById('op-badge').innerHTML = `● ${state.operador}`;
  document.getElementById('op-badge2').innerHTML = `● ${state.operador}`;

  // Restore pedido if resuming
  if (state.pedido) {
    document.getElementById('pedido-input').value = state.pedido;
  } else {
    document.getElementById('pedido-input').value = '';
  }

  atualizarStepper();
}

// ══════════════════════════════════════
//  STEPPER
// ══════════════════════════════════════
function atualizarStepper() {
  ETAPAS.forEach((_, i) => {
    const step = document.getElementById(`step-${i}`);
    step.classList.remove('active','done');
    if (i < state.etapaIdx) step.classList.add('done');
    else if (i === state.etapaIdx) step.classList.add('active');

    if (i < 2) {
      const line = document.getElementById(`line-${i}`);
      line.classList.toggle('done', i < state.etapaIdx);
    }
  });
}

// ══════════════════════════════════════
//  TIMER
// ══════════════════════════════════════
function atualizarTimer() {
  const h = Math.floor(state.elapsed/3600);
  const m = Math.floor((state.elapsed%3600)/60);
  const s = state.elapsed%60;
  document.getElementById('timer').textContent =
    `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

function iniciarTimer() {
  state.startTime = Date.now();
  state.timerInterval = setInterval(() => {
    state.elapsed = Math.floor((Date.now() - state.startTime) / 1000);
    atualizarTimer();
  }, 1000);
}

function pararTimer() {
  clearInterval(state.timerInterval);
  state.timerInterval = null;
}

// ══════════════════════════════════════
//  PRODUCTION FLOW
// ══════════════════════════════════════
function iniciar() {
  const val = document.getElementById('pedido-input').value.trim();
  if (!val) { document.getElementById('pedido-input').focus(); return; }
  state.pedido = val;
  state.elapsed = 0;

  document.getElementById('state-input').style.display = 'none';
  document.getElementById('state-running').style.display = 'block';
  document.getElementById('pedido-display').textContent = state.pedido;
  document.getElementById('etapa-label').textContent = `Etapa: ${ETAPAS[state.etapaIdx]}`;

  iniciarTimer();
}

function finalizar() {
  pararTimer();
  const tempoGasto = state.elapsed;

  // Salvar registro
  const reg = {
    pedido: state.pedido,
    operador: state.operador,
    etapa: ETAPAS[state.etapaIdx],
    etapaIdx: state.etapaIdx,
    tempo: tempoGasto,
    data: new Date().toLocaleString('pt-BR')
  };
  state.registros.push(reg);
  salvarDados();

  // Próxima etapa?
  if (state.etapaIdx < 2) {
    const next = ETAPAS[state.etapaIdx + 1];
    document.getElementById('modal-next-msg').innerHTML =
      `<strong>${ETAPAS[state.etapaIdx]}</strong> concluída em <strong>${formatTempo(tempoGasto)}</strong>.<br>Deseja ir para a etapa <strong>${next}</strong>?`;
    abrirModal('modal-next');
  } else {
    // Pedido 100% concluído
    alert(`🎉 Pedido ${state.pedido} concluído com sucesso!\nEmbalagem finalizada em ${formatTempo(tempoGasto)}.`);
    state.pedido = null;
    state.etapaIdx = 0;
    voltarHome();
  }
}

// ── MODAL NEXT ──
function simProxima() {
  fecharModal('modal-next');
  const next = ETAPAS[state.etapaIdx + 1];
  document.getElementById('modal-quem-label').innerHTML =
    `${ETAPAS[state.etapaIdx]} → <strong>${next}</strong>`;
  abrirModal('modal-quem');
}

function naoProxima() {
  fecharModal('modal-next');
  state.pedido = null;
  state.etapaIdx = 0;
  voltarHome();
}

// ── MODAL QUEM ──
function euMesmo() {
  fecharModal('modal-quem');
  state.etapaIdx++;
  mostrarInputEtapa();
}

function outroOp() {
  fecharModal('modal-quem');
  const nextEtapaIdx = state.etapaIdx + 1;
  const pedidoAtual = state.pedido;
  // Voltar para home, mas ao selecionar op, já vai para a próxima etapa
  state.etapaIdx = nextEtapaIdx;
  // pedido mantido
  renderOps();
  // Override click para manter pedido
  const grid = document.getElementById('ops-grid');
  grid.querySelectorAll('.op-card').forEach((card, i) => {
    card.onclick = () => {
      state.operador = OPERADORES[i];
      state.pedido = pedidoAtual;
      mostrarInputEtapa();
      showScreen('screen-prod');
    };
  });
  showScreen('screen-home');
}

// ══════════════════════════════════════
//  ADMIN
// ══════════════════════════════════════
function abrirAdmin() {
  document.getElementById('pwd-input').value = '';
  abrirModal('modal-pwd');
  setTimeout(() => document.getElementById('pwd-input').focus(), 100);
}

function checkPwd() {
  const v = document.getElementById('pwd-input').value;
  if (v === ADMIN_PWD) {
    fecharModal('modal-pwd');
    renderAdmin();
    showScreen('screen-admin');
  } else {
    document.getElementById('pwd-input').style.borderColor = 'var(--accent)';
    document.getElementById('pwd-input').value = '';
    document.getElementById('pwd-input').placeholder = 'Senha incorreta';
    setTimeout(() => {
      document.getElementById('pwd-input').style.borderColor = '';
      document.getElementById('pwd-input').placeholder = 'Senha';
    }, 1500);
  }
}

function renderAdmin() {
  const regs = state.registros;

  // Stats
  const pedidosUniq = [...new Set(regs.filter(r => r.etapaIdx === 2).map(r => r.pedido))];
  const opsAtivos = [...new Set(regs.map(r => r.operador))];
  const totalTempo = regs.reduce((a, r) => a + r.tempo, 0);
  const avg = regs.length ? Math.floor(totalTempo / regs.length / 60) : 0;

  document.getElementById('admin-total').textContent = pedidosUniq.length;
  document.getElementById('admin-ops').textContent = opsAtivos.length;
  document.getElementById('admin-avg').textContent = avg + 'm';

  // Por operador
  const opMap = {};
  regs.forEach(r => {
    if (!opMap[r.operador]) opMap[r.operador] = { pedidos: new Set(), sep: [], conf: [], emb: [] };
    opMap[r.operador].pedidos.add(r.pedido);
    if (r.etapaIdx === 0) opMap[r.operador].sep.push(r.tempo);
    if (r.etapaIdx === 1) opMap[r.operador].conf.push(r.tempo);
    if (r.etapaIdx === 2) opMap[r.operador].emb.push(r.tempo);
  });

  const tbody = document.getElementById('admin-ops-table');
  if (!Object.keys(opMap).length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">Nenhum registro ainda</td></tr>`;
  } else {
    tbody.innerHTML = Object.entries(opMap).map(([op, d]) => `
      <tr>
        <td><div class="op-row"><div class="op-mini">${op[0]}</div>${op}</div></td>
        <td>${d.pedidos.size}</td>
        <td>${d.sep.length ? formatTempo(Math.floor(d.sep.reduce((a,b)=>a+b,0)/d.sep.length)) : '—'}</td>
        <td>${d.conf.length ? formatTempo(Math.floor(d.conf.reduce((a,b)=>a+b,0)/d.conf.length)) : '—'}</td>
        <td>${d.emb.length ? formatTempo(Math.floor(d.emb.reduce((a,b)=>a+b,0)/d.emb.length)) : '—'}</td>
      </tr>
    `).join('');
  }

  // Histórico
  const tagMap = ['tag-sep','tag-conf','tag-emb'];
  const hist = document.getElementById('admin-hist-table');
  if (!regs.length) {
    hist.innerHTML = `<tr><td colspan="5" class="empty-state">Nenhum registro ainda</td></tr>`;
  } else {
    hist.innerHTML = [...regs].reverse().slice(0,50).map(r => `
      <tr>
        <td><span style="font-family:'DM Mono',monospace;font-size:12px">${r.pedido}</span></td>
        <td><div class="op-row"><div class="op-mini">${r.operador[0]}</div>${r.operador}</div></td>
        <td><span class="tag ${tagMap[r.etapaIdx]}">${r.etapa}</span></td>
        <td style="font-family:'DM Mono',monospace;font-size:12px">${formatTempo(r.tempo)}</td>
        <td style="color:var(--text-muted);font-size:12px">${r.data}</td>
      </tr>
    `).join('');
  }
}

function limparDados() {
  if (confirm('Limpar todos os registros? Esta ação não pode ser desfeita.')) {
    state.registros = [];
    salvarDados();
    renderAdmin();
  }
}

// ══════════════════════════════════════
//  PDF REPORT
// ══════════════════════════════════════
function gerarPDF() {
  const regs = state.registros;
  const now = new Date().toLocaleString('pt-BR');

  // Estatísticas por operador
  const opMap = {};
  regs.forEach(r => {
    if (!opMap[r.operador]) opMap[r.operador] = { pedidos: new Set(), sep: [], conf: [], emb: [] };
    opMap[r.operador].pedidos.add(r.pedido);
    if (r.etapaIdx === 0) opMap[r.operador].sep.push(r.tempo);
    if (r.etapaIdx === 1) opMap[r.operador].conf.push(r.tempo);
    if (r.etapaIdx === 2) opMap[r.operador].emb.push(r.tempo);
  });

  const opsRows = Object.entries(opMap).map(([op, d]) => `
    <tr>
      <td>${op}</td>
      <td>${d.pedidos.size}</td>
      <td>${d.sep.length ? formatTempo(Math.floor(d.sep.reduce((a,b)=>a+b,0)/d.sep.length)) : '—'}</td>
      <td>${d.conf.length ? formatTempo(Math.floor(d.conf.reduce((a,b)=>a+b,0)/d.conf.length)) : '—'}</td>
      <td>${d.emb.length ? formatTempo(Math.floor(d.emb.reduce((a,b)=>a+b,0)/d.emb.length)) : '—'}</td>
    </tr>
  `).join('');

  const histRows = [...regs].reverse().map(r => `
    <tr>
      <td>${r.pedido}</td>
      <td>${r.operador}</td>
      <td>${r.etapa}</td>
      <td>${formatTempo(r.tempo)}</td>
      <td>${r.data}</td>
    </tr>
  `).join('');

  const html = `
  <!DOCTYPE html><html><head><meta charset="UTF-8">
  <style>
    body{font-family:sans-serif;padding:32px;color:#1A1714;font-size:13px;}
    h1{font-size:22px;color:#C8566A;margin-bottom:4px;}
    .sub{color:#8C8480;font-size:12px;margin-bottom:24px;}
    h2{font-size:14px;margin:24px 0 10px;color:#3D3530;}
    table{width:100%;border-collapse:collapse;margin-bottom:16px;}
    th{background:#F0EDE8;padding:8px 10px;text-align:left;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#8C8480;}
    td{padding:8px 10px;border-bottom:1px solid #E8E3DC;}
    .stats{display:flex;gap:24px;margin-bottom:24px;}
    .s{background:#F7F5F2;padding:16px;border-radius:8px;text-align:center;}
    .sn{font-size:28px;font-weight:700;color:#C8566A;}
    .sl{font-size:11px;color:#8C8480;margin-top:4px;}
  </style></head><body>
  <h1>Vi Lingerie — Relatório de Produção</h1>
  <div class="sub">Gerado em ${now}</div>
  <div class="stats">
    <div class="s"><div class="sn">${regs.length}</div><div class="sl">Registros</div></div>
    <div class="s"><div class="sn">${[...new Set(regs.map(r=>r.operador))].length}</div><div class="sl">Operadores</div></div>
    <div class="s"><div class="sn">${[...new Set(regs.filter(r=>r.etapaIdx===2).map(r=>r.pedido))].length}</div><div class="sl">Pedidos Completos</div></div>
  </div>
  <h2>Desempenho por Operador</h2>
  <table><thead><tr><th>Operador</th><th>Pedidos</th><th>Separação (med.)</th><th>Conferência (med.)</th><th>Embalagem (med.)</th></tr></thead>
  <tbody>${opsRows || '<tr><td colspan="5" style="text-align:center;color:#ccc">Sem dados</td></tr>'}</tbody></table>
  <h2>Histórico Completo</h2>
  <table><thead><tr><th>Pedido</th><th>Operador</th><th>Etapa</th><th>Tempo</th><th>Data</th></tr></thead>
  <tbody>${histRows || '<tr><td colspan="5" style="text-align:center;color:#ccc">Sem dados</td></tr>'}</tbody></table>
  </body></html>`;

  const w = window.open('', '_blank');
  w.document.write(html);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 600);
}

// ══════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════
function formatTempo(s) {
  if (s < 60) return `${s}s`;
  const m = Math.floor(s/60), sec = s%60;
  if (m < 60) return `${m}m ${String(sec).padStart(2,'0')}s`;
  const h = Math.floor(m/60), min = m%60;
  return `${h}h ${String(min).padStart(2,'0')}m`;
}

function salvarDados() {
  try { localStorage.setItem('vi_registros', JSON.stringify(state.registros)); } catch(e) {}
}

function abrirModal(id) { document.getElementById(id).classList.remove('hidden'); }
function fecharModal(id) { document.getElementById(id).classList.add('hidden'); }

// ══════════════════════════════════════
//  START
// ══════════════════════════════════════
init();
</script>
</body>
</html>
