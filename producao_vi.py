import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Sistema de Produção", layout="wide")

# =========================
# CONFIG
# =========================

PEDIDOS_FILE = "pedidos.json"
CONCLUIDOS_FILE = "concluidos.json"
HISTORICO_FILE = "historico.json"
SENHA_GERENCIA = "vi2026"

ETAPAS = [
    "Separação",
    "Embalagem",
    "Conferência"
]

OPERADORES = [
    "Daniel",
    "Eduardo",
    "Maria",
    "João"
]

# =========================
# UTIL
# =========================

def carregar_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def carregar_pedidos():
    return carregar_json(PEDIDOS_FILE, [])

def salvar_pedidos(data):
    salvar_json(PEDIDOS_FILE, data)

def carregar_concluidos():
    return carregar_json(CONCLUIDOS_FILE, [])

def salvar_concluidos(data):
    salvar_json(CONCLUIDOS_FILE, data)

def carregar_historico():
    return carregar_json(HISTORICO_FILE, [])

def salvar_historico(data):
    salvar_json(HISTORICO_FILE, data)

# =========================
# CSS
# =========================

st.markdown("""
<style>

html, body, [data-testid="stAppViewContainer"]{
    background-color:#0b0c10;
}

.vi-center-page{
    display:flex;
    justify-content:center;
    align-items:center;
    min-height:85vh;
}

.vi-login-card{
    background:#1a1a24;
    border-radius:20px;
    padding:40px 36px;
    border:1px solid rgba(255,255,255,.08);
    width:100%;
    max-width:560px;
    margin:auto;
}

.vi-divider{
    height:1px;
    background:rgba(255,255,255,.06);
    margin:20px 0;
}

.card-etapa{
    background:#1a1a24;
    padding:20px;
    border-radius:16px;
    border:1px solid rgba(255,255,255,.06);
}

.stButton > button{
    height:44px;
    border-radius:10px;
    font-weight:600;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TELA INICIAL
# =========================

def tela_inicial():

    st.markdown('<div class="vi-center-page">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.markdown("""
        <div class="vi-login-card">

        <div style="text-align:center;margin-bottom:20px">
            <div style="font-size:32px;font-weight:800;color:#ff4b4b">
            Vi Lingerie
            </div>

            <div style="font-size:24px;font-weight:700;color:white">
            Sistema de Produção
            </div>

            <div style="font-size:12px;color:#9ca3af">
            Linha de Montagem
            </div>
        </div>

        <div class="vi-divider"></div>

        <div style="text-align:center;font-size:12px;color:#9ca3af;margin-bottom:20px">
        COMO DESEJA ACESSAR
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div style="background:rgba(255,255,255,.04);
                        border:1px solid rgba(255,255,255,.08);
                        border-radius:14px;
                        padding:20px;
                        text-align:center;
                        margin-bottom:10px">
                <div style="font-size:32px">🏭</div>
                <div style="font-weight:700;color:white">Operador</div>
                <div style="font-size:12px;color:#9ca3af">Registrar produção</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Entrar", use_container_width=True):
                st.session_state["modo"] = "operador"
                st.rerun()

        with c2:
            st.markdown("""
            <div style="background:rgba(255,255,255,.04);
                        border:1px solid rgba(255,255,255,.08);
                        border-radius:14px;
                        padding:20px;
                        text-align:center;
                        margin-bottom:10px">
                <div style="font-size:32px">📊</div>
                <div style="font-weight:700;color:white">Gerência</div>
                <div style="font-size:12px;color:#9ca3af">Extrato e relatórios</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Acessar", use_container_width=True):
                st.session_state["modo"] = "login_gerencia"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# OPERADOR
# =========================

def tela_operador():

    st.title("Produção")

    operador = st.selectbox("Operador", OPERADORES)

    pedido = st.text_input("Número do pedido")

    if st.button("Iniciar Pedido"):

        pedidos = carregar_pedidos()
        concluidos = carregar_concluidos()

        if any(p["pedido"] == pedido for p in pedidos) or any(c["pedido"] == pedido for c in concluidos):
            st.error("Pedido já existe")
            return

        novo = {
            "pedido": pedido,
            "etapa": 0,
            "operadores": {},
            "inicio": datetime.now().isoformat()
        }

        pedidos.append(novo)
        salvar_pedidos(pedidos)

        st.success("Pedido iniciado")

    st.divider()

    pedidos = carregar_pedidos()

    for p in pedidos:

        st.markdown(f"""
        <div class="card-etapa">
        <b>Pedido:</b> {p["pedido"]}<br>
        <b>Etapa:</b> {ETAPAS[p["etapa"]]}
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Avançar {p['pedido']}"):

            pedidos = carregar_pedidos()

            for ped in pedidos:
                if ped["pedido"] == p["pedido"]:

                    ped["operadores"][ETAPAS[ped["etapa"]]] = operador
                    ped["etapa"] += 1

                    if ped["etapa"] >= len(ETAPAS):

                        concluidos = carregar_concluidos()
                        historico = carregar_historico()

                        ped["fim"] = datetime.now().isoformat()

                        concluidos.append(ped)
                        historico.append(ped)

                        salvar_concluidos(concluidos)
                        salvar_historico(historico)

                        pedidos.remove(ped)
                        salvar_pedidos(pedidos)

                        st.success("Pedido concluído")
                        st.rerun()

                    salvar_pedidos(pedidos)
                    st.rerun()

# =========================
# GERENCIA LOGIN
# =========================

def tela_login_gerencia():

    st.title("Login Gerência")

    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if senha == SENHA_GERENCIA:
            st.session_state["modo"] = "gerencia"
            st.rerun()
        else:
            st.error("Senha incorreta")

# =========================
# GERENCIA
# =========================

def tela_gerencia():

    st.title("Painel da Gerência")

    pedidos = carregar_pedidos()
    concluidos = carregar_concluidos()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Pedidos em Produção")
        st.metric("Quantidade", len(pedidos))

    with col2:
        st.subheader("Pedidos Concluídos")
        st.metric("Quantidade", len(concluidos))

    st.divider()

    st.subheader("Pedidos Ativos")

    for p in pedidos:
        st.write(p["pedido"], "-", ETAPAS[p["etapa"]])

    st.divider()

    st.subheader("Histórico")

    historico = carregar_historico()

    for h in historico[-20:]:
        st.write(h["pedido"], "concluído")

# =========================
# CONTROLE
# =========================

if "modo" not in st.session_state:
    tela_inicial()

elif st.session_state["modo"] == "operador":
    tela_operador()

elif st.session_state["modo"] == "login_gerencia":
    tela_login_gerencia()

elif st.session_state["modo"] == "gerencia":
    tela_gerencia()
