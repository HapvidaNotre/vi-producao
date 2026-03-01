"""
Vi Lingerie — Sistema de Apontamento de Produção
Reconstruído do zero. Sem hacks de CSS. Botões 100% nativos.
"""

import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import BytesIO

# ─────────────────────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="centered",
    page_icon="🏭",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────
ETAPAS = [
    "Separação do Pedido",
    "Mesa de Embalagem",
    "Conferência do Pedido",
]
ETAPA_LABELS  = ["SEPARAÇÃO", "EMBALAGEM", "CONFERÊNCIA"]
ETAPA_ICONS   = ["📦", "📬", "✅"]
ETAPA_COLORS  = ["#1D4ED8", "#7C3AED", "#16A34A"]   # azul, roxo, verde

OPERADORES = [
    "Lucivanio", "Enágio", "Daniel",
    "Ítalo",     "Cildenir", "Samya",
    "Neide",     "Eduardo",  "Talyson",
]

# Paleta de cores dos avatares (por índice do nome)
AV_PALETTE = [
    "#7C3AED", "#1D4ED8", "#B91C1C",
    "#047857", "#C2410C", "#6D28D9",
    "#0369A1", "#374151", "#BE185D",
]

SENHA_GERENCIA = "vi2026"

# ─────────────────────────────────────────────────────────────
# PERSISTÊNCIA
# ─────────────────────────────────────────────────────────────
STATE_DIR      = "vi_state"
FILE_PEDIDOS   = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS= os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO = os.path.join(STATE_DIR, "historico.json")
os.makedirs(STATE_DIR, exist_ok=True)


