import streamlit as st
import json
import os
import time
from datetime import datetime
from io import BytesIO

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="centered",
    page_icon="🏭",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONSTANTES
# ============================================================
OPERADORES = [
    "Lucivanio", "Enágio", "Daniel", "Ítalo", "Cildenir",
    "Samya", "Neide", "Eduardo", "Talyson",
]

ETAPAS      = ["Separação", "Embalagem", "Conferência"]
ETAPA_FULL  = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_ICONS = ["📦", "📬", "✅"]

ETAPA_CORES = {
    0: {"main": "#1565C0", "light": "#E3F0FF"},
    1: {"main": "#7B1FA2", "light": "#F3E8FF"},
    2: {"main": "#1B5E20", "light": "#E8F5E9"},
}

SENHA_GERENCIA = "vi2026"

STATE_DIR       = "vi_producao_state"
os.makedirs(STATE_DIR, exist_ok=True)
FILE_PEDIDOS    = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS = os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO  = os.path.join(STATE_DIR, "historico.json")

OP_CORES = [
    "#7B1FA2","#1565C0","#4A148C","#1B5E20",
    "#E65100","#880E4F","#006064","#37474F","#BF360C",
]

# ============================================================
# STORAGE
# ============================================================
def _load(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_pedidos():     return _load(FILE_PEDIDOS)
def save_pedidos(d):    _save(FILE_PEDIDOS, d)
def load_concluidos():
    d = _load(FILE_CONCLUIDOS)
    return d if isinstance(d, list) else []
def save_concluidos(d): _save(FILE_CONCLUIDOS, d)
def load_historico():
    d = _load(FILE_HISTORICO)
    return d if isinstance(d, list) else []

def reg_historico(pedido, operador, etapa, status="em_andamento"):
    now  = agora_str()
    hist = load_historico()
    hist.append({
        "data_hora": now,
        "data": now.split(" ")[0],
        "pedido": pedido,
        "operador": operador,
        "etapa": etapa,
        "status_pedido": status,
    })
    _save(FILE_HISTORICO, hist)

def agora_str():
    from datetime import timezone, timedelta
    br = timezone(timedelta(hours=-3))
    return datetime.now(br).strftime("%d/%m/%Y %H:%M")

def fmt_tempo(seg):
    if seg is None or seg < 0: return "00:00:00"
    h = int(seg // 3600); m = int((seg % 3600) // 60); s = int(seg % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def op_cor(nome):
    return OP_CORES[sum(ord(c) for c in nome) % len(OP_CORES)]

def op_iniciais(nome):
    p = nome.strip().split()
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()

# ============================================================
# CSS GLOBAL — TEMA BRANCO
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stApp"] {
    font-family: 'Inter', sans-serif !important;
    background: #EEEAE3 !important;
    color: #1a1a1a !important;
    min-height: 100vh;
}

[data-testid="stSidebar"],
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

.block-container {
    padding: 0 16px 0 !important;
    max-width: 520px !important;
    margin: 0 auto !important;
}

/* Esconde label dos botões usados como trigger de seleção */
.vi-op-btn-wrap > div > button {
    opacity: 0 !important;
    position: absolute !important;
    top: 0; left: 0;
    width: 100% !important;
    height: 100% !important;
    cursor: pointer !important;
    z-index: 10 !important;
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
}

/* ─── CARD ─── */
.vi-card {
    background: #fff;
    border-radius: 22px;
    box-shadow: 0 2px 20px rgba(0,0,0,.07);
    overflow: hidden;
    margin-bottom: 14px;
}

/* ─── CARD HEADER ─── */
.vi-card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px 14px;
    border-bottom: 3px solid #eee;
}
.vi-card-header-info { flex: 1; min-width: 0; }
.vi-card-header-sub  { font-size: .58rem; font-weight: 700; color: #9ca3af; letter-spacing:.14em; text-transform: uppercase; }
.vi-card-header-name { font-size: .95rem; font-weight: 700; color: #111; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.vi-etapa-badge {
    font-size: .58rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; padding: 5px 12px;
    border-radius: 20px; border: 1.5px solid currentColor;
    white-space: nowrap;
}

/* ─── CARD BODY ─── */
.vi-card-body { padding: 22px 20px; }

/* ─── STEPPER ─── */
.vi-stepper {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    margin-bottom: 22px;
}
.vi-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 0 0 auto;
    min-width: 70px;
}
.vi-step-circle {
    width: 38px; height: 38px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .78rem; font-weight: 700;
    border: 2px solid #e5e7eb;
    background: #fff; color: #9ca3af;
    position: relative; z-index: 2;
    transition: all .3s;
}
.vi-step-label {
    font-size: .55rem; font-weight: 700; color: #9ca3af;
    text-transform: uppercase; letter-spacing: .1em;
    text-align: center; white-space: nowrap;
}
.vi-step-connector {
    flex: 1; height: 2px;
    background: #e5e7eb;
    margin-top: 19px;
    position: relative; z-index: 1;
    transition: background .3s;
}

