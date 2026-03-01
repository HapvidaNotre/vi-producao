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
OPERADORES = [
    "Lucivanio", "Enágio", "Daniel", "Ítalo", "Cildenir",
    "Samya", "Neide", "Eduardo", "Talyson",
]

SENHA_GERENCIA = "vi2026"

# Diretório para arquivos de estado
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

def registrar_historico(pedido_num, operador, etapa, data_hora, status="em_andamento"):
    hist = carregar_historico()
    hist.append({
        "data_hora": data_hora,
        "data": data_hora.split(" ")[0],
        "pedido": pedido_num,
        "operador": operador,
        "etapa": etapa,
        "status": status,
    })
    salvar_historico(hist)

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def agora_str():
    br = timezone(timedelta(hours=-3))
    return datetime.now(br).strftime("%d/%m/%Y %H:%M")

def format_tempo(segundos):
    if segundos is None or segundos <= 0:
        return "00:00:00"
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def avatar_iniciais(nome, tamanho=48):
    partes = nome.strip().split()
    iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper()
    cores = ["#1976D2", "#7B1FA2", "#2E7D32", "#C2185B", "#F57C00", "#0288D1"]
    cor = cores[sum(ord(c) for c in nome) % len(cores)]
    return f"""
    <div style="width:{tamanho}px; height:{tamanho}px; border-radius:50%;
                background:{cor}; display:flex; align-items:center;
                justify-content:center; font-size:{tamanho*0.4}px;
                font-weight:700; color:white;">
        {iniciais}
    </div>
    """

def logo_html():
    return '<span style="font-size:2rem; font-weight:900; color:#1e293b;">VI</span>'

# ============================================================
# CSS GLOBAL (TEMA CLARO, BASEADO NAS IMAGENS)
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stApp"] {
        font-family: 'Inter', sans-serif;
        background: #f8fafc !important;
        color: #0f172a !important;
        height: 100vh;
        overflow: hidden;
    }

    /* Remove cabeçalho e sidebar padrão */
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
    .card {
        background: white;
        border-radius: 32px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05), 0 8px 10px -6px rgba(0,0,0,0.02);
        padding: 28px 24px;
        border: 1px solid #e9eef2;
    }

    .divider {
        height: 1px;
        background: #e2e8f0;
        margin: 20px 0;
    }

    /* Avatar grande */
    .avatar-large {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: #1976D2;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        font-weight: 700;
        color: white;
    }

    /* Estações (etapas) */
    .estacao-titulo {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    .numero-pedido-grande {
        font-family: 'Inter', monospace;
        font-weight: 700;
        font-size: 3.2rem;
        color: #0f172a;
        text-align: center;
        line-height: 1.2;
    }

    .timer-grande {
        font-family: 'Inter', monospace;
        font-size: 2rem;
        font-weight: 500;
        color: #475569;
        text-align: center;
        letter-spacing: 2px;
        margin: 8px 0 24px;
    }

    /* Botões */
    .stButton > button {
        border-radius: 40px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 14px 28px !important;
        border: none !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 6px -2px rgba(0,0,0,0.05) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1) !important;
    }

    /* Botão primário (iniciar) */
    button[kind="primary"] {
        background: #0f172a !important;
        color: white !important;
    }

    /* Botão finalizar (vermelho) */
    .btn-finalizar > button {
        background: #dc2626 !important;
        color: white !important;
        box-shadow: 0 4px 10px rgba(220,38,38,0.3) !important;
    }

    /* Inputs */
    [data-testid="stTextInput"] input {
        background: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 40px !important;
        padding: 14px 20px !important;
        font-size: 1rem !important;
    }
    [data-testid="stTextInput"] label {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        margin-bottom: 8px !important;
    }

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {
        background: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 40px !important;
        padding: 8px 16px !important;
    }

    /* Layout da estação central */
    .layout-4colunas {
        display: grid;
        grid-template-columns: 280px 1fr 1fr 1fr;
        height: 100vh;
        gap: 1px;
        background: #e9eef2;
    }
    .painel-esquerdo {
        background: white;
        padding: 32px 24px;
        overflow-y: auto;
    }
    .coluna-etapa {
        background: white;
        padding: 32px 24px;
        overflow-y: auto;
        border-left: 1px solid #e9eef2;
    }

    /* Animações */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220,38,38,0.4); }
        70% { box-shadow: 0 0 0 12px rgba(220,38,38,0); }
        100% { box-shadow: 0 0 0 0 rgba(220,38,38,0); }
    }
    .pulse {
        animation: pulse 2s infinite;
        border-radius: 40px;
    }

    /* Scroll */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TELA INICIAL (COMO NA IMAGEM)
