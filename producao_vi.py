import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import BytesIO
import base64 as _b64

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="centered",
    page_icon="🏭",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONSTANTES E VARIÁVEIS
# ============================================================
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

# ============================================================
# FUNÇÕES DE ESTADO E DADOS
# ============================================================
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
    max-width: 600px !important; /* Ajustado levemente para monitores */
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
    font-size: 1.8rem;
    font-weight: 500;
    text-align: center;
    color: #6b7280;
    letter-spacing: .1em;
    margin-bottom: 24px;
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
    text-align: center;
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

@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
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
    if not nome or nome == "— Selecione —":
        iniciais = "??"
    else:
        partes = nome.strip().split()
        iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
    
    cores = ["#8B0000", "#1565C0", "#4A148C", "#1B5E20", "#E65100", "#880E4F", "#006064", "#37474F"]
    cor = cores[sum(ord(c) for c in nome) % len(cores)]
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{cor};display:flex;align-items:center;justify-content:center;font-size:{int(size*.36)}px;font-weight:700;color:#fff;flex-shrink:0;">{iniciais}</div>'

def stepper_html(etapa_atual):
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
# TELAS DE LOGIN E GERÊNCIA
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
                    st.download_button("⬇️ CSV", data=df_exib.to_csv(index=False).encode("utf-8"), file_name=f"{nome_arq}.csv", mime="text/csv", use_container_width=True)
                with col_dl2:
                    xlsx_buf = BytesIO()
                    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                        df_exib.to_excel(writer, index=False, sheet_name="Detalhado")
                    st.download_button("⬇️ Excel", data=xlsx_buf.getvalue(), file_name=f"{nome_arq}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    with aba2:
        if concluidos:
            df_conc = pd.DataFrame(concluidos)
            df_show = df_conc.rename(columns={
                "pedido": "Pedido", "op_sep": "Op. Sep.", "dt_sep": "Data Sep.",
                "op_emb": "Op. Emb.", "dt_emb": "Data Emb.",
                "op_conf": "Op. Conf.", "dt_conf": "Data Conf."
            }).drop(columns=["etapa"], errors="ignore")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
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
            st.session_state["_flow_state"]    = "idle"
            st.session_state["_etapa_idx"]     = 0
            st.session_state["_pedido_atual"]  = None
            st.session_state["_ts_inicio"]     = None
            st.rerun()


# ============================================================
# TELA DE OPERAÇÃO UNIFICADA (FLUXO CONTÍNUO)
# ============================================================
def tela_operacao():
    operador = st.session_state.get("_operador", "Operador")
    flow_state = st.session_state.get("_flow_state", "idle") # idle | aguardando_inicio | running | transicao
    etapa_idx = st.session_state.get("_etapa_idx", 0)
    pedido_atual = st.session_state.get("_pedido_atual")

    pedidos = carregar_pedidos()

    # ── HEADER FIXO (Sempre visível) ──
    st.markdown(f"""
    <div class="vi-main-card" style="margin-bottom:16px;">
        <div class="vi-card-header" style="justify-content:space-between; padding: 16px 24px;">
            <div class="vi-card-header-accent" style="background:{ETAPA_CORES[min(etapa_idx, 2)]}"></div>
            <div style="display:flex;align-items:center;gap:12px;">
                {avatar_html(operador, size=38)}
                <div>
                    <div style="font-size:.60rem;font-weight:700;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase">Estação Central</div>
                    <div style="font-size:.95rem;font-weight:700;color:#1a1a2e;line-height:1.1">{operador}</div>
                </div>
            </div>
            <div>
                <div class="vi-etapa-badge" style="background:{ETAPA_CORES_LIGHT[min(etapa_idx, 2)]};color:{ETAPA_CORES[min(etapa_idx, 2)]};border:1px solid {ETAPA_CORES[min(etapa_idx, 2)]}44">
                    {ETAPA_ICONS[min(etapa_idx, 2)]} {ETAPA_NOMES_CURTOS[min(etapa_idx, 2)]}
                </div>
            </div>
        </div>
        <div class="vi-card-body" style="padding: 16px 24px 24px;">
    """, unsafe_allow_html=True)

    # ── 1. ESTADO: IDLE (Aguardando Pedido) ──
    if flow_state == "idle":
        st.markdown('<div style="text-align:center; font-size:.85rem;font-weight:700;color:#374151;margin-bottom:12px">Bipar ou digitar número do pedido:</div>', unsafe_allow_html=True)
        novo_pedido = st.text_input("Número do pedido", placeholder="Ex: 12345", key="inp_pedido_idle", label_visibility="collapsed")
        
        st.markdown('<div class="btn-start" style="margin-top:16px;">', unsafe_allow_html=True)
        if st.button("▶ BUSCAR PEDIDO", key="btn_buscar"):
            if not novo_pedido.strip():
                st.markdown('<div class="vi-alert vi-alert-err">⚠️ Digite o número do pedido.</div>', unsafe_allow_html=True)
            else:
                num = novo_pedido.strip().upper()
                # Regras de Negócio Iniciais
                if num in pedidos:
                    st.session_state["_pedido_atual"] = num
                    st.session_state["_etapa_idx"] = pedidos[num].get("etapa", 0)
                else:
                    pedidos[num] = {"pedido": num, "etapa": 0}
                    salvar_pedidos(pedidos)
                    st.session_state["_pedido_atual"] = num
                    st.session_state["_etapa_idx"] = 0
                
                st.session_state["_flow_state"] = "aguardando_inicio"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Se houver um pedido ativo, mostramos o Stepper e o número do pedido
    if flow_state in ["aguardando_inicio", "running", "transicao"] and pedido_atual:
        st.markdown(stepper_html(etapa_idx), unsafe_allow_html=True)
        st.markdown(f'<div class="vi-pedido-num" style="font-size: 2.6rem; margin: 8px 0;">#{pedido_atual}</div>', unsafe_allow_html=True)

    # ── 2. ESTADO: AGUARDANDO INÍCIO DA ETAPA ──
    if flow_state == "aguardando_inicio":
        st.markdown('<div class="btn-start">', unsafe_allow_html=True)
        if st.button(f"▶ INICIAR {ETAPA_NOMES_CURTOS[etapa_idx].upper()}", key="btn_iniciar_etapa"):
            st.session_state["_flow_state"] = "running"
            st.session_state["_ts_inicio"] = time.time()
            registrar_historico(pedido_atual, operador, ETAPAS[etapa_idx], agora_str(), "em_andamento")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 3. ESTADO: RUNNING (Rodando) ──
    elif flow_state == "running":
        tempo_decorrido = time.time() - st.session_state.get("_ts_inicio", time.time())
        st.markdown(f'<div class="vi-timer-display" id="timer_display">⏱ {fmt_tempo(tempo_decorrido)}</div>', unsafe_allow_html=True)
        
        # Refresh automático do cronômetro
        time.sleep(1)
        st.rerun()

        st.markdown('<div class="btn-stop">', unsafe_allow_html=True)
        if st.button(f"⏹ CONCLUIR {ETAPA_NOMES_CURTOS[etapa_idx].upper()}", key="btn_concluir_etapa"):
            # Salvar dados da etapa concluída
            pedidos_atuais = carregar_pedidos()
            campos_op = ["op_sep", "op_emb", "op_conf"]
            campos_dt = ["dt_sep", "dt_emb", "dt_conf"]
            
            pedidos_atuais[pedido_atual][campos_op[etapa_idx]] = operador
            pedidos_atuais[pedido_atual][campos_dt[etapa_idx]] = agora_str()
            registrar_historico(pedido_atual, operador, ETAPAS[etapa_idx], agora_str(), "concluido")

            if etapa_idx == 2: # Última etapa concluída
                concluidos = carregar_concluidos()
                concluidos.append(pedidos_atuais[pedido_atual])
                salvar_concluidos(concluidos)
                del pedidos_atuais[pedido_atual]
                salvar_pedidos(pedidos_atuais)
                
                st.session_state["_flow_state"] = "idle"
                st.session_state["_pedido_atual"] = None
                st.session_state["_etapa_idx"] = 0
                st.balloons() # Feedback de sucesso
                st.rerun()
            else:
                pedidos_atuais[pedido_atual]["etapa"] = etapa_idx + 1
                salvar_pedidos(pedidos_atuais)
                st.session_state["_etapa_idx"] = etapa_idx + 1
                st.session_state["_flow_state"] = "transicao"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── 4. ESTADO: TRANSIÇÃO (Mesmo operador ou outro?) ──
    elif flow_state == "transicao":
        st.markdown(f"""
        <div style="background:{ETAPA_CORES_LIGHT[etapa_idx]}; border: 1px solid {ETAPA_CORES[etapa_idx]}44; border-radius: 12px; padding: 12px; text-align:center; margin-bottom: 16px;">
            <div style="font-size:.8rem; font-weight:700; color:{ETAPA_CORES[etapa_idx]};">✅ Etapa anterior concluída!</div>
            <div style="font-size:.9rem; font-weight:700; color:#1a1a2e; margin-top:4px;">Quem fará a {ETAPAS[etapa_idx]}?</div>
        </div>
        """, unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            if st.button(f"👤 Continuar comigo", use_container_width=True, key="btn_eu_mesmo"):
                st.session_state["_flow_state"] = "aguardando_inicio"
                st.session_state.pop("_trans_modo", None)
                st.rerun()
        
        with colB:
            if st.button("👥 Outro operador", use_container_width=True, type="secondary", key="btn_outro_op"):
                st.session_state["_trans_modo"] = "selecionar"
                st.rerun()

        if st.session_state.get("_trans_modo") == "selecionar":
            st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
            novo_op = st.selectbox(
                "Selecione o operador:", 
                options=["— Selecione —"] + OPERADORES, 
                label_visibility="collapsed", 
                key="sel_trans_op"
            )
            if st.button("Confirmar Troca", use_container_width=True):
                if novo_op == "— Selecione —":
                    st.warning("Selecione um operador na lista.")
                else:
                    st.session_state["_operador"] = novo_op
                    st.session_state["_flow_state"] = "aguardando_inicio"
                    st.session_state.pop("_trans_modo", None)
                    st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Botão super discreto no rodapé apenas para trocar operador geral / sair
    st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
    if st.button("↺ Sair da Estação / Trocar Operador", type="secondary", use_container_width=False):
        st.session_state.pop("_operador", None)
        st.session_state.pop("_flow_state", None)
        st.session_state.pop("_pedido_atual", None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# CONTROLE DE FLUXO PRINCIPAL E ENTRYPOINT
# ============================================================
def main():
    splash_once()

    if "_gerencia_ok" in st.session_state and st.session_state["_gerencia_ok"]:
        tela_extrato()
        return

    if "_modo" in st.session_state and st.session_state["_modo"] == "gerencia":
        tela_login_gerencia()
        return

    if "_operador" not in st.session_state:
        tela_selecao_operador()
        st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
        if st.button("🔐 Acesso Gerência", type="secondary", use_container_width=True):
            st.session_state["_modo"] = "gerencia"
            st.rerun()
        return

    # O operador está logado. Toda a mágica agora acontece em uma única tela.
    tela_operacao()

if __name__ == "__main__":
    main()