/* ─── ORDER NUMBER ─── */
.vi-order-num {
    font-family: 'Playfair Display', serif;
    font-size: 3rem; font-weight: 900; color: #111;
    text-align: center; margin: 4px 0 4px;
    letter-spacing: -.02em; line-height: 1.1;
}
.vi-order-num .hash { color: #9ca3af; font-size: 2rem; }

/* ─── TIMER ─── */
.vi-timer {
    font-family: 'DM Mono', monospace;
    font-size: 1.25rem; font-weight: 500;
    text-align: center; color: #374151;
    margin-bottom: 18px; letter-spacing: .1em;
}

/* ─── SCAN AREA ─── */
.vi-scan-area {
    text-align: center;
    padding: 16px 0 10px;
}
.vi-scan-icon { font-size: 2.2rem; color: #d1d5db; margin-bottom: 8px; }
.vi-scan-title { font-size: .95rem; font-weight: 700; color: #111; margin-bottom: 3px; }
.vi-scan-hint  { font-size: .73rem; color: #9ca3af; }

/* ─── BUTTONS (reset) ─── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 14px !important;
    font-size: .85rem !important;
    letter-spacing: .03em !important;
    padding: 13px 20px !important;
    width: 100% !important;
    transition: all .18s !important;
    border: none !important;
    background: #f3f4f6 !important;
    color: #374151 !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    background: #e5e7eb !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,.08) !important;
}

/* Variações de cor */
.vi-btn-blue > button   { background:#1565C0 !important; color:#fff !important; box-shadow:0 4px 16px rgba(21,101,192,.25) !important; }
.vi-btn-blue > button:hover   { background:#0d47a1 !important; box-shadow:0 6px 20px rgba(21,101,192,.35) !important; }

.vi-btn-red > button    { background:#DC2626 !important; color:#fff !important; box-shadow:0 4px 16px rgba(220,38,38,.25) !important; }
.vi-btn-red > button:hover    { background:#b91c1c !important; }

.vi-btn-purple > button { background:#7B1FA2 !important; color:#fff !important; box-shadow:0 4px 16px rgba(123,31,162,.25) !important; }
.vi-btn-purple > button:hover { background:#6a1b9a !important; }

.vi-btn-green > button  { background:#1B5E20 !important; color:#fff !important; box-shadow:0 4px 16px rgba(27,94,32,.25) !important; }
.vi-btn-green > button:hover  { background:#145218 !important; }

.vi-btn-outline > button {
    background:#fff !important; color:#374151 !important;
    border:1.5px solid #e5e7eb !important; box-shadow:none !important;
}
.vi-btn-outline > button:hover { background:#f9fafb !important; border-color:#d1d5db !important; }

.vi-btn-ghost > button {
    background:transparent !important; color:#9ca3af !important;
    border:none !important; box-shadow:none !important;
    font-size:.78rem !important; padding:8px !important;
}
.vi-btn-ghost > button:hover { color:#374151 !important; background:#f3f4f6 !important; }

/* ─── INPUTS ─── */
[data-testid="stTextInput"] input {
    background:#f9fafb !important;
    border:2px solid #e5e7eb !important;
    border-radius:14px !important;
    color:#111 !important;
    font-family:'DM Mono', monospace !important;
    font-size:1.1rem !important;
    padding:14px 18px !important;
    text-align:center !important;
    transition:border-color .18s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color:#1565C0 !important;
    box-shadow:0 0 0 3px rgba(21,101,192,.12) !important;
    background:#fff !important;
    outline:none !important;
}
[data-testid="stTextInput"] label { display:none !important; }

[data-testid="stSelectbox"] > div > div {
    background:#f9fafb !important;
    border:2px solid #e5e7eb !important;
    border-radius:12px !important;
    color:#111 !important;
}
[data-testid="stSelectbox"] label p {
    color:#6b7280 !important; font-size:.68rem !important;
    font-weight:700 !important; letter-spacing:.1em !important;
    text-transform:uppercase !important;
}

/* ─── ALERTS ─── */
.vi-alert {
    padding:11px 15px; border-radius:12px;
    font-size:.78rem; font-weight:500; margin:8px 0;
}
.vi-alert-err  { background:#FEF2F2; border:1.5px solid #FECACA; color:#DC2626; }
.vi-alert-ok   { background:#F0FDF4; border:1.5px solid #BBF7D0; color:#16a34a; }
.vi-alert-inf  { background:#EFF6FF; border:1.5px solid #BFDBFE; color:#1d4ed8; }
.vi-alert-warn { background:#FFFBEB; border:1.5px solid #FDE68A; color:#d97706; }

/* ─── OPERATOR GRID ─── */
.vi-op-wrap {
    position: relative;
    border-radius: 16px;
    overflow: hidden;
}
.vi-op-face {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 7px;
    padding: 16px 8px 14px;
    border-radius: 16px;
    background: #f9fafb;
    border: 2px solid transparent;
    cursor: pointer;
    transition: all .2s;
    text-align: center;
    user-select: none;
}
.vi-op-face:hover    { background:#f0f0f8; border-color:#d1d5db; transform:translateY(-2px); }
.vi-op-face.selected { background:#EFF6FF; border-color:#1565C0; }
.vi-op-name          { font-size:.72rem; font-weight:600; color:#374151; }
.vi-op-avatar {
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; color: #fff;
}

/* ─── DONE CARD ─── */
.vi-done-card {
    background:#F0FDF4; border:2px solid #BBF7D0;
    border-radius:18px; padding:26px 20px;
    text-align:center; margin:4px 0;
}
.vi-done-emoji  { font-size:2.5rem; margin-bottom:10px; }
.vi-done-title  { font-family:'Playfair Display',serif; font-size:1.3rem; font-weight:900; color:#16a34a; margin-bottom:6px; }
.vi-done-num    { font-family:'DM Mono',monospace; font-size:1.8rem; font-weight:700; color:#111; margin-bottom:4px; }
.vi-done-meta   { font-size:.72rem; color:#6b7280; }

/* ─── ASK BANNER ─── */
.vi-ask-banner {
    border-radius:14px; padding:14px 18px;
    text-align:center; margin-bottom:16px;
    border:1.5px solid;
}
.vi-ask-label { font-size:.65rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:4px; }
.vi-ask-question { font-size:.92rem; font-weight:600; color:#111; }

/* ─── DIVIDER ─── */
.vi-div { height:1px; background:#f3f4f6; margin:12px 0; }

/* ─── STAT ROW ─── */
.vi-stat-row {
    display:flex; justify-content:space-between; align-items:center;
    padding:9px 0; border-bottom:1px solid #f3f4f6;
}
.vi-stat-row:last-child { border-bottom:none; }
.vi-stat-lbl { font-size:.72rem; color:#9ca3af; font-weight:500; }
.vi-stat-val { font-size:.85rem; color:#111; font-weight:700; font-family:'DM Mono',monospace; }

/* ─── LOGIN ─── */
.vi-login-header { text-align:center; padding:32px 20px 16px; }
.vi-login-brand  { font-family:'Playfair Display',serif; font-size:2rem; font-weight:900; color:#8B0000; letter-spacing:.06em; }
.vi-login-sub    { font-size:.85rem; font-weight:500; color:#374151; margin-top:4px; }
.vi-login-hint   { font-size:.72rem; color:#9ca3af; margin-top:3px; }

/* ─── SECTION LABEL ─── */
.vi-section-lbl {
    font-size:.58rem; font-weight:700; color:#9ca3af;
    letter-spacing:.18em; text-transform:uppercase; margin-bottom:14px;
}

/* Scrollbar */
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(0,0,0,.15); border-radius:4px; }

/* Tab */
button[data-baseweb="tab"] { font-family:'Inter',sans-serif !important; font-size:.75rem !important; font-weight:600 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def avatar(nome: str, size: int = 44) -> str:
    cor = op_cor(nome)
    ini = op_iniciais(nome)
    fs  = max(12, size // 3)
    return (
        f'<div class="vi-op-avatar" '
        f'style="width:{size}px;height:{size}px;background:{cor};font-size:{fs}px;">'
        f'{ini}</div>'
    )


def stepper_html(etapa_atual: int) -> str:
    parts = []
    for i in range(3):
        cor  = ETAPA_CORES[i]["main"]
        icon = ETAPA_ICONS[i]
        lbl  = ETAPAS[i].upper()

        if i < etapa_atual:          # concluído
            circle = (f'<div class="vi-step-circle" '
                      f'style="background:{cor};border-color:{cor};color:#fff;font-size:1.1rem">✓</div>')
            label  = f'<div class="vi-step-label" style="color:{cor}">{lbl}</div>'
        elif i == etapa_atual:       # ativo
            circle = (f'<div class="vi-step-circle" '
                      f'style="background:{cor};border-color:{cor};color:#fff">{icon}</div>')
            label  = f'<div class="vi-step-label" style="color:{cor};font-weight:800">{lbl}</div>'
        else:                        # futuro
            circle = f'<div class="vi-step-circle">{icon}</div>'
            label  = f'<div class="vi-step-label">{lbl}</div>'

        parts.append(f'<div class="vi-step">{circle}{label}</div>')

        if i < 2:
            conn_cor = ETAPA_CORES[i]["main"] if i < etapa_atual else "#e5e7eb"
            parts.append(f'<div class="vi-step-connector" style="background:{conn_cor}"></div>')

    return f'<div class="vi-stepper">{"".join(parts)}</div>'


def card_header(operador: str, etapa_idx: int) -> str:
    cor  = ETAPA_CORES[etapa_idx]["main"]
    nome = ETAPAS[etapa_idx].upper()
    av   = avatar(operador, 44)
    return f"""
    <div class="vi-card-header" style="border-bottom-color:{cor}">
        {av}
        <div class="vi-card-header-info">
            <div class="vi-card-header-sub">Estação Central</div>
            <div class="vi-card-header-name">{operador}</div>
        </div>
        <div class="vi-etapa-badge" style="color:{cor};border-color:{cor}">{nome}</div>
    </div>
    """


def btn_class(etapa_idx: int) -> str:
    return ["vi-btn-blue", "vi-btn-purple", "vi-btn-green"][etapa_idx]


# ============================================================
# TELA DE SELEÇÃO DE OPERADOR
# ============================================================
def tela_selecao():
    st.markdown("""
    <div class="vi-login-header">
        <div class="vi-login-brand">VI LINGERIE</div>
        <div class="vi-login-sub">Apontamento de Produção</div>
        <div class="vi-login-hint">Selecione seu nome para começar</div>
    </div>
    """, unsafe_allow_html=True)

    selecionado = st.session_state.get("_op_sel")

    # Card com grade de operadores
    st.markdown('<div class="vi-card"><div class="vi-card-body">', unsafe_allow_html=True)
    st.markdown('<div class="vi-section-lbl">Quem é você?</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Grade fora do card (evita conflito HTML/widget)
    rows = [OPERADORES[i:i+3] for i in range(0, len(OPERADORES), 3)]
    for row in rows:
        cols = st.columns(len(row))
        for col, nome in zip(cols, row):
            with col:
                is_sel = selecionado == nome
                cor_av  = op_cor(nome)
                ini     = op_iniciais(nome)
                bg      = "#EFF6FF" if is_sel else "#f9fafb"
                borda   = "#1565C0" if is_sel else "transparent"
                st.markdown(f"""
                <div class="vi-op-face {'selected' if is_sel else ''}"
                     style="background:{bg};border-color:{borda}">
                    <div style="width:46px;height:46px;border-radius:50%;background:{cor_av};
                                display:flex;align-items:center;justify-content:center;
                                font-size:16px;font-weight:700;color:#fff;">{ini}</div>
                    <div class="vi-op-name">{nome.split()[0]}</div>
                </div>
                """, unsafe_allow_html=True)
                # Botão invisível sobreposto
                if st.button(f" ", key=f"op_{nome}", use_container_width=True):
                    st.session_state["_op_sel"] = nome
                    st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Feedback do selecionado
    if selecionado:
        st.markdown(f"""
        <div style="text-align:center;font-size:.78rem;color:#6b7280;margin-bottom:6px">
            Entrando como <strong style="color:#111">{selecionado}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
    if st.button("→  Entrar no sistema", use_container_width=True, key="btn_entrar"):
        if not selecionado:
            st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione seu nome antes de continuar.</div>', unsafe_allow_html=True)
        else:
            st.session_state.update({
                "_operador":    selecionado,
                "_turno_inicio": time.time(),
                "_state":       "idle",
                "_pedido":      None,
                "_etapa":       0,
                "_ts_inicio":   None,
                "_ts_fim":      None,
            })
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Link gerência
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="vi-btn-ghost">', unsafe_allow_html=True)
    if st.button("🔒  Acesso Gerência", use_container_width=True, key="btn_ger_link"):
        st.session_state["_modo"] = "gerencia"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)


# ============================================================
# TELA PRINCIPAL DO OPERADOR
# ============================================================
def tela_operador():
    operador  = st.session_state.get("_operador", "")
    state     = st.session_state.get("_state", "idle")
    pedido    = st.session_state.get("_pedido")
    etapa_idx = st.session_state.get("_etapa", 0)
    ts_inicio = st.session_state.get("_ts_inicio")

    cor       = ETAPA_CORES[etapa_idx]["main"]
    cor_light = ETAPA_CORES[etapa_idx]["light"]

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── HEADER CARD ──
    st.markdown(f'<div class="vi-card">{card_header(operador, etapa_idx)}</div>', unsafe_allow_html=True)

    # ── BOTÃO SAIR ──
    c_sair, _ = st.columns([1, 5])
    with c_sair:
        st.markdown('<div class="vi-btn-ghost">', unsafe_allow_html=True)
        if st.button("⏏ Sair", key="btn_sair_op"):
            for k in list(st.session_state.keys()):
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── CARD DE TRABALHO ──
    st.markdown('<div class="vi-card"><div class="vi-card-body">', unsafe_allow_html=True)
    st.markdown(stepper_html(etapa_idx), unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # ── CONTEÚDO POR STATE ──

    # ════ IDLE ════
    if state == "idle":
        st.markdown('<div class="vi-card"><div class="vi-card-body">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="vi-scan-area">
            <div class="vi-scan-icon">⬛</div>
            <div class="vi-scan-title">Bipar ou digitar pedido</div>
            <div class="vi-scan-hint">Insira o número do pedido para iniciar</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        if etapa_idx == 0:
            num = st.text_input("_", placeholder="Ex: 12345", key="inp_pedido", label_visibility="collapsed")
            col_inp, col_btn = st.columns([5, 1])
            with col_btn:
                st.markdown(f'<div class="{btn_class(etapa_idx)}">', unsafe_allow_html=True)
                if st.button("→", key="btn_ir", use_container_width=True):
                    n  = num.strip()
                    db = load_pedidos()
                    if not n:
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Informe o número.</div>', unsafe_allow_html=True)
                    elif n in db:
                        st.markdown(f'<div class="vi-alert vi-alert-err">⚠️ Pedido #{n} já em andamento.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["_pedido"] = n
                        st.session_state["_state"]  = "preview"
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        else:
            db          = load_pedidos()
            chave_op    = "op_emb" if etapa_idx == 1 else "op_conf"
            etapa_need  = 1 if etapa_idx == 1 else 2
            disponiveis = sorted([
                p for p, d in db.items()
                if d.get("etapa") == etapa_need and chave_op not in d
            ])
            if not disponiveis:
                st.markdown('<div class="vi-alert vi-alert-warn">⏳ Aguardando etapa anterior...</div>', unsafe_allow_html=True)
                st.markdown('<div class="vi-btn-outline">', unsafe_allow_html=True)
                if st.button("🔄 Atualizar", use_container_width=True, key="btn_refresh"):
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                sel = st.selectbox("Selecione o pedido", ["— Selecione —"] + disponiveis, key="sel_ped")
                st.markdown(f'<div class="{btn_class(etapa_idx)}" style="margin-top:8px">', unsafe_allow_html=True)
                if st.button("Confirmar →", use_container_width=True, key="btn_confirmar"):
                    if sel == "— Selecione —":
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["_pedido"] = sel
                        st.session_state["_state"]  = "preview"
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ════ PREVIEW ════
    elif state == "preview":
        st.markdown(f"""
        <div class="vi-card">
            <div class="vi-card-body" style="text-align:center;padding:28px 20px">
                <div class="vi-order-num"><span class="hash">#</span>{pedido}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="{btn_class(etapa_idx)}">', unsafe_allow_html=True)
        if st.button(f"▶  INICIAR {ETAPAS[etapa_idx].upper()}", use_container_width=True, key="btn_iniciar"):
            st.session_state["_state"]    = "running"
            st.session_state["_ts_inicio"] = time.time()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="vi-btn-outline">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True, key="btn_cancel_prev"):
            st.session_state["_state"]  = "idle"
            st.session_state["_pedido"] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ RUNNING ════
    elif state == "running":
        elapsed = fmt_tempo(time.time() - ts_inicio) if ts_inicio else "00:00:00"
        st.markdown(f"""
        <div class="vi-card">
            <div class="vi-card-body" style="text-align:center;padding:28px 20px 20px">
                <div class="vi-order-num"><span class="hash">#</span>{pedido}</div>
                <div class="vi-timer">⏱  {elapsed}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-btn-red">', unsafe_allow_html=True)
        if st.button(f"■  CONCLUIR {ETAPAS[etapa_idx].upper()}", use_container_width=True, key="btn_concluir"):
            _concluir_etapa(pedido, operador, etapa_idx)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="vi-btn-outline">', unsafe_allow_html=True)
        if st.button("✕ Cancelar", use_container_width=True, key="btn_cancel_run"):
            st.session_state.update({"_state": "idle", "_pedido": None, "_ts_inicio": None})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ════ ASK_NEXT ════
    elif state == "ask_next":
        ts_ini = st.session_state.get("_ts_inicio")
        ts_fim = st.session_state.get("_ts_fim")
        dur    = fmt_tempo((ts_fim - ts_ini) if ts_fim and ts_ini else 0)

        if etapa_idx == 2:
            # Concluído
            st.markdown(f"""
            <div class="vi-done-card">
                <div class="vi-done-emoji">🎉</div>
                <div class="vi-done-title">Pedido Concluído!</div>
                <div class="vi-done-num">#{pedido}</div>
                <div class="vi-done-meta">Todas as etapas finalizadas · {dur}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
            if st.button("▶  Novo Pedido", use_container_width=True, key="btn_novo"):
                st.session_state.update({
                    "_state": "idle", "_pedido": None,
                    "_ts_inicio": None, "_ts_fim": None, "_etapa": 0
                })
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            prox_idx   = etapa_idx + 1
            prox_nome  = ETAPAS[prox_idx]
            prox_cor   = ETAPA_CORES[prox_idx]["main"]
            prox_light = ETAPA_CORES[prox_idx]["light"]

            st.markdown(f"""
            <div class="vi-card">
                <div class="vi-card-body" style="text-align:center;padding:24px 20px 20px">
                    <div class="vi-order-num"><span class="hash">#</span>{pedido}</div>
                    <div style="font-size:.72rem;color:#9ca3af;margin-bottom:16px">✓ Etapa concluída em {dur}</div>
                    <div class="vi-ask-banner"
                         style="background:{prox_light};border-color:{prox_cor}55;color:{prox_cor}">
                        <div class="vi-ask-label">Etapa anterior concluída!</div>
                        <div class="vi-ask-question">Quem fará a {prox_nome}?</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            ask_mode = st.session_state.get("_ask_mode")
            c1, c2   = st.columns(2)
            bc        = btn_class(prox_idx)

            with c1:
                st.markdown(f'<div class="{bc}">', unsafe_allow_html=True)
                if st.button(f"👤  Eu mesmo\n({operador.split()[0]})", use_container_width=True, key="btn_mesmo"):
                    _avancar_etapa(etapa_idx, pedido, operador)
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="vi-btn-outline">', unsafe_allow_html=True)
                if st.button("👥  Outro\noperador", use_container_width=True, key="btn_outro"):
                    st.session_state["_ask_mode"] = "selecionando"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            if ask_mode == "selecionando":
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                outros = [op for op in OPERADORES if op != operador]
                outro  = st.selectbox("Selecione o operador", ["— Selecione —"] + outros, key="sel_outro_op")
                st.markdown(f'<div class="{bc}" style="margin-top:6px">', unsafe_allow_html=True)
                if st.button("▶  Confirmar e Iniciar", use_container_width=True, key="btn_conf_outro"):
                    if outro == "— Selecione —":
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione.</div>', unsafe_allow_html=True)
                    else:
                        _avancar_etapa(etapa_idx, pedido, outro)
                st.markdown('</div>', unsafe_allow_html=True)

    # ── RODAPÉ STATS ──
    hoje_str  = agora_str().split(" ")[0]
    historico = load_historico()
    hist_hoje = [h for h in historico if h.get("operador") == operador and h.get("data") == hoje_str]
    conc      = load_concluidos()
    conc_hoje = [c for c in conc if hoje_str in (c.get("dt_conf","") or "")]
    h_turno   = fmt_tempo(time.time() - st.session_state.get("_turno_inicio", time.time()))

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="vi-card">
        <div class="vi-card-body" style="padding:10px 20px">
            <div class="vi-stat-row">
                <span class="vi-stat-lbl">Operações hoje</span>
                <span class="vi-stat-val">{len(hist_hoje)}</span>
            </div>
            <div class="vi-stat-row">
                <span class="vi-stat-lbl">Concluídos hoje</span>
                <span class="vi-stat-val" style="color:#16a34a">{len(conc_hoje)}</span>
            </div>
            <div class="vi-stat-row">
                <span class="vi-stat-lbl">Tempo de turno</span>
                <span class="vi-stat-val">{h_turno}</span>
            </div>
        </div>
    </div>
    <div style="height:28px"></div>
    """, unsafe_allow_html=True)


def _concluir_etapa(pedido: str, operador: str, etapa_idx: int):
    now    = agora_str()
    ts_fim = time.time()
    db     = load_pedidos()

    if etapa_idx == 0:
        db[pedido] = {"pedido": pedido, "etapa": 1, "op_sep": operador, "dt_sep": now}
        reg_historico(pedido, operador, ETAPA_FULL[0], "em_andamento")

    elif etapa_idx == 1:
        if pedido in db:
            db[pedido]["etapa"]  = 2
            db[pedido]["op_emb"] = operador
            db[pedido]["dt_emb"] = now
            reg_historico(pedido, operador, ETAPA_FULL[1], "em_andamento")

    elif etapa_idx == 2:
        if pedido in db:
            db[pedido]["etapa"]   = 3
            db[pedido]["op_conf"] = operador
            db[pedido]["dt_conf"] = now
            conc = load_concluidos()
            conc.append(db[pedido])
            save_concluidos(conc)
            del db[pedido]
            reg_historico(pedido, operador, ETAPA_FULL[2], "concluido")

    save_pedidos(db)
    st.session_state["_ts_fim"] = ts_fim
    st.session_state["_state"]  = "ask_next"
    st.rerun()


def _avancar_etapa(etapa_atual: int, pedido: str, prox_operador: str):
    st.session_state.pop("_ask_mode", None)
    st.session_state.update({
        "_etapa":    etapa_atual + 1,
        "_state":    "preview",
        "_pedido":   pedido,
        "_operador": prox_operador,
        "_ts_inicio": None,
        "_ts_fim":   None,
    })
    st.rerun()


# ============================================================
# TELA LOGIN GERÊNCIA
# ============================================================
def tela_login_gerencia():
    st.markdown("<div style='height:50px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:20px">
        <div style="font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:900;color:#8B0000">
            VI LINGERIE
        </div>
        <div style="font-size:.82rem;color:#6b7280;margin-top:4px">Área Restrita — Gerência</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="vi-card"><div class="vi-card-body">', unsafe_allow_html=True)
    st.markdown('<div class="vi-section-lbl">Senha de acesso</div>', unsafe_allow_html=True)
    senha = st.text_input("_s", type="password", placeholder="••••••••", key="inp_senha", label_visibility="collapsed")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
    if st.button("🔓  Acessar Gerência", use_container_width=True, key="btn_ger_login"):
        if senha == SENHA_GERENCIA:
            st.session_state["_gerencia_ok"] = True
            st.rerun()
        else:
            st.markdown('<div class="vi-alert vi-alert-err">❌ Senha incorreta.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="vi-btn-outline">', unsafe_allow_html=True)
    if st.button("← Voltar", use_container_width=True, key="btn_voltar_ger"):
        st.session_state.pop("_modo", None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# TELA EXTRATO (GERÊNCIA)
# ============================================================
def tela_extrato():
    historico  = load_historico()
    concluidos = load_concluidos()
    pedidos_db = load_pedidos()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:16px">
        <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:900;color:#8B0000">
            VI LINGERIE
        </div>
        <div style="font-size:.78rem;color:#6b7280">Extrato de Produção</div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    total_sep  = len([h for h in historico if h.get("etapa") == ETAPA_FULL[0]])
    total_emb  = len([h for h in historico if h.get("etapa") == ETAPA_FULL[1]])
    total_conf = len([h for h in historico if h.get("etapa") == ETAPA_FULL[2]])
    total_conc = len(concluidos)

    st.markdown('<div class="vi-card"><div class="vi-card-body" style="padding:10px 20px">', unsafe_allow_html=True)
    for lbl, val, cor in [
        ("📦 Separações",   total_sep,  "#1565C0"),
        ("📬 Embalagens",   total_emb,  "#7B1FA2"),
        ("✅ Conferências", total_conf, "#1B5E20"),
        ("🎯 Concluídos",  total_conc, "#DC2626"),
    ]:
        st.markdown(f"""
        <div class="vi-stat-row">
            <span class="vi-stat-lbl">{lbl}</span>
            <span class="vi-stat-val" style="color:{cor}">{val}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    aba1, aba2, aba3 = st.tabs(["📅 Histórico", "📋 Concluídos", "⏳ Em Andamento"])

    with aba1:
        if not historico or not HAS_PANDAS:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação registrada.</div>', unsafe_allow_html=True)
        else:
            df = pd.DataFrame(historico)
            def parse_dt(s):
                try: return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
                except: return pd.NaT
            df["_dt"] = df["data"].apply(parse_dt)
            from datetime import date, timedelta as td
            hoje = date.today()
            c1, c2 = st.columns(2)
            with c1: d_ini = st.date_input("De", value=hoje - td(days=7), key="d_ini", format="DD/MM/YYYY")
            with c2: d_fim = st.date_input("Até", value=hoje, key="d_fim", format="DD/MM/YYYY")
            c3, c4 = st.columns(2)
            with c3:
                ops  = ["Todos"] + sorted(df["operador"].dropna().unique().tolist())
                op_f = st.selectbox("Funcionário", ops, key="op_f")
            with c4:
                et_f = st.selectbox("Etapa", ["Todas"] + ETAPA_FULL, key="et_f")

            mask = (df["_dt"] >= pd.Timestamp(d_ini)) & (df["_dt"] <= pd.Timestamp(d_fim))
            dff  = df[mask].copy()
            if op_f != "Todos":  dff = dff[dff["operador"] == op_f]
            if et_f != "Todas":  dff = dff[dff["etapa"] == et_f]
            dff  = dff.sort_values("data_hora", ascending=False)
            n    = len(dff)
            st.markdown(f'<div class="vi-alert vi-alert-inf">🔍 <b>{n}</b> operação(ões)</div>', unsafe_allow_html=True)
            if n > 0:
                if op_f == "Todos":
                    res = dff.groupby(["operador","etapa"]).size().reset_index(name="Qtd")
                    res.columns = ["Funcionário","Etapa","Qtd"]
                    st.dataframe(res, use_container_width=True, hide_index=True)
                df_s = dff[["data_hora","pedido","operador","etapa","status_pedido"]].rename(columns={
                    "data_hora":"Data/Hora","pedido":"Pedido",
                    "operador":"Funcionário","etapa":"Etapa","status_pedido":"Status"
                })
                df_s["Status"] = df_s["Status"].map({"em_andamento":"⏳","concluido":"✅"}).fillna(df_s["Status"])
                st.dataframe(df_s, use_container_width=True, hide_index=True)
                fname = f"extrato_{op_f.replace(' ','_')}_{d_ini.strftime('%d%m%Y')}_{d_fim.strftime('%d%m%Y')}"
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button("⬇️ CSV", df_s.to_csv(index=False).encode(), f"{fname}.csv", "text/csv", use_container_width=True, key="dl_csv")
                with col_b:
                    buf = BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w: df_s.to_excel(w, index=False)
                    buf.seek(0)
                    st.download_button("⬇️ Excel", buf.getvalue(), f"{fname}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True, key="dl_xlsx")

    with aba2:
        if concluidos and HAS_PANDAS:
            df_c = pd.DataFrame(concluidos).rename(columns={
                "pedido":"Pedido","op_sep":"Op.Sep","dt_sep":"Dt.Sep",
                "op_emb":"Op.Emb","dt_emb":"Dt.Emb","op_conf":"Op.Conf","dt_conf":"Dt.Conf"
            }).drop(columns=["etapa"], errors="ignore")
            st.dataframe(df_c, use_container_width=True, hide_index=True)
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button("⬇️ CSV", df_c.to_csv(index=False).encode(),
                    f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv", "text/csv",
                    use_container_width=True, key="dl_conc_csv")
            with col_b:
                buf2 = BytesIO()
                with pd.ExcelWriter(buf2, engine="openpyxl") as w: df_c.to_excel(w, index=False)
                buf2.seek(0)
                st.download_button("⬇️ Excel", buf2.getvalue(),
                    f"concluidos_{datetime.now().strftime('%d%m%Y')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl_conc_xlsx")
        else:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido finalizado ainda.</div>', unsafe_allow_html=True)

    with aba3:
        if pedidos_db:
            lbs = {1:"📬 Aguard. Embalagem", 2:"✅ Aguard. Conferência"}
            rows = [{"Pedido":f"#{p}","Etapa":lbs.get(d.get("etapa",0),"—"),
                     "Op.Sep":d.get("op_sep","—"),"Op.Emb":d.get("op_emb","—")}
                    for p, d in pedidos_db.items()]
            if HAS_PANDAS:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                for r in rows: st.write(r)
        else:
            st.markdown('<div class="vi-alert vi-alert-ok">✅ Nenhum pedido em andamento no momento.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="vi-btn-outline">', unsafe_allow_html=True)
    if st.button("← Sair da Gerência", use_container_width=True, key="btn_sair_ger"):
        st.session_state.pop("_modo", None)
        st.session_state.pop("_gerencia_ok", None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)


# ============================================================
# ROTEADOR PRINCIPAL
# ============================================================
modo = st.session_state.get("_modo")

if modo == "gerencia":
    if not st.session_state.get("_gerencia_ok"):
        tela_login_gerencia()
    else:
        tela_extrato()
elif "_operador" in st.session_state:
    tela_operador()
else:
    tela_selecao()
