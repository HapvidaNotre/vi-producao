import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import BytesIO

st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="centered",
    page_icon="🏭",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# CONFIGURAÇÕES GLOBAIS
# =============================================================================
ETAPAS = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_ICONS = ["📦", "📬", "✅"]
ETAPA_CORES = ["#1565C0", "#6A0DAD", "#1B5E20"]

OPERADORES = [
    "Lucivanio",
    "Enágio",
    "Daniel",
    "Ítalo",
    "Cildenir",
    "Samya",
    "Neide",
    "Eduardo",
    "Talyson",
]

SENHA_GERENCIA = "vi2026"

# =============================================================================
# PERSISTÊNCIA DE DADOS
# =============================================================================
STATE_DIR = "vi_producao_state"
os.makedirs(STATE_DIR, exist_ok=True)

FILE_PEDIDOS    = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS = os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO  = os.path.join(STATE_DIR, "historico.json")


def _carregar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def carregar_pedidos():
    return _carregar(FILE_PEDIDOS)


def salvar_pedidos(data):
    _salvar(FILE_PEDIDOS, data)


def carregar_concluidos():
    d = _carregar(FILE_CONCLUIDOS)
    return d if isinstance(d, list) else []


def salvar_concluidos(data):
    _salvar(FILE_CONCLUIDOS, data)


def carregar_historico():
    d = _carregar(FILE_HISTORICO)
    return d if isinstance(d, list) else []


def registrar_historico(pedido_num, operador, etapa_nome, data_hora, status_pedido="em_andamento"):
    hist = carregar_historico()
    hist.append({
        "data_hora":     data_hora,
        "data":          data_hora.split(" ")[0] if " " in data_hora else data_hora,
        "pedido":        pedido_num,
        "operador":      operador,
        "etapa":         etapa_nome,
        "status_pedido": status_pedido,
    })
    _salvar(FILE_HISTORICO, hist)


# =============================================================================
# HELPERS DE DATA/HORA
# =============================================================================
def agora_str():
    from datetime import timezone, timedelta
    br = timezone(timedelta(hours=-3))
    return datetime.now(br).strftime("%d/%m/%Y %H:%M")


# =============================================================================
# LOGO
# =============================================================================
import base64 as _b64


def _get_logo_b64():
    for p in ["logo_vi.png", "../logo_vi.png"]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return _b64.b64encode(f.read()).decode()
    return ""


_logo_b64 = _get_logo_b64()
_logo_src = f"data:image/png;base64,{_logo_b64}" if _logo_b64 else ""

if _logo_b64:
    logo_tag_dark  = f'<img src="{_logo_src}" style="height:48px;object-fit:contain;display:block;margin:0 auto 8px;filter:drop-shadow(0 3px 10px rgba(139,0,0,.5));" />'
    logo_tag_light = f'<img src="{_logo_src}" style="height:44px;object-fit:contain;display:block;" />'
else:
    logo_tag_dark  = '<div style="font-size:1.3rem;font-weight:900;color:#fff;letter-spacing:.1em;text-align:center;margin-bottom:8px">VI LINGERIE</div>'
    logo_tag_light = '<div style="font-size:1.2rem;font-weight:900;color:#1a2a4a;letter-spacing:.08em">VI LINGERIE</div>'

# =============================================================================
# CSS DARK (gerência + tela inicial)
# =============================================================================
CSS_DARK = f"""
<style id="css-dark">
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stApp"] {{
    font-family: 'DM Sans', sans-serif !important;
    background: #0b0b14 !important;
    color: #e8e8f0 !important;
    min-height: 100vh;
}}
[data-testid="stSidebar"] {{ display:none !important; }}
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {{ display:none !important; }}
.block-container {{ padding: 2rem 1.5rem !important; max-width: 560px !important; margin: 0 auto !important; }}

.vi-card {{
    background: linear-gradient(158deg, #13132a 0%, #0d0d1e 100%);
    border: 1px solid rgba(139,0,0,.45);
    border-radius: 20px;
    padding: 36px 32px 32px;
    position: relative; overflow: hidden;
    box-shadow: 0 20px 50px rgba(0,0,0,.7);
    animation: vi-fadein .5s cubic-bezier(.22,1,.36,1) both;
}}
@keyframes vi-fadein {{
    from {{ opacity:0; transform:translateY(18px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes vi-spin {{
    to {{ transform:rotate(360deg); }}
}}
@keyframes vi-pulse {{
    0%,100% {{ opacity:1; }} 50% {{ opacity:.5; }}
}}
@keyframes vi-shimmer {{
    from {{ transform:translateX(-120%); }}
    to   {{ transform:translateX(300%); }}
}}

.vi-loading {{
    position:fixed; inset:0;
    background:#0b0b14;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    z-index:9999;
}}
.vi-spinner {{
    width:48px; height:48px;
    border:3px solid rgba(139,0,0,.2);
    border-top-color:#dc2626;
    border-radius:50%;
    animation:vi-spin .8s linear infinite;
    margin:20px auto 14px;
}}
.vi-loading-text {{
    font-size:.82rem; font-weight:600;
    color:#9ca3af; letter-spacing:.12em;
    text-transform:uppercase;
    animation:vi-pulse 1.4s ease infinite;
}}

.vi-section-title {{
    font-size:.68rem; font-weight:700;
    color:#6b7280; letter-spacing:.14em;
    text-transform:uppercase;
    margin-bottom:16px;
    display:flex; align-items:center; gap:8px;
}}
.vi-section-title::before {{
    content:''; display:inline-block;
    width:20px; height:2px;
    background:#8B0000; border-radius:2px;
}}

.vi-div {{
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(139,0,0,.5),transparent);
    margin:20px 0;
}}

.vi-alert {{ padding:12px 16px; border-radius:10px; font-size:.82rem; font-weight:500; margin:12px 0; }}
.vi-alert-ok  {{ background:rgba(27,94,32,.25); border:1px solid rgba(76,175,80,.3); color:#a5d6a7; }}
.vi-alert-err {{ background:rgba(139,0,0,.2);   border:1px solid rgba(220,38,38,.35); color:#f87171; }}
.vi-alert-inf {{ background:rgba(21,101,192,.2); border:1px solid rgba(66,165,245,.3); color:#90caf9; }}

[data-testid="stTextInput"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stNumberInput"] label p {{
    color:#9ca3af !important; font-size:.7rem !important;
    font-weight:700 !important; letter-spacing:.08em !important;
    text-transform:uppercase !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
    background:rgba(255,255,255,.05) !important;
    border:1px solid rgba(139,0,0,.35) !important;
    border-radius:10px !important; color:#fff !important;
    font-family:'DM Mono',monospace !important; font-size:1rem !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background:rgba(255,255,255,.05) !important;
    border:1px solid rgba(139,0,0,.35) !important;
    border-radius:10px !important; color:#fff !important;
}}

.stButton > button {{
    background:linear-gradient(135deg,#7f1d1d 0%,#dc2626 100%) !important;
    border:none !important; border-radius:10px !important;
    color:#fff !important; font-weight:700 !important;
    font-size:.88rem !important; letter-spacing:.04em !important;
    padding:11px 20px !important;
    width:100%;
    transition:opacity .2s, transform .15s !important;
}}
.stButton > button:hover {{ opacity:.85 !important; transform:translateY(-1px) !important; }}
.stButton > button[kind="secondary"] {{
    background:rgba(255,255,255,.06) !important;
    border:1px solid rgba(255,255,255,.12) !important;
    color:#9ca3af !important;
}}
</style>
"""

