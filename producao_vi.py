import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO
import base64

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="wide",
    page_icon="🧵",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONSTANTES
# ============================================================
ETAPAS = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_ICONS = ["📦", "📬", "✅"]
ETAPA_CORES = ["#1976D2", "#7B1FA2", "#2E7D32"]  # azul, roxo, verde (para detalhes)
ETAPA_NOMES_CURTOS = ["Separação", "Embalagem", "Conferência"]

OPERADORES = [
    "Lucivanio", "Enágio", "Daniel", "Ítalo", "Cildenir",
    "Samya", "Neide", "Eduardo", "Talyson",
]

SENHA_GERENCIA = "vi2026"

# Diretório para armazenar os JSONs
STATE_DIR = "vi_producao_state"
os.makedirs(STATE_DIR, exist_ok=True)

FILE_PEDIDOS = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS = os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO = os.path.join(STATE_DIR, "historico.json")

# ============================================================
# FUNÇÕES DE PERSISTÊNCIA
# ============================================================
def _carregar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {} if "pedidos" in path else []

def _salvar(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def carregar_pedidos():
    return _carregar(FILE_PEDIDOS)

def salvar_pedidos(data):
    _salvar(FILE_PEDIDOS, data)

def carregar_concluidos():
    return _carregar(FILE_CONCLUIDOS)

def salvar_concluidos(data):
    _salvar(FILE_CONCLUIDOS, data)

def carregar_historico():
    return _carregar(FILE_HISTORICO)

def salvar_historico(data):
    _salvar(FILE_HISTORICO, data)

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
    salvar_historico(hist)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def agora_str():
    br = timezone(timedelta(hours=-3))
    return datetime.now(br).strftime("%d/%m/%Y %H:%M")

def fmt_tempo(segundos):
    if segundos is None or segundos <= 0:
        return "---"
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def avatar_html(nome, size=40):
    partes = nome.strip().split()
    iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
    cores = ["#1976D2", "#7B1FA2", "#2E7D32", "#C2185B", "#F57C00", "#546E7A"]
    cor = cores[sum(ord(c) for c in nome) % len(cores)]
    return f"""
    <div style="width:{size}px; height:{size}px; border-radius:50%;
                background:{cor}; display:flex; align-items:center;
                justify-content:center; font-size:{size*0.4}px;
                font-weight:700; color:white; flex-shrink:0;">
        {iniciais}
    </div>
    """

def logo_html():
    # Tenta carregar imagem local, caso contrário texto
    logo_paths = ["logo_vi.png", "../logo_vi.png"]
    for p in logo_paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/png;base64,{b64}" style="height:44px; object-fit:contain;">'
    return '<div style="font-size:1.8rem; font-weight:900; color:#2c3e50;">VI</div>'

# ============================================================
# CSS GLOBAL (TEMA CLARO)
# ============================================================
st.markdown("""
<style>
    /* RESET E FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [data-testid="stApp"] {
        font-family: 'Inter', sans-serif;
        background: #ffffff !important;
        color: #1e293b !important;
        height: 100vh;
        overflow: hidden;
    }

    /* Remove sidebar e cabeçalho padrão */
    [data-testid="stSidebar"], header[data-testid="stHeader"],
    [data-testid="stToolbar"], [data-testid="stDecoration"] {
        display: none !important;
    }

    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        height: 100vh;
    }

    /* Cards e containers */
    .vi-card {
        background: #ffffff;
        border-radius: 24px;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.08);
        padding: 24px 20px;
        border: 1px solid #e9eef2;
    }

    .vi-divider {
        height: 1px;
        background: #e2e8f0;
        margin: 20px 0;
    }

    /* Badges */
    .vi-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 30px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .vi-badge-success {
        background: #e8f5e9;
        color: #2e7d32;
        border: 1px solid #c8e6c9;
    }
    .vi-badge-warning {
        background: #fff3e0;
        color: #ef6c00;
        border: 1px solid #ffe0b2;
    }
    .vi-badge-info {
        background: #e3f2fd;
        color: #1565c0;
        border: 1px solid #bbdefb;
    }

    /* Alertas */
    .vi-alert {
        padding: 12px 16px;
        border-radius: 16px;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 8px 0;
    }
    .vi-alert-info {
        background: #e3f2fd;
        border: 1px solid #bbdefb;
        color: #1565c0;
    }
    .vi-alert-success {
        background: #e8f5e9;
        border: 1px solid #c8e6c9;
        color: #2e7d32;
    }
    .vi-alert-warning {
        background: #fff3e0;
        border: 1px solid #ffe0b2;
        color: #ef6c00;
    }
    .vi-alert-error {
        background: #ffebee;
        border: 1px solid #ffcdd2;
        color: #c62828;
    }

    /* Estatísticas */
    .vi-stat {
        background: #f8fafc;
        border-radius: 16px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 8px;
    }
    .vi-stat-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .vi-stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.2;
    }

    /* Histórico item */
    .vi-history-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .vi-history-pedido {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 1rem;
        color: #0f172a;
    }
    .vi-history-meta {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 2px;
    }

    /* Número grande do pedido */
    .vi-big-number {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 3.2rem;
        color: #0f172a;
        text-align: center;
        line-height: 1.2;
        margin: 8px 0;
    }
    .vi-timer {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 500;
        color: #475569;
        text-align: center;
        letter-spacing: 2px;
        margin: 4px 0 16px;
    }

    /* Botões personalizados */
    .stButton > button {
        border-radius: 14px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 12px 20px !important;
        transition: all 0.2s !important;
        border: none !important;
        box-shadow: 0 4px 6px -2px rgba(0,0,0,0.05) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1) !important;
    }

    /* Botão primário (iniciar) */
    div[data-testid="column"]:has(> .vi-btn-primary) .stButton > button {
        background: linear-gradient(135deg, #1976D2, #42a5f5) !important;
        color: white !important;
    }
    /* Botão finalizar */
    div[data-testid="column"]:has(> .vi-btn-danger) .stButton > button {
        background: linear-gradient(135deg, #d32f2f, #ef5350) !important;
        color: white !important;
    }
    /* Botão secundário */
    .stButton > button {
        background: white !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Inputs */
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
        background: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 14px !important;
        padding: 12px !important;
        font-family: 'JetBrains Mono', monospace !important;
        color: #0f172a !important;
    }
    [data-testid="stTextInput"] label, [data-testid="stSelectbox"] label {
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {
        background: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 14px !important;
    }

    /* Layout das colunas centrais */
    .vi-layout {
        display: grid;
        grid-template-columns: 280px 1fr 1fr 1fr 280px;
        height: 100vh;
        gap: 1px;
        background: #e9eef2;
    }
    .vi-panel-left, .vi-panel-right {
        background: white;
        padding: 24px 16px;
        overflow-y: auto;
    }
    .vi-center-col {
        background: white;
        padding: 24px 16px;
        overflow-y: auto;
        border-left: 1px solid #e9eef2;
        border-right: 1px solid #e9eef2;
    }

    /* Animações */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(211,47,47,0.3); }
        70% { box-shadow: 0 0 0 10px rgba(211,47,47,0); }
        100% { box-shadow: 0 0 0 0 rgba(211,47,47,0); }
    }
    .pulse {
        animation: pulse-border 2s infinite;
        border-radius: 16px;
    }

    /* Scrollbar fina */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TELA INICIAL
# ============================================================
def tela_inicial():
    st.markdown("<div style='height:15vh'></div>", unsafe_allow_html=True)
    cols = st.columns([1,1.2,1])
    with cols[1]:
        st.markdown(f"""
        <div class="vi-card" style="text-align:center;">
            {logo_html()}
            <h2 style="font-size:1.8rem; margin:16px 0 4px; color:#0f172a;">Sistema de Produção</h2>
            <p style="color:#64748b; font-size:0.9rem;">Vi Lingerie · Linha de Montagem</p>
            <div class="vi-divider"></div>
            <p style="font-weight:600; color:#475569; text-transform:uppercase; font-size:0.8rem;">Como deseja acessar?</p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div style="background:#f8fafc; border-radius:20px; padding:20px; border:1px solid #e2e8f0; text-align:center;">
                <div style="font-size:2.5rem;">👤</div>
                <div style="font-weight:700;">Operador</div>
                <div style="font-size:0.75rem; color:#64748b;">Registrar produção</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶ Entrar", key="btn_op", use_container_width=True):
                st.session_state["_modo"] = "operador"
                st.rerun()
        with c2:
            st.markdown("""
            <div style="background:#f8fafc; border-radius:20px; padding:20px; border:1px solid #e2e8f0; text-align:center;">
                <div style="font-size:2.5rem;">📊</div>
                <div style="font-weight:700;">Gerência</div>
                <div style="font-size:0.75rem; color:#64748b;">Extrato e relatórios</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔓 Acessar", key="btn_ger", use_container_width=True):
                st.session_state["_modo"] = "gerencia"
                st.rerun()

        st.markdown("<p style='text-align:center; color:#94a3b8; font-size:0.7rem; margin-top:32px;'>vi lingerie · sistema interno v2.0</p>", unsafe_allow_html=True)

# ============================================================
# SELEÇÃO DE OPERADOR
# ============================================================
def tela_selecao_operador():
    st.markdown("<div style='height:15vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1.4,1])
    with col:
        st.markdown(f"""
        <div class="vi-card" style="text-align:center;">
            {logo_html()}
            <h3 style="margin:12px 0 4px;">Identificação do Operador</h3>
            <p style="color:#64748b;">Selecione seu nome para começar</p>
            <div class="vi-divider"></div>
        </div>
        """, unsafe_allow_html=True)

        operador = st.selectbox(
            "Selecione seu nome",
            options=["— Selecione —"] + OPERADORES,
            key="sel_operador_inicial"
        )
        if st.button("▶ Entrar no Sistema", use_container_width=True, key="btn_entrar"):
            if operador == "— Selecione —":
                st.markdown('<div class="vi-alert vi-alert-error">⚠️ Selecione seu nome.</div>', unsafe_allow_html=True)
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

        if st.button("← Voltar", use_container_width=True, key="btn_voltar_sel"):
            st.session_state.pop("_modo", None)
            st.rerun()

# ============================================================
# LOGIN GERÊNCIA
# ============================================================
def tela_login_gerencia():
    st.markdown("<div style='height:15vh'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1.2,1])
    with col:
        st.markdown(f"""
        <div class="vi-card" style="text-align:center;">
            {logo_html()}
            <h3 style="margin:12px 0 4px;">Área da Gerência</h3>
            <div class="vi-divider"></div>
        </div>
        """, unsafe_allow_html=True)

        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        if st.button("🔓 Acessar", use_container_width=True, key="btn_login_ger"):
            if senha == SENHA_GERENCIA:
                st.session_state["_gerencia_ok"] = True
                st.rerun()
            else:
                st.markdown('<div class="vi-alert vi-alert-error">❌ Senha incorreta.</div>', unsafe_allow_html=True)

        if st.button("← Voltar", use_container_width=True, key="btn_voltar_login"):
            st.session_state.pop("_modo", None)
            st.rerun()

# ============================================================
# TELA DE EXTRATO (GERÊNCIA)
# ============================================================
def tela_extrato():
    concluidos = carregar_concluidos()
    pedidos_andamento = carregar_pedidos()
    historico = carregar_historico()

    st.markdown(f"""
    <div style="padding:24px 32px; background:white; border-bottom:1px solid #e2e8f0;">
        <div style="display:flex; align-items:center; gap:16px;">
            {logo_html()}
            <div>
                <h2 style="margin:0;">Extrato de Produção</h2>
                <p style="color:#64748b; margin:0;">Consulta, filtros e relatórios</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Cards de estatísticas
    total_sep = len([h for h in historico if h.get("etapa") == "Separação do Pedido"])
    total_emb = len([h for h in historico if h.get("etapa") == "Mesa de Embalagem"])
    total_conf = len([h for h in historico if h.get("etapa") == "Conferência do Pedido"])
    total_conc = len(concluidos)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="vi-stat"><div class="vi-stat-label">📦 Separações</div><div class="vi-stat-value">{total_sep}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="vi-stat"><div class="vi-stat-label">📬 Embalagens</div><div class="vi-stat-value">{total_emb}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="vi-stat"><div class="vi-stat-label">✅ Conferências</div><div class="vi-stat-value">{total_conf}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="vi-stat"><div class="vi-stat-label">🎯 Concluídos</div><div class="vi-stat-value">{total_conc}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📅 Histórico", "📋 Concluídos", "⏳ Em Andamento"])

    with tab1:
        if not historico:
            st.markdown('<div class="vi-alert vi-alert-info">ℹ️ Nenhuma operação registrada.</div>', unsafe_allow_html=True)
        else:
            df_hist = pd.DataFrame(historico)
            df_hist["data_dt"] = pd.to_datetime(df_hist["data"], format="%d/%m/%Y", errors="coerce")
            hoje = datetime.now().date()

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                data_ini = st.date_input("Data inicial", value=hoje - timedelta(days=7), format="DD/MM/YYYY")
            with col_f2:
                data_fim = st.date_input("Data final", value=hoje, format="DD/MM/YYYY")
            with col_f3:
                ops = ["Todos"] + sorted(df_hist["operador"].dropna().unique().tolist())
                op_filtro = st.selectbox("Funcionário", options=ops)
            with col_f4:
                etapas = ["Todas"] + ETAPAS
                etapa_filtro = st.selectbox("Etapa", options=etapas)

            mask = (df_hist["data_dt"] >= pd.Timestamp(data_ini)) & (df_hist["data_dt"] <= pd.Timestamp(data_fim))
            df_filtrado = df_hist[mask].copy()
            if op_filtro != "Todos":
                df_filtrado = df_filtrado[df_filtrado["operador"] == op_filtro]
            if etapa_filtro != "Todas":
                df_filtrado = df_filtrado[df_filtrado["etapa"] == etapa_filtro]
            df_filtrado = df_filtrado.sort_values("data_hora", ascending=False)

            st.markdown(f'<div class="vi-alert vi-alert-info">🔍 {len(df_filtrado)} operação(ões) encontrada(s)</div>', unsafe_allow_html=True)
            if not df_filtrado.empty:
                df_show = df_filtrado[["data_hora", "pedido", "operador", "etapa", "status_pedido"]].copy()
                df_show.columns = ["Data/Hora", "Pedido", "Funcionário", "Etapa", "Status"]
                df_show["Status"] = df_show["Status"].map({"em_andamento": "⏳", "concluido": "✅"}).fillna(df_show["Status"])
                st.dataframe(df_show, use_container_width=True, hide_index=True)

                # Download CSV/Excel
                nome_arq = f"extrato_{data_ini.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"
                csv = df_show.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ CSV", data=csv, file_name=f"{nome_arq}.csv", mime="text/csv")

    with tab2:
        if concluidos:
            df_conc = pd.DataFrame(concluidos)
            df_show = df_conc.rename(columns={
                "pedido": "Pedido", "op_sep": "Op. Sep.", "dt_sep": "Data Sep.",
                "op_emb": "Op. Emb.", "dt_emb": "Data Emb.",
                "op_conf": "Op. Conf.", "dt_conf": "Data Conf."
            }).drop(columns=["etapa"], errors="ignore")
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            csv = df_show.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ CSV Concluídos", data=csv, file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv", mime="text/csv")
        else:
            st.markdown('<div class="vi-alert vi-alert-info">ℹ️ Nenhum pedido finalizado ainda.</div>', unsafe_allow_html=True)

    with tab3:
        if pedidos_andamento:
            rows = []
            for p, d in pedidos_andamento.items():
                etapa_atual = d.get("etapa", 0)
                label = {1: "📬 Aguard. Embalagem", 2: "✅ Aguard. Conferência"}.get(etapa_atual, "—")
                rows.append({"Pedido": f"#{p}", "Etapa": label, "Op. Sep.": d.get("op_sep", "—"), "Op. Emb.": d.get("op_emb", "—")})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="vi-alert vi-alert-success">✅ Nenhum pedido em andamento.</div>', unsafe_allow_html=True)

    if st.button("← Sair da Gerência", use_container_width=True, key="btn_sair_ger"):
        st.session_state.pop("_modo", None)
        st.session_state.pop("_gerencia_ok", None)
        st.rerun()

# ============================================================
# CARD DE ETAPA
# ============================================================
def card_etapa(etapa_idx, operador_padrao):
    state_key = f"_etapa_{etapa_idx}_state"
    pedido_key = f"_etapa_{etapa_idx}_pedido"
    ts_key = f"_etapa_{etapa_idx}_ts"
    op_key = f"_etapa_{etapa_idx}_op"

    state = st.session_state.get(state_key, "idle")
    pedido = st.session_state.get(pedido_key)
    ts_inicio = st.session_state.get(ts_key)
    operador = st.session_state.get(op_key, operador_padrao)

    etapa_nome = ETAPAS[etapa_idx]
    etapa_icon = ETAPA_ICONS[etapa_idx]
    etapa_cor = ETAPA_CORES[etapa_idx]
    etapa_curto = ETAPA_NOMES_CURTOS[etapa_idx]

    elapsed = fmt_tempo(time.time() - ts_inicio) if ts_inicio and state == "running" else "---"

    # Cabeçalho
    st.markdown(f"""
    <div style="margin-bottom:16px;">
        <div style="height:4px; background:{etapa_cor}; border-radius:2px; margin-bottom:12px; opacity:{1 if state in ['running','ask_next'] else 0.3};"></div>
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:2rem;">{etapa_icon}</span>
            <div>
                <div style="font-size:0.65rem; font-weight:600; color:#64748b; text-transform:uppercase;">ETAPA {etapa_idx+1}</div>
                <div style="font-size:1.1rem; font-weight:700; color:#0f172a;">{etapa_nome}</div>
            </div>
            {f'<span class="vi-badge vi-badge-warning">● EM CURSO</span>' if state == "running" else ''}
            {f'<span class="vi-badge vi-badge-success">✓ OK</span>' if state == "done" else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mostra operador se não for idle
    if state != "idle":
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:16px;">
            {avatar_html(operador, 32)}
            <span style="color:#334155;">{operador}</span>
        </div>
        """, unsafe_allow_html=True)

    # IDLE
    if state == "idle":
        if etapa_idx == 0:
            num = st.text_input("Nº do Pedido", placeholder="Ex: 12345", key=f"inp_num_{etapa_idx}")
            if st.button(f"▶ INICIAR {etapa_curto.upper()}", key=f"btn_ini_{etapa_idx}", use_container_width=True):
                num = num.strip()
                pedidos_db = carregar_pedidos()
                if not num:
                    st.markdown('<div class="vi-alert vi-alert-error">⚠️ Informe o número.</div>', unsafe_allow_html=True)
                elif num in pedidos_db:
                    st.markdown(f'<div class="vi-alert vi-alert-error">⚠️ Pedido #{num} já em andamento.</div>', unsafe_allow_html=True)
                else:
                    st.session_state[state_key] = "running"
                    st.session_state[pedido_key] = num
                    st.session_state[ts_key] = time.time()
                    st.session_state[op_key] = operador_padrao
                    st.rerun()
        else:
            pedidos_db = carregar_pedidos()
            chave_op = "op_emb" if etapa_idx == 1 else "op_conf"
            etapa_needed = 1 if etapa_idx == 1 else 2
            disponiveis = [p for p, d in pedidos_db.items() if d.get("etapa") == etapa_needed and chave_op not in d]
            if not disponiveis:
                st.markdown('<div class="vi-alert vi-alert-warning">⏳ Aguardando etapa anterior...</div>', unsafe_allow_html=True)
                if st.button("🔄 Atualizar", key=f"btn_atualizar_{etapa_idx}", use_container_width=True):
                    st.rerun()
            else:
                pedido_sel = st.selectbox("Selecione o Pedido", options=["— Selecione —"] + sorted(disponiveis), key=f"sel_ped_{etapa_idx}")
                if st.button(f"▶ INICIAR {etapa_curto.upper()}", key=f"btn_ini_{etapa_idx}", use_container_width=True):
                    if pedido_sel == "— Selecione —":
                        st.markdown('<div class="vi-alert vi-alert-error">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state[state_key] = "running"
                        st.session_state[pedido_key] = pedido_sel
                        st.session_state[ts_key] = time.time()
                        st.session_state[op_key] = operador_padrao
                        st.rerun()

    # RUNNING
    elif state == "running":
        st.markdown(f"""
        <div style="text-align:center; margin:16px 0;">
            <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase;">PEDIDO EM CURSO</div>
            <div class="vi-big-number">#{pedido}</div>
            <div class="vi-timer" style="color:{etapa_cor};">⏱ {elapsed}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3,1])
        with col1:
            if st.button(f"⏹ FINALIZAR {etapa_curto.upper()}", key=f"btn_fin_{etapa_idx}", use_container_width=True):
                now = agora_str()
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
                        pedidos_db[pedido]["etapa"] = 2
                        pedidos_db[pedido]["op_emb"] = operador
                        pedidos_db[pedido]["dt_emb"] = now
                        registrar_historico(pedido, operador, "Mesa de Embalagem", now, "em_andamento")
                elif etapa_idx == 2:
                    if pedido in pedidos_db:
                        pedidos_db[pedido]["etapa"] = 3
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
        with col2:
            if st.button("✕", key=f"btn_cancel_{etapa_idx}"):
                st.session_state[state_key] = "idle"
                st.session_state[pedido_key] = None
                st.session_state[ts_key] = None
                st.rerun()

    # ASK_NEXT
    elif state == "ask_next":
        ts_fim = st.session_state.get(f"_etapa_{etapa_idx}_ts_fim")
        dur = fmt_tempo((ts_fim - ts_inicio) if ts_fim and ts_inicio else 0)

        if etapa_idx == 2:
            st.markdown(f"""
            <div style="background:#e8f5e9; border:2px solid #c8e6c9; border-radius:24px; padding:24px; text-align:center;">
                <div style="font-size:3rem;">🎉</div>
                <h3 style="color:#2e7d32;">Pedido Concluído!</h3>
                <div class="vi-big-number">#{pedido}</div>
                <p style="color:#64748b;">Todas as etapas finalizadas · {dur}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶ Novo Pedido", key=f"btn_novo_{etapa_idx}", use_container_width=True):
                st.session_state[state_key] = "idle"
                st.session_state[pedido_key] = None
                st.session_state[ts_key] = None
                st.rerun()
            return

        prox_idx = etapa_idx + 1
        prox_icon = ETAPA_ICONS[prox_idx]
        prox_nome = ETAPA_NOMES_CURTOS[prox_idx]

        st.markdown(f"""
        <div style="background:#f1f5f9; border-radius:16px; padding:16px; text-align:center; margin-bottom:16px;">
            <span class="vi-badge vi-badge-success" style="margin-bottom:8px;">✓ Etapa finalizada</span>
            <div class="vi-big-number" style="font-size:2rem;">#{pedido}</div>
            <p style="color:#475569;">Duração {dur}</p>
        </div>
        <div style="background:white; border:1px solid #e2e8f0; border-radius:16px; padding:16px;">
            <p style="font-weight:600; color:{ETAPA_CORES[prox_idx]}; text-align:center;">
                {prox_icon} Próxima: {prox_nome}<br>
                <span style="color:#64748b; font-size:0.8rem; font-weight:400;">Quem vai realizar?</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        ask_key = f"_ask_mode_{etapa_idx}"
        if ask_key not in st.session_state:
            st.session_state[ask_key] = None

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"✅ Sou eu\n({operador.split()[0]})", key=f"btn_mesmo_{etapa_idx}", use_container_width=True):
                _iniciar_proxima_etapa(etapa_idx, pedido, operador)
        with c2:
            if st.button("👤 Outro operador", key=f"btn_outro_{etapa_idx}", use_container_width=True):
                st.session_state[ask_key] = "selecionando"
                st.rerun()

        if st.session_state.get(ask_key) == "selecionando":
            outros = [op for op in OPERADORES if op != operador]
            outro_op = st.selectbox("Selecione o operador", options=["— Selecione —"] + outros, key=f"sel_op_prox_{etapa_idx}")
            if st.button("▶ Confirmar e Iniciar", key=f"btn_conf_op_{etapa_idx}", use_container_width=True):
                if outro_op == "— Selecione —":
                    st.markdown('<div class="vi-alert vi-alert-error">⚠️ Selecione um operador.</div>', unsafe_allow_html=True)
                else:
                    _iniciar_proxima_etapa(etapa_idx, pedido, outro_op)

def _iniciar_proxima_etapa(etapa_atual_idx, pedido, operador_proximo):
    prox = etapa_atual_idx + 1
    st.session_state.pop(f"_ask_mode_{etapa_atual_idx}", None)
    st.session_state[f"_etapa_{etapa_atual_idx}_state"] = "done"
    st.session_state[f"_etapa_{etapa_atual_idx}_pedido"] = pedido
    st.session_state[f"_etapa_{prox}_state"] = "running"
    st.session_state[f"_etapa_{prox}_pedido"] = pedido
    st.session_state[f"_etapa_{prox}_ts"] = time.time()
    st.session_state[f"_etapa_{prox}_op"] = operador_proximo
    st.session_state["_operador"] = operador_proximo
    st.rerun()

# ============================================================
# TELA PRINCIPAL DO OPERADOR
# ============================================================
def tela_operador():
    operador = st.session_state.get("_operador", "")
    turno_inicio = st.session_state.get("_turno_inicio", time.time())
    hoje_str = agora_str().split(" ")[0]
    historico = carregar_historico()
    hist_hoje = [h for h in historico if h.get("operador") == operador and h.get("data") == hoje_str]
    pedidos_hoje = len(hist_hoje)
    tempo_turno = fmt_tempo(time.time() - turno_inicio)
    hora_inicio = datetime.fromtimestamp(turno_inicio).strftime("%H:%M")

    # Layout: 5 colunas (esquerda, 3 etapas, direita)
    col_left, col_c1, col_c2, col_c3, col_right = st.columns([1.2, 1, 1, 1, 1.2])

    # PAINEL ESQUERDO
    with col_left:
        st.markdown(f"""
        <div style="background:white; height:100vh; padding:24px 16px; overflow-y:auto; border-right:1px solid #e9eef2;">
            <div style="margin-bottom:24px;">
                <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase;">Operador Ativo</div>
                <div style="display:flex; align-items:center; gap:12px; margin-top:8px;">
                    {avatar_html(operador, 48)}
                    <div>
                        <div style="font-weight:700; font-size:1.1rem;">{operador}</div>
                        <div style="color:#64748b; font-size:0.8rem;">Em operação</div>
                    </div>
                </div>
            </div>
            <div class="vi-divider"></div>
            <div class="vi-stat">
                <div class="vi-stat-label">Início do turno</div>
                <div class="vi-stat-value" style="font-size:1.4rem;">{hora_inicio}</div>
            </div>
            <div class="vi-stat">
                <div class="vi-stat-label">Tempo de turno</div>
                <div class="vi-stat-value" style="font-size:1.4rem;">{tempo_turno}</div>
            </div>
            <div class="vi-stat">
                <div class="vi-stat-label">Operações hoje</div>
                <div class="vi-stat-value" style="color:#2e7d32;">{pedidos_hoje}</div>
            </div>
            <div class="vi-divider"></div>
            <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:12px;">Últimas operações</div>
        """, unsafe_allow_html=True)

        for h in sorted(hist_hoje, key=lambda x: x.get("data_hora", ""), reverse=True)[:5]:
            hora = h.get("data_hora", "").split(" ")[-1]
            icone = {"Separação do Pedido": "📦", "Mesa de Embalagem": "📬", "Conferência do Pedido": "✅"}.get(h.get("etapa"), "○")
            st.markdown(f"""
            <div class="vi-history-item">
                <div class="vi-history-pedido">{icone} #{h.get('pedido','')}</div>
                <div class="vi-history-meta">{h.get('etapa','').split(' ')[0]} · {hora}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f'<div style="margin-top:auto; padding-top:20px;">{logo_html()}</div>', unsafe_allow_html=True)

    # COLUNAS CENTRAIS (ETAPAS)
    for idx, col in enumerate([col_c1, col_c2, col_c3]):
        with col:
            st.markdown('<div style="background:white; height:100vh; padding:24px 16px; overflow-y:auto;">', unsafe_allow_html=True)
            card_etapa(idx, operador)
            st.markdown('</div>', unsafe_allow_html=True)

    # PAINEL DIREITO
    with col_right:
        st.markdown("""
        <div style="background:white; height:100vh; padding:24px 16px; overflow-y:auto; border-left:1px solid #e9eef2;">
            <div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:12px;">Em Andamento</div>
        """, unsafe_allow_html=True)

        pedidos_db = carregar_pedidos()
        if not pedidos_db:
            st.markdown('<p style="color:#94a3b8; text-align:center;">Nenhum pedido em curso.</p>', unsafe_allow_html=True)
        else:
            for p, d in list(pedidos_db.items())[:6]:
                etapa_txt = {1: "📬 Embalagem", 2: "✅ Conferência"}.get(d.get("etapa"), "—")
                st.markdown(f"""
                <div class="vi-history-item">
                    <div class="vi-history-pedido">#{p}</div>
                    <div class="vi-history-meta">{etapa_txt}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.7rem; color:#64748b; text-transform:uppercase; margin-bottom:12px;">Concluídos Hoje</div>', unsafe_allow_html=True)

        concluidos = carregar_concluidos()
        conc_hoje = [c for c in concluidos if hoje_str in (c.get("dt_conf", "") or "")]
        st.markdown(f'<div class="vi-stat"><div class="vi-stat-label">Total do dia</div><div class="vi-stat-value" style="color:#2e7d32;">{len(conc_hoje)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="vi-divider"></div>', unsafe_allow_html=True)
        if st.button("🔄 Atualizar", use_container_width=True, key="btn_atualizar_global"):
            st.rerun()
        if st.button("⏏ Trocar Operador", use_container_width=True, key="btn_trocar_op"):
            for k in list(st.session_state.keys()):
                if k.startswith("_etapa_") or k in ["_operador", "_turno_inicio", "_ask_mode_0", "_ask_mode_1", "_ask_mode_2"]:
                    st.session_state.pop(k, None)
            st.rerun()
        if st.button("← Sair", use_container_width=True, key="btn_sair_op"):
            for k in list(st.session_state.keys()):
                if k != "_splash_done":
                    st.session_state.pop(k, None)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

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
