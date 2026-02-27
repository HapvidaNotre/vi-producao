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

ETAPAS = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_ICONS = ["📦", "📬", "✅"]
ETAPA_CORES = ["#1565C0", "#6A0DAD", "#1B5E20"]
ETAPA_CORES_LIGHT = ["rgba(21,101,192,0.12)", "rgba(106,13,173,0.12)", "rgba(27,94,32,0.12)"]
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
    logo_tag = f'<img src="{_logo_src}" style="height:52px;object-fit:contain;display:block;margin:0 auto 6px;filter:drop-shadow(0 2px 8px rgba(139,0,0,.45));" />'
else:
    logo_tag = '<div style="font-size:1.2rem;font-weight:900;color:#8B0000;letter-spacing:.12em;text-align:center;margin-bottom:6px;font-family:\'Playfair Display\',serif">VI LINGERIE</div>'

# ============================================================
# CSS GLOBAL
# ============================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stApp"] {{
    font-family: 'DM Sans', sans-serif !important;
    background: #f7f5f2 !important;
    color: #1a1a2e !important;
    min-height: 100vh;
}}

[data-testid="stSidebar"] {{ display: none !important; }}
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {{ display: none !important; }}

.block-container {{
    padding: 1.5rem 1rem !important;
    max-width: 540px !important;
    margin: 0 auto !important;
}}

/* ── TELA PRINCIPAL ── */
.vi-main-card {{
    background: #ffffff;
    border-radius: 24px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06);
    overflow: hidden;
    animation: fadeUp .45s cubic-bezier(.22,1,.36,1) both;
}}

/* ── HEADER DO CARD ── */
.vi-card-header {{
    padding: 24px 28px 20px;
    border-bottom: 1px solid #f0ede8;
    display: flex;
    align-items: center;
    gap: 14px;
    position: relative;
}}
.vi-card-header-accent {{
    position: absolute;
    top: 0; left: 0;
    width: 4px;
    height: 100%;
    border-radius: 0 4px 4px 0;
}}
.vi-card-body {{
    padding: 24px 28px 28px;
}}

/* ── BADGE DE ETAPA ── */
.vi-etapa-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
}}

/* ── STEPPER ── */
.vi-stepper {{
    display: flex;
    align-items: center;
    gap: 0;
    margin: 0 0 22px 0;
}}
.vi-step {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    flex: 1;
    position: relative;
}}
.vi-step-circle {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: .8rem;
    font-weight: 700;
    position: relative;
    z-index: 1;
    transition: all .3s ease;
}}
.vi-step-label {{
    font-size: .58rem;
    font-weight: 600;
    letter-spacing: .06em;
    text-transform: uppercase;
    text-align: center;
    line-height: 1.2;
}}
.vi-step-line {{
    flex: 1;
    height: 2px;
    margin-top: -20px;
    z-index: 0;
}}

/* ── PEDIDO DISPLAY ── */
.vi-pedido-num {{
    font-family: 'Playfair Display', serif;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: .02em;
    line-height: 1;
    text-align: center;
    color: #1a1a2e;
    margin: 16px 0 6px;
}}
.vi-timer-display {{
    font-family: 'DM Mono', monospace;
    font-size: 1.2rem;
    font-weight: 500;
    text-align: center;
    color: #6b7280;
    letter-spacing: .1em;
    margin-bottom: 20px;
}}

/* ── BOTÕES GRANDES (INÍCIO / FIM) ── */
.btn-start > button {{
    background: linear-gradient(135deg, #1B5E20 0%, #388e3c 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: .04em !important;
    padding: 18px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: opacity .2s, transform .12s !important;
    box-shadow: 0 6px 20px rgba(27,94,32,.35) !important;
}}
.btn-start > button:hover {{
    opacity: .88 !important;
    transform: translateY(-2px) !important;
}}

.btn-stop > button {{
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: .04em !important;
    padding: 18px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: opacity .2s, transform .12s !important;
    box-shadow: 0 6px 20px rgba(127,29,29,.35) !important;
}}
.btn-stop > button:hover {{
    opacity: .88 !important;
    transform: translateY(-2px) !important;
}}

/* ── BOTÕES NORMAIS ── */
.stButton > button {{
    background: linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: .9rem !important;
    letter-spacing: .04em !important;
    padding: 12px 20px !important;
    font-family: 'DM Sans', sans-serif !important;
    width: 100%;
    transition: opacity .2s, transform .12s !important;
}}
.stButton > button:hover {{
    opacity: .85 !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="secondary"] {{
    background: #ffffff !important;
    border: 2px solid #e5e7eb !important;
    color: #374151 !important;
    box-shadow: none !important;
}}
.stButton > button[kind="secondary"]:hover {{
    background: #f9fafb !important;
    opacity: 1 !important;
    transform: none !important;
}}

/* ── INPUTS ── */
[data-testid="stTextInput"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stNumberInput"] label p {{
    color: #6b7280 !important;
    font-size: .68rem !important;
    font-weight: 700 !important;
    letter-spacing: .1em !important;
    text-transform: uppercase !important;
    font-family: 'DM Sans', sans-serif !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
    background: #fafafa !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 12px !important;
    color: #1a1a2e !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1.1rem !important;
    transition: border-color .2s !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background: #fafafa !important;
    border: 2px solid #e5e7eb !important;
    border-radius: 12px !important;
    color: #1a1a2e !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stNumberInput"] input:focus {{
    border-color: #8B0000 !important;
    box-shadow: 0 0 0 3px rgba(139,0,0,.12) !important;
}}

/* ── TELA DE TRANSIÇÃO (pergunta operador) ── */
.vi-transition-card {{
    background: #ffffff;
    border-radius: 24px;
    box-shadow: 0 8px 40px rgba(0,0,0,.12);
    padding: 32px 28px;
    text-align: center;
    animation: fadeUp .4s cubic-bezier(.22,1,.36,1) both;
}}
.vi-transition-next-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    border-radius: 30px;
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    margin: 12px 0 20px;
}}