# =============================================================================
# CSS LIGHT (operador)
# =============================================================================
CSS_LIGHT = """
<style id="css-light">
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stApp"] {
    font-family: 'DM Sans', sans-serif !important;
    background: #f0f2f5 !important;
    color: #1a2a4a !important;
    min-height: 100vh;
}
[data-testid="stSidebar"] { display:none !important; }
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display:none !important; }
.block-container { padding: 0 !important; max-width: 960px !important; margin: 0 auto !important; }

/* ── ANIMAÇÕES ── */
@keyframes vi-fadein  { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
@keyframes vi-spin    { to { transform:rotate(360deg); } }
@keyframes vi-pulse   { 0%,100% { opacity:1; } 50% { opacity:.5; } }
@keyframes vi-shimmer { from { transform:translateX(-120%); } to { transform:translateX(300%); } }

/* ── LOADING ── */
.vi-loading {
    position:fixed; inset:0;
    background:#f0f2f5;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    z-index:9999;
}
.vi-spinner {
    width:48px; height:48px;
    border:3px solid rgba(21,101,192,.15);
    border-top-color:#1565C0;
    border-radius:50%;
    animation:vi-spin .8s linear infinite;
    margin:20px auto 14px;
}
.vi-loading-text {
    font-size:.82rem; font-weight:700;
    color:#6b7280; letter-spacing:.12em;
    text-transform:uppercase;
    animation:vi-pulse 1.4s ease infinite;
}

/* ── HEADER AZUL ── */
.op-header {
    background: linear-gradient(135deg, #1a2a4a 0%, #1565C0 100%);
    padding: 16px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 20px rgba(21,101,192,.25);
    margin-bottom: 0;
    animation: vi-fadein .4s ease both;
}
.op-header-user {
    display: flex;
    align-items: center;
    gap: 14px;
}
.op-header-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
}
.op-header-role {
    font-size: .72rem;
    color: rgba(255,255,255,.65);
    margin-top: 2px;
}

/* ── AVATAR ── */
.op-avatar {
    width: 46px; height: 46px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 700; color: #fff;
    border: 2px solid rgba(255,255,255,.3);
    flex-shrink: 0;
}

/* ── MAIN CONTENT AREA ── */
.op-content {
    padding: 24px 28px;
}

/* ── CARD BRANCO ── */
.op-card {
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,.08);
    padding: 24px;
    margin-bottom: 16px;
    animation: vi-fadein .4s ease both;
}
.op-card-title {
    font-size: .7rem;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.op-card-title::before {
    content: '';
    display: inline-block;
    width: 16px; height: 3px;
    background: #1565C0;
    border-radius: 2px;
}

/* ── PEDIDO NÚMERO ── */
.op-pedido-num {
    font-family: 'DM Mono', monospace;
    font-size: 3rem;
    font-weight: 700;
    color: #1a2a4a;
    letter-spacing: .04em;
    text-align: center;
    line-height: 1;
    margin: 8px 0 4px;
}
.op-pedido-timer {
    text-align: center;
    font-family: 'DM Mono', monospace;
    font-size: 1rem;
    color: #1565C0;
    font-weight: 600;
    margin-bottom: 4px;
}

/* ── ETAPA BADGE ── */
.op-etapa-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: .72rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
}

/* ── RESUMO CARDS ── */
.op-resumo-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}
.op-resumo-item {
    background: #f8f9fc;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
}
.op-resumo-label {
    font-size: .6rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 6px;
}
.op-resumo-valor {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1a2a4a;
    font-family: 'DM Mono', monospace;
}

/* ── ÚLTIMO PEDIDO ── */
.op-ultimo {
    background: #f0f6ff;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 14px 18px;
    margin-top: 14px;
}
.op-ultimo-label {
    font-size: .62rem;
    font-weight: 700;
    color: #1565C0;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 8px;
}

/* ── ETAPA SELECTION ── */
.op-etapa-row {
    background: #f8f9fc;
    border: 1.5px solid #e5e7eb;
    border-radius: 14px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 10px;
    transition: border-color .2s, background .2s;
}
.op-etapa-row:hover {
    border-color: #1565C0;
    background: #eff6ff;
}

/* ── INPUTS LIGHT ── */
[data-testid="stTextInput"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stNumberInput"] label p {
    color: #6b7280 !important;
    font-size: .7rem !important;
    font-weight: 700 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: #f8f9fc !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 10px !important;
    color: #1a2a4a !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #1565C0 !important;
    box-shadow: 0 0 0 3px rgba(21,101,192,.12) !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #f8f9fc !important;
    border: 1.5px solid #d1d5db !important;
    border-radius: 10px !important;
    color: #1a2a4a !important;
}
[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #1565C0 !important;
    box-shadow: 0 0 0 3px rgba(21,101,192,.12) !important;
}
/* Texto do selectbox */
[data-testid="stSelectbox"] span,
[data-testid="stSelectbox"] p {
    color: #1a2a4a !important;
}

/* ── BOTÕES LIGHT ── */
/* Default = INICIAR (verde) */
.stButton > button {
    background: linear-gradient(135deg, #1B5E20 0%, #43a047 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: .92rem !important;
    letter-spacing: .04em !important;
    padding: 13px 20px !important;
    width: 100%;
    box-shadow: 0 4px 14px rgba(27,94,32,.3) !important;
    transition: opacity .2s, transform .15s !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }

/* Botão secundário = cinza */
.stButton > button[kind="secondary"] {
    background: #fff !important;
    border: 1.5px solid #d1d5db !important;
    color: #374151 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,.06) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #f3f4f6 !important;
    opacity: 1 !important;
}

/* Classe para FINALIZAR (vermelho) */
.btn-finalizar .stButton > button {
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%) !important;
    box-shadow: 0 4px 14px rgba(220,38,38,.3) !important;
}

/* Classe para INICIAR (verde) */
.btn-iniciar .stButton > button {
    background: linear-gradient(135deg, #1B5E20 0%, #43a047 100%) !important;
    box-shadow: 0 4px 14px rgba(27,94,32,.3) !important;
}

/* Trocar etapa / Cancelar */
.btn-neutro .stButton > button {
    background: #fff !important;
    border: 1.5px solid #d1d5db !important;
    color: #374151 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,.06) !important;
    font-size: .82rem !important;
}

/* Sair do sistema */
.btn-sair .stButton > button {
    background: #fff !important;
    border: 1.5px solid #e5e7eb !important;
    color: #6b7280 !important;
    box-shadow: none !important;
    font-size: .82rem !important;
}

/* ── ALERT ── */
.vi-alert { padding: 12px 16px; border-radius: 10px; font-size: .82rem; font-weight: 500; margin: 10px 0; }
.vi-alert-ok  { background: #f0fdf4; border: 1px solid #86efac; color: #166534; }
.vi-alert-err { background: #fef2f2; border: 1px solid #fca5a5; color: #991b1b; }
.vi-alert-inf { background: #eff6ff; border: 1px solid #93c5fd; color: #1e40af; }

/* ── DIVIDER ── */
.vi-div {
    height: 1px;
    background: #e5e7eb;
    margin: 16px 0;
}

/* ── TABS ── */
[data-testid="stTabs"] button {
    color: #6b7280 !important;
    font-weight: 600 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1565C0 !important;
    border-bottom-color: #1565C0 !important;
}

/* SECTION TITLE */
.vi-section-title {
    font-size: .68rem;
    font-weight: 700;
    color: #6b7280;
    letter-spacing: .14em;
    text-transform: uppercase;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.vi-section-title::before {
    content: '';
    display: inline-block;
    width: 16px; height: 3px;
    background: #1565C0;
    border-radius: 2px;
}
</style>
"""

