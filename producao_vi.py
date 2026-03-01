import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import BytesIO

st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="collapsed"
)

ETAPAS = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_ICONS = ["📦", "📬", "✅"]
ETAPA_CORES = ["#1565C0", "#6A0DAD", "#1B5E20"]
ETAPA_CORES_LIGHT = ["rgba(21,101,192,0.15)", "rgba(106,13,173,0.15)", "rgba(27,94,32,0.15)"]
ETAPA_NOMES_CURTOS = ["Separação", "Embalagem", "Conferência"]

OPERADORES = [
    "Lucivanio", "Enágio", "Daniel", "Ítalo", "Cildenir",
    "Samya", "Neide", "Eduardo", "Talyson",
]

SENHA_GERENCIA = "vi2026"

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

def carregar_pedidos():    return _carregar(FILE_PEDIDOS)
def salvar_pedidos(data):  _salvar(FILE_PEDIDOS, data)
def carregar_concluidos():
    d = _carregar(FILE_CONCLUIDOS)
    return d if isinstance(d, list) else []
def salvar_concluidos(data): _salvar(FILE_CONCLUIDOS, data)
def carregar_historico():
    d = _carregar(FILE_HISTORICO)
    return d if isinstance(d, list) else []

def registrar_historico(pedido_num, operador, etapa_nome, data_hora, status_pedido="em_andamento"):
    hist = carregar_historico()
    hist.append({
        "data_hora": data_hora,
        "data": data_hora.split(" ")[0] if " " in data_hora else data_hora,
        "pedido": pedido_num,
        "operador": operador,
        "etapa": etapa_nome,
        "status_pedido": status_pedido,
    })
    _salvar(FILE_HISTORICO, hist)

def agora_str():
    from datetime import timezone, timedelta
    br = timezone(timedelta(hours=-3))
    return datetime.now(br).strftime("%d/%m/%Y %H:%M")

def fmt_tempo(segundos):
    if segundos is None or segundos < 0:
        return "--:--:--"
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

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
    logo_tag = f'<img src="{_logo_src}" style="height:44px;object-fit:contain;display:block;margin:0 auto;filter:drop-shadow(0 2px 8px rgba(139,0,0,.45));" />'
else:
    logo_tag = '<div style="font-size:1.1rem;font-weight:900;color:#8B0000;letter-spacing:.12em;text-align:center;font-family:\'Playfair Display\',serif">VI LINGERIE</div>'

# ============================================================
# CSS GLOBAL
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500;600&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stApp"] {{
    font-family: 'DM Sans', sans-serif !important;
    background: #0f0f13 !important;
    color: #f0ede8 !important;
    height: 100vh;
    overflow: hidden;
}}

[data-testid="stSidebar"],
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {{ display: none !important; }}

.block-container {{
    padding: 0 !important;
    max-width: 100% !important;
    height: 100vh;
}}

/* ─── TELA INICIAL: espaçamento vertical ─── */
.vi-initial-spacer {{
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0;
}}

/* ─── CARD INICIAL ─── */
.vi-login-card {{
    background: #1a1a24;
    border-radius: 20px;
    padding: 36px 32px 28px;
    border: 1px solid rgba(255,255,255,.08);
    animation: fadeUp .4s cubic-bezier(.22,1,.36,1) both;
    width: 100%;
}}
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ─── LAYOUT PRINCIPAL 3 COLUNAS ─── */
.vi-layout {{
    display: grid;
    grid-template-columns: 260px 1fr 260px;
    grid-template-rows: 100vh;
    gap: 0;
    height: 100vh;
    overflow: hidden;
}}

/* ─── PAINEL LATERAL ESQUERDO ─── */
.vi-sidebar {{
    background: #16161d;
    border-right: 1px solid rgba(255,255,255,.07);
    padding: 28px 20px;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow-y: auto;
}}

/* ─── PAINEL LATERAL DIREITO ─── */
.vi-sidebar-right {{
    background: #16161d;
    border-left: 1px solid rgba(255,255,255,.07);
    padding: 28px 20px;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow-y: auto;
}}

/* ─── CENTRO: 3 CARDS DE ETAPA ─── */
.vi-center {{
    background: #0f0f13;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: 100vh;
    gap: 1px;
    overflow: hidden;
}}