/* ── MINI-STATS ── */
.vi-stat-row {{
    display: flex;
    gap: 10px;
    margin-top: 18px;
}}
.vi-stat-box {{
    flex: 1;
    background: #f7f5f2;
    border-radius: 14px;
    padding: 12px 8px;
    text-align: center;
    border: 1px solid #ece9e4;
}}
.vi-stat-label {{
    font-size: .58rem;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 4px;
}}
.vi-stat-val {{
    font-size: 1.3rem;
    font-weight: 700;
    color: #1a1a2e;
    font-family: 'DM Mono', monospace;
    line-height: 1;
}}

/* ── ÚLTIMO PEDIDO ── */
.vi-last-pedido {{
    background: #fff7f5;
    border: 1.5px solid rgba(139,0,0,.2);
    border-radius: 14px;
    padding: 12px 16px;
    margin-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}}

/* ── ALERTS ── */
.vi-alert {{
    padding: 12px 16px;
    border-radius: 12px;
    font-size: .82rem;
    font-weight: 500;
    margin: 10px 0;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}}
.vi-alert-ok    {{ background:rgba(27,94,32,.1);  border:1.5px solid rgba(76,175,80,.3);  color:#2e7d32; }}
.vi-alert-err   {{ background:rgba(139,0,0,.08);  border:1.5px solid rgba(220,38,38,.3);  color:#b91c1c; }}
.vi-alert-inf   {{ background:rgba(21,101,192,.1);border:1.5px solid rgba(66,165,245,.3);color:#1565C0; }}
.vi-alert-warn  {{ background:rgba(180,83,9,.1);  border:1.5px solid rgba(217,119,6,.3);  color:#b45309; }}

/* ── SELETOR DE OPERADOR (tela de transição) ── */
.vi-op-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 16px 0;
}}
.vi-op-btn {{
    background: #f7f5f2;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 12px 8px;
    cursor: pointer;
    transition: all .18s ease;
    text-align: center;
    font-size: .75rem;
    font-weight: 600;
    color: #374151;
    font-family: 'DM Sans', sans-serif;
}}
.vi-op-btn:hover {{
    border-color: #8B0000;
    background: #fff7f5;
    color: #8B0000;
}}
.vi-op-btn-selected {{
    border-color: #8B0000 !important;
    background: rgba(139,0,0,.08) !important;
    color: #8B0000 !important;
}}
.vi-avatar-sm {{
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: .8rem;
    font-weight: 700;
    color: #fff;
    margin: 0 auto 6px;
}}

/* ── CONCLUÍDO ── */
.vi-concluido-card {{
    background: linear-gradient(135deg, #1B5E20 0%, #2e7d32 100%);
    border-radius: 20px;
    padding: 28px 24px;
    text-align: center;
    color: #ffffff;
    box-shadow: 0 8px 28px rgba(27,94,32,.35);
    animation: vi-pop .5s cubic-bezier(.34,1.56,.64,1) both;
}}

@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes vi-pop {{
    from {{ opacity: 0; transform: scale(.85); }}
    to   {{ opacity: 1; transform: scale(1); }}
}}
@keyframes vi-spin {{
    to {{ transform: rotate(360deg); }}
}}
@keyframes vi-pulse {{
    0%,100% {{ opacity:1; }} 50% {{ opacity:.4; }}
}}

/* ── LOADING ── */
.vi-loading {{
    position: fixed;
    inset: 0;
    background: #f7f5f2;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}}
.vi-spinner {{
    width: 44px;
    height: 44px;
    border: 3px solid rgba(139,0,0,.18);
    border-top-color: #dc2626;
    border-radius: 50%;
    animation: vi-spin .75s linear infinite;
    margin: 18px auto 12px;
}}
.vi-loading-text {{
    font-size: .75rem;
    font-weight: 700;
    color: #9ca3af;
    letter-spacing: .14em;
    text-transform: uppercase;
    animation: vi-pulse 1.4s ease infinite;
}}

/* ── DIVISOR ── */
.vi-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, #e5e0d8, transparent);
    margin: 18px 0;
}}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS VISUAIS
# ============================================================
def tela_loading(mensagem="Carregando...", duracao=2.0):
    if _logo_src:
        img = f'<img src="{_logo_src}" style="height:48px;object-fit:contain;filter:drop-shadow(0 2px 8px rgba(139,0,0,.45));" />'
    else:
        img = '<div style="font-size:1.1rem;font-weight:900;color:#8B0000;letter-spacing:.12em;font-family:\'Playfair Display\',serif">VI LINGERIE</div>'
    ph = st.empty()
    ph.markdown(f'<div class="vi-loading">{img}<div class="vi-spinner"></div><div class="vi-loading-text">{mensagem}</div></div>', unsafe_allow_html=True)
    time.sleep(duracao)
    ph.empty()


def avatar_html(nome, size=44):
    partes = nome.strip().split()
    iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
    cores = ["#8B0000", "#1565C0", "#4A148C", "#1B5E20", "#E65100", "#880E4F", "#006064", "#37474F"]
    cor = cores[sum(ord(c) for c in nome) % len(cores)]
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{cor};display:flex;align-items:center;justify-content:center;font-size:{int(size*.36)}px;font-weight:700;color:#fff;flex-shrink:0;">{iniciais}</div>'


def stepper_html(etapa_atual):
    """Renderiza o stepper das 3 etapas."""
    html = '<div class="vi-stepper">'
    for i, (nome, icon) in enumerate(zip(ETAPA_NOMES_CURTOS, ETAPA_ICONS)):
        if i < etapa_atual:
            circle_style = f"background:{ETAPA_CORES[i]};color:#fff;"
            label_style  = f"color:{ETAPA_CORES[i]};"
            content = "✓"
        elif i == etapa_atual:
            circle_style = f"background:{ETAPA_CORES[i]};color:#fff;box-shadow:0 0 0 4px {ETAPA_CORES_LIGHT[i]};"
            label_style  = f"color:{ETAPA_CORES[i]};font-weight:700;"
            content = icon
        else:
            circle_style = "background:#e5e7eb;color:#9ca3af;"
            label_style  = "color:#9ca3af;"
            content = str(i + 1)

        html += f'''
        <div class="vi-step">
            <div class="vi-step-circle" style="{circle_style}">{content}</div>
            <div class="vi-step-label" style="{label_style}">{nome}</div>
        </div>
        '''
        if i < 2:
            line_bg = ETAPA_CORES[i] if i < etapa_atual else "#e5e7eb"
            html += f'<div class="vi-step-line" style="background:{line_bg}"></div>'

    html += '</div>'
    return html


def splash_once():
    if "_splash_done" not in st.session_state:
        tela_loading("Iniciando sistema de produção", duracao=2.2)
        st.session_state["_splash_done"] = True


# ============================================================
# TELA DE LOGIN DE GERÊNCIA
# ============================================================
def tela_login_gerencia():
    st.markdown(f"""
    <div class="vi-main-card">
        <div class="vi-card-header">
            <div class="vi-card-header-accent" style="background:#8B0000"></div>
            <div>{logo_tag}</div>
            <div>
                <div style="font-size:.65rem;font-weight:700;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase">Acesso</div>
                <div style="font-size:.95rem;font-weight:700;color:#1a1a2e">Área da Gerência</div>
            </div>
        </div>
        <div class="vi-card-body">
    """, unsafe_allow_html=True)

    senha = st.text_input("Senha de gerência", type="password", placeholder="••••••••")
    st.markdown("")
    if st.button("🔓 Acessar", use_container_width=True):
        if senha == SENHA_GERENCIA:
            st.session_state["_gerencia_ok"] = True
            st.rerun()
        else:
            st.markdown('<div class="vi-alert vi-alert-err">❌ Senha incorreta.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("← Voltar", use_container_width=True, type="secondary"):
        st.session_state.pop("_modo", None)
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)


# ============================================================
# TELA DE EXTRATO (GERÊNCIA)
# ============================================================
def tela_extrato():
    concluidos        = carregar_concluidos()
    pedidos_andamento = carregar_pedidos()
    historico         = carregar_historico()

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:20px;padding-top:8px">
        {logo_tag}
        <div style="font-size:1rem;font-weight:700;color:#1a1a2e;margin-top:4px">Extrato de Produção</div>
        <div style="font-size:.73rem;color:#6b7280">Consulta, filtros e download</div>
    </div>
    """, unsafe_allow_html=True)

    total_sep  = len([h for h in historico if h.get("etapa") == "Separação do Pedido"])
    total_emb  = len([h for h in historico if h.get("etapa") == "Mesa de Embalagem"])
    total_conf = len([h for h in historico if h.get("etapa") == "Conferência do Pedido"])
    total_conc = len(concluidos)

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, cor, bg in [
        (c1, "📦 Sep.", total_sep,  "#64b5f6", "rgba(21,101,192,.1)"),
        (c2, "📬 Emb.", total_emb,  "#ce93d8", "rgba(106,13,173,.1)"),
        (c3, "✅ Conf.", total_conf, "#a5d6a7", "rgba(27,94,32,.1)"),
        (c4, "🎯 Conc.", total_conc, "#f87171", "rgba(127,29,29,.1)"),
    ]:
        with col:
            st.markdown(f'<div style="background:{bg};border-radius:14px;padding:12px 6px;text-align:center;border:1px solid rgba(0,0,0,.08)"><div style="font-size:.58rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;font-weight:700;margin-bottom:2px">{label}</div><div style="font-size:1.6rem;font-weight:700;color:{cor}">{val}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
    aba1, aba2, aba3 = st.tabs(["📅 Histórico", "📋 Concluídos", "⏳ Em Andamento"])

    with aba1:
        if not historico:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação registrada ainda.</div>', unsafe_allow_html=True)
        else:
            df_hist = pd.DataFrame(historico)
            def parse_data(s):
                try:
                    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
                except:
                    return pd.NaT
            df_hist["_data_dt"] = df_hist["data"].apply(parse_data)

            col_f1, col_f2 = st.columns(2)
            from datetime import date, timedelta as td
            hoje = date.today()
            with col_f1:
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

            mask = (df_hist["_data_dt"] >= pd.Timestamp(data_ini)) & (df_hist["_data_dt"] <= pd.Timestamp(data_fim))
            df_filtrado = df_hist[mask].copy()
            if op_filtro != "Todos":
                df_filtrado = df_filtrado[df_filtrado["operador"] == op_filtro]
            if etapa_filtro != "Todas":
                df_filtrado = df_filtrado[df_filtrado["etapa"] == etapa_filtro]
            df_filtrado = df_filtrado.sort_values("data_hora", ascending=False)

            n_res = len(df_filtrado)
            st.markdown(f'<div class="vi-alert vi-alert-inf">🔍 <b>{n_res}</b> operação(ões) encontrada(s)</div>', unsafe_allow_html=True)

            if n_res > 0:
                if op_filtro == "Todos":
                    resumo = df_filtrado.groupby(["operador", "etapa"]).size().reset_index(name="qtd")
                    resumo.columns = ["Funcionário", "Etapa", "Qtd."]
                    st.dataframe(resumo, use_container_width=True, hide_index=True)
                    st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)

                df_exib = df_filtrado[["data_hora", "pedido", "operador", "etapa", "status_pedido"]].rename(columns={
                    "data_hora": "Data/Hora", "pedido": "Pedido",
                    "operador": "Funcionário", "etapa": "Etapa", "status_pedido": "Status"
                })
                df_exib["Status"] = df_exib["Status"].map({
                    "em_andamento": "⏳", "concluido": "✅"
                }).fillna(df_exib["Status"])
                st.dataframe(df_exib, use_container_width=True, hide_index=True)

                nome_arq = f"extrato_{op_filtro.replace(' ','_')}_{data_ini.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button("⬇️ CSV", data=df_exib.to_csv(index=False).encode("utf-8"),
                                       file_name=f"{nome_arq}.csv", mime="text/csv",
                                       use_container_width=True, key="dl_hist_csv")
                with col_dl2:
                    xlsx_buf = BytesIO()
                    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                        df_exib.to_excel(writer, index=False, sheet_name="Detalhado")
                    xlsx_buf.seek(0)
                    st.download_button("⬇️ Excel", data=xlsx_buf.getvalue(),
                                       file_name=f"{nome_arq}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True, key="dl_hist_xlsx")

    with aba2:
        if concluidos:
            df_conc = pd.DataFrame(concluidos)
            df_show = df_conc.rename(columns={
                "pedido": "Pedido", "op_sep": "Op. Sep.", "dt_sep": "Data Sep.",
                "op_emb": "Op. Emb.", "dt_emb": "Data Emb.",
                "op_conf": "Op. Conf.", "dt_conf": "Data Conf."
            }).drop(columns=["etapa"], errors="ignore")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.download_button("⬇️ CSV", data=df_show.to_csv(index=False).encode("utf-8"),
                                   file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv",
                                   mime="text/csv", use_container_width=True, key="dl_conc_csv")
            with col_c2:
                xlsx_buf2 = BytesIO()
                with pd.ExcelWriter(xlsx_buf2, engine="openpyxl") as writer:
                    df_show.to_excel(writer, index=False, sheet_name="Concluídos")
                xlsx_buf2.seek(0)
                st.download_button("⬇️ Excel", data=xlsx_buf2.getvalue(),
                                   file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True, key="dl_conc_xlsx")
        else:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido finalizado ainda.</div>', unsafe_allow_html=True)

    with aba3:
        if pedidos_andamento:
            rows = []
            etapa_labels = {1: "📬 Aguard. Embalagem", 2: "✅ Aguard. Conferência"}
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
    if st.button("← Sair da Gerência", use_container_width=True, type="secondary"):
        st.session_state.pop("_modo", None)
        st.session_state.pop("_gerencia_ok", None)
        st.rerun()


# ============================================================
# TELA DE SELEÇÃO DE OPERADOR
# ============================================================
def tela_selecao_operador():
    st.markdown(f"""
    <div style="text-align:center;padding:24px 0 12px">
        {logo_tag}
        <div style="font-size:1rem;font-weight:700;color:#1a1a2e;margin-top:4px">Apontamento de Produção</div>
        <div style="font-size:.73rem;color:#6b7280;margin-top:2px">Selecione seu nome para começar</div>
    </div>
    <div class="vi-divider"></div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.68rem;font-weight:700;color:#6b7280;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px">👤 Quem é você?</div>', unsafe_allow_html=True)

    operador = st.selectbox(
        "Selecione seu nome",
        options=["— Selecione —"] + OPERADORES,
        key="sel_operador_inicial",
        label_visibility="collapsed"
    )
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("▶  Entrar no sistema", use_container_width=True):
        if operador == "— Selecione —":
            st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione seu nome.</div>', unsafe_allow_html=True)
        else:
            st.session_state["_operador"]      = operador
            st.session_state["_turno_inicio"]  = time.time()
            st.session_state["_flow_state"]    = "idle"  # idle | running | transitioning | concluido
            st.session_state["_etapa_idx"]     = 0
            st.session_state["_pedido_atual"]  = None
            st.session_state["_ts_inicio"]     = None
            st.rerun()


# ============================================================
# TELA DE TRANSIÇÃO ENTRE ETAPAS
# ============================================================
def tela_transicao():
    """
    Pergunta se o próximo operador é o mesmo ou outro.
    Se outro → mostra grid de seleção.
    Ao confirmar → vai para tela da próxima etapa (ou concluído).
    """
    pedido_num     = st.session_state.get("_pedido_finalizado")
    etapa_concluida = st.session_state.get("_etapa_concluida", 0)  # 0,1,2
    proxima_etapa  = etapa_concluida + 1
    operador_atual = st.session_state.get("_operador", "")

    # ── Pedido totalmente concluído ──
    if etapa_concluida == 2:
        st.markdown(f"""
        <div class="vi-concluido-card">
            <div style="font-size:2.8rem;margin-bottom:10px">🎉</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:800;margin-bottom:6px">Pedido Concluído!</div>
            <div style="font-size:2.2rem;font-weight:700;font-family:'DM Mono',monospace;opacity:.9;margin:10px 0">#{pedido_num}</div>
            <div style="font-size:.82rem;opacity:.8">Todas as 3 etapas foram finalizadas com sucesso</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="btn-start">', unsafe_allow_html=True)
            if st.button("▶  Novo Pedido", use_container_width=True, key="btn_novo_concluido"):
                st.session_state["_flow_state"]   = "idle"
                st.session_state["_pedido_atual"] = None
                st.session_state["_ts_inicio"]    = None
                st.session_state["_etapa_idx"]    = 0
                st.session_state.pop("_pedido_finalizado", None)
                st.session_state.pop("_etapa_concluida", None)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            if st.button("Trocar operador", use_container_width=True, type="secondary", key="btn_trocar_op_conc"):
                for k in ["_operador", "_turno_inicio", "_flow_state", "_etapa_idx",
                          "_pedido_atual", "_ts_inicio", "_pedido_finalizado", "_etapa_concluida",
                          "_proximo_operador", "_trans_modo", "_ultimo_pedido_num",
                          "_ultimo_inicio", "_ultimo_fim"]:
                    st.session_state.pop(k, None)
                st.rerun()
        return

    # ── Transição entre etapas ──
    prox_icon  = ETAPA_ICONS[proxima_etapa]
    prox_nome  = ETAPAS[proxima_etapa]
    prox_cor   = ETAPA_CORES[proxima_etapa]
    prox_cor_l = ETAPA_CORES_LIGHT[proxima_etapa]

    st.markdown(f"""
    <div class="vi-transition-card">
        {stepper_html(proxima_etapa)}
        <div class="vi-divider"></div>
        <div style="font-size:.7rem;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px">Pedido</div>
        <div style="font-family:'Playfair Display',serif;font-size:2.4rem;font-weight:800;color:#1a1a2e">#{pedido_num}</div>
        <div class="vi-transition-next-badge" style="background:{prox_cor_l};color:{prox_cor};border:1.5px solid {prox_cor}44;margin:10px auto;">
            {prox_icon} Próxima: {prox_nome}
        </div>
        <div style="font-size:.88rem;font-weight:600;color:#374151;margin-bottom:6px">Quem vai realizar esta etapa?</div>
    </div>
    """, unsafe_allow_html=True)

    # Inicializa modo de transição
    if "_trans_modo" not in st.session_state:
        st.session_state["_trans_modo"] = None

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col_mesmo, col_outro = st.columns(2)
    with col_mesmo:
        st.markdown('<div class="btn-start">', unsafe_allow_html=True)
        if st.button(f"✅  Sou eu mesmo\n({operador_atual.split()[0]})", use_container_width=True, key="btn_mesmo_op"):
            st.session_state["_proximo_operador"] = operador_atual
            st.session_state["_trans_modo"]       = "confirmado"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_outro:
        if st.button("👤  Outro operador", use_container_width=True, type="secondary", key="btn_outro_op"):
            st.session_state["_trans_modo"] = "selecionando"
            st.rerun()

    # ── Selecionando outro operador ──
    if st.session_state.get("_trans_modo") == "selecionando":
        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.68rem;font-weight:700;color:#6b7280;letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px">Selecione o operador</div>', unsafe_allow_html=True)

        outro_op = st.selectbox(
            "Operador",
            options=["— Selecione —"] + [op for op in OPERADORES if op != operador_atual],
            key="sel_outro_op",
            label_visibility="collapsed"
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("▶  Confirmar e Iniciar", use_container_width=True, key="btn_confirma_outro"):
            if outro_op == "— Selecione —":
                st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione um operador.</div>', unsafe_allow_html=True)
            else:
                st.session_state["_proximo_operador"] = outro_op
                st.session_state["_trans_modo"]       = "confirmado"
                st.rerun()

    # ── Confirmado → avança ──
    if st.session_state.get("_trans_modo") == "confirmado":
        proximo_op = st.session_state.get("_proximo_operador", operador_atual)
        st.session_state["_operador"]     = proximo_op
        st.session_state["_etapa_idx"]   = proxima_etapa
        st.session_state["_flow_state"]  = "idle"
        st.session_state["_pedido_atual"] = pedido_num  # mantém pedido para a próxima etapa
        st.session_state["_ts_inicio"]   = None
        st.session_state.pop("_pedido_finalizado", None)
        st.session_state.pop("_etapa_concluida", None)
        st.session_state.pop("_trans_modo", None)
        st.rerun()


# ============================================================
# TELA PRINCIPAL DO OPERADOR (fluxo início/fim)
# ============================================================
def tela_operador_fluxo():
    import time as _time

    operador      = st.session_state.get("_operador", "")
    etapa_idx     = st.session_state.get("_etapa_idx", 0)
    flow_state    = st.session_state.get("_flow_state", "idle")  # idle | running
    pedido_atual  = st.session_state.get("_pedido_atual")
    ts_inicio     = st.session_state.get("_ts_inicio")
    turno_inicio  = st.session_state.get("_turno_inicio", _time.time())

    hoje_str   = agora_str().split(" ")[0]
    historico  = carregar_historico()
    hist_hoje  = [h for h in historico if h.get("operador") == operador and h.get("data") == hoje_str]
    pedidos_hoje = len(hist_hoje)

    etapa_nome  = ETAPAS[etapa_idx]
    etapa_icon  = ETAPA_ICONS[etapa_idx]
    etapa_cor   = ETAPA_CORES[etapa_idx]
    etapa_cor_l = ETAPA_CORES_LIGHT[etapa_idx]

    ultimo_inicio   = st.session_state.get("_ultimo_inicio")
    ultimo_fim      = st.session_state.get("_ultimo_fim")
    ultimo_pedido_n = st.session_state.get("_ultimo_pedido_num")

    h_turno = fmt_tempo(_time.time() - turno_inicio)
    h_inicio_turno = datetime.fromtimestamp(turno_inicio).strftime("%H:%M")

    # ── CABEÇALHO ──
    st.markdown(f"""
    <div class="vi-main-card">
        <div class="vi-card-header">
            <div class="vi-card-header-accent" style="background:{etapa_cor}"></div>
            {avatar_html(operador, 44)}
            <div style="flex:1">
                <div style="font-size:.62rem;font-weight:700;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase">{operador}</div>
                <div class="vi-etapa-badge" style="background:{etapa_cor_l};color:{etapa_cor};border:1.5px solid {etapa_cor}44;margin-top:4px">
                    {etapa_icon} {etapa_nome}
                </div>
            </div>
            <div style="text-align:right">{logo_tag.replace('margin:0 auto 6px','margin:0')}</div>
        </div>
        <div class="vi-card-body">
            {stepper_html(etapa_idx)}
    """, unsafe_allow_html=True)

    # ══════════════════════════════
    # ESTADO: IDLE (aguardando início)
    # ══════════════════════════════
    if flow_state == "idle":

        if etapa_idx == 0:
            # Separação: digita número
            st.markdown('<div style="font-size:.68rem;font-weight:700;color:#6b7280;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">Número do Pedido</div>', unsafe_allow_html=True)
            num = st.text_input(
                "", placeholder="Ex: 12345",
                key="inp_num_pedido", label_visibility="collapsed"
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="btn-start">', unsafe_allow_html=True)
            if st.button("▶  INICIAR SEPARAÇÃO", use_container_width=True, key="btn_iniciar_sep"):
                num = num.strip()
                pedidos_db = carregar_pedidos()
                if not num:
                    st.markdown('<div class="vi-alert vi-alert-err">⚠️ Informe o número do pedido.</div>', unsafe_allow_html=True)
                elif num in pedidos_db:
                    st.markdown(f'<div class="vi-alert vi-alert-err">⚠️ Pedido #{num} já está em andamento.</div>', unsafe_allow_html=True)
                else:
                    st.session_state["_pedido_atual"] = num
                    st.session_state["_flow_state"]   = "running"
                    st.session_state["_ts_inicio"]    = _time.time()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            # Embalagem ou Conferência: seleciona de lista
            pedidos_db   = carregar_pedidos()
            chave_op     = "op_emb" if etapa_idx == 1 else "op_conf"
            etapa_needed = 1 if etapa_idx == 1 else 2
            disponiveis  = sorted([
                p for p, d in pedidos_db.items()
                if d.get("etapa") == etapa_needed and chave_op not in d
            ])

            if pedido_atual and pedido_atual in disponiveis:
                # Pedido já vinculado (veio da transição) → inicia direto
                st.markdown(f"""
                <div style="background:{etapa_cor_l};border:1.5px solid {etapa_cor}44;border-radius:14px;padding:14px 18px;text-align:center;margin-bottom:16px">
                    <div style="font-size:.62rem;font-weight:700;color:{etapa_cor};letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px">Pedido vinculado da etapa anterior</div>
                    <div style="font-family:'Playfair Display',serif;font-size:2rem;font-weight:800;color:#1a1a2e">#{pedido_atual}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<div class="btn-start">', unsafe_allow_html=True)
                if st.button(f"▶  INICIAR {ETAPA_NOMES_CURTOS[etapa_idx].upper()}", use_container_width=True, key="btn_iniciar_vinc"):
                    st.session_state["_flow_state"] = "running"
                    st.session_state["_ts_inicio"]  = _time.time()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("Escolher outro pedido", use_container_width=True, type="secondary", key="btn_outro_ped"):
                    st.session_state["_pedido_atual"] = None
                    st.rerun()

            elif not disponiveis:
                st.markdown(f'<div class="vi-alert vi-alert-warn">⏳ Nenhum pedido disponível para <b>{etapa_nome}</b>. Aguarde a etapa anterior ser concluída.</div>', unsafe_allow_html=True)
                st.session_state["_pedido_atual"] = None

            else:
                st.markdown(f'<div style="font-size:.68rem;font-weight:700;color:#6b7280;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">Selecione o Pedido</div>', unsafe_allow_html=True)
                pedido_sel = st.selectbox(
                    "", options=["— Selecione —"] + disponiveis,
                    key=f"sel_ped_{etapa_idx}", label_visibility="collapsed"
                )
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="btn-start">', unsafe_allow_html=True)
                if st.button(f"▶  INICIAR {ETAPA_NOMES_CURTOS[etapa_idx].upper()}", use_container_width=True, key="btn_iniciar_sel"):
                    if pedido_sel == "— Selecione —":
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["_pedido_atual"] = pedido_sel
                        st.session_state["_flow_state"]   = "running"
                        st.session_state["_ts_inicio"]    = _time.time()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════
    # ESTADO: RUNNING (em execução)
    # ══════════════════════════════
    elif flow_state == "running":
        elapsed = fmt_tempo(_time.time() - ts_inicio) if ts_inicio else "--:--:--"

        st.markdown(f"""
        <div style="text-align:center;margin-bottom:8px">
            <div style="font-size:.65rem;color:#9ca3af;letter-spacing:.12em;text-transform:uppercase;margin-bottom:2px">Em Operação</div>
            <div class="vi-pedido-num">#{pedido_atual}</div>
            <div class="vi-timer-display">⏱ {elapsed}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="btn-stop">', unsafe_allow_html=True)
        if st.button("⏹  FINALIZAR", use_container_width=True, key="btn_finalizar"):
            now    = agora_str()
            ts_fim = _time.time()
            pedidos_db = carregar_pedidos()

            if etapa_idx == 0:
                pedidos_db[pedido_atual] = {
                    "pedido": pedido_atual, "etapa": 1,
                    "op_sep": operador, "dt_sep": now
                }
                registrar_historico(pedido_atual, operador, "Separação do Pedido", now, "em_andamento")

            elif etapa_idx == 1:
                if pedido_atual in pedidos_db:
                    pedidos_db[pedido_atual]["etapa"]  = 2
                    pedidos_db[pedido_atual]["op_emb"] = operador
                    pedidos_db[pedido_atual]["dt_emb"] = now
                    registrar_historico(pedido_atual, operador, "Mesa de Embalagem", now, "em_andamento")

            elif etapa_idx == 2:
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
            st.session_state["_pedido_finalizado"] = pedido_atual
            st.session_state["_etapa_concluida"]   = etapa_idx
            st.session_state["_flow_state"]        = "transitioning"
            st.session_state["_pedido_atual"]      = None
            st.session_state["_ts_inicio"]         = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Cancelar operação", use_container_width=True, type="secondary", key="btn_cancelar"):
            st.session_state["_flow_state"]   = "idle"
            st.session_state["_pedido_atual"] = None
            st.session_state["_ts_inicio"]    = None
            st.rerun()

    # ── Fechamento do card ──
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Resumo do turno ──
    st.markdown(f"""
    <div class="vi-stat-row">
        <div class="vi-stat-box">
            <div class="vi-stat-label">Pedidos hoje</div>
            <div class="vi-stat-val" style="color:#1B5E20">{pedidos_hoje}</div>
        </div>
        <div class="vi-stat-box">
            <div class="vi-stat-label">Início turno</div>
            <div class="vi-stat-val" style="font-size:1rem">{h_inicio_turno}</div>
        </div>
        <div class="vi-stat-box">
            <div class="vi-stat-label">Tempo turno</div>
            <div class="vi-stat-val" style="font-size:.95rem">{h_turno}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Último pedido ──
    if ultimo_pedido_n and ultimo_inicio and ultimo_fim:
        dur = ultimo_fim - ultimo_inicio
        st.markdown(f"""
        <div class="vi-last-pedido">
            <div>
                <div style="font-size:.6rem;font-weight:700;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase">⏱ Último pedido</div>
                <div style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#1a1a2e">#{ultimo_pedido_n}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:.7rem;color:#6b7280">{datetime.fromtimestamp(ultimo_inicio).strftime("%H:%M:%S")} → {datetime.fromtimestamp(ultimo_fim).strftime("%H:%M:%S")}</div>
                <div style="font-family:'DM Mono',monospace;font-weight:700;color:#8B0000;font-size:.9rem">{fmt_tempo(dur)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Botão trocar operador ──
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("⏏  Trocar operador / Sair", use_container_width=True, type="secondary", key="btn_sair"):
        for k in ["_operador", "_turno_inicio", "_flow_state", "_etapa_idx",
                  "_pedido_atual", "_ts_inicio", "_pedido_finalizado", "_etapa_concluida",
                  "_proximo_operador", "_trans_modo", "_ultimo_pedido_num",
                  "_ultimo_inicio", "_ultimo_fim"]:
            st.session_state.pop(k, None)
        st.rerun()


# ============================================================
# TELA INICIAL (escolha operador / gerência)
# ============================================================
def tela_inicial():
    st.markdown(f"""
    <div style="text-align:center;padding:32px 0 20px">
        {logo_tag}
        <div style="font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:800;color:#1a1a2e;margin-top:6px">Sistema de Produção</div>
        <div style="font-size:.72rem;color:#9ca3af;margin-top:3px;letter-spacing:.06em">Vi Lingerie · Linha de Montagem</div>
    </div>
    <div class="vi-divider"></div>
    <div style="font-size:.68rem;font-weight:700;color:#6b7280;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px">🚀 Como deseja acessar?</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:#fff;border:2px solid #e5e7eb;border-radius:18px;padding:22px 16px;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.08)">
            <div style="font-size:2rem;margin-bottom:8px">🏭</div>
            <div style="font-size:.9rem;font-weight:700;color:#1a1a2e">Operador</div>
            <div style="font-size:.68rem;color:#9ca3af;margin-top:4px">Registrar etapas de produção</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Entrar como Operador", use_container_width=True, key="btn_op"):
            st.session_state["_modo"] = "operador"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background:#fff;border:2px solid #e5e7eb;border-radius:18px;padding:22px 16px;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,.08)">
            <div style="font-size:2rem;margin-bottom:8px">📊</div>
            <div style="font-size:.9rem;font-weight:700;color:#1a1a2e">Gerência</div>
            <div style="font-size:.68rem;color:#9ca3af;margin-top:4px">Extrato e relatórios</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Entrar como Gerência", use_container_width=True, type="secondary", key="btn_ger"):
            st.session_state["_modo"] = "gerencia"
            st.rerun()


# ============================================================
# ROTEADOR PRINCIPAL
# ============================================================
splash_once()

modo = st.session_state.get("_modo")

if not modo:
    tela_inicial()

elif modo == "gerencia":
    if not st.session_state.get("_gerencia_ok"):
        tela_login_gerencia()
    else:
        tela_extrato()

elif modo == "operador":
    # Sem operador selecionado → tela de seleção
    if "_operador" not in st.session_state:
        tela_selecao_operador()

    # Em transição entre etapas
    elif st.session_state.get("_flow_state") == "transitioning":
        tela_transicao()

    # Fluxo normal (idle ou running)
    else:
        tela_operador_fluxo()