# =============================================================================
# TELA DE LOADING
# =============================================================================
def tela_loading(mensagem="Carregando...", duracao=2.2, light=False):
    bg    = "#f0f2f5" if light else "#0b0b14"
    color = "#1565C0"  if light else "#dc2626"
    txt   = "#6b7280"  if light else "#9ca3af"
    if _logo_src:
        img = f'<img src="{_logo_src}" style="height:52px;object-fit:contain;" />'
    else:
        lc = "#1a2a4a" if light else "#fff"
        img = f'<div style="font-size:1.2rem;font-weight:900;color:{lc};letter-spacing:.1em">VI LINGERIE</div>'

    placeholder = st.empty()
    placeholder.markdown(f"""
    <div style="position:fixed;inset:0;background:{bg};display:flex;flex-direction:column;
        align-items:center;justify-content:center;z-index:9999;">
        {img}
        <div style="width:48px;height:48px;border:3px solid rgba(0,0,0,.08);
            border-top-color:{color};border-radius:50%;
            animation:vi-spin .8s linear infinite;margin:20px auto 14px;"></div>
        <div style="font-size:.82rem;font-weight:700;color:{txt};letter-spacing:.12em;
            text-transform:uppercase;">{mensagem}</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(duracao)
    placeholder.empty()


# =============================================================================
# SPLASH INICIAL
# =============================================================================
if "_splash_done" not in st.session_state:
    st.markdown(CSS_DARK, unsafe_allow_html=True)
    tela_loading("Iniciando sistema de produção", duracao=2.2)
    st.session_state["_splash_done"] = True


# =============================================================================
# TELA DE LOGIN DA GERÊNCIA
# =============================================================================
def tela_login_gerencia():
    st.markdown(CSS_DARK, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="vi-card" style="max-width:400px;margin:60px auto 0;">
        <div style="text-align:center;margin-bottom:4px">{logo_tag_dark}</div>
        <div style="text-align:center;margin-bottom:6px">
            <span style="font-size:.65rem;font-weight:700;color:#f87171;
                letter-spacing:.14em;text-transform:uppercase;
                background:rgba(139,0,0,.15);border:1px solid rgba(139,0,0,.4);
                padding:3px 12px;border-radius:20px;">
                🔒 Área da Gerência
            </span>
        </div>
        <div class="vi-div"></div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 5, 1])
    with col_c:
        senha = st.text_input("Senha de gerência", type="password", placeholder="••••••••")
        if st.button("🔓 Acessar", use_container_width=True):
            if senha == SENHA_GERENCIA:
                st.session_state["_gerencia_ok"] = True
                st.rerun()
            else:
                st.markdown('<div class="vi-alert vi-alert-err">❌ Senha incorreta.</div>', unsafe_allow_html=True)
        st.markdown("")
        if st.button("← Voltar", use_container_width=True, type="secondary"):
            st.session_state.pop("_modo", None)
            st.rerun()


# =============================================================================
# TELA DE EXTRATO GERENCIAL
# =============================================================================
def tela_extrato():
    st.markdown(CSS_DARK, unsafe_allow_html=True)
    concluidos        = carregar_concluidos()
    pedidos_andamento = carregar_pedidos()
    historico         = carregar_historico()

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:20px">
        {logo_tag_dark}
        <div style="font-size:1.1rem;font-weight:700;color:#fff;margin-top:4px">Extrato de Produção</div>
        <div style="font-size:.75rem;color:#9ca3af;margin-top:2px">Consulta, filtros e download por data e funcionário</div>
    </div>
    """, unsafe_allow_html=True)

    total_op_sep  = len([h for h in historico if h.get("etapa") == "Separação do Pedido"])
    total_op_emb  = len([h for h in historico if h.get("etapa") == "Mesa de Embalagem"])
    total_op_conf = len([h for h in historico if h.get("etapa") == "Conferência do Pedido"])
    total_conc    = len(concluidos)

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, cor, bg, border in [
        (c1, "📦 Separações",   total_op_sep,  "#64b5f6", "rgba(21,101,192,.2)",  "rgba(66,165,245,.25)"),
        (c2, "📬 Embalagens",   total_op_emb,  "#ce93d8", "rgba(106,13,173,.2)",  "rgba(171,71,188,.25)"),
        (c3, "✅ Conferências", total_op_conf, "#a5d6a7", "rgba(27,94,32,.2)",    "rgba(76,175,80,.25)"),
        (c4, "🎯 Concluídos",   total_conc,    "#f87171", "rgba(127,29,29,.2)",   "rgba(239,68,68,.25)"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:12px;
                padding:12px 8px;text-align:center;">
                <div style="font-size:.58rem;color:#9ca3af;text-transform:uppercase;
                    letter-spacing:.07em;font-weight:700;margin-bottom:3px">{label}</div>
                <div style="font-size:1.7rem;font-weight:700;color:{cor}">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

    aba1, aba2, aba3 = st.tabs(["📅 Histórico Completo", "📋 Pedidos Concluídos", "⏳ Em Andamento"])

    with aba1:
        st.markdown('<div class="vi-section-title" style="margin-top:16px">🔍 Filtros de Consulta</div>', unsafe_allow_html=True)
        if not historico:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação registrada ainda.</div>', unsafe_allow_html=True)
        else:
            df_hist = pd.DataFrame(historico)
            def parse_data(s):
                try:
                    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
                except Exception:
                    return pd.NaT
            df_hist["_data_dt"] = df_hist["data"].apply(parse_data)

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                from datetime import date, timedelta as td
                hoje = date.today()
                data_ini = st.date_input("📅 Data inicial", value=hoje - td(days=7), key="dt_ini", format="DD/MM/YYYY")
            with col_f2:
                data_fim = st.date_input("📅 Data final", value=hoje, key="dt_fim", format="DD/MM/YYYY")

            col_f3, col_f4 = st.columns(2)
            with col_f3:
                ops_lista = ["Todos"] + sorted(df_hist["operador"].dropna().unique().tolist())
                op_filtro = st.selectbox("👤 Funcionário", options=ops_lista, key="hist_op")
            with col_f4:
                etapas_lista = ["Todas"] + ETAPAS
                etapa_filtro = st.selectbox("⚙️ Etapa", options=etapas_lista, key="hist_etapa")

            mask = (
                (df_hist["_data_dt"] >= pd.Timestamp(data_ini)) &
                (df_hist["_data_dt"] <= pd.Timestamp(data_fim))
            )
            df_filtrado = df_hist[mask].copy()
            if op_filtro != "Todos":
                df_filtrado = df_filtrado[df_filtrado["operador"] == op_filtro]
            if etapa_filtro != "Todas":
                df_filtrado = df_filtrado[df_filtrado["etapa"] == etapa_filtro]
            df_filtrado = df_filtrado.sort_values("data_hora", ascending=False)

            st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)
            n_res = len(df_filtrado)
            periodo_txt = f"{data_ini.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
            op_txt = op_filtro if op_filtro != "Todos" else "todos os funcionários"
            etapa_txt = etapa_filtro if etapa_filtro != "Todas" else "todas as etapas"

            st.markdown(f"""
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
                border-radius:12px;padding:14px 18px;margin-bottom:16px;">
                <div style="font-size:.7rem;color:#9ca3af;margin-bottom:6px;text-transform:uppercase;letter-spacing:.08em;font-weight:700">Resultado da consulta</div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center;">
                    <div style="font-size:.82rem;color:#fff">📅 <b>{periodo_txt}</b></div>
                    <div style="font-size:.82rem;color:#f87171">👤 <b>{op_txt}</b></div>
                    <div style="font-size:.82rem;color:#90caf9">⚙️ <b>{etapa_txt}</b></div>
                    <div style="font-size:.82rem;color:#a5d6a7;margin-left:auto;font-weight:700">{n_res} operação(ões)</div>
                </div>
            </div>""", unsafe_allow_html=True)

            if n_res == 0:
                st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação encontrada para os filtros selecionados.</div>', unsafe_allow_html=True)
            else:
                if op_filtro == "Todos":
                    resumo = df_filtrado.groupby(["operador", "etapa"]).size().reset_index(name="qtd")
                    resumo.columns = ["Funcionário", "Etapa", "Qtd. Operações"]
                    st.markdown('<div class="vi-section-title">📊 Resumo por Funcionário no Período</div>', unsafe_allow_html=True)
                    st.dataframe(resumo, use_container_width=True, hide_index=True)
                    st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

                st.markdown('<div class="vi-section-title">📋 Detalhamento das Operações</div>', unsafe_allow_html=True)
                df_exib = df_filtrado[["data_hora","pedido","operador","etapa","status_pedido"]].rename(columns={
                    "data_hora": "Data / Hora", "pedido": "Pedido",
                    "operador": "Funcionário", "etapa": "Etapa", "status_pedido": "Status",
                })
                df_exib["Status"] = df_exib["Status"].map(
                    {"em_andamento": "⏳ Em andamento", "concluido": "✅ Concluído"}
                ).fillna(df_exib["Status"])
                st.dataframe(df_exib, use_container_width=True, hide_index=True)

                st.markdown("")
                st.markdown('<div class="vi-section-title">⬇️ Baixar Extrato</div>', unsafe_allow_html=True)
                nome_arquivo = f"extrato_{op_filtro.replace(' ','_')}_{data_ini.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button("⬇️ Baixar CSV", data=df_exib.to_csv(index=False).encode("utf-8"),
                        file_name=f"{nome_arquivo}.csv", mime="text/csv",
                        use_container_width=True, key="dl_hist_csv")
                with col_dl2:
                    xlsx_buf = BytesIO()
                    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                        df_exib.to_excel(writer, index=False, sheet_name="Detalhado")
                        if op_filtro == "Todos":
                            resumo.to_excel(writer, index=False, sheet_name="Resumo por Funcionário")
                    xlsx_buf.seek(0)
                    st.download_button("⬇️ Baixar Excel", data=xlsx_buf.getvalue(),
                        file_name=f"{nome_arquivo}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True, key="dl_hist_xlsx")

    with aba2:
        st.markdown('<div class="vi-section-title" style="margin-top:16px">Pedidos Finalizados nas 3 Etapas</div>', unsafe_allow_html=True)
        if concluidos:
            df_conc = pd.DataFrame(concluidos)
            df_show = df_conc.rename(columns={
                "pedido": "Pedido",
                "op_sep": "Op. Separação",   "dt_sep": "Data Separação",
                "op_emb": "Op. Embalagem",   "dt_emb": "Data Embalagem",
                "op_conf": "Op. Conferência","dt_conf": "Data Conferência",
            }).drop(columns=["etapa"], errors="ignore")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            st.markdown("")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.download_button("⬇️ Baixar CSV", data=df_show.to_csv(index=False).encode("utf-8"),
                    file_name=f"pedidos_concluidos_{datetime.now().strftime('%d%m%Y_%H%M')}.csv",
                    mime="text/csv", use_container_width=True, key="dl_conc_csv")
            with col_c2:
                xlsx_buf2 = BytesIO()
                with pd.ExcelWriter(xlsx_buf2, engine="openpyxl") as writer:
                    df_show.to_excel(writer, index=False, sheet_name="Concluídos")
                xlsx_buf2.seek(0)
                st.download_button("⬇️ Baixar Excel", data=xlsx_buf2.getvalue(),
                    file_name=f"pedidos_concluidos_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="dl_conc_xlsx")
        else:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido finalizado ainda.</div>', unsafe_allow_html=True)

    with aba3:
        st.markdown('<div class="vi-section-title" style="margin-top:16px">Pedidos em Andamento</div>', unsafe_allow_html=True)
        if pedidos_andamento:
            etapa_labels = {1: "⏳ Aguardando Embalagem", 2: "⏳ Aguardando Conferência"}
            rows = []
            for p in pedidos_andamento.values():
                rows.append({
                    "Pedido": f"#{p['pedido']}",
                    "Etapa Atual": etapa_labels.get(p.get("etapa", 0), "—"),
                    "Op. Separação": p.get("op_sep", "—"),
                    "Data Separação": p.get("dt_sep", "—"),
                    "Op. Embalagem": p.get("op_emb", "—"),
                    "Data Embalagem": p.get("dt_emb", "—"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="vi-alert vi-alert-ok">✅ Nenhum pedido em andamento no momento.</div>', unsafe_allow_html=True)

    st.markdown("")
    if st.button("← Sair da Gerência", use_container_width=True, type="secondary"):
        st.session_state.pop("_modo", None)
        st.session_state.pop("_gerencia_ok", None)
        st.rerun()


# =============================================================================
# HELPERS VISUAIS
# =============================================================================
def avatar_html_light(nome, size=46):
    partes = nome.strip().split()
    iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
    cores = ["#1565C0","#7B1FA2","#2E7D32","#E65100","#C62828","#00695C","#37474F","#4527A0"]
    cor = cores[sum(ord(c) for c in nome) % len(cores)]
    return f"""<div class="op-avatar" style="background:{cor};width:{size}px;height:{size}px;font-size:{int(size*.36)}px;">{iniciais}</div>"""


def fmt_tempo(segundos):
    if segundos is None or segundos < 0:
        return "--:--:--"
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# =============================================================================
# FLUXO PRINCIPAL DO OPERADOR (LIGHT)
# =============================================================================
def tela_operador():
    import time as _time

    # Inject light CSS
    st.markdown(CSS_LIGHT, unsafe_allow_html=True)

    pedidos   = carregar_pedidos()
    historico = carregar_historico()

    # ══════════════════════════════════════════════════════════════════
    # TELA 1 — IDENTIFICAÇÃO
    # ══════════════════════════════════════════════════════════════════
    if "_operador" not in st.session_state:
        # Header azul
        if _logo_src:
            logo_h = f'<img src="{_logo_src}" style="height:38px;object-fit:contain;filter:brightness(0) invert(1);" />'
        else:
            logo_h = '<span style="font-size:1.1rem;font-weight:900;color:#fff;letter-spacing:.08em">VI LINGERIE</span>'

        st.markdown(f"""
        <div class="op-header" style="border-radius:0 0 20px 20px;margin-bottom:28px">
            <div style="font-size:1.1rem;font-weight:700;color:#fff">🏭 Apontamento de Produção</div>
            {logo_h}
        </div>
        """, unsafe_allow_html=True)

        col_l, col_c, col_r = st.columns([1, 4, 1])
        with col_c:
            st.markdown("""
            <div class="op-card">
                <div class="op-card-title">👤 Identificação do Operador</div>
            """, unsafe_allow_html=True)

            operador = st.selectbox("Selecione seu nome", options=["— Selecione —"] + OPERADORES,
                                    key="sel_operador", label_visibility="collapsed")
            st.markdown("")
            if st.button("▶  Entrar no sistema", use_container_width=True):
                if operador == "— Selecione —":
                    st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione seu nome.</div>', unsafe_allow_html=True)
                else:
                    st.session_state["_operador"] = operador
                    st.session_state["_turno_inicio"] = _time.time()
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
        return

    operador     = st.session_state["_operador"]
    turno_inicio = st.session_state.get("_turno_inicio", _time.time())

    hoje_str   = agora_str().split(" ")[0]
    hist_hoje  = [h for h in historico if h.get("operador") == operador and h.get("data") == hoje_str]
    pedidos_hoje = len(hist_hoje)

    ultimo_inicio = st.session_state.get("_ultimo_inicio")
    ultimo_fim    = st.session_state.get("_ultimo_fim")
    ultimo_pedido = st.session_state.get("_ultimo_pedido_num")
    tempo_turno   = _time.time() - turno_inicio

    # ══════════════════════════════════════════════════════════════════
    # HEADER LIGHT
    # ══════════════════════════════════════════════════════════════════
    etapa_idx  = st.session_state.get("_etapa_idx")
    etapa_nome = ETAPAS[etapa_idx] if etapa_idx is not None else "—"
    etapa_icon = ETAPA_ICONS[etapa_idx] if etapa_idx is not None else ""
    etapa_cor  = ["#1565C0","#6A0DAD","#1B5E20"][etapa_idx] if etapa_idx is not None else "#1a2a4a"

    if _logo_src:
        logo_h = f'<img src="{_logo_src}" style="height:36px;object-fit:contain;filter:brightness(0) invert(1);" />'
    else:
        logo_h = '<span style="font-size:1rem;font-weight:900;color:#fff;letter-spacing:.08em">VI LINGERIE</span>'

    etapa_pill = (
        f'<span style="background:{etapa_cor}33;border:1px solid {etapa_cor}88;color:#fff;'
        f'padding:3px 10px;border-radius:20px;font-size:.68rem;font-weight:700;'
        f'letter-spacing:.06em;text-transform:uppercase;margin-top:4px;display:inline-block;">'
        f'{etapa_icon} {etapa_nome}</span>'
    ) if etapa_idx is not None else ""

    st.markdown(f"""
    <div class="op-header" style="border-radius:0 0 20px 20px;">
        <div class="op-header-user">
            {avatar_html_light(operador, 46)}
            <div>
                <div class="op-header-name">{operador}</div>
                {etapa_pill if etapa_idx is not None else '<div class="op-header-role">Selecione a operação</div>'}
            </div>
        </div>
        {logo_h}
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # TELA 2 — SELECIONAR ETAPA
    # ══════════════════════════════════════════════════════════════════
    if etapa_idx is None:
        st.markdown('<div style="padding: 20px 24px;">', unsafe_allow_html=True)

        # Resumo diário
        h_turno  = fmt_tempo(tempo_turno)
        h_inicio = datetime.fromtimestamp(turno_inicio).strftime("%H:%M")

        st.markdown(f"""
        <div class="op-card">
            <div class="op-card-title">📊 Resumo do Dia</div>
            <div class="op-resumo-grid">
                <div class="op-resumo-item">
                    <div class="op-resumo-label">Pedidos feitos</div>
                    <div class="op-resumo-valor" style="color:#1B5E20">{pedidos_hoje}</div>
                </div>
                <div class="op-resumo-item">
                    <div class="op-resumo-label">Hora de início</div>
                    <div class="op-resumo-valor" style="font-size:1.2rem">{h_inicio}</div>
                </div>
                <div class="op-resumo-item">
                    <div class="op-resumo-label">Tempo no turno</div>
                    <div class="op-resumo-valor" style="font-size:1rem">{h_turno}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if ultimo_pedido and ultimo_inicio and ultimo_fim:
            dur = ultimo_fim - ultimo_inicio
            st.markdown(f"""
            <div class="op-ultimo">
                <div class="op-ultimo-label">⏱ Último pedido — #{ultimo_pedido}</div>
                <div style="display:flex;gap:24px;flex-wrap:wrap">
                    <div><span style="font-size:.7rem;color:#6b7280">Início: </span>
                         <span style="font-family:'DM Mono',monospace;color:#1a2a4a;font-size:.85rem;font-weight:600">
                         {datetime.fromtimestamp(ultimo_inicio).strftime('%H:%M:%S')}</span></div>
                    <div><span style="font-size:.7rem;color:#6b7280">Fim: </span>
                         <span style="font-family:'DM Mono',monospace;color:#1a2a4a;font-size:.85rem;font-weight:600">
                         {datetime.fromtimestamp(ultimo_fim).strftime('%H:%M:%S')}</span></div>
                    <div><span style="font-size:.7rem;color:#6b7280">Duração: </span>
                         <span style="font-family:'DM Mono',monospace;color:#dc2626;font-weight:700;font-size:.85rem">
                         {fmt_tempo(dur)}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Seleção de etapa
        st.markdown("""
        <div class="op-card">
            <div class="op-card-title">⚙️ Qual operação você vai realizar?</div>
        """, unsafe_allow_html=True)

        for idx, (etapa, icon, cor) in enumerate(zip(ETAPAS, ETAPA_ICONS, ETAPA_CORES)):
            if idx == 0:
                n_disp = None
            elif idx == 1:
                n_disp = sum(1 for p, d in pedidos.items() if d.get("etapa") == 1 and "op_emb" not in d)
            else:
                n_disp = sum(1 for p, d in pedidos.items() if d.get("etapa") == 2 and "op_conf" not in d)

            badge = (
                f'<span style="background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;'
                f'padding:2px 8px;border-radius:8px;font-size:.62rem;font-weight:700">'
                f'{n_disp} disponível(is)</span>'
            ) if n_disp is not None else ""

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div class="op-etapa-row">
                    <div style="font-size:1.8rem">{icon}</div>
                    <div>
                        <div style="font-size:.92rem;font-weight:700;color:#1a2a4a">{etapa}</div>
                        <div style="font-size:.68rem;color:#6b7280;margin-top:3px">
                            Etapa {idx+1} de 3 &nbsp;{badge}
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if st.button("Selecionar", key=f"btn_etapa_{idx}", use_container_width=True):
                    st.session_state["_etapa_idx"] = idx
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)
        st.markdown('<div class="btn-sair">', unsafe_allow_html=True)
        col_tc, col_sa = st.columns(2)
        with col_tc:
            if st.button("← Trocar operador", use_container_width=True, type="secondary"):
                for k in ["_operador","_turno_inicio","_etapa_idx","_pedido_atual",
                          "_pedido_iniciado","_ts_inicio","_ultimo_inicio","_ultimo_fim","_ultimo_pedido_num"]:
                    st.session_state.pop(k, None)
                st.rerun()
        with col_sa:
            if st.button("⏏  Sair do sistema", use_container_width=True, type="secondary"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ══════════════════════════════════════════════════════════════════
    # TELA 3 — PAINEL DE OPERAÇÃO
    # ══════════════════════════════════════════════════════════════════
    pedido_atual    = st.session_state.get("_pedido_atual")
    pedido_iniciado = st.session_state.get("_pedido_iniciado", False)
    ts_inicio       = st.session_state.get("_ts_inicio")

    st.markdown('<div style="padding: 20px 24px;">', unsafe_allow_html=True)

    # ── ÁREA DO PEDIDO ────────────────────────────────────────────────
    if not pedido_atual:
        st.markdown("""
        <div class="op-card">
            <div class="op-card-title">🔢 Número do Pedido</div>
        """, unsafe_allow_html=True)

        if etapa_idx == 0:
            num = st.text_input("", placeholder="Ex: 49822", key="inp_num", label_visibility="collapsed")
            st.markdown("")
            col_ini, col_tro = st.columns([3, 1])
            with col_ini:
                st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
                if st.button("▶  INICIAR PEDIDO", use_container_width=True, key="btn_iniciar"):
                    num = num.strip()
                    if not num:
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Informe o número do pedido.</div>', unsafe_allow_html=True)
                    elif num in pedidos:
                        st.markdown(f'<div class="vi-alert vi-alert-err">⚠️ Pedido #{num} já foi registrado.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["_pedido_atual"]    = num
                        st.session_state["_pedido_iniciado"] = True
                        st.session_state["_ts_inicio"]       = _time.time()
                        tela_loading("Cadastrando pedido...", duracao=1.2, light=True)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col_tro:
                st.markdown('<div class="btn-neutro">', unsafe_allow_html=True)
                if st.button("Trocar etapa", use_container_width=True, type="secondary", key="btn_tro_etapa"):
                    st.session_state.pop("_etapa_idx", None)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            if etapa_idx == 1:
                disponiveis = sorted([p for p, d in pedidos.items() if d.get("etapa") == 1 and "op_emb" not in d])
            else:
                disponiveis = sorted([p for p, d in pedidos.items() if d.get("etapa") == 2 and "op_conf" not in d])

            if not disponiveis:
                st.markdown(f'<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido disponível. Aguarde: <b>{ETAPAS[etapa_idx-1]}</b>.</div>', unsafe_allow_html=True)
            else:
                pedido_sel = st.selectbox("", options=["— Selecione um pedido —"] + disponiveis,
                                          key=f"sel_ped_{etapa_idx}", label_visibility="collapsed")
                st.markdown("")
                col_ini2, col_tro2 = st.columns([3, 1])
                with col_ini2:
                    st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
                    if st.button("▶  INICIAR PEDIDO", use_container_width=True, key="btn_iniciar2"):
                        if pedido_sel == "— Selecione um pedido —":
                            st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                        else:
                            st.session_state["_pedido_atual"]    = pedido_sel
                            st.session_state["_pedido_iniciado"] = True
                            st.session_state["_ts_inicio"]       = _time.time()
                            tela_loading("Cadastrando pedido...", duracao=1.2, light=True)
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with col_tro2:
                    st.markdown('<div class="btn-neutro">', unsafe_allow_html=True)
                    if st.button("Trocar etapa", use_container_width=True, type="secondary", key="btn_tro_etapa2"):
                        st.session_state.pop("_etapa_idx", None)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # ── PEDIDO EM ANDAMENTO ──────────────────────────────────────
        elapsed = fmt_tempo(_time.time() - ts_inicio) if ts_inicio else "--:--:--"
        etapa_bg = ["#eff6ff","#faf5ff","#f0fdf4"][etapa_idx]
        etapa_border = ["#bfdbfe","#e9d5ff","#86efac"][etapa_idx]
        etapa_text   = ["#1e40af","#6b21a8","#14532d"][etapa_idx]

        st.markdown(f"""
        <div class="op-card" style="text-align:center;border:2px solid {etapa_border};background:{etapa_bg};">
            <div style="font-size:.62rem;font-weight:700;color:#9ca3af;letter-spacing:.12em;
                text-transform:uppercase;margin-bottom:8px;">Pedido em Operação</div>
            <div class="op-pedido-num">#{pedido_atual}</div>
            <div style="margin:10px 0 6px">
                <span style="background:{etapa_cor}22;border:1px solid {etapa_cor}55;
                    color:{etapa_text};padding:5px 16px;border-radius:20px;
                    font-size:.74rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;">
                    {etapa_icon} {etapa_nome}
                </span>
            </div>
            <div class="op-pedido-timer">⏱ {elapsed}</div>
        </div>
        """, unsafe_allow_html=True)

        col_fin, col_can = st.columns([3, 1])
        with col_fin:
            st.markdown('<div class="btn-finalizar">', unsafe_allow_html=True)
            if st.button("⏹  FINALIZAR PEDIDO", use_container_width=True, key="btn_finalizar"):
                now    = agora_str()
                ts_fim = _time.time()
                pedidos_db = carregar_pedidos()

                if etapa_idx == 0:
                    pedidos_db[pedido_atual] = {
                        "pedido": pedido_atual, "etapa": 1,
                        "op_sep": operador, "dt_sep": now,
                    }
                    registrar_historico(pedido_atual, operador, "Separação do Pedido", now, "em_andamento")
                elif etapa_idx == 1:
                    if pedido_atual in pedidos_db:
                        pedidos_db[pedido_atual]["etapa"]  = 2
                        pedidos_db[pedido_atual]["op_emb"] = operador
                        pedidos_db[pedido_atual]["dt_emb"] = now
                        registrar_historico(pedido_atual, operador, "Mesa de Embalagem", now, "em_andamento")
                else:
                    if pedido_atual in pedidos_db:
                        pedidos_db[pedido_atual]["etapa"]   = 3
                        pedidos_db[pedido_atual]["op_conf"] = operador
                        pedidos_db[pedido_atual]["dt_conf"] = now
                        conc = carregar_concluidos()
                        conc.append(pedidos_db[pedido_atual])
                        salvar_concluidos(conc)
                        del pedidos_db[pedido_atual]
                        registrar_historico(pedido_atual, operador, "Conferência do Pedido", now, "concluido")

                salvar_pedidos(pedidos_db)
                st.session_state["_ultimo_inicio"]     = ts_inicio
                st.session_state["_ultimo_fim"]        = ts_fim
                st.session_state["_ultimo_pedido_num"] = pedido_atual

                for k in ["_pedido_atual","_pedido_iniciado","_ts_inicio","_etapa_idx"]:
                    st.session_state.pop(k, None)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_can:
            st.markdown('<div class="btn-neutro">', unsafe_allow_html=True)
            if st.button("Cancelar", use_container_width=True, type="secondary", key="btn_cancelar"):
                for k in ["_pedido_atual","_pedido_iniciado","_ts_inicio"]:
                    st.session_state.pop(k, None)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── RESUMO DIÁRIO ────────────────────────────────────────────────
    h_turno  = fmt_tempo(_time.time() - turno_inicio)
    h_inicio = datetime.fromtimestamp(turno_inicio).strftime("%H:%M")

    st.markdown(f"""
    <div class="op-card">
        <div class="op-card-title">📊 Resumo do Dia</div>
        <div class="op-resumo-grid">
            <div class="op-resumo-item">
                <div class="op-resumo-label">Pedidos feitos</div>
                <div class="op-resumo-valor" style="color:#1B5E20">{pedidos_hoje}</div>
            </div>
            <div class="op-resumo-item">
                <div class="op-resumo-label">Hora de início</div>
                <div class="op-resumo-valor" style="font-size:1.2rem">{h_inicio}</div>
            </div>
            <div class="op-resumo-item">
                <div class="op-resumo-label">Tempo no turno</div>
                <div class="op-resumo-valor" style="font-size:1rem">{h_turno}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if ultimo_pedido and ultimo_inicio and ultimo_fim:
        dur = ultimo_fim - ultimo_inicio
        st.markdown(f"""
        <div class="op-ultimo">
            <div class="op-ultimo-label">⏱ Último pedido — #{ultimo_pedido}</div>
            <div style="display:flex;gap:24px;flex-wrap:wrap">
                <div><span style="font-size:.7rem;color:#6b7280">Início: </span>
                     <span style="font-family:'DM Mono',monospace;color:#1a2a4a;font-size:.85rem;font-weight:600">
                     {datetime.fromtimestamp(ultimo_inicio).strftime('%H:%M:%S')}</span></div>
                <div><span style="font-size:.7rem;color:#6b7280">Fim: </span>
                     <span style="font-family:'DM Mono',monospace;color:#1a2a4a;font-size:.85rem;font-weight:600">
                     {datetime.fromtimestamp(ultimo_fim).strftime('%H:%M:%S')}</span></div>
                <div><span style="font-size:.7rem;color:#6b7280">Duração: </span>
                     <span style="font-family:'DM Mono',monospace;color:#dc2626;font-weight:700;font-size:.85rem">
                     {fmt_tempo(dur)}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # fecha padding div


# =============================================================================
# TELA INICIAL (dark)
# =============================================================================
if "_modo" not in st.session_state:
    st.markdown(CSS_DARK, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center;padding:40px 0 28px">
        {logo_tag_dark}
        <div style="font-size:1.05rem;font-weight:700;color:#fff;margin-top:6px">Sistema de Produção</div>
        <div style="font-size:.75rem;color:#6b7280;margin-top:3px">Vi Lingerie — Linha de Montagem</div>
    </div>
    <div class="vi-div"></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="vi-section-title">🚀 Como deseja acessar?</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
            border-radius:14px;padding:20px;text-align:center;margin-bottom:12px">
            <div style="font-size:2rem">🏭</div>
            <div style="font-size:.88rem;font-weight:700;color:#fff;margin-top:8px">Operador</div>
            <div style="font-size:.68rem;color:#9ca3af;margin-top:4px">Registrar etapas de produção</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Entrar como Operador", use_container_width=True, key="btn_op"):
            st.session_state["_modo"] = "operador"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
            border-radius:14px;padding:20px;text-align:center;margin-bottom:12px">
            <div style="font-size:2rem">📊</div>
            <div style="font-size:.88rem;font-weight:700;color:#fff;margin-top:8px">Gerência</div>
            <div style="font-size:.68rem;color:#9ca3af;margin-top:4px">Extrato e relatórios</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Entrar como Gerência", use_container_width=True, key="btn_ger", type="secondary"):
            st.session_state["_modo"] = "gerencia"
            st.rerun()

elif st.session_state["_modo"] == "operador":
    tela_operador()

elif st.session_state["_modo"] == "gerencia":
    if not st.session_state.get("_gerencia_ok"):
        tela_login_gerencia()
    else:
        tela_extrato()