/* ─── CARD DE ETAPA ─── */
.vi-etapa-card {{
    background: #1a1a24;
    display: flex;
    flex-direction: column;
    padding: 24px 20px;
    position: relative;
    overflow: hidden;
    transition: background .3s ease;
}}
.vi-etapa-card.active {{ background: #1e1e2c; }}
.vi-etapa-card.done   {{ background: #141a14; }}

/* ─── ETAPA HEADER ─── */
.vi-etapa-header    {{ margin-bottom: 16px; }}
.vi-etapa-num       {{ font-size:.6rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#6b7280;margin-bottom:4px; }}
.vi-etapa-title     {{ font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:800;color:#f0ede8;line-height:1.2; }}
.vi-etapa-icon-big  {{ font-size:1.8rem;margin-bottom:6px;display:block; }}

/* ─── STATUS BADGES ─── */
.vi-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: .6rem;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}}

/* ─── PEDIDO BIG NUM ─── */
.vi-big-pedido {{
    font-family: 'DM Mono', monospace;
    font-weight: 600;
    font-size: 3.4rem;
    color: #f0ede8;
    line-height: 1;
    text-align: center;
    margin: 8px 0;
    letter-spacing: -.02em;
}}
.vi-big-pedido span {{ font-size:1.4rem;color:#6b7280;vertical-align:super; }}

/* ─── TIMER GRANDE ─── */
.vi-timer-big {{
    font-family: 'DM Mono', monospace;
    font-size: 1.5rem;
    font-weight: 500;
    text-align: center;
    letter-spacing: .12em;
    margin: 4px 0 16px;
}}

/* ─── BOTÕES PRINCIPAIS ─── */
.vi-btn-iniciar > button {{
    background: linear-gradient(135deg, #1B5E20 0%, #43a047 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: .95rem !important;
    letter-spacing: .05em !important;
    padding: 16px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: all .2s !important;
    box-shadow: 0 4px 20px rgba(27,94,32,.4) !important;
}}
.vi-btn-iniciar > button:hover {{
    opacity: .88 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(27,94,32,.5) !important;
}}

.vi-btn-finalizar > button {{
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: .95rem !important;
    letter-spacing: .05em !important;
    padding: 16px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: all .2s !important;
    box-shadow: 0 4px 20px rgba(127,29,29,.4) !important;
}}
.vi-btn-finalizar > button:hover {{
    opacity: .88 !important;
    transform: translateY(-2px) !important;
}}

/* ─── BOTÕES SECUNDÁRIOS ─── */
.stButton > button {{
    background: rgba(255,255,255,.06) !important;
    border: 1px solid rgba(255,255,255,.12) !important;
    border-radius: 10px !important;
    color: #9ca3af !important;
    font-weight: 600 !important;
    font-size: .78rem !important;
    letter-spacing: .04em !important;
    padding: 10px 16px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: all .18s !important;
}}
.stButton > button:hover {{
    background: rgba(255,255,255,.1) !important;
    color: #f0ede8 !important;
    border-color: rgba(255,255,255,.2) !important;
}}

/* ─── INPUTS ─── */
[data-testid="stTextInput"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stNumberInput"] label p {{
    color: #6b7280 !important;
    font-size: .62rem !important;
    font-weight: 700 !important;
    letter-spacing: .12em !important;
    text-transform: uppercase !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(255,255,255,.12) !important;
    border-radius: 10px !important;
    color: #f0ede8 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1rem !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(255,255,255,.12) !important;
    border-radius: 10px !important;
    color: #f0ede8 !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {{
    border-color: rgba(139,0,0,.6) !important;
    box-shadow: 0 0 0 3px rgba(139,0,0,.15) !important;
}}

/* ─── DIVIDER ─── */
.vi-divider {{
    height: 1px;
    background: rgba(255,255,255,.07);
    margin: 14px 0;
}}

/* ─── STAT BOX ─── */
.vi-stat {{
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 8px;
}}
.vi-stat-label {{
    font-size: .56rem;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: 2px;
}}
.vi-stat-val {{
    font-family: 'DM Mono', monospace;
    font-size: 1.2rem;
    font-weight: 600;
    color: #f0ede8;
}}

/* ─── ALERT ─── */
.vi-alert {{
    padding: 10px 14px;
    border-radius: 10px;
    font-size: .75rem;
    font-weight: 500;
    margin: 8px 0;
    display: flex;
    align-items: flex-start;
    gap: 8px;
}}
.vi-alert-ok   {{ background:rgba(27,94,32,.2); border:1px solid rgba(76,175,80,.3); color:#86efac; }}
.vi-alert-err  {{ background:rgba(139,0,0,.2);  border:1px solid rgba(220,38,38,.3); color:#fca5a5; }}
.vi-alert-inf  {{ background:rgba(21,101,192,.2);border:1px solid rgba(66,165,245,.3);color:#93c5fd; }}
.vi-alert-warn {{ background:rgba(180,83,9,.2); border:1px solid rgba(217,119,6,.3); color:#fcd34d; }}

/* ─── SIDEBAR LABELS ─── */
.vi-sidebar-section-label {{
    font-size: .55rem;
    font-weight: 700;
    color: #4b5563;
    text-transform: uppercase;
    letter-spacing: .16em;
    margin-bottom: 10px;
    margin-top: 16px;
}}
.vi-sidebar-section-label:first-child {{ margin-top: 0; }}

/* ─── AVATAR ─── */
.vi-avatar {{
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: .75rem; font-weight: 700; color: #fff;
    flex-shrink: 0;
}}

/* ─── HISTÓRICO ITEM ─── */
.vi-hist-item {{
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.06);
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 5px;
    display: flex;
    flex-direction: column;
    gap: 2px;
}}
.vi-hist-ped  {{ font-family:'DM Mono',monospace;font-size:.8rem;font-weight:600;color:#f0ede8; }}
.vi-hist-meta {{ font-size:.62rem;color:#6b7280; }}

/* ─── TRANSIÇÃO / PERGUNTA OPERADOR ─── */
.vi-ask-card {{
    background: #1e1e2c;
    border-radius: 14px;
    padding: 18px 16px;
    border: 1px solid rgba(255,255,255,.08);
    margin-top: 8px;
}}
.vi-ask-title {{
    font-size: .68rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: 10px;
    text-align: center;
}}

/* ─── PULSE ANIMATION ─── */
@keyframes vi-pulse-border {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(220,38,38,0); }}
    50%       {{ box-shadow: 0 0 0 6px rgba(220,38,38,.15); }}
}}
.running-pulse {{
    animation: vi-pulse-border 2s ease infinite;
    border-radius: 12px;
}}

/* ─── CONCLUÍDO CARD ─── */
@keyframes vi-pop {{
    from {{ opacity: 0; transform: scale(.88); }}
    to   {{ opacity: 1; transform: scale(1); }}
}}
.vi-done-card {{
    background: linear-gradient(135deg, #14291a 0%, #1a3a20 100%);
    border: 1.5px solid rgba(76,175,80,.3);
    border-radius: 14px;
    padding: 20px 16px;
    text-align: center;
    animation: vi-pop .4s cubic-bezier(.34,1.56,.64,1) both;
}}

/* ─── CARDS DE MODO (tela inicial) ─── */
.vi-mode-card {{
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 14px;
    padding: 18px 12px;
    text-align: center;
    margin-bottom: 10px;
}}

.vi-btn-confirm > button {{
    background: linear-gradient(135deg, #1565C0 0%, #42a5f5 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: .8rem !important;
    letter-spacing: .04em !important;
    padding: 12px 16px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: all .2s !important;
    box-shadow: 0 4px 16px rgba(21,101,192,.35) !important;
}}

/* Tab styling */
[data-testid="stTabs"] [data-testid="stTabsContent"] {{ background: transparent !important; }}
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: #6b7280 !important;
    font-weight: 600 !important;
    font-size: .75rem !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: #f0ede8 !important;
    border-bottom-color: #8B0000 !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,.15); border-radius: 4px; }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS VISUAIS
# ============================================================
def avatar_html(nome, size=40):
    partes = nome.strip().split()
    iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
    cores = ["#8B0000","#1565C0","#4A148C","#1B5E20","#E65100","#880E4F","#006064","#37474F","#BF360C"]
    cor = cores[sum(ord(c) for c in nome) % len(cores)]
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{cor};'
        f'display:flex;align-items:center;justify-content:center;font-size:{int(size*.34)}px;'
        f'font-weight:700;color:#fff;flex-shrink:0;">{iniciais}</div>'
    )


# ============================================================
# TELA INICIAL — CORRIGIDA
# Não mistura divs HTML abertos com widgets Streamlit.
# Cada st.markdown é auto-contido.
# ============================================================
def tela_inicial():
    # Espaçamento: empurra conteúdo para o centro vertical
    st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)

    _, col_center, _ = st.columns([2, 1.2, 2])

    with col_center:
        # ── Cabeçalho do card (HTML puro, sem widgets) ──
        st.markdown(f"""
        <div class="vi-login-card">
            <div style="text-align:center;margin-bottom:28px">
                {logo_tag}
                <div style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;
                            color:#f0ede8;margin-top:12px;letter-spacing:.02em">
                    Sistema de Produção
                </div>
                <div style="font-size:.7rem;color:#4b5563;margin-top:4px;letter-spacing:.06em">
                    Vi Lingerie · Linha de Montagem
                </div>
            </div>
            <div class="vi-divider"></div>
            <div style="font-size:.62rem;font-weight:700;color:#4b5563;letter-spacing:.14em;
                        text-transform:uppercase;margin:14px 0;text-align:center">
                Como deseja acessar?
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Cards de modo + botões (sem div aberto entre eles) ──
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div class="vi-mode-card">
                <div style="font-size:1.8rem;margin-bottom:6px">🏭</div>
                <div style="font-size:.85rem;font-weight:700;color:#f0ede8">Operador</div>
                <div style="font-size:.62rem;color:#6b7280;margin-top:3px">Registrar produção</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="vi-btn-iniciar">', unsafe_allow_html=True)
            if st.button("▶  Entrar", use_container_width=True, key="btn_op"):
                st.session_state["_modo"] = "operador"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown("""
            <div class="vi-mode-card">
                <div style="font-size:1.8rem;margin-bottom:6px">📊</div>
                <div style="font-size:.85rem;font-weight:700;color:#f0ede8">Gerência</div>
                <div style="font-size:.62rem;color:#6b7280;margin-top:3px">Extrato e relatórios</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔓 Acessar", use_container_width=True, key="btn_ger"):
                st.session_state["_modo"] = "gerencia"
                st.rerun()

        # ── Rodapé ──
        st.markdown("""
        <div style="margin-top:14px;text-align:center">
            <div style="font-size:.55rem;color:#2d2d3a;letter-spacing:.08em">
                vi lingerie · sistema interno v1.0
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TELA DE SELEÇÃO DE OPERADOR INICIAL
# ============================================================
def tela_selecao_operador():
    st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([2, 1.2, 2])
    with col:
        st.markdown(f"""
        <div class="vi-login-card">
            <div style="text-align:center;margin-bottom:20px">
                {logo_tag}
                <div style="font-size:.95rem;font-weight:700;color:#f0ede8;margin-top:10px">
                    Identificação do Operador
                </div>
                <div style="font-size:.68rem;color:#6b7280;margin-top:3px">
                    Selecione seu nome para começar
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)

        operador = st.selectbox(
            "Selecione seu nome",
            options=["— Selecione —"] + OPERADORES,
            key="sel_operador_inicial"
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="vi-btn-iniciar">', unsafe_allow_html=True)
        if st.button("▶  Entrar no Sistema", use_container_width=True, key="btn_entrar"):
            if operador == "— Selecione —":
                st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione seu nome.</div>', unsafe_allow_html=True)
            else:
                st.session_state.update({
                    "_operador": operador,
                    "_turno_inicio": time.time(),
                    "_etapa_0_state": "idle",
                    "_etapa_1_state": "idle",
                    "_etapa_2_state": "idle",
                    "_etapa_0_pedido": None,
                    "_etapa_1_pedido": None,
                    "_etapa_2_pedido": None,
                    "_etapa_0_ts": None,
                    "_etapa_1_ts": None,
                    "_etapa_2_ts": None,
                    "_etapa_0_op": operador,
                    "_etapa_1_op": operador,
                    "_etapa_2_op": operador,
                })
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True, key="btn_voltar_sel"):
            st.session_state.pop("_modo", None)
            st.rerun()


# ============================================================
# TELA DE LOGIN GERÊNCIA
# ============================================================
def tela_login_gerencia():
    st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([2, 1.2, 2])
    with col:
        st.markdown(f"""
        <div class="vi-login-card">
            <div style="text-align:center;margin-bottom:20px">
                {logo_tag}
                <div style="font-size:.95rem;font-weight:700;color:#f0ede8;margin-top:10px">
                    Área da Gerência
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)

        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="vi-btn-iniciar">', unsafe_allow_html=True)
        if st.button("🔓 Acessar", use_container_width=True, key="btn_login_ger"):
            if senha == SENHA_GERENCIA:
                st.session_state["_gerencia_ok"] = True
                st.rerun()
            else:
                st.markdown('<div class="vi-alert vi-alert-err">❌ Senha incorreta.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True, key="btn_voltar_login"):
            st.session_state.pop("_modo", None)
            st.rerun()


# ============================================================
# TELA DE EXTRATO (GERÊNCIA)
# ============================================================
def tela_extrato():
    concluidos        = carregar_concluidos()
    pedidos_andamento = carregar_pedidos()
    historico         = carregar_historico()

    _, col_main, _ = st.columns([0.1, 3, 0.1])
    with col_main:
        st.markdown(f"""
        <div style="padding:20px 0 10px;display:flex;align-items:center;gap:14px;">
            {logo_tag.replace('margin:0 auto','margin:0')}
            <div>
                <div style="font-size:1rem;font-weight:700;color:#f0ede8">Extrato de Produção</div>
                <div style="font-size:.68rem;color:#6b7280">Consulta, filtros e relatórios</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        total_sep  = len([h for h in historico if h.get("etapa") == "Separação do Pedido"])
        total_emb  = len([h for h in historico if h.get("etapa") == "Mesa de Embalagem"])
        total_conf = len([h for h in historico if h.get("etapa") == "Conferência do Pedido"])
        total_conc = len(concluidos)

        c1, c2, c3, c4 = st.columns(4)
        for col, label, val, cor in [
            (c1, "📦 Separações",   total_sep,  "#64b5f6"),
            (c2, "📬 Embalagens",   total_emb,  "#ce93d8"),
            (c3, "✅ Conferências", total_conf, "#86efac"),
            (c4, "🎯 Concluídos",  total_conc, "#f87171"),
        ]:
            with col:
                st.markdown(
                    f'<div class="vi-stat"><div class="vi-stat-label">{label}</div>'
                    f'<div class="vi-stat-val" style="color:{cor};font-size:1.6rem">{val}</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
        aba1, aba2, aba3 = st.tabs(["📅 Histórico", "📋 Concluídos", "⏳ Em Andamento"])

        with aba1:
            if not historico:
                st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação registrada.</div>', unsafe_allow_html=True)
            else:
                df_hist = pd.DataFrame(historico)
                def parse_data(s):
                    try:
                        return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
                    except:
                        return pd.NaT
                df_hist["_data_dt"] = df_hist["data"].apply(parse_data)
                from datetime import date, timedelta as td
                hoje = date.today()
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1:
                    data_ini = st.date_input("Data inicial", value=hoje - td(days=7), key="dt_ini", format="DD/MM/YYYY")
                with col_f2:
                    data_fim = st.date_input("Data final", value=hoje, key="dt_fim", format="DD/MM/YYYY")
                with col_f3:
                    ops_lista = ["Todos"] + sorted(df_hist["operador"].dropna().unique().tolist())
                    op_filtro = st.selectbox("Funcionário", options=ops_lista, key="hist_op")
                with col_f4:
                    etapas_lista = ["Todas"] + ETAPAS
                    etapa_filtro = st.selectbox("Etapa", options=etapas_lista, key="hist_etapa")

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
                n_res = len(df_filtrado)
                st.markdown(
                    f'<div class="vi-alert vi-alert-inf">🔍 <b>{n_res}</b> operação(ões) encontrada(s)</div>',
                    unsafe_allow_html=True
                )
                if n_res > 0:
                    if op_filtro == "Todos":
                        resumo = df_filtrado.groupby(["operador","etapa"]).size().reset_index(name="qtd")
                        resumo.columns = ["Funcionário","Etapa","Qtd."]
                        st.dataframe(resumo, use_container_width=True, hide_index=True)
                        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
                    df_exib = df_filtrado[["data_hora","pedido","operador","etapa","status_pedido"]].rename(columns={
                        "data_hora":"Data/Hora","pedido":"Pedido",
                        "operador":"Funcionário","etapa":"Etapa","status_pedido":"Status"
                    })
                    df_exib["Status"] = df_exib["Status"].map(
                        {"em_andamento":"⏳","concluido":"✅"}
                    ).fillna(df_exib["Status"])
                    st.dataframe(df_exib, use_container_width=True, hide_index=True)
                    nome_arq = (
                        f"extrato_{op_filtro.replace(' ','_')}_"
                        f"{data_ini.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"
                    )
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "⬇️ CSV",
                            data=df_exib.to_csv(index=False).encode("utf-8"),
                            file_name=f"{nome_arq}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="dl_hist_csv"
                        )
                    with col_dl2:
                        xlsx_buf = BytesIO()
                        with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                            df_exib.to_excel(writer, index=False, sheet_name="Detalhado")
                        xlsx_buf.seek(0)
                        st.download_button(
                            "⬇️ Excel",
                            data=xlsx_buf.getvalue(),
                            file_name=f"{nome_arq}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="dl_hist_xlsx"
                        )

        with aba2:
            if concluidos:
                df_conc = pd.DataFrame(concluidos)
                df_show = df_conc.rename(columns={
                    "pedido":"Pedido","op_sep":"Op. Sep.","dt_sep":"Data Sep.",
                    "op_emb":"Op. Emb.","dt_emb":"Data Emb.",
                    "op_conf":"Op. Conf.","dt_conf":"Data Conf."
                }).drop(columns=["etapa"], errors="ignore")
                st.dataframe(df_show, use_container_width=True, hide_index=True)
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.download_button(
                        "⬇️ CSV",
                        data=df_show.to_csv(index=False).encode("utf-8"),
                        file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="dl_conc_csv"
                    )
                with col_c2:
                    xlsx_buf2 = BytesIO()
                    with pd.ExcelWriter(xlsx_buf2, engine="openpyxl") as writer:
                        df_show.to_excel(writer, index=False, sheet_name="Concluídos")
                    xlsx_buf2.seek(0)
                    st.download_button(
                        "⬇️ Excel",
                        data=xlsx_buf2.getvalue(),
                        file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="dl_conc_xlsx"
                    )
            else:
                st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido finalizado ainda.</div>', unsafe_allow_html=True)

        with aba3:
            if pedidos_andamento:
                rows = []
                etapa_labels = {1:"📬 Aguard. Embalagem", 2:"✅ Aguard. Conferência"}
                for p, d in pedidos_andamento.items():
                    rows.append({
                        "Pedido": f"#{d['pedido']}",
                        "Etapa": etapa_labels.get(d.get("etapa", 0), "—"),
                        "Op. Sep.": d.get("op_sep", "—"),
                        "Op. Emb.": d.get("op_emb", "—"),
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.markdown('<div class="vi-alert vi-alert-ok">✅ Nenhum pedido em andamento.</div>', unsafe_allow_html=True)

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
        if st.button("← Sair da Gerência", use_container_width=True, key="btn_sair_ger"):
            st.session_state.pop("_modo", None)
            st.session_state.pop("_gerencia_ok", None)
            st.rerun()


# ============================================================
# CARD DE ETAPA
# ============================================================
def card_etapa(etapa_idx: int, operador_padrao: str):
    state_key  = f"_etapa_{etapa_idx}_state"
    pedido_key = f"_etapa_{etapa_idx}_pedido"
    ts_key     = f"_etapa_{etapa_idx}_ts"
    op_key     = f"_etapa_{etapa_idx}_op"

    state     = st.session_state.get(state_key, "idle")
    pedido    = st.session_state.get(pedido_key)
    ts_inicio = st.session_state.get(ts_key)
    operador  = st.session_state.get(op_key, operador_padrao)

    etapa_nome       = ETAPAS[etapa_idx]
    etapa_icon       = ETAPA_ICONS[etapa_idx]
    etapa_cor        = ETAPA_CORES[etapa_idx]
    etapa_nome_curto = ETAPA_NOMES_CURTOS[etapa_idx]

    elapsed = fmt_tempo(time.time() - ts_inicio) if ts_inicio and state == "running" else "--:--:--"

    # ── HEADER ──
    running_badge = (
        '<span style="background:rgba(220,38,38,.2);color:#f87171;border:1px solid rgba(220,38,38,.3);'
        'padding:3px 8px;border-radius:20px;font-size:.55rem;font-weight:700;letter-spacing:.1em;'
        'text-transform:uppercase">● EM CURSO</span>'
    ) if state == "running" else ""
    done_badge = (
        '<span style="background:rgba(76,175,80,.15);color:#86efac;border:1px solid rgba(76,175,80,.3);'
        'padding:3px 8px;border-radius:20px;font-size:.55rem;font-weight:700;letter-spacing:.1em;'
        'text-transform:uppercase">✓ OK</span>'
    ) if state == "done" else ""

    st.markdown(f"""
    <div style="border-bottom:1px solid rgba(255,255,255,.07);padding-bottom:14px;margin-bottom:14px">
        <div style="height:3px;background:{etapa_cor};border-radius:2px;margin-bottom:12px;
                    opacity:{'1' if state in ['running','ask_next'] else '0.5'}"></div>
        <div style="display:flex;align-items:center;gap:10px">
            <div style="font-size:1.5rem">{etapa_icon}</div>
            <div>
                <div style="font-size:.55rem;font-weight:700;color:#4b5563;letter-spacing:.16em;
                            text-transform:uppercase">Etapa {etapa_idx + 1}</div>
                <div style="font-size:.85rem;font-weight:700;color:#f0ede8">{etapa_nome}</div>
            </div>
            <div style="margin-left:auto">{running_badge}{done_badge}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── OPERADOR ATUAL ──
    if state != "idle":
        partes = operador.strip().split()
        iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
        cores_op = ["#8B0000","#1565C0","#4A148C","#1B5E20","#E65100","#880E4F","#006064","#37474F","#BF360C"]
        cor_op = cores_op[sum(ord(c) for c in operador) % len(cores_op)]
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <div style="width:28px;height:28px;border-radius:50%;background:{cor_op};display:flex;
                        align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:#fff">
                {iniciais}
            </div>
            <div style="font-size:.72rem;color:#9ca3af">{operador}</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════ IDLE ══════════════
    if state == "idle":
        if etapa_idx == 0:
            num = st.text_input("Nº do Pedido", placeholder="Ex: 12345",
                                key=f"inp_num_{etapa_idx}", label_visibility="visible")
            st.markdown('<div class="vi-btn-iniciar" style="margin-top:8px">', unsafe_allow_html=True)
            if st.button(f"▶  INICIAR {etapa_nome_curto.upper()}", use_container_width=True, key=f"btn_ini_{etapa_idx}"):
                num = num.strip()
                pedidos_db = carregar_pedidos()
                if not num:
                    st.markdown('<div class="vi-alert vi-alert-err">⚠️ Informe o número.</div>', unsafe_allow_html=True)
                elif num in pedidos_db:
                    st.markdown(f'<div class="vi-alert vi-alert-err">⚠️ Pedido #{num} já em andamento.</div>', unsafe_allow_html=True)
                else:
                    st.session_state[state_key]  = "running"
                    st.session_state[pedido_key] = num
                    st.session_state[ts_key]     = time.time()
                    st.session_state[op_key]     = operador_padrao
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            pedidos_db  = carregar_pedidos()
            chave_op    = "op_emb" if etapa_idx == 1 else "op_conf"
            etapa_needed = 1 if etapa_idx == 1 else 2
            disponiveis = sorted([
                p for p, d in pedidos_db.items()
                if d.get("etapa") == etapa_needed and chave_op not in d
            ])

            if not disponiveis:
                st.markdown(
                    '<div class="vi-alert vi-alert-warn" style="margin-top:8px">⏳ Aguardando etapa anterior...</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    '<div style="font-size:.65rem;color:#4b5563;margin-top:8px;text-align:center">'
                    'Quando um pedido for finalizado na etapa anterior, ele aparecerá aqui automaticamente.</div>',
                    unsafe_allow_html=True
                )
                if st.button("🔄 Atualizar", use_container_width=True, key=f"btn_atualizar_{etapa_idx}"):
                    st.rerun()
            else:
                pedido_sel = st.selectbox(
                    "Selecione o Pedido",
                    options=["— Selecione —"] + disponiveis,
                    key=f"sel_ped_{etapa_idx}"
                )
                st.markdown('<div class="vi-btn-iniciar" style="margin-top:8px">', unsafe_allow_html=True)
                if st.button(f"▶  INICIAR {etapa_nome_curto.upper()}", use_container_width=True, key=f"btn_ini_{etapa_idx}"):
                    if pedido_sel == "— Selecione —":
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state[state_key]  = "running"
                        st.session_state[pedido_key] = pedido_sel
                        st.session_state[ts_key]     = time.time()
                        st.session_state[op_key]     = operador_padrao
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════ RUNNING ══════════════
    elif state == "running":
        st.markdown(f"""
        <div style="text-align:center;margin:8px 0 12px">
            <div style="font-size:.58rem;color:#6b7280;letter-spacing:.14em;text-transform:uppercase;margin-bottom:2px">
                PEDIDO EM CURSO
            </div>
            <div class="vi-big-pedido"><span>#</span>{pedido}</div>
            <div class="vi-timer-big" style="color:{etapa_cor}">⏱ {elapsed}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-btn-finalizar running-pulse">', unsafe_allow_html=True)
        if st.button(f"⏹  FINALIZAR {etapa_nome_curto.upper()}", use_container_width=True, key=f"btn_fin_{etapa_idx}"):
            now    = agora_str()
            ts_fim = time.time()
            pedidos_db = carregar_pedidos()

            if etapa_idx == 0:
                pedidos_db[pedido] = {
                    "pedido": pedido, "etapa": 1,
                    "op_sep": operador, "dt_sep": now
                }
                registrar_historico(pedido, operador, "Separação do Pedido", now, "em_andamento")

            elif etapa_idx == 1:
                if pedido in pedidos_db:
                    pedidos_db[pedido]["etapa"]  = 2
                    pedidos_db[pedido]["op_emb"] = operador
                    pedidos_db[pedido]["dt_emb"] = now
                    registrar_historico(pedido, operador, "Mesa de Embalagem", now, "em_andamento")

            elif etapa_idx == 2:
                if pedido in pedidos_db:
                    pedidos_db[pedido]["etapa"]   = 3
                    pedidos_db[pedido]["op_conf"] = operador
                    pedidos_db[pedido]["dt_conf"] = now
                    conc = carregar_concluidos()
                    conc.append(pedidos_db[pedido])
                    salvar_concluidos(conc)
                    del pedidos_db[pedido]
                    registrar_historico(pedido, operador, "Conferência do Pedido", now, "concluido")

            salvar_pedidos(pedidos_db)
            st.session_state[f"_etapa_{etapa_idx}_ts_fim"] = ts_fim
            st.session_state[state_key] = "ask_next"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("✕ Cancelar", use_container_width=True, key=f"btn_cancel_{etapa_idx}"):
            st.session_state[state_key]  = "idle"
            st.session_state[pedido_key] = None
            st.session_state[ts_key]     = None
            st.rerun()

    # ══════════════ ASK_NEXT ══════════════
    elif state == "ask_next":
        ts_fim    = st.session_state.get(f"_etapa_{etapa_idx}_ts_fim")
        ts_ini_op = st.session_state.get(ts_key, ts_fim)
        dur       = fmt_tempo((ts_fim - ts_ini_op) if ts_fim and ts_ini_op else 0)

        if etapa_idx == 2:
            st.markdown(f"""
            <div class="vi-done-card">
                <div style="font-size:2rem;margin-bottom:6px">🎉</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:800;color:#86efac">
                    Pedido Concluído!
                </div>
                <div style="font-family:'DM Mono',monospace;font-size:1.6rem;font-weight:700;color:#f0ede8;margin:6px 0">
                    #{pedido}
                </div>
                <div style="font-size:.68rem;color:#6b7280">Todas as etapas finalizadas · {dur}</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="vi-btn-iniciar">', unsafe_allow_html=True)
            if st.button("▶  Novo Pedido", use_container_width=True, key=f"btn_novo_{etapa_idx}"):
                st.session_state[state_key]  = "idle"
                st.session_state[pedido_key] = None
                st.session_state[ts_key]     = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return

        prox_idx       = etapa_idx + 1
        prox_icon      = ETAPA_ICONS[prox_idx]
        prox_nome      = ETAPA_NOMES_CURTOS[prox_idx]
        prox_cor       = ETAPA_CORES[prox_idx]

        st.markdown(f"""
        <div style="background:rgba(27,94,32,.12);border:1px solid rgba(76,175,80,.25);border-radius:12px;
                    padding:12px 14px;text-align:center;margin-bottom:10px">
            <div style="font-size:.6rem;color:#86efac;font-weight:700;letter-spacing:.1em;text-transform:uppercase">
                ✓ Etapa finalizada
            </div>
            <div style="font-family:'DM Mono',monospace;font-size:1.4rem;font-weight:700;color:#f0ede8">#{pedido}</div>
            <div style="font-size:.62rem;color:#6b7280">Duração: {dur}</div>
        </div>
        <div class="vi-ask-card">
            <div class="vi-ask-title" style="color:{prox_cor}">
                {prox_icon} Próxima: {prox_nome}<br>
                <span style="color:#6b7280;font-size:.58rem;text-transform:none;letter-spacing:.04em;font-weight:400">
                    Quem vai realizar?
                </span>
            </div>
        """, unsafe_allow_html=True)

        ask_key = f"_ask_mode_{etapa_idx}"
        if ask_key not in st.session_state:
            st.session_state[ask_key] = None

        c_mesmo, c_outro = st.columns(2)
        with c_mesmo:
            st.markdown('<div class="vi-btn-iniciar">', unsafe_allow_html=True)
            if st.button(f"✅ Sou eu\n({operador.split()[0]})", use_container_width=True, key=f"btn_mesmo_{etapa_idx}"):
                _iniciar_proxima_etapa(etapa_idx, pedido, operador)
            st.markdown('</div>', unsafe_allow_html=True)
        with c_outro:
            if st.button("👤 Outro\noperador", use_container_width=True, key=f"btn_outro_{etapa_idx}"):
                st.session_state[ask_key] = "selecionando"
                st.rerun()

        if st.session_state.get(ask_key) == "selecionando":
            outros = [op for op in OPERADORES if op != operador]
            outro_op = st.selectbox(
                "Selecione o operador",
                options=["— Selecione —"] + outros,
                key=f"sel_op_prox_{etapa_idx}",
                label_visibility="visible"
            )
            st.markdown('<div class="vi-btn-confirm" style="margin-top:6px">', unsafe_allow_html=True)
            if st.button("▶ Confirmar e Iniciar", use_container_width=True, key=f"btn_conf_op_{etapa_idx}"):
                if outro_op == "— Selecione —":
                    st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione.</div>', unsafe_allow_html=True)
                else:
                    _iniciar_proxima_etapa(etapa_idx, pedido, outro_op)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def _iniciar_proxima_etapa(etapa_atual_idx: int, pedido: str, operador_proximo: str):
    prox = etapa_atual_idx + 1
    st.session_state.pop(f"_ask_mode_{etapa_atual_idx}", None)
    st.session_state[f"_etapa_{etapa_atual_idx}_state"]  = "done"
    st.session_state[f"_etapa_{etapa_atual_idx}_pedido"] = pedido
    st.session_state[f"_etapa_{prox}_state"]  = "running"
    st.session_state[f"_etapa_{prox}_pedido"] = pedido
    st.session_state[f"_etapa_{prox}_ts"]     = time.time()
    st.session_state[f"_etapa_{prox}_op"]     = operador_proximo
    st.session_state["_operador"] = operador_proximo
    st.rerun()


# ============================================================
# TELA PRINCIPAL DO OPERADOR
# ============================================================
def tela_operador():
    operador     = st.session_state.get("_operador", "")
    turno_inicio = st.session_state.get("_turno_inicio", time.time())
    hoje_str     = agora_str().split(" ")[0]
    historico    = carregar_historico()
    hist_hoje    = [h for h in historico if h.get("operador") == operador and h.get("data") == hoje_str]
    pedidos_hoje = len(hist_hoje)
    h_turno      = fmt_tempo(time.time() - turno_inicio)
    h_inicio_turno = datetime.fromtimestamp(turno_inicio).strftime("%H:%M")

    col_left, col_center1, col_center2, col_center3, col_right = st.columns([1, 1.15, 1.15, 1.15, 1])

    with col_left:
        st.markdown(f"""
        <div class="vi-sidebar-section-label">Operador Ativo</div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
            {avatar_html(operador, 44)}
            <div>
                <div style="font-size:.85rem;font-weight:700;color:#f0ede8">{operador}</div>
                <div style="font-size:.62rem;color:#6b7280">Em operação</div>
            </div>
        </div>
        <div class="vi-divider"></div>
        <div class="vi-sidebar-section-label">Turno</div>
        <div class="vi-stat">
            <div class="vi-stat-label">Início do turno</div>
            <div class="vi-stat-val" style="font-size:.95rem">{h_inicio_turno}</div>
        </div>
        <div class="vi-stat">
            <div class="vi-stat-label">Tempo de turno</div>
            <div class="vi-stat-val" style="font-size:.95rem">{h_turno}</div>
        </div>
        <div class="vi-stat">
            <div class="vi-stat-label">Operações hoje</div>
            <div class="vi-stat-val" style="color:#86efac">{pedidos_hoje}</div>
        </div>
        <div class="vi-divider"></div>
        <div class="vi-sidebar-section-label">Últimas operações</div>
        """, unsafe_allow_html=True)

        hist_recentes = sorted(hist_hoje, key=lambda x: x.get("data_hora",""), reverse=True)[:5]
        if not hist_recentes:
            st.markdown('<div style="font-size:.65rem;color:#4b5563;text-align:center;padding:8px 0">Nenhuma operação hoje.</div>', unsafe_allow_html=True)
        for h in hist_recentes:
            hora = h.get("data_hora","").split(" ")[-1] if " " in h.get("data_hora","") else h.get("data_hora","")
            icone = {
                "Separação do Pedido": "📦",
                "Mesa de Embalagem":   "📬",
                "Conferência do Pedido":"✅"
            }.get(h.get("etapa",""), "○")
            st.markdown(f"""
            <div class="vi-hist-item">
                <div class="vi-hist-ped">{icone} #{h.get('pedido','')}</div>
                <div class="vi-hist-meta">{h.get('etapa','').split(' ')[0]} · {hora}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:auto;padding-top:20px">
            {logo_tag}
        </div>
        """, unsafe_allow_html=True)

    # ── 3 CARDS DE ETAPA ──
    for idx, col in enumerate([col_center1, col_center2, col_center3]):
        with col:
            st.markdown("""
            <div style="background:#1a1a24;height:100vh;padding:20px 16px;
                        border-left:1px solid rgba(255,255,255,.05);
                        border-right:1px solid rgba(255,255,255,.05);
                        overflow-y:auto;">
            """, unsafe_allow_html=True)
            card_etapa(idx, operador)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── SIDEBAR DIREITA ──
    with col_right:
        pedidos_db = carregar_pedidos()
        concluidos = carregar_concluidos()

        st.markdown('<div class="vi-sidebar-section-label">Em Andamento</div>', unsafe_allow_html=True)

        if not pedidos_db:
            st.markdown('<div style="font-size:.65rem;color:#4b5563;text-align:center;padding:8px 0">Nenhum pedido em curso.</div>', unsafe_allow_html=True)
        else:
            etapa_labels = {1:"📬 Embalagem", 2:"✅ Conferência", 3:"🎯 Concluindo"}
            for p, d in list(pedidos_db.items())[:6]:
                etapa_txt = etapa_labels.get(d.get("etapa", 0), "—")
                st.markdown(f"""
                <div class="vi-hist-item">
                    <div class="vi-hist-ped">#{p}</div>
                    <div class="vi-hist-meta">{etapa_txt}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="vi-sidebar-section-label">Concluídos Hoje</div>', unsafe_allow_html=True)

        conc_hoje = [c for c in concluidos if hoje_str in (c.get("dt_conf","") or "")]
        st.markdown(
            f'<div class="vi-stat"><div class="vi-stat-label">Total do dia</div>'
            f'<div class="vi-stat-val" style="color:#86efac;font-size:1.8rem">{len(conc_hoje)}</div></div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)

        if st.button("🔄 Atualizar", use_container_width=True, key="btn_atualizar_global"):
            st.rerun()

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("⏏ Trocar Operador", use_container_width=True, key="btn_trocar_op"):
            keys_to_clear = [
                k for k in st.session_state.keys()
                if k.startswith("_etapa_") or k in [
                    "_operador","_turno_inicio",
                    "_ask_mode_0","_ask_mode_1","_ask_mode_2"
                ]
            ]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("← Sair", use_container_width=True, key="btn_sair_op"):
            for k in list(st.session_state.keys()):
                if k != "_splash_done":
                    st.session_state.pop(k, None)
            st.rerun()


# ============================================================
# ROTEADOR PRINCIPAL
# ============================================================
modo = st.session_state.get("_modo")

if not modo:
    tela_inicial()
elif modo == "gerencia":
    if not st.session_state.get("_gerencia_ok"):
        tela_login_gerencia()
    else:
        tela_extrato()
elif modo == "operador":
    if "_operador" not in st.session_state:
        tela_selecao_operador()
    else:
        tela_operador()
