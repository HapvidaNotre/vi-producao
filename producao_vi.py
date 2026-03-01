"""
Vi Lingerie — Apontamento de Produção
Solução definitiva:
- Grade de operadores: componente HTML puro (st.components.v1.html)
  que envia a seleção via window.parent.postMessage → capturado por
  st.query_params para comunicar ao Streamlit.
- Todas as outras telas: Streamlit nativo, sem hacks de CSS.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json, os, time, base64
from datetime import datetime
from io import BytesIO

st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="centered",
    page_icon="🏭",
    initial_sidebar_state="collapsed",
)

# ───────────────────────────────────────────────
# CONSTANTES
# ───────────────────────────────────────────────
ETAPAS       = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_LABELS = ["SEPARAÇÃO", "EMBALAGEM", "CONFERÊNCIA"]
ETAPA_ICONS  = ["📦", "📬", "✅"]
ETAPA_COLORS = ["#1D4ED8", "#7C3AED", "#16A34A"]

OPERADORES = [
    "Lucivanio", "Enágio",   "Daniel",
    "Ítalo",     "Cildenir", "Samya",
    "Neide",     "Eduardo",  "Talyson",
]

# Cor do avatar por operador (fixo, determinístico)
AV_CORES = [
    "#DC2626", "#059669", "#D97706",
    "#7C3AED", "#DB2777", "#0369A1",
    "#BE185D", "#2563EB", "#6D28D9",
]

SENHA_GERENCIA = "vi2026"

STATE_DIR       = "vi_state"
FILE_PEDIDOS    = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS = os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO  = os.path.join(STATE_DIR, "historico.json")
os.makedirs(STATE_DIR, exist_ok=True)

# ───────────────────────────────────────────────
# PERSISTÊNCIA
# ───────────────────────────────────────────────
def _ler(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _gravar(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def db_pedidos()    -> dict: return _ler(FILE_PEDIDOS, {})
def db_concluidos() -> list:
    d = _ler(FILE_CONCLUIDOS, [])
    return d if isinstance(d, list) else []
def db_historico()  -> list:
    d = _ler(FILE_HISTORICO, [])
    return d if isinstance(d, list) else []

def salvar_pedidos(d):    _gravar(FILE_PEDIDOS, d)
def salvar_concluidos(d): _gravar(FILE_CONCLUIDOS, d)

def log_evento(pedido, operador, etapa, status="em_andamento"):
    dh = agora()
    h  = db_historico()
    h.append({"data_hora": dh, "data": dh.split(" ")[0],
               "pedido": pedido, "operador": operador,
               "etapa": etapa, "status": status})
    _gravar(FILE_HISTORICO, h)

# ───────────────────────────────────────────────
# UTILITÁRIOS
# ───────────────────────────────────────────────
def agora() -> str:
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def fmt_hms(s: float) -> str:
    if not s or s < 0: return "00:00:00"
    s = int(s)
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

def av_cor(nome: str) -> str:
    return AV_CORES[OPERADORES.index(nome) if nome in OPERADORES
                    else sum(ord(c) for c in nome) % len(AV_CORES)]

def av_ini(nome: str) -> str:
    p = nome.strip().split()
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()

def _logo():
    for p in ["logo_vi.png", "../logo_vi.png"]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                b = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/png;base64,{b}" style="height:36px;" />'
    return ('<span style="font-family:Georgia,serif;font-size:1.7rem;'
            'font-weight:900;color:#8B0000;letter-spacing:.03em;">Vi LINGERIE</span>')

LOGO = _logo()

# ───────────────────────────────────────────────
# CSS GLOBAL
# ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stApp"] {
    font-family: 'DM Sans', sans-serif !important;
    background: #ECEAE6 !important;
    color: #111827 !important;
}
[data-testid="stSidebar"],
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

.block-container {
    max-width: 500px !important;
    padding: 1.8rem 1.2rem 4rem !important;
    margin: 0 auto !important;
}

/* WORDMARK */
.vi-wm { text-align:center; margin-bottom:16px; }

/* CARD */
.vi-card {
    background: #fff;
    border-radius: 20px;
    box-shadow: 0 2px 24px rgba(0,0,0,.08), 0 1px 4px rgba(0,0,0,.04);
    overflow: hidden;
    animation: fadeup .28s ease both;
}
@keyframes fadeup { from{opacity:0;transform:translateY(8px);} to{opacity:1;transform:translateY(0);} }

/* HEADER CARD */
.vi-hdr {
    display:flex; align-items:center; gap:12px;
    padding:16px 20px 14px;
    border-bottom: 3px solid var(--ec,#1D4ED8);
}
.vi-av {
    width:46px; height:46px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:16px; font-weight:700; color:#fff; flex-shrink:0;
}
.vi-hdr-sub  { font-size:.58rem; font-weight:700; color:#9ca3af;
               text-transform:uppercase; letter-spacing:.14em; }
.vi-hdr-nome { font-size:.94rem; font-weight:700; color:#111827; margin-top:1px; }
.vi-badge {
    margin-left:auto; padding:5px 13px; border-radius:999px;
    font-size:.6rem; font-weight:700; letter-spacing:.1em;
    border:1.5px solid currentColor; white-space:nowrap;
}

/* BODY */
.vi-body { padding:24px 20px 26px; }
.vi-hr   { height:1px; background:#F0EDE8; border:none; margin:14px 0; }
.vi-sec  { font-size:.6rem; font-weight:700; color:#9ca3af;
           text-transform:uppercase; letter-spacing:.14em; margin-bottom:12px; }

/* STEPPER */
.vi-step-wrap { display:flex; align-items:flex-start; margin-bottom:22px; }
.vi-step      { display:flex; flex-direction:column; align-items:center; gap:5px; flex:0 0 auto; }
.vi-dot       { width:42px; height:42px; border-radius:50%;
                display:flex; align-items:center; justify-content:center; font-size:.95rem; }
.vi-step-lbl  { font-size:.53rem; font-weight:700; letter-spacing:.08em;
                text-transform:uppercase; text-align:center; white-space:nowrap; }
.vi-line      { flex:1; height:1.5px; background:#E5E7EB; margin-top:20px; }
.vi-line-done { background:#1D4ED8 !important; }

/* PEDIDO */
.vi-num {
    font-family:'Playfair Display',serif;
    font-size:4rem; font-weight:900; color:#111827;
    line-height:1; text-align:center; margin:10px 0 4px;
}
.vi-num-hash { color:#9CA3AF; font-size:2.2rem; vertical-align:.22em; }

/* TIMER */
.vi-timer {
    text-align:center; font-family:'DM Mono',monospace;
    font-size:1.5rem; font-weight:500; color:#374151;
    letter-spacing:.08em; margin-bottom:18px;
}

/* SCAN */
.vi-scan { text-align:center; padding:10px 0 14px; }
.vi-scan-title { font-size:1rem; font-weight:700; color:#111827; margin:8px 0 3px; }
.vi-scan-sub   { font-size:.73rem; color:#9ca3af; }

/* INPUTS */
[data-testid="stTextInput"]     label,
[data-testid="stPasswordInput"] label,
[data-testid="stSelectbox"]     label { display:none !important; }

[data-testid="stTextInput"] input,
[data-testid="stPasswordInput"] input {
    background:#F5F4F2 !important; border:1.5px solid #E5E2DC !important;
    border-radius:12px !important; color:#111827 !important;
    font-family:'DM Mono',monospace !important; font-size:1rem !important;
    padding:14px 18px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stPasswordInput"] input:focus {
    border-color:#1D4ED8 !important;
    box-shadow:0 0 0 3px rgba(29,78,216,.1) !important;
    outline:none !important;
}
[data-testid="stTextInput"] input::placeholder { color:#B0A99F !important; }
[data-testid="stSelectbox"] > div > div {
    background:#F5F4F2 !important; border:1.5px solid #E5E2DC !important;
    border-radius:12px !important;
}

/* BOTÕES — sistema por classe wrapper */
[data-testid="stButton"] > button {
    font-family:'DM Sans',sans-serif !important;
    font-weight:700 !important; border-radius:14px !important;
    transition:all .18s ease !important; width:100% !important;
    border:none !important; outline:none !important; cursor:pointer !important;
}

/* Azul */
.btn-blue [data-testid="stButton"] > button {
    background:#1D4ED8 !important; color:#fff !important;
    font-size:.9rem !important; letter-spacing:.05em !important;
    padding:16px 20px !important;
    box-shadow:0 4px 14px rgba(29,78,216,.35) !important;
}
.btn-blue [data-testid="stButton"] > button:hover {
    background:#1e40af !important; transform:translateY(-1px) !important;
    box-shadow:0 6px 20px rgba(29,78,216,.45) !important;
}

/* Vermelho pulsante */
.btn-red [data-testid="stButton"] > button {
    background:#DC2626 !important; color:#fff !important;
    font-size:.9rem !important; letter-spacing:.05em !important;
    padding:16px 20px !important;
    animation:pulse-r 2s ease infinite !important;
}
@keyframes pulse-r {
    0%,100% { box-shadow:0 4px 14px rgba(220,38,38,.35); }
    50%      { box-shadow:0 4px 24px rgba(220,38,38,.62); }
}
.btn-red [data-testid="stButton"] > button:hover {
    background:#b91c1c !important; transform:translateY(-1px) !important;
}

/* Ghost */
.btn-ghost [data-testid="stButton"] > button {
    background:transparent !important; color:#6B7280 !important;
    border:1.5px solid #E5E7EB !important; font-size:.82rem !important;
    padding:12px 20px !important; box-shadow:none !important;
}
.btn-ghost [data-testid="stButton"] > button:hover {
    background:#F9FAFB !important; color:#374151 !important;
    border-color:#D1D5DB !important;
}

/* Link pequeno */
.btn-link [data-testid="stButton"] > button {
    background:transparent !important; color:#9CA3AF !important;
    border:none !important; font-size:.72rem !important;
    font-weight:500 !important; padding:8px !important; box-shadow:none !important;
}
.btn-link [data-testid="stButton"] > button:hover {
    color:#374151 !important; background:transparent !important;
}

/* ALERTS */
.vi-alert {
    display:flex; align-items:center; gap:8px;
    padding:11px 15px; border-radius:12px;
    font-size:.8rem; font-weight:500; margin:8px 0;
}
.vi-ok   { background:#F0FDF4; border:1.5px solid #BBF7D0; color:#16A34A; }
.vi-err  { background:#FEF2F2; border:1.5px solid #FECACA; color:#DC2626; }
.vi-inf  { background:#EFF6FF; border:1.5px solid #BFDBFE; color:#1D4ED8; }
.vi-warn { background:#FFFBEB; border:1.5px solid #FDE68A; color:#D97706; }

/* DONE */
.vi-done {
    background:linear-gradient(135deg,#F0FDF4,#DCFCE7);
    border:2px solid #BBF7D0; border-radius:18px;
    padding:32px 20px; text-align:center;
    animation:pop .4s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes pop { from{opacity:0;transform:scale(.88);} to{opacity:1;transform:scale(1);} }

/* ASK NEXT */
.vi-ask {
    background:#F9FAFB; border-radius:14px;
    padding:16px 16px 18px; margin-top:14px;
    border:1px solid #F0EDE8;
}
.vi-ask-title {
    font-size:.66rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.12em; margin-bottom:12px;
}

/* STATS */
.vi-stat {
    background:#F9FAFB; border:1px solid #F0EDE8;
    border-radius:12px; padding:10px 14px; text-align:center;
}
.vi-stat-lbl { font-size:.58rem; font-weight:700; color:#9CA3AF;
               text-transform:uppercase; letter-spacing:.1em; margin-bottom:2px; }
.vi-stat-val { font-family:'DM Mono',monospace; font-size:1.3rem;
               font-weight:600; color:#111827; }

/* iframe (componente HTML) sem borda */
iframe { border:none !important; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────
# COMPONENTE HTML DA GRADE DE OPERADORES
# Retorna o nome clicado via valor do componente
# ───────────────────────────────────────────────
def grade_operadores(operadores: list, height: int = 380) -> str | None:
    """
    Renderiza a grade de operadores como HTML puro dentro de um iframe.
    Retorna o nome do operador clicado, ou None.
    """
    cards = ""
    for nome in operadores:
        cor = av_cor(nome)
        ini = av_ini(nome)
        cards += f"""
        <button class="op-card" onclick="selecionar('{nome}')"
                style="--cor:{cor};">
            <div class="av-circle">{ini}</div>
            <span class="av-nome">{nome}</span>
        </button>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  body {{
    background: transparent;
    font-family: 'DM Sans', 'Helvetica Neue', sans-serif;
    padding: 4px 0 8px;
  }}
  .grade {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
  }}
  .op-card {{
    background: #F9FAFB;
    border: 2px solid #F0EDE8;
    border-radius: 16px;
    padding: 16px 8px 14px;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    transition: all .18s ease;
    outline: none;
    width: 100%;
  }}
  .op-card:hover {{
    background: #EFF6FF;
    border-color: #93C5FD;
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(29,78,216,.14);
  }}
  .op-card:active {{
    transform: translateY(0px);
    box-shadow: none;
  }}
  .av-circle {{
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background: var(--cor);
    color: #fff;
    font-size: 22px;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px color-mix(in srgb, var(--cor) 50%, transparent);
    flex-shrink: 0;
  }}
  .av-nome {{
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    text-align: center;
    line-height: 1.25;
    word-break: break-word;
  }}
  .op-card:hover .av-nome {{ color: #1D4ED8; }}
</style>
</head>
<body>
  <div class="grade">
    {cards}
  </div>
  <script>
    function selecionar(nome) {{
      // Envia o valor via Streamlit component value
      window.parent.postMessage({{
        type: "streamlit:setComponentValue",
        value: nome
      }}, "*");
    }}
  </script>
</body>
</html>"""

    resultado = components.html(html, height=height, scrolling=False)
    return resultado


# ───────────────────────────────────────────────
# HELPERS DE RENDERIZAÇÃO
# ───────────────────────────────────────────────
def wm():
    st.markdown(f'<div class="vi-wm">{LOGO}</div>', unsafe_allow_html=True)

def alerta(msg: str, kind: str = "inf"):
    st.markdown(f'<div class="vi-alert vi-{kind}">{msg}</div>', unsafe_allow_html=True)

def card_header(operador: str, etapa_idx: int):
    cor = ETAPA_COLORS[etapa_idx]
    ini = av_ini(operador); c = av_cor(operador)
    st.markdown(f"""
    <div class="vi-hdr" style="--ec:{cor};">
        <div class="vi-av" style="background:{c};">{ini}</div>
        <div>
            <div class="vi-hdr-sub">ESTAÇÃO CENTRAL</div>
            <div class="vi-hdr-nome">{operador}</div>
        </div>
        <div class="vi-badge" style="color:{cor};">{ETAPA_LABELS[etapa_idx]}</div>
    </div>
    """, unsafe_allow_html=True)

def stepper(etapa_idx: int):
    html = '<div class="vi-step-wrap">'
    for i, (lbl, ico) in enumerate(zip(ETAPA_LABELS, ETAPA_ICONS)):
        cor = ETAPA_COLORS[i]
        done = i < etapa_idx; active = i == etapa_idx
        if done:
            ds = f"background:{cor};color:#fff;"
            ls = f"color:{cor};"
            dc = "✓"
        elif active:
            ds = f"background:{cor};color:#fff;box-shadow:0 0 0 5px {cor}22;"
            ls = f"color:{cor};font-weight:800;"
            dc = ico
        else:
            ds = "background:#F0EDE8;color:#C4BAB0;"
            ls = "color:#C4BAB0;"
            dc = ico
        html += (f'<div class="vi-step">'
                 f'<div class="vi-dot" style="{ds}">{dc}</div>'
                 f'<div class="vi-step-lbl" style="{ls}">{lbl}</div>'
                 f'</div>')
        if i < 2:
            html += f'<div class="vi-line {"vi-line-done" if done else ""}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def pedido_num(num: str):
    st.markdown(
        f'<div class="vi-num"><span class="vi-num-hash">#</span>{num}</div>',
        unsafe_allow_html=True)

def timer_display(ts: float):
    e = fmt_hms(time.time() - ts) if ts else "00:00:00"
    st.markdown(f'<div class="vi-timer">⏱ {e}</div>', unsafe_allow_html=True)


# ───────────────────────────────────────────────
# TELA 1 — SELEÇÃO DE OPERADOR
# ───────────────────────────────────────────────
def tela_selecao():
    wm()

    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:1.05rem;font-weight:700;color:#111827;">
            Apontamento de Produção</div>
        <div style="font-size:.75rem;color:#9ca3af;margin-top:4px;">
            Toque no seu nome para começar</div>
    </div>
    """, unsafe_allow_html=True)

    # Card com a grade
    st.markdown('<div class="vi-card"><div class="vi-body">', unsafe_allow_html=True)
    st.markdown('<div class="vi-sec">QUEM É VOCÊ?</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Grade HTML — retorna o operador clicado
    escolha = grade_operadores(OPERADORES, height=390)

    if escolha and isinstance(escolha, str) and escolha in OPERADORES:
        st.session_state.update({
            "_operador":  escolha,
            "_turno_ts":  time.time(),
            "_etapa_idx": 0,
            "_flow":      "input",
            "_pedido":    None,
            "_ts_inicio": None,
            "_ts_fim":    None,
            "_ask_mode":  None,
        })
        st.rerun()

    # Link gerência
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    _, cm, _ = st.columns([1, 2, 1])
    with cm:
        st.markdown('<div class="btn-link">', unsafe_allow_html=True)
        if st.button("🔒  Acesso Gerência", key="btn_ger_link", use_container_width=True):
            st.session_state["_modo"] = "gerencia"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ───────────────────────────────────────────────
# TELA 2 — FLUXO DO OPERADOR
# ───────────────────────────────────────────────
def tela_operador():
    operador  = st.session_state["_operador"]
    etapa_idx = st.session_state.get("_etapa_idx", 0)
    flow      = st.session_state.get("_flow", "input")
    pedido    = st.session_state.get("_pedido")
    ts_inicio = st.session_state.get("_ts_inicio")
    ts_turno  = st.session_state.get("_turno_ts", time.time())

    wm()
    st.markdown('<div class="vi-card">', unsafe_allow_html=True)
    card_header(operador, etapa_idx)
    st.markdown('<div class="vi-body">', unsafe_allow_html=True)

    # ════ INPUT ════════════════════════════════
    if flow == "input":

        if etapa_idx == 0:
            st.markdown("""
            <div class="vi-scan">
                <svg width="52" height="52" viewBox="0 0 24 24" fill="none"
                     stroke="#C4BAB0" stroke-width="1.4" stroke-linecap="round">
                  <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                  <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                  <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                  <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                  <line x1="8" y1="12" x2="16" y2="12"/>
                  <line x1="12" y1="8"  x2="12" y2="16"/>
                </svg>
                <div class="vi-scan-title">Bipar ou digitar pedido</div>
                <div class="vi-scan-sub">Insira o número do pedido para iniciar</div>
            </div>
            """, unsafe_allow_html=True)

            ci, cb = st.columns([5, 1], gap="small")
            with ci:
                st.text_input("_", placeholder="Ex: 12345",
                              key="inp_num", label_visibility="collapsed")
            with cb:
                st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
                ir = st.button("→", key="btn_ir", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if ir:
                num = st.session_state.get("inp_num", "").strip()
                if not num:
                    alerta("⚠️ Informe o número do pedido.", "err")
                elif num in db_pedidos():
                    alerta(f"⚠️ Pedido #{num} já em andamento.", "err")
                else:
                    st.session_state.update({"_pedido": num, "_flow": "confirm"})
                    st.rerun()
        else:
            stepper(etapa_idx)
            db = db_pedidos()
            chave_op   = "op_emb" if etapa_idx == 1 else "op_conf"
            disponiveis = sorted([
                p for p, d in db.items()
                if d.get("etapa") == etapa_idx and chave_op not in d
            ])
            if not disponiveis:
                alerta(f"⏳ Nenhum pedido aguardando {ETAPA_LABELS[etapa_idx]}. "
                       "Aguarde a etapa anterior.", "warn")
                st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                if st.button("🔄 Atualizar", key="btn_att", use_container_width=True):
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                sp = st.selectbox("_p",
                    ["— Selecione o pedido —"] + disponiveis,
                    key=f"sel_ped_{etapa_idx}",
                    label_visibility="collapsed")
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
                if st.button(f"▶  INICIAR {ETAPA_LABELS[etapa_idx]}",
                             key=f"btn_ini_{etapa_idx}", use_container_width=True):
                    if sp == "— Selecione o pedido —":
                        alerta("⚠️ Selecione um pedido.", "err")
                    else:
                        st.session_state.update({"_pedido": sp, "_flow": "confirm"})
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ════ CONFIRM ══════════════════════════════
    elif flow == "confirm":
        stepper(etapa_idx)
        pedido_num(pedido)
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button(f"▶  INICIAR {ETAPA_LABELS[etapa_idx]}",
                     key="btn_confirmar", use_container_width=True):
            st.session_state.update({"_flow": "running", "_ts_inicio": time.time()})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("← Alterar pedido", key="btn_alt", use_container_width=True):
            st.session_state.update({"_flow": "input", "_pedido": None})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ RUNNING ══════════════════════════════
    elif flow == "running":
        stepper(etapa_idx)
        pedido_num(pedido)
        timer_display(ts_inicio)

        st.markdown('<div class="btn-red">', unsafe_allow_html=True)
        if st.button(f"■  CONCLUIR {ETAPA_LABELS[etapa_idx]}",
                     key="btn_concluir", use_container_width=True):
            _finalizar(operador, etapa_idx, pedido)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("✕ Cancelar", key="btn_cancel", use_container_width=True):
            st.session_state.update(
                {"_flow": "input", "_pedido": None, "_ts_inicio": None})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ ASK_NEXT ═════════════════════════════
    elif flow == "ask_next":
        prox     = etapa_idx + 1
        prox_cor = ETAPA_COLORS[prox]
        ts_fim   = st.session_state.get("_ts_fim", time.time())
        dur      = fmt_hms(ts_fim - ts_inicio) if ts_inicio else "--"

        stepper(etapa_idx)
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:8px;">
            <div style="display:inline-block;background:#F0FDF4;
                border:1.5px solid #BBF7D0;border-radius:10px;padding:8px 18px;">
                <span style="font-size:.62rem;font-weight:700;color:#16A34A;
                    text-transform:uppercase;letter-spacing:.1em;">
                    ✓ {ETAPA_LABELS[etapa_idx]} CONCLUÍDA · {dur}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        pedido_num(pedido)

        st.markdown(f"""
        <div class="vi-ask">
            <div class="vi-ask-title" style="color:{prox_cor};">
                {ETAPA_ICONS[prox]}&nbsp; Próxima: {ETAPA_LABELS[prox]}<br>
                <span style="color:#9CA3AF;font-weight:500;font-size:.62rem;
                    text-transform:none;letter-spacing:.02em;">
                    Quem vai realizar esta etapa?
                </span>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button(f"✓  Sou eu  ({operador.split()[0]})",
                         key="btn_mesmo", use_container_width=True):
                _avancar(etapa_idx, pedido, operador)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("👤  Outro operador", key="btn_outro", use_container_width=True):
                st.session_state["_ask_mode"] = "select"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get("_ask_mode") == "select":
            st.markdown("<div class='vi-hr'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:.62rem;font-weight:700;color:#9ca3af;"
                "text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;'>"
                "Selecione o próximo operador:</div>",
                unsafe_allow_html=True)
            outros = [op for op in OPERADORES if op != operador]
            st.markdown('</div>', unsafe_allow_html=True)  # fecha vi-ask antes da grade
            escolha2 = grade_operadores(outros, height=270)
            if escolha2 and isinstance(escolha2, str) and escolha2 in outros:
                _avancar(etapa_idx, pedido, escolha2)
        else:
            st.markdown('</div>', unsafe_allow_html=True)  # fecha vi-ask

    # ════ DONE ═════════════════════════════════
    elif flow == "done":
        ts_fim = st.session_state.get("_ts_fim", time.time())
        dur    = fmt_hms(ts_fim - ts_inicio) if ts_inicio else "--"
        st.markdown(f"""
        <div class="vi-done">
            <div style="font-size:3rem;margin-bottom:8px;">🎉</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.5rem;
                font-weight:900;color:#16A34A;margin-bottom:4px;">Pedido Concluído!</div>
            <div style="font-family:'DM Mono',monospace;font-size:2.4rem;
                font-weight:700;color:#111827;margin:8px 0;">#{pedido}</div>
            <div style="font-size:.72rem;color:#6B7280;">
                Todas as 3 etapas · {dur}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("▶  Iniciar Novo Pedido", key="btn_novo", use_container_width=True):
            st.session_state.update({
                "_flow": "input", "_etapa_idx": 0,
                "_pedido": None, "_ts_inicio": None,
                "_ts_fim": None, "_ask_mode": None,
            })
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Rodapé
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    hoje = agora().split(" ")[0]
    ops_hoje = len([h for h in db_historico()
                    if h.get("operador") == operador and h.get("data") == hoje])
    turno_dur = fmt_hms(time.time() - ts_turno)

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown(
            f'<div class="vi-stat"><div class="vi-stat-lbl">Operações hoje</div>'
            f'<div class="vi-stat-val" style="color:#16A34A;">{ops_hoje}</div></div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="vi-stat"><div class="vi-stat-lbl">Tempo de turno</div>'
            f'<div class="vi-stat-val">{turno_dur}</div></div>',
            unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("⏏  Trocar Operador / Sair", key="btn_sair", use_container_width=True):
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ───────────────────────────────────────────────
# AÇÕES DE NEGÓCIO
# ───────────────────────────────────────────────
def _finalizar(operador: str, etapa_idx: int, pedido: str):
    now = agora(); ts_fim = time.time()
    db  = db_pedidos()

    if etapa_idx == 0:
        db[pedido] = {"pedido": pedido, "etapa": 1,
                      "op_sep": operador, "dt_sep": now}
        log_evento(pedido, operador, ETAPAS[0])

    elif etapa_idx == 1:
        if pedido in db:
            db[pedido].update({"etapa": 2, "op_emb": operador, "dt_emb": now})
            log_evento(pedido, operador, ETAPAS[1])

    elif etapa_idx == 2:
        if pedido in db:
            db[pedido].update({"etapa": 3, "op_conf": operador, "dt_conf": now})
            c = db_concluidos(); c.append(db[pedido])
            salvar_concluidos(c); del db[pedido]
            log_evento(pedido, operador, ETAPAS[2], "concluido")

    salvar_pedidos(db)
    st.session_state.update({
        "_ts_fim": ts_fim,
        "_flow":   "ask_next" if etapa_idx < 2 else "done",
    })
    st.rerun()


def _avancar(etapa_atual: int, pedido: str, proximo: str):
    st.session_state.update({
        "_operador":  proximo,
        "_etapa_idx": etapa_atual + 1,
        "_flow":      "confirm",
        "_pedido":    pedido,
        "_ts_inicio": None,
        "_ts_fim":    None,
        "_ask_mode":  None,
    })
    st.rerun()


# ───────────────────────────────────────────────
# TELA 3 — LOGIN GERÊNCIA
# ───────────────────────────────────────────────
def tela_login_gerencia():
    wm()
    st.markdown('<div class="vi-card"><div class="vi-body">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:1.05rem;font-weight:700;color:#111827;">Área da Gerência</div>
        <div style="font-size:.73rem;color:#9ca3af;margin-top:4px;">
            Informe a senha de acesso</div>
    </div>
    """, unsafe_allow_html=True)

    senha = st.text_input("_s", type="password", placeholder="••••••••",
                          key="inp_senha", label_visibility="collapsed")
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
    if st.button("🔓  Acessar", key="btn_ger_acesso", use_container_width=True):
        if senha == SENHA_GERENCIA:
            st.session_state["_ger_ok"] = True; st.rerun()
        else:
            alerta("❌ Senha incorreta.", "err")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("← Voltar", key="btn_ger_volta", use_container_width=True):
        st.session_state.pop("_modo", None); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)


# ───────────────────────────────────────────────
# TELA 4 — EXTRATO GERÊNCIA
# ───────────────────────────────────────────────
def tela_extrato():
    conc = db_concluidos(); pend = db_pedidos(); hist = db_historico()
    wm()
    st.markdown("""
    <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:1.05rem;font-weight:700;color:#111827;">
            Extrato de Produção</div>
        <div style="font-size:.72rem;color:#9ca3af;margin-top:3px;">
            Consulta, filtros e relatórios</div>
    </div>
    """, unsafe_allow_html=True)

    ts=len([h for h in hist if h.get("etapa")==ETAPAS[0]])
    te=len([h for h in hist if h.get("etapa")==ETAPAS[1]])
    tc=len([h for h in hist if h.get("etapa")==ETAPAS[2]])
    tk=len(conc)
    for col,lab,val,cor in zip(
        st.columns(4, gap="small"),
        ["📦 Sep.","📬 Emb.","✅ Conf.","🎯 Conc."],
        [ts,te,tc,tk],
        ["#1D4ED8","#7C3AED","#16A34A","#DC2626"],
    ):
        with col:
            st.markdown(
                f'<div class="vi-stat"><div class="vi-stat-lbl">{lab}</div>'
                f'<div class="vi-stat-val" style="color:{cor};font-size:1.6rem;">{val}</div></div>',
                unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    a1, a2, a3 = st.tabs(["📅 Histórico","📋 Concluídos","⏳ Em Andamento"])

    with a1:
        if not hist:
            alerta("ℹ️ Nenhuma operação registrada.", "inf")
        else:
            df = pd.DataFrame(hist)
            df["_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
            from datetime import date, timedelta as td
            hoje = date.today()
            c1,c2,c3,c4 = st.columns(4, gap="small")
            with c1: di  = st.date_input("Início", hoje-td(days=7), key="g_di",  format="DD/MM/YYYY")
            with c2: dfv = st.date_input("Fim",    hoje,            key="g_df",  format="DD/MM/YYYY")
            with c3:
                ops=["Todos"]+sorted(df["operador"].dropna().unique().tolist())
                opf=st.selectbox("Func.", ops, key="g_op", label_visibility="visible")
            with c4:
                ets=["Todas"]+ETAPAS
                etf=st.selectbox("Etapa", ets, key="g_et", label_visibility="visible")

            mask=(df["_dt"]>=pd.Timestamp(di))&(df["_dt"]<=pd.Timestamp(dfv))
            dff=df[mask].copy()
            if opf!="Todos": dff=dff[dff["operador"]==opf]
            if etf!="Todas": dff=dff[dff["etapa"]==etf]
            dff=dff.sort_values("data_hora",ascending=False)
            alerta(f"🔍 <b>{len(dff)}</b> operação(ões)","inf")

            if len(dff):
                if opf=="Todos":
                    r=dff.groupby(["operador","etapa"]).size().reset_index(name="Qtd.")
                    r.columns=["Funcionário","Etapa","Qtd."]
                    st.dataframe(r,use_container_width=True,hide_index=True)
                    st.markdown("<div class='vi-hr'></div>",unsafe_allow_html=True)
                de=dff[["data_hora","pedido","operador","etapa","status"]].rename(columns={
                    "data_hora":"Data/Hora","pedido":"Pedido",
                    "operador":"Funcionário","etapa":"Etapa","status":"Status"})
                de["Status"]=de["Status"].map({"em_andamento":"⏳","concluido":"✅"}).fillna(de["Status"])
                st.dataframe(de,use_container_width=True,hide_index=True)
                arq=f"extrato_{opf.replace(' ','_')}_{di.strftime('%d%m%Y')}"
                d1,d2=st.columns(2,gap="small")
                with d1:
                    st.download_button("⬇️ CSV",
                        data=de.to_csv(index=False).encode("utf-8"),
                        file_name=f"{arq}.csv",mime="text/csv",
                        use_container_width=True,key="dl_csv")
                with d2:
                    xb=BytesIO()
                    with pd.ExcelWriter(xb,engine="openpyxl") as w:
                        de.to_excel(w,index=False,sheet_name="Histórico")
                    xb.seek(0)
                    st.download_button("⬇️ Excel",data=xb.getvalue(),
                        file_name=f"{arq}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,key="dl_xlsx")

    with a2:
        if not conc:
            alerta("ℹ️ Nenhum pedido finalizado.", "inf")
        else:
            dc=pd.DataFrame(conc).rename(columns={
                "pedido":"Pedido","op_sep":"Op. Sep.","dt_sep":"Data Sep.",
                "op_emb":"Op. Emb.","dt_emb":"Data Emb.",
                "op_conf":"Op. Conf.","dt_conf":"Data Conf.",
            }).drop(columns=["etapa"],errors="ignore")
            st.dataframe(dc,use_container_width=True,hide_index=True)
            xb2=BytesIO()
            with pd.ExcelWriter(xb2,engine="openpyxl") as w:
                dc.to_excel(w,index=False,sheet_name="Concluídos")
            xb2.seek(0)
            e1,e2=st.columns(2,gap="small")
            with e1:
                st.download_button("⬇️ CSV",
                    data=dc.to_csv(index=False).encode("utf-8"),
                    file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv",
                    mime="text/csv",use_container_width=True,key="dl_cc")
            with e2:
                st.download_button("⬇️ Excel",data=xb2.getvalue(),
                    file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,key="dl_cx")

    with a3:
        if not pend:
            alerta("✅ Nenhum pedido em andamento.","ok")
        else:
            el={1:"📬 Aguard. Embalagem",2:"✅ Aguard. Conferência"}
            rows=[{"Pedido":f"#{d['pedido']}",
                   "Etapa":el.get(d.get("etapa",0),"—"),
                   "Op. Sep.":d.get("op_sep","—"),
                   "Op. Emb.":d.get("op_emb","—")}
                  for d in pend.values()]
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    st.markdown("<div style='height:14px;'></div>",unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">',unsafe_allow_html=True)
    if st.button("← Sair da Gerência",key="btn_ger_sair",use_container_width=True):
        st.session_state.pop("_modo",None)
        st.session_state.pop("_ger_ok",None)
        st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)


# ───────────────────────────────────────────────
# ROTEADOR
# ───────────────────────────────────────────────
def main():
    modo = st.session_state.get("_modo")
    if modo == "gerencia":
        if st.session_state.get("_ger_ok"):
            tela_extrato()
        else:
            tela_login_gerencia()
        return
    if "_operador" in st.session_state:
        tela_operador()
    else:
        tela_selecao()

main()