# ============================================================
def tela_inicial():
    st.markdown("<div style='height:12vh'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.8, 1])
    with cols[1]:
        st.markdown(f"""
        <div class="card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 8px;">🧵</div>
            <h1 style="font-size: 2.5rem; margin: 0; color: #0f172a;">VI LINGERIE</h1>
            <p style="color: #475569; font-size: 1.2rem; margin-top: 8px;">Apontamento de Produção</p>
            <p style="color: #64748b;">Selecione seu nome para começar</p>
            <div class="divider"></div>
            <p style="font-weight: 600; color: #334155;">QUEM É VOCÊ?</p>
        </div>
        """, unsafe_allow_html=True)

        # Grade de operadores (como na imagem)
        ops_por_linha = 3
        for i in range(0, len(OPERADORES), ops_por_linha):
            cols_ops = st.columns(ops_por_linha)
            for j, op in enumerate(OPERADORES[i:i+ops_por_linha]):
                with cols_ops[j]:
                    iniciais = "".join([p[0] for p in op.split()]).upper()[:2]
                    st.markdown(f"""
                    <div style="text-align: center; padding: 12px;">
                        <div style="width: 56px; height: 56px; border-radius: 50%;
                                    background: #e2e8f0; display: flex; align-items: center;
                                    justify-content: center; margin: 0 auto 8px;
                                    font-size: 20px; font-weight: 700; color: #1e293b;">
                            {iniciais}
                        </div>
                        <div style="font-weight: 600;">{op}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        if st.button("➡️ Entrar no sistema", key="btn_entrar_inicial", use_container_width=True):
            st.session_state["_modo"] = "selecao_operador"
            st.rerun()

        st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
        if st.button("🔐 Acesso Gerência", key="btn_gerencia_inicial", use_container_width=True):
            st.session_state["_modo"] = "gerencia_login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# SELEÇÃO DE OPERADOR (APÓS CLICAR EM "ENTRAR NO SISTEMA")
# ============================================================
def tela_selecao_operador():
    st.markdown("<div style='height:15vh'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h2 style="margin-bottom: 24px;">Selecione seu nome</h2>
        </div>
        """, unsafe_allow_html=True)

        operador = st.selectbox("", options=["— Selecione —"] + OPERADORES, label_visibility="collapsed")
        if st.button("▶ Entrar no Sistema", use_container_width=True, key="btn_confirmar_operador"):
            if operador == "— Selecione —":
                st.error("Selecione um operador.")
            else:
                st.session_state["_operador"] = operador
                st.session_state["_turno_inicio"] = time.time()
                st.session_state["_etapa_0_state"] = "idle"
                st.session_state["_etapa_1_state"] = "idle"
                st.session_state["_etapa_2_state"] = "idle"
                st.session_state["_modo"] = "operador"
                st.rerun()

        if st.button("← Voltar", use_container_width=True):
            st.session_state["_modo"] = "inicial"
            st.rerun()

# ============================================================
# LOGIN GERÊNCIA
# ============================================================
def tela_login_gerencia():
    st.markdown("<div style='height:20vh'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1.2, 1])
    with cols[1]:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h2>Área da Gerência</h2>
            <div class="divider"></div>
        </div>
        """, unsafe_allow_html=True)

        senha = st.text_input("Senha", type="password")
        if st.button("🔓 Acessar", use_container_width=True):
            if senha == SENHA_GERENCIA:
                st.session_state["_gerencia_ok"] = True
                st.session_state["_modo"] = "gerencia"
                st.rerun()
            else:
                st.error("Senha incorreta.")

        if st.button("← Voltar", use_container_width=True):
            st.session_state["_modo"] = "inicial"
            st.rerun()

# ============================================================
# TELA DE EXTRATO (GERÊNCIA)
# ============================================================
def tela_extrato():
    st.markdown(f"""
    <div style="padding: 24px 32px; background: white; border-bottom: 1px solid #e2e8f0;">
        <div style="display: flex; align-items: center; gap: 16px;">
            {logo_html()}
            <h2 style="margin: 0;">Extrato de Produção</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    concluidos = carregar_concluidos()
    pedidos_andamento = carregar_pedidos()
    historico = carregar_historico()

    # Estatísticas
    total_sep = len([h for h in historico if h["etapa"] == "Separação"])
    total_emb = len([h for h in historico if h["etapa"] == "Embalagem"])
    total_conf = len([h for h in historico if h["etapa"] == "Conferência"])
    total_conc = len(concluidos)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Separações", total_sep)
    with col2:
        st.metric("Embalagens", total_emb)
    with col3:
        st.metric("Conferências", total_conf)
    with col4:
        st.metric("Concluídos", total_conc)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📅 Histórico", "📋 Concluídos", "⏳ Em Andamento"])

    with tab1:
        if not historico:
            st.info("Nenhuma operação registrada.")
        else:
            df = pd.DataFrame(historico)
            df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
            hoje = datetime.now().date()

            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                data_ini = st.date_input("Data inicial", hoje - timedelta(days=7))
            with col_f2:
                data_fim = st.date_input("Data final", hoje)
            with col_f3:
                op_filtro = st.selectbox("Funcionário", ["Todos"] + sorted(df["operador"].unique()))

            mask = (df["data_dt"] >= pd.Timestamp(data_ini)) & (df["data_dt"] <= pd.Timestamp(data_fim))
            df_filtrado = df[mask]
            if op_filtro != "Todos":
                df_filtrado = df_filtrado[df_filtrado["operador"] == op_filtro]
            df_filtrado = df_filtrado.sort_values("data_hora", ascending=False)

            st.write(f"**{len(df_filtrado)}** operações encontradas.")
            if not df_filtrado.empty:
                st.dataframe(df_filtrado[["data_hora", "pedido", "operador", "etapa", "status"]],
                             use_container_width=True, hide_index=True)

    with tab2:
        if concluidos:
            df_conc = pd.DataFrame(concluidos)
            st.dataframe(df_conc, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum pedido concluído.")

    with tab3:
        if pedidos_andamento:
            rows = []
            for p, d in pedidos_andamento.items():
                etapa_atual = {1: "Embalagem", 2: "Conferência"}.get(d.get("etapa"), "Desconhecida")
                rows.append({"Pedido": p, "Etapa": etapa_atual, "Operador Sep.": d.get("op_sep", "—")})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum pedido em andamento.")

    if st.button("← Sair da Gerência", use_container_width=True):
        st.session_state["_modo"] = "inicial"
        st.session_state.pop("_gerencia_ok", None)
        st.rerun()

# ============================================================
# COMPONENTE DE ETAPA (SEPARAÇÃO, EMBALAGEM, CONFERÊNCIA)
# ============================================================
def render_etapa(indice, nome, icone, operador_logado):
    state_key = f"_etapa_{indice}_state"
    pedido_key = f"_etapa_{indice}_pedido"
    ts_key = f"_etapa_{indice}_ts"
    op_key = f"_etapa_{indice}_op"

    state = st.session_state.get(state_key, "idle")
    pedido = st.session_state.get(pedido_key)
    ts_inicio = st.session_state.get(ts_key)
    operador = st.session_state.get(op_key, operador_logado)

    # Cabeçalho da etapa
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <div style="font-size: 1.8rem; margin-bottom: 4px;">{icone}</div>
        <div class="estacao-titulo">{nome.upper()}</div>
    </div>
    """, unsafe_allow_html=True)

    # Estado IDLE
    if state == "idle":
        if indice == 0:  # Separação
            num = st.text_input("Nº do Pedido", placeholder="Ex: 12345", key=f"input_{indice}")
            if st.button("INICIAR SEPARAÇÃO", key=f"btn_iniciar_{indice}", use_container_width=True):
                num = num.strip()
                if not num:
                    st.error("Informe o número do pedido.")
                else:
                    pedidos_db = carregar_pedidos()
                    if num in pedidos_db:
                        st.error(f"Pedido #{num} já está em andamento.")
                    else:
                        st.session_state[state_key] = "running"
                        st.session_state[pedido_key] = num
                        st.session_state[ts_key] = time.time()
                        st.session_state[op_key] = operador_logado
                        st.rerun()
        else:  # Embalagem ou Conferência
            pedidos_db = carregar_pedidos()
            etapa_necessaria = 1 if indice == 1 else 2
            disponiveis = [p for p, d in pedidos_db.items() if d.get("etapa") == etapa_necessaria]
            if not disponiveis:
                st.info("Aguardando etapa anterior...")
            else:
                pedido_sel = st.selectbox("Selecione o pedido", [""] + sorted(disponiveis), key=f"select_{indice}")
                if st.button(f"INICIAR {nome.upper()}", key=f"btn_iniciar_{indice}", use_container_width=True):
                    if not pedido_sel:
                        st.error("Selecione um pedido.")
                    else:
                        st.session_state[state_key] = "running"
                        st.session_state[pedido_key] = pedido_sel
                        st.session_state[ts_key] = time.time()
                        st.session_state[op_key] = operador_logado
                        st.rerun()

    # Estado RUNNING
    elif state == "running":
        elapsed = format_tempo(time.time() - ts_inicio)
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="numero-pedido-grande">#{pedido}</div>
            <div class="timer-grande">{elapsed}</div>
        </div>
        """, unsafe_allow_html=True)

        # Botão finalizar com efeito pulse
        st.markdown('<div class="btn-finalizar pulse">', unsafe_allow_html=True)
        if st.button(f"CONCLUIR {nome.upper()}", key=f"btn_finalizar_{indice}", use_container_width=True):
            now = agora_str()
            ts_fim = time.time()
            pedidos_db = carregar_pedidos()

            if indice == 0:
                pedidos_db[pedido] = {
                    "pedido": pedido,
                    "etapa": 1,
                    "op_sep": operador,
                    "dt_sep": now
                }
                registrar_historico(pedido, operador, "Separação", now)
            elif indice == 1:
                if pedido in pedidos_db:
                    pedidos_db[pedido]["etapa"] = 2
                    pedidos_db[pedido]["op_emb"] = operador
                    pedidos_db[pedido]["dt_emb"] = now
                    registrar_historico(pedido, operador, "Embalagem", now)
            elif indice == 2:
                if pedido in pedidos_db:
                    pedidos_db[pedido]["etapa"] = 3
                    pedidos_db[pedido]["op_conf"] = operador
                    pedidos_db[pedido]["dt_conf"] = now
                    concluidos = carregar_concluidos()
                    concluidos.append(pedidos_db[pedido])
                    salvar_concluidos(concluidos)
                    del pedidos_db[pedido]
                    registrar_historico(pedido, operador, "Conferência", now, "concluido")

            salvar_pedidos(pedidos_db)
            st.session_state[f"_etapa_{indice}_ts_fim"] = ts_fim
            st.session_state[state_key] = "ask_next"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("✕ Cancelar", key=f"btn_cancelar_{indice}", use_container_width=True):
            st.session_state[state_key] = "idle"
            st.session_state[pedido_key] = None
            st.session_state[ts_key] = None
            st.rerun()

    # Estado ASK_NEXT (após finalizar)
    elif state == "ask_next":
        ts_fim = st.session_state.get(f"_etapa_{indice}_ts_fim")
        duracao = format_tempo((ts_fim - ts_inicio) if ts_fim and ts_inicio else 0)

        if indice == 2:  # Conferência finalizada
            st.markdown(f"""
            <div style="background: #e8f5e9; border-radius: 32px; padding: 32px; text-align: center;">
                <div style="font-size: 3rem;">🎉</div>
                <h3 style="color: #2e7d32;">Pedido Concluído!</h3>
                <div class="numero-pedido-grande">#{pedido}</div>
                <p style="color: #64748b;">Tempo total: {duracao}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Novo Pedido", key=f"btn_novo_{indice}", use_container_width=True):
                st.session_state[state_key] = "idle"
                st.session_state[pedido_key] = None
                st.session_state[ts_key] = None
                st.rerun()
        else:
            st.markdown(f"""
            <div style="background: #f1f5f9; border-radius: 32px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <p style="font-weight: 600; color: #334155;">Etapa anterior concluída!</p>
                <div class="numero-pedido-grande" style="font-size: 2rem;">#{pedido}</div>
                <p style="color: #64748b;">Duração: {duracao}</p>
            </div>
            <p style="font-weight: 600; text-align: center;">Quem fará a próxima etapa?</p>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Eu mesmo", key=f"btn_mesmo_{indice}", use_container_width=True):
                    _proxima_etapa(indice, pedido, operador_logado)
            with col2:
                if st.button("Outro operador", key=f"btn_outro_{indice}", use_container_width=True):
                    st.session_state[f"_ask_mode_{indice}"] = "selecionando"
                    st.rerun()

            if st.session_state.get(f"_ask_mode_{indice}") == "selecionando":
                outros = [op for op in OPERADORES if op != operador_logado]
                outro = st.selectbox("Selecione", [""] + outros, key=f"select_outro_{indice}")
                if st.button("Confirmar", key=f"btn_confirmar_{indice}", use_container_width=True):
                    if not outro:
                        st.error("Selecione um operador.")
                    else:
                        _proxima_etapa(indice, pedido, outro)

def _proxima_etapa(etapa_atual, pedido, novo_operador):
    prox = etapa_atual + 1
    st.session_state[f"_etapa_{etapa_atual}_state"] = "done"
    st.session_state[f"_etapa_{etapa_atual}_pedido"] = pedido
    st.session_state[f"_etapa_{prox}_state"] = "running"
    st.session_state[f"_etapa_{prox}_pedido"] = pedido
    st.session_state[f"_etapa_{prox}_ts"] = time.time()
    st.session_state[f"_etapa_{prox}_op"] = novo_operador
    st.session_state["_operador"] = novo_operador
    st.rerun()

# ============================================================
# TELA PRINCIPAL DO OPERADOR (COMO NAS IMAGENS)
# ============================================================
def tela_operador():
    operador = st.session_state["_operador"]
    turno_inicio = st.session_state.get("_turno_inicio", time.time())
    tempo_turno = format_tempo(time.time() - turno_inicio)

    # Layout de 4 colunas (painel esquerdo + 3 etapas)
    st.markdown('<div class="layout-4colunas">', unsafe_allow_html=True)

    # PAINEL ESQUERDO (ESTAÇÃO CENTRAL)
    st.markdown('<div class="painel-esquerdo">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-bottom: 32px;">
        <div style="font-size: 1.2rem; font-weight: 600; color: #334155;">ESTAÇÃO CENTRAL</div>
        <div style="display: flex; align-items: center; gap: 12px; margin-top: 16px;">
            {avatar_iniciais(operador, 56)}
            <span style="font-size: 1.4rem; font-weight: 600;">{operador}</span>
        </div>
    </div>
    <div class="divider"></div>
    <div style="margin-top: 24px;">
        <p style="color: #475569; font-size: 0.9rem;">Tempo de turno: <strong>{tempo_turno}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # fecha painel esquerdo

    # COLUNAS DAS ETAPAS
    with st.container():
        # Separação
        st.markdown('<div class="coluna-etapa">', unsafe_allow_html=True)
        render_etapa(0, "SEPARAÇÃO", "📦", operador)
        st.markdown('</div>', unsafe_allow_html=True)

        # Embalagem
        st.markdown('<div class="coluna-etapa">', unsafe_allow_html=True)
        render_etapa(1, "EMBALAGEM", "📬", operador)
        st.markdown('</div>', unsafe_allow_html=True)

        # Conferência
        st.markdown('<div class="coluna-etapa">', unsafe_allow_html=True)
        render_etapa(2, "CONFERÊNCIA", "✅", operador)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # fecha layout-4colunas

# ============================================================
# ROTEADOR PRINCIPAL
# ============================================================
if "_modo" not in st.session_state:
    st.session_state["_modo"] = "inicial"

modo = st.session_state["_modo"]

if modo == "inicial":
    tela_inicial()
elif modo == "selecao_operador":
    tela_selecao_operador()
elif modo == "gerencia_login":
    tela_login_gerencia()
elif modo == "gerencia":
    if st.session_state.get("_gerencia_ok"):
        tela_extrato()
    else:
        st.session_state["_modo"] = "gerencia_login"
        st.rerun()
elif modo == "operador":
    if "_operador" in st.session_state:
        tela_operador()
    else:
        st.session_state["_modo"] = "selecao_operador"
        st.rerun()