def _ler(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _gravar(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def db_pedidos()    -> dict: return _ler(FILE_PEDIDOS, {})
def db_concluidos() -> list: d = _ler(FILE_CONCLUIDOS, []); return d if isinstance(d, list) else []
def db_historico()  -> list: d = _ler(FILE_HISTORICO,  []); return d if isinstance(d, list) else []

def salvar_pedidos(d):    _gravar(FILE_PEDIDOS, d)
def salvar_concluidos(d): _gravar(FILE_CONCLUIDOS, d)

def registrar_log(pedido, operador, etapa, status="em_andamento"):
    dh   = agora()
    hist = db_historico()
    hist.append({
        "data_hora": dh,
        "data":      dh.split(" ")[0],
        "pedido":    pedido,
        "operador":  operador,
        "etapa":     etapa,
        "status":    status,
    })
    _gravar(FILE_HISTORICO, hist)


# ─────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────────────────────
def agora() -> str:
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")


def fmt_hms(seg: float) -> str:
    if not seg or seg < 0:
        return "00:00:00"
    seg = int(seg)
    return f"{seg//3600:02d}:{(seg%3600)//60:02d}:{seg%60:02d}"


def av_cor(nome: str) -> str:
    return AV_PALETTE[sum(ord(c) for c in nome) % len(AV_PALETTE)]


def av_ini(nome: str) -> str:
    p = nome.strip().split()
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()


# ─────────────────────────────────────────────────────────────
# LOGO
# ─────────────────────────────────────────────────────────────
import base64 as _b64

def _logo_b64() -> str:
    for p in ["logo_vi.png", "../logo_vi.png"]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return _b64.b64encode(f.read()).decode()
    return ""

_LB64 = _logo_b64()
LOGO_HTML = (
    f'<img src="data:image/png;base64,{_LB64}" style="height:36px;object-fit:contain;" />'
    if _LB64
    else '<span style="font-family:\'Playfair Display\',serif;font-size:1.7rem;'
         'font-weight:900;color:#8B0000;letter-spacing:.05em;">VI LINGERIE</span>'
)

# ─────────────────────────────────────────────────────────────
# CSS  —  CLEAN, SEM HACKS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── FONTES ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500;600&display=swap');

/* ── BASE ────────────────────────────────────────────────── */
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
    max-width: 520px !important;
    padding: 2rem 1rem 4rem !important;
    margin: 0 auto !important;
}

/* ── CARD ────────────────────────────────────────────────── */
.vi-card {
    background: #ffffff;
    border-radius: 18px;
    box-shadow: 0 2px 20px rgba(0,0,0,.08), 0 1px 3px rgba(0,0,0,.04);
    overflow: hidden;
}

/* ── HEADER DO CARD ──────────────────────────────────────── */
.vi-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px 14px;
    border-bottom: 3px solid var(--etapa-cor, #1D4ED8);
}
.vi-av {
    width: 46px; height: 46px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 700; color: #fff;
    flex-shrink: 0;
}
.vi-header-info { flex: 1; }
.vi-header-sub  { font-size: .6rem; font-weight: 700; color: #9ca3af;
                  text-transform: uppercase; letter-spacing: .14em; }
.vi-header-name { font-size: .95rem; font-weight: 700; color: #111827; margin-top: 1px; }
.vi-badge {
    padding: 5px 14px; border-radius: 999px;
    font-size: .62rem; font-weight: 700; letter-spacing: .1em;
    border: 1.5px solid currentColor; white-space: nowrap;
}

/* ── BODY ────────────────────────────────────────────────── */
.vi-body { padding: 24px 20px 26px; }

/* ── WORDMARK ────────────────────────────────────────────── */
.vi-wm { text-align: center; margin-bottom: 16px; padding-top: 2px; }

/* ── DIVIDER ─────────────────────────────────────────────── */
.vi-hr { height: 1px; background: #F0EDE8; border: none; margin: 16px 0; }

/* ── TÍTULO DE SEÇÃO ─────────────────────────────────────── */
.vi-section-label {
    font-size: .6rem; font-weight: 700; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .14em;
    margin-bottom: 14px;
}

/* ── STEPPER ─────────────────────────────────────────────── */
.vi-stepper {
    display: flex; align-items: flex-start;
    margin-bottom: 24px; gap: 0;
}
.vi-step { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 0 0 auto; }
.vi-step-dot {
    width: 42px; height: 42px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 700; transition: all .25s;
}
.vi-step-lbl {
    font-size: .55rem; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; text-align: center; white-space: nowrap;
}
.vi-step-line { flex: 1; height: 1.5px; background: #E5E7EB; margin-top: 20px; }
.vi-step-line-done { background: #1D4ED8 !important; }

/* ── NÚMERO DO PEDIDO ────────────────────────────────────── */
.vi-pedido {
    font-family: 'Playfair Display', serif;
    font-size: 4rem; font-weight: 900;
    color: #111827; line-height: 1;
    text-align: center; margin: 10px 0 4px;
}
.vi-pedido-hash { color: #9CA3AF; font-size: 2.2rem; vertical-align: .22em; }

/* ── TIMER ───────────────────────────────────────────────── */
.vi-timer {
    text-align: center;
    font-family: 'DM Mono', monospace;
    font-size: 1.5rem; font-weight: 500;
    color: #374151; letter-spacing: .08em;
    margin-bottom: 20px;
}

/* ── SCAN AREA ───────────────────────────────────────────── */
.vi-scan { text-align: center; padding: 12px 0 16px; }
.vi-scan-title { font-size: 1rem; font-weight: 700; color: #111827; margin: 10px 0 4px; }
.vi-scan-sub   { font-size: .73rem; color: #9ca3af; }

/* ── INPUTS STREAMLIT ────────────────────────────────────── */
[data-testid="stTextInput"]     label { display: none !important; }
[data-testid="stPasswordInput"] label { display: none !important; }
[data-testid="stSelectbox"]     label { display: none !important; }
[data-testid="stNumberInput"]   label { display: none !important; }

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stPasswordInput"] input {
    background:   #F5F4F2 !important;
    border:       1.5px solid #E5E2DC !important;
    border-radius: 12px !important;
    color:        #111827 !important;
    font-family:  'DM Mono', monospace !important;
    font-size:    1rem !important;
    padding:      14px 18px !important;
    transition:   border-color .2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stPasswordInput"] input:focus {
    border-color: #1D4ED8 !important;
    box-shadow:   0 0 0 3px rgba(29,78,216,.1) !important;
    outline:      none !important;
}
[data-testid="stTextInput"] input::placeholder { color: #B0A99F !important; }

[data-testid="stSelectbox"] > div > div {
    background:    #F5F4F2 !important;
    border:        1.5px solid #E5E2DC !important;
    border-radius: 12px !important;
    font-family:   'DM Sans', sans-serif !important;
}

/* ── BOTÕES STREAMLIT — ESTILOS GLOBAIS ──────────────────── */
/* Reset geral */
[data-testid="stButton"] > button {
    width: 100% !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: .88rem !important;
    letter-spacing: .04em !important;
    border-radius: 12px !important;
    padding: 14px 20px !important;
    transition: all .18s ease !important;
    cursor: pointer !important;
    border: none !important;
}

/* Botão primário azul — classe aplicada via container */
.btn-blue [data-testid="stButton"] > button {
    background: #1D4ED8 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(29,78,216,.35) !important;
}
.btn-blue [data-testid="stButton"] > button:hover {
    background: #1e40af !important;
    box-shadow: 0 6px 18px rgba(29,78,216,.45) !important;
    transform: translateY(-1px) !important;
}

/* Botão vermelho — concluir */
.btn-red [data-testid="stButton"] > button {
    background: #DC2626 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(220,38,38,.35) !important;
    animation: pulse-red 2s ease infinite !important;
}
@keyframes pulse-red {
    0%,100% { box-shadow: 0 4px 14px rgba(220,38,38,.35); }
    50%      { box-shadow: 0 4px 22px rgba(220,38,38,.58); }
}
.btn-red [data-testid="stButton"] > button:hover {
    background: #b91c1c !important;
    transform: translateY(-1px) !important;
}

/* Botão verde */
.btn-green [data-testid="stButton"] > button {
    background: #16A34A !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(22,163,74,.32) !important;
}
.btn-green [data-testid="stButton"] > button:hover {
    background: #15803d !important;
    transform: translateY(-1px) !important;
}

/* Botão ghost (secundário) */
.btn-ghost [data-testid="stButton"] > button {
    background:   transparent !important;
    color:        #6B7280 !important;
    border:       1.5px solid #E5E7EB !important;
    box-shadow:   none !important;
    font-weight:  600 !important;
}
.btn-ghost [data-testid="stButton"] > button:hover {
    background:   #F9FAFB !important;
    color:        #374151 !important;
    border-color: #D1D5DB !important;
}

/* Botão de OPERADOR — card com avatar */
.btn-op [data-testid="stButton"] > button {
    background:    #F9FAFB !important;
    color:         #374151 !important;
    border:        2px solid #F0EDE8 !important;
    border-radius: 16px !important;
    padding:       16px 8px 14px !important;
    font-size:     .78rem !important;
    font-weight:   600 !important;
    height:        auto !important;
    min-height:    90px !important;
    display:       flex !important;
    flex-direction: column !important;
    align-items:   center !important;
    justify-content: center !important;
    gap:           8px !important;
    line-height:   1.3 !important;
    white-space:   normal !important;
    box-shadow:    none !important;
}
.btn-op [data-testid="stButton"] > button:hover {
    background:   #EFF6FF !important;
    border-color: #93C5FD !important;
    color:        #1D4ED8 !important;
    transform:    translateY(-2px) !important;
    box-shadow:   0 4px 12px rgba(29,78,216,.12) !important;
}
.btn-op-sel [data-testid="stButton"] > button {
    background:   #EFF6FF !important;
    border:       2px solid #1D4ED8 !important;
    color:        #1D4ED8 !important;
    border-radius: 16px !important;
    padding:       16px 8px 14px !important;
    font-size:     .78rem !important;
    font-weight:   700 !important;
    min-height:    90px !important;
    display:       flex !important;
    flex-direction: column !important;
    align-items:   center !important;
    justify-content: center !important;
    gap:           8px !important;
    line-height:   1.3 !important;
    white-space:   normal !important;
    box-shadow:    0 0 0 3px rgba(29,78,216,.15) !important;
}

/* Botão de link pequeno */
.btn-link [data-testid="stButton"] > button {
    background:   transparent !important;
    color:        #9CA3AF !important;
    border:       none !important;
    box-shadow:   none !important;
    font-size:    .72rem !important;
    font-weight:  500 !important;
    padding:      8px !important;
}
.btn-link [data-testid="stButton"] > button:hover {
    color:        #374151 !important;
    background:   transparent !important;
}

/* ── ALERTS ──────────────────────────────────────────────── */
.vi-alert {
    display: flex; align-items: center; gap: 8px;
    padding: 11px 15px; border-radius: 12px;
    font-size: .8rem; font-weight: 500; margin: 8px 0;
}
.vi-ok   { background:#F0FDF4; border:1.5px solid #BBF7D0; color:#16A34A; }
.vi-err  { background:#FEF2F2; border:1.5px solid #FECACA; color:#DC2626; }
.vi-inf  { background:#EFF6FF; border:1.5px solid #BFDBFE; color:#1D4ED8; }
.vi-warn { background:#FFFBEB; border:1.5px solid #FDE68A; color:#D97706; }

/* ── CARD DE CONCLUSÃO ───────────────────────────────────── */
.vi-done {
    background: linear-gradient(135deg,#F0FDF4,#DCFCE7);
    border: 2px solid #BBF7D0; border-radius: 18px;
    padding: 32px 20px; text-align: center;
    animation: pop .4s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes pop { from{opacity:0;transform:scale(.88);} to{opacity:1;transform:scale(1);} }

/* ── CARD ASK NEXT ───────────────────────────────────────── */
.vi-ask {
    background: #F9FAFB; border-radius: 14px;
    padding: 16px 16px 18px; margin-top: 14px;
    border: 1px solid #F0EDE8;
}
.vi-ask-title {
    font-size: .66rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .12em; margin-bottom: 12px;
}

/* ── MINI STAT ───────────────────────────────────────────── */
.vi-stat {
    background: #F9FAFB; border: 1px solid #F0EDE8;
    border-radius: 12px; padding: 10px 14px; text-align: center;
}
.vi-stat-label { font-size: .58rem; font-weight:700; color:#9CA3AF;
                 text-transform:uppercase; letter-spacing:.1em; margin-bottom:2px; }
.vi-stat-val   { font-family:'DM Mono',monospace; font-size:1.3rem; font-weight:600; color:#111827; }

/* ── ANIMAÇÃO ENTRADA ────────────────────────────────────── */
@keyframes fadeup { from{opacity:0;transform:translateY(10px);} to{opacity:1;transform:translateY(0);} }
.vi-card { animation: fadeup .3s ease both; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HELPERS HTML
# ─────────────────────────────────────────────────────────────
def avatar_div(nome: str, size: int = 46) -> str:
    cor = av_cor(nome); ini = av_ini(nome); fs = int(size * .37)
    return (
        f'<div class="vi-av" style="width:{size}px;height:{size}px;'
        f'background:{cor};font-size:{fs}px;">{ini}</div>'
    )


def render_wordmark():
    st.markdown(f'<div class="vi-wm">{LOGO_HTML}</div>', unsafe_allow_html=True)


def render_card_header(operador: str, etapa_idx: int):
    cor   = ETAPA_COLORS[etapa_idx]
    label = ETAPA_LABELS[etapa_idx]
    av    = avatar_div(operador, 46)
    st.markdown(f"""
    <div class="vi-header" style="--etapa-cor:{cor};">
        {av}
        <div class="vi-header-info">
            <div class="vi-header-sub">ESTAÇÃO CENTRAL</div>
            <div class="vi-header-name">{operador}</div>
        </div>
        <div class="vi-badge" style="color:{cor};">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_stepper(etapa_idx: int):
    CHECK = "✓"
    html  = '<div class="vi-stepper">'
    for i, (label, icon) in enumerate(zip(ETAPA_LABELS, ETAPA_ICONS)):
        cor  = ETAPA_COLORS[i]
        done   = i < etapa_idx
        active = i == etapa_idx

        if done:
            dot_style = f"background:{cor};color:#fff;"
            lbl_style = f"color:{cor};"
            dot_content = CHECK
        elif active:
            dot_style = f"background:{cor};color:#fff;box-shadow:0 0 0 5px {cor}22;"
            lbl_style = f"color:{cor};font-weight:800;"
            dot_content = icon
        else:
            dot_style = "background:#F0EDE8;color:#C4BAB0;"
            lbl_style = "color:#C4BAB0;"
            dot_content = icon

        html += f"""
        <div class="vi-step">
            <div class="vi-step-dot" style="{dot_style}">{dot_content}</div>
            <div class="vi-step-lbl" style="{lbl_style}">{label}</div>
        </div>"""

        if i < 2:
            line_cls = "vi-step-line vi-step-line-done" if done else "vi-step-line"
            html += f'<div class="{line_cls}"></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_pedido_num(num: str):
    st.markdown(
        f'<div class="vi-pedido"><span class="vi-pedido-hash">#</span>{num}</div>',
        unsafe_allow_html=True,
    )


def render_timer(ts_inicio: float):
    elapsed = fmt_hms(time.time() - ts_inicio) if ts_inicio else "00:00:00"
    st.markdown(
        f'<div class="vi-timer">⏱ {elapsed}</div>',
        unsafe_allow_html=True,
    )


def alert(msg: str, kind: str = "inf"):
    st.markdown(f'<div class="vi-alert vi-{kind}">{msg}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# TELA 1 — SELEÇÃO DE OPERADOR
# ─────────────────────────────────────────────────────────────
def tela_selecao():
    render_wordmark()

    # ── Títulos fora do card ──────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:1.05rem;font-weight:700;color:#111827;">Apontamento de Produção</div>
        <div style="font-size:.75rem;color:#9ca3af;margin-top:4px;">Selecione seu nome para começar</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Card ─────────────────────────────────────────────
    st.markdown('<div class="vi-card"><div class="vi-body">', unsafe_allow_html=True)
    st.markdown('<div class="vi-section-label">QUEM É VOCÊ?</div>', unsafe_allow_html=True)

    # ── Grade de operadores — 3 colunas com botões REAIS ─
    sel = st.session_state.get("_sel_op", None)

    linhas = [OPERADORES[i:i+3] for i in range(0, len(OPERADORES), 3)]
    for linha in linhas:
        colunas = st.columns(3, gap="small")
        for col_idx, nome in enumerate(linha):
            with colunas[col_idx]:
                cor = av_cor(nome)
                ini = av_ini(nome)
                css_class = "btn-op-sel" if sel == nome else "btn-op"

                # Avatar como HTML dentro do label do botão não é possível nativamente,
                # então exibimos o avatar acima e o botão abaixo com espaço zero.
                st.markdown(
                    f"""<div style="text-align:center;margin-bottom:4px;">
                        <div style="width:52px;height:52px;border-radius:50%;
                            background:{cor};display:flex;align-items:center;
                            justify-content:center;font-size:18px;font-weight:700;
                            color:#fff;margin:0 auto;
                            box-shadow:0 3px 10px {cor}44;">
                            {ini}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

                st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                if st.button(nome, key=f"op__{nome}", use_container_width=True):
                    # ✅ Um único clique = seleciona E entra no sistema
                    st.session_state["_sel_op"]       = nome
                    st.session_state["_operador"]     = nome
                    st.session_state["_turno_ts"]     = time.time()
                    st.session_state["_etapa_idx"]    = 0
                    st.session_state["_flow"]         = "input"
                    st.session_state["_pedido"]       = None
                    st.session_state["_ts_inicio"]    = None
                    st.session_state["_ts_fim"]       = None
                    st.session_state["_ask_mode"]     = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Preenche células vazias na última linha
        for vazio in range(len(linha), 3):
            with colunas[vazio]:
                st.empty()

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

    # ── Link gerência ─────────────────────────────────────
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown('<div class="btn-link">', unsafe_allow_html=True)
        if st.button("🔒  Acesso Gerência", key="btn__ger_link", use_container_width=True):
            st.session_state["_modo"] = "gerencia"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# TELA 2 — FLUXO DO OPERADOR
# Estados: input → confirm → running → ask_next → done
# ─────────────────────────────────────────────────────────────
def tela_operador():
    operador  = st.session_state["_operador"]
    etapa_idx = st.session_state.get("_etapa_idx", 0)
    flow      = st.session_state.get("_flow", "input")
    pedido    = st.session_state.get("_pedido")
    ts_inicio = st.session_state.get("_ts_inicio")
    ts_turno  = st.session_state.get("_turno_ts", time.time())

    render_wordmark()

    # ── CARD ──────────────────────────────────────────────
    st.markdown('<div class="vi-card">', unsafe_allow_html=True)
    render_card_header(operador, etapa_idx)
    st.markdown('<div class="vi-body">', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # ESTADO: INPUT
    # ════════════════════════════════════════════════════
    if flow == "input":

        # ── Etapa 0 (Separação): digitar/bipar número ──
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

            col_inp, col_btn = st.columns([5, 1], gap="small")
            with col_inp:
                numero = st.text_input(
                    "num", placeholder="Ex: 12345",
                    key="inp__numero", label_visibility="collapsed",
                )
            with col_btn:
                st.markdown('<div class="btn-blue" style="padding-top:2px;">', unsafe_allow_html=True)
                ir = st.button("→", key="btn__ir", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            if ir:
                num = st.session_state.get("inp__numero", "").strip()
                db  = db_pedidos()
                if not num:
                    alert("⚠️ Informe o número do pedido.", "err")
                elif num in db:
                    alert(f"⚠️ Pedido #{num} já está em andamento.", "err")
                else:
                    st.session_state["_pedido"] = num
                    st.session_state["_flow"]   = "confirm"
                    st.rerun()

        # ── Etapa 1/2: selecionar da lista ──
        else:
            render_stepper(etapa_idx)

            db         = db_pedidos()
            chave_op   = "op_emb" if etapa_idx == 1 else "op_conf"
            etapa_need = etapa_idx          # etapa 1 → busca pedidos com etapa==1
            disponiveis = sorted([
                p for p, d in db.items()
                if d.get("etapa") == etapa_need and chave_op not in d
            ])

            if not disponiveis:
                alert(
                    f"⏳ Nenhum pedido aguardando {ETAPA_LABELS[etapa_idx]}. "
                    "Aguarde a etapa anterior ser concluída.",
                    "warn",
                )
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                if st.button("🔄  Atualizar lista", key="btn__atualizar", use_container_width=True):
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                sel_ped = st.selectbox(
                    "Pedido",
                    options=["— Selecione o pedido —"] + disponiveis,
                    key=f"sel__ped_{etapa_idx}",
                    label_visibility="collapsed",
                )
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
                if st.button(
                    f"▶  INICIAR {ETAPA_LABELS[etapa_idx]}",
                    key=f"btn__ini_{etapa_idx}",
                    use_container_width=True,
                ):
                    if sel_ped == "— Selecione o pedido —":
                        alert("⚠️ Selecione um pedido da lista.", "err")
                    else:
                        st.session_state["_pedido"] = sel_ped
                        st.session_state["_flow"]   = "confirm"
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # ESTADO: CONFIRM  — exibe o número e pede confirmação
    # ════════════════════════════════════════════════════
    elif flow == "confirm":
        render_stepper(etapa_idx)
        render_pedido_num(pedido)
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button(
            f"▶  INICIAR {ETAPA_LABELS[etapa_idx]}",
            key="btn__confirmar",
            use_container_width=True,
        ):
            st.session_state["_flow"]      = "running"
            st.session_state["_ts_inicio"] = time.time()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("← Alterar pedido", key="btn__alterar", use_container_width=True):
            st.session_state["_flow"]   = "input"
            st.session_state["_pedido"] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # ESTADO: RUNNING  — cronômetro + botão CONCLUIR
    # ════════════════════════════════════════════════════
    elif flow == "running":
        render_stepper(etapa_idx)
        render_pedido_num(pedido)
        render_timer(ts_inicio)

        st.markdown('<div class="btn-red">', unsafe_allow_html=True)
        if st.button(
            f"■  CONCLUIR {ETAPA_LABELS[etapa_idx]}",
            key="btn__concluir",
            use_container_width=True,
        ):
            _finalizar_etapa(operador, etapa_idx, pedido)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("✕  Cancelar operação", key="btn__cancelar", use_container_width=True):
            st.session_state.update({
                "_flow": "input", "_pedido": None, "_ts_inicio": None,
            })
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # ESTADO: ASK_NEXT — etapa concluída, quem faz a próxima?
    # ════════════════════════════════════════════════════
    elif flow == "ask_next":
        prox_idx  = etapa_idx + 1
        prox_cor  = ETAPA_COLORS[prox_idx]
        prox_nome = ETAPA_LABELS[prox_idx]
        ts_fim    = st.session_state.get("_ts_fim", time.time())
        dur       = fmt_hms(ts_fim - ts_inicio) if ts_inicio else "--"

        render_stepper(etapa_idx)

        # Pill de confirmação
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:6px;">
            <div style="display:inline-block;background:#F0FDF4;border:1.5px solid #BBF7D0;
                border-radius:10px;padding:8px 18px;">
                <span style="font-size:.62rem;font-weight:700;color:#16A34A;
                    text-transform:uppercase;letter-spacing:.1em;">
                    ✓ {ETAPA_LABELS[etapa_idx]} CONCLUÍDA &nbsp;·&nbsp; {dur}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_pedido_num(pedido)

        # Card de pergunta
        st.markdown(f"""
        <div class="vi-ask">
            <div class="vi-ask-title" style="color:{prox_cor};">
                {ETAPA_ICONS[prox_idx]} &nbsp;Próxima etapa: {prox_nome}<br>
                <span style="color:#9CA3AF;font-weight:500;font-size:.6rem;
                    text-transform:none;letter-spacing:.03em;">
                    Quem vai realizar esta etapa?
                </span>
            </div>
        """, unsafe_allow_html=True)

        ask_mode = st.session_state.get("_ask_mode")

        # Dois botões lado a lado
        col_eu, col_outro = st.columns(2, gap="small")
        with col_eu:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button(
                f"✓  Sou eu\n({operador.split()[0]})",
                key="btn__mesmo_op",
                use_container_width=True,
            ):
                _avancar_etapa(etapa_idx, pedido, operador)
            st.markdown('</div>', unsafe_allow_html=True)
        with col_outro:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("👤  Outro operador", key="btn__outro_op", use_container_width=True):
                st.session_state["_ask_mode"] = "select"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Sub-grid de seleção de outro operador
        if ask_mode == "select":
            st.markdown("<div class='vi-hr'></div>", unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.62rem;font-weight:700;color:#9ca3af;'
                'text-transform:uppercase;letter-spacing:.12em;margin-bottom:10px;">'
                "Selecione o operador:</div>",
                unsafe_allow_html=True,
            )
            outros = [op for op in OPERADORES if op != operador]
            linhas2 = [outros[i:i+3] for i in range(0, len(outros), 3)]
            for linha2 in linhas2:
                cols2 = st.columns(3, gap="small")
                for ci, nome2 in enumerate(linha2):
                    with cols2[ci]:
                        cor2 = av_cor(nome2); ini2 = av_ini(nome2)
                        st.markdown(
                            f"""<div style="text-align:center;margin-bottom:4px;">
                                <div style="width:44px;height:44px;border-radius:50%;
                                    background:{cor2};display:flex;align-items:center;
                                    justify-content:center;font-size:15px;font-weight:700;
                                    color:#fff;margin:0 auto;
                                    box-shadow:0 2px 8px {cor2}44;">{ini2}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                        st.markdown('<div class="btn-op">', unsafe_allow_html=True)
                        if st.button(nome2, key=f"prox__{nome2}", use_container_width=True):
                            _avancar_etapa(etapa_idx, pedido, nome2)
                        st.markdown('</div>', unsafe_allow_html=True)
                for vz in range(len(linha2), 3):
                    with cols2[vz]:
                        st.empty()

        st.markdown('</div>', unsafe_allow_html=True)  # vi-ask

    # ════════════════════════════════════════════════════
    # ESTADO: DONE — pedido totalmente concluído
    # ════════════════════════════════════════════════════
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
                Todas as 3 etapas finalizadas &nbsp;·&nbsp; {dur}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("▶  Iniciar Novo Pedido", key="btn__novo_ped", use_container_width=True):
            st.session_state.update({
                "_flow": "input", "_etapa_idx": 0,
                "_pedido": None, "_ts_inicio": None, "_ts_fim": None, "_ask_mode": None,
            })
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Fecha body e card ──────────────────────────────
    st.markdown('</div></div>', unsafe_allow_html=True)

    # ── Rodapé: stats do turno + trocar operador ──────
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    hoje_str = agora().split(" ")[0]
    hist = db_historico()
    ops_hoje = len([h for h in hist if h.get("operador") == operador and h.get("data") == hoje_str])
    turno_dur = fmt_hms(time.time() - ts_turno)

    c1, c2 = st.columns(2, gap="small")
    with c1:
        st.markdown(
            f'<div class="vi-stat"><div class="vi-stat-label">Operações hoje</div>'
            f'<div class="vi-stat-val" style="color:#16A34A;">{ops_hoje}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="vi-stat"><div class="vi-stat-label">Tempo de turno</div>'
            f'<div class="vi-stat-val">{turno_dur}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("⏏  Trocar Operador / Sair", key="btn__sair_op", use_container_width=True):
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# AÇÕES DE NEGÓCIO
# ─────────────────────────────────────────────────────────────
def _finalizar_etapa(operador: str, etapa_idx: int, pedido: str):
    now    = agora()
    ts_fim = time.time()
    db     = db_pedidos()

    if etapa_idx == 0:
        db[pedido] = {
            "pedido": pedido, "etapa": 1,
            "op_sep": operador, "dt_sep": now,
        }
        registrar_log(pedido, operador, ETAPAS[0], "em_andamento")

    elif etapa_idx == 1:
        if pedido in db:
            db[pedido].update({"etapa": 2, "op_emb": operador, "dt_emb": now})
            registrar_log(pedido, operador, ETAPAS[1], "em_andamento")

    elif etapa_idx == 2:
        if pedido in db:
            db[pedido].update({"etapa": 3, "op_conf": operador, "dt_conf": now})
            conc = db_concluidos()
            conc.append(db[pedido])
            salvar_concluidos(conc)
            del db[pedido]
            registrar_log(pedido, operador, ETAPAS[2], "concluido")

    salvar_pedidos(db)
    next_flow = "ask_next" if etapa_idx < 2 else "done"
    st.session_state.update({"_ts_fim": ts_fim, "_flow": next_flow})
    st.rerun()


def _avancar_etapa(etapa_atual: int, pedido: str, proximo_op: str):
    st.session_state.update({
        "_operador":  proximo_op,
        "_etapa_idx": etapa_atual + 1,
        "_flow":      "confirm",
        "_pedido":    pedido,
        "_ts_inicio": None,
        "_ts_fim":    None,
        "_ask_mode":  None,
    })
    st.rerun()


# ─────────────────────────────────────────────────────────────
# TELA 3 — LOGIN GERÊNCIA
# ─────────────────────────────────────────────────────────────
def tela_login_gerencia():
    render_wordmark()
    st.markdown('<div class="vi-card"><div class="vi-body">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px;">
        <div style="font-size:1.05rem;font-weight:700;color:#111827;">Área da Gerência</div>
        <div style="font-size:.73rem;color:#9ca3af;margin-top:4px;">Informe a senha de acesso</div>
    </div>
    """, unsafe_allow_html=True)

    senha = st.text_input(
        "senha", type="password", placeholder="••••••••",
        key="inp__senha_ger", label_visibility="collapsed",
    )
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
    if st.button("🔓  Acessar", key="btn__acessar_ger", use_container_width=True):
        if senha == SENHA_GERENCIA:
            st.session_state["_ger_ok"] = True
            st.rerun()
        else:
            alert("❌ Senha incorreta.", "err")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("← Voltar", key="btn__volta_ger", use_container_width=True):
        st.session_state.pop("_modo", None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# TELA 4 — EXTRATO GERÊNCIA
# ─────────────────────────────────────────────────────────────
def tela_extrato():
    conc = db_concluidos()
    pend = db_pedidos()
    hist = db_historico()

    render_wordmark()
    st.markdown("""
    <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:1.05rem;font-weight:700;color:#111827;">Extrato de Produção</div>
        <div style="font-size:.72rem;color:#9ca3af;margin-top:3px;">Consulta, filtros e relatórios</div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    ts = len([h for h in hist if h.get("etapa") == ETAPAS[0]])
    te = len([h for h in hist if h.get("etapa") == ETAPAS[1]])
    tc = len([h for h in hist if h.get("etapa") == ETAPAS[2]])
    tk = len(conc)
    k1, k2, k3, k4 = st.columns(4, gap="small")
    for col, lab, val, cor in [
        (k1, "📦 Sep.",   ts, "#1D4ED8"),
        (k2, "📬 Emb.",   te, "#7C3AED"),
        (k3, "✅ Conf.",  tc, "#16A34A"),
        (k4, "🎯 Conc.",  tk, "#DC2626"),
    ]:
        with col:
            st.markdown(
                f'<div class="vi-stat"><div class="vi-stat-label">{lab}</div>'
                f'<div class="vi-stat-val" style="color:{cor};font-size:1.6rem;">{val}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    aba1, aba2, aba3 = st.tabs(["📅 Histórico", "📋 Concluídos", "⏳ Em Andamento"])

    # ── Aba Histórico ─────────────────────────────────
    with aba1:
        if not hist:
            alert("ℹ️ Nenhuma operação registrada ainda.", "inf")
        else:
            df = pd.DataFrame(hist)
            df["_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")

            from datetime import date, timedelta as td
            hoje = date.today()
            cf1, cf2, cf3, cf4 = st.columns(4, gap="small")
            with cf1:
                di = st.date_input("Início", value=hoje - td(days=7),
                                   key="ger__di", format="DD/MM/YYYY")
            with cf2:
                df_v = st.date_input("Fim", value=hoje,
                                     key="ger__df", format="DD/MM/YYYY")
            with cf3:
                ops_l = ["Todos"] + sorted(df["operador"].dropna().unique().tolist())
                opf   = st.selectbox("Funcionário", ops_l, key="ger__op",
                                     label_visibility="visible")
            with cf4:
                etl  = ["Todas"] + ETAPAS
                etf  = st.selectbox("Etapa", etl, key="ger__et",
                                    label_visibility="visible")

            mask = (df["_dt"] >= pd.Timestamp(di)) & (df["_dt"] <= pd.Timestamp(df_v))
            dff  = df[mask].copy()
            if opf != "Todos": dff = dff[dff["operador"] == opf]
            if etf != "Todas": dff = dff[dff["etapa"]    == etf]
            dff  = dff.sort_values("data_hora", ascending=False)

            alert(f"🔍 <b>{len(dff)}</b> operação(ões) encontrada(s)", "inf")

            if len(dff):
                if opf == "Todos":
                    res = dff.groupby(["operador", "etapa"]).size().reset_index(name="Qtd.")
                    res.columns = ["Funcionário", "Etapa", "Qtd."]
                    st.dataframe(res, use_container_width=True, hide_index=True)
                    st.markdown("<div class='vi-hr'></div>", unsafe_allow_html=True)

                de = dff[["data_hora","pedido","operador","etapa","status"]].rename(columns={
                    "data_hora": "Data/Hora", "pedido": "Pedido",
                    "operador": "Funcionário", "etapa": "Etapa", "status": "Status"
                })
                de["Status"] = de["Status"].map(
                    {"em_andamento": "⏳", "concluido": "✅"}
                ).fillna(de["Status"])
                st.dataframe(de, use_container_width=True, hide_index=True)

                nome_arq = f"extrato_{opf.replace(' ','_')}_{di.strftime('%d%m%Y')}"
                d1, d2 = st.columns(2, gap="small")
                with d1:
                    st.download_button(
                        "⬇️ CSV", data=de.to_csv(index=False).encode("utf-8"),
                        file_name=f"{nome_arq}.csv", mime="text/csv",
                        use_container_width=True, key="dl__csv",
                    )
                with d2:
                    xb = BytesIO()
                    with pd.ExcelWriter(xb, engine="openpyxl") as w:
                        de.to_excel(w, index=False, sheet_name="Histórico")
                    xb.seek(0)
                    st.download_button(
                        "⬇️ Excel", data=xb.getvalue(),
                        file_name=f"{nome_arq}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True, key="dl__xlsx",
                    )

    # ── Aba Concluídos ────────────────────────────────
    with aba2:
        if not conc:
            alert("ℹ️ Nenhum pedido finalizado ainda.", "inf")
        else:
            dc = pd.DataFrame(conc).rename(columns={
                "pedido": "Pedido", "op_sep": "Op. Sep.", "dt_sep": "Data Sep.",
                "op_emb": "Op. Emb.", "dt_emb": "Data Emb.",
                "op_conf": "Op. Conf.", "dt_conf": "Data Conf.",
            }).drop(columns=["etapa"], errors="ignore")
            st.dataframe(dc, use_container_width=True, hide_index=True)
            xb2 = BytesIO()
            with pd.ExcelWriter(xb2, engine="openpyxl") as w:
                dc.to_excel(w, index=False, sheet_name="Concluídos")
            xb2.seek(0)
            e1, e2 = st.columns(2, gap="small")
            with e1:
                st.download_button(
                    "⬇️ CSV", data=dc.to_csv(index=False).encode("utf-8"),
                    file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv",
                    mime="text/csv", use_container_width=True, key="dl__conc_csv",
                )
            with e2:
                st.download_button(
                    "⬇️ Excel", data=xb2.getvalue(),
                    file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl__conc_xlsx",
                )

    # ── Aba Em Andamento ──────────────────────────────
    with aba3:
        if not pend:
            alert("✅ Nenhum pedido em andamento.", "ok")
        else:
            el = {1: "📬 Aguard. Embalagem", 2: "✅ Aguard. Conferência"}
            rows = [
                {
                    "Pedido":   f"#{d['pedido']}",
                    "Etapa":    el.get(d.get("etapa", 0), "—"),
                    "Op. Sep.": d.get("op_sep", "—"),
                    "Op. Emb.": d.get("op_emb", "—"),
                }
                for d in pend.values()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("← Sair da Gerência", key="btn__sair_ger", use_container_width=True):
        st.session_state.pop("_modo",   None)
        st.session_state.pop("_ger_ok", None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# ROTEADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────
def main():
    modo = st.session_state.get("_modo")

    if modo == "gerencia":
        if st.session_state.get("_ger_ok"):
            tela_extrato()
        else:
            tela_login_gerencia()
        return

    # Modo operador
    if "_operador" in st.session_state:
        tela_operador()
    else:
        tela_selecao()


main()
