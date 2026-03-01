import streamlit as st
import json
import os
import time
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

# ─── Config ───
st.set_page_config(page_title="VI LINGERIE - Apontamento", page_icon="👙", layout="wide")

# Arquivos
DATA_FILE = "orders.json"
LOCK_FILE = DATA_FILE + ".lock"

# Operadores e etapas
OPERATORS = [
    "LUCIVANIO", "ENÁGIO", "DANIEL", "ÍTALO",
    "CILDENIR", "SAMYA", "NEIDE", "EDUARDO", "TALYSON"
]
STEPS = [
    {"key": "separacao", "label": "SEPARAÇÃO"},
    {"key": "embalagem", "label": "EMBALAGEM"},
    {"key": "conferencia", "label": "CONFERÊNCIA"},
]
OPERATOR_COLORS = {
    "LUCIVANIO": "#7B2D8E",
    "ENÁGIO": "#2E8B57",
    "DANIEL": "#4B0082",
    "ÍTALO": "#2563EB",
    "CILDENIR": "#1B5E20",
    "SAMYA": "#CC7722",
    "NEIDE": "#A0365A",
    "EDUARDO": "#DC2626",
    "TALYSON": "#7C5CBF",
}

# Logo no GitHub (pode usar direto por URL)
LOGO_URL = "https://raw.githubusercontent.com/HapvidaNotre/vi-producao/main/logo_vi.png"

# ─── File Lock (sem dependências) ───
@contextmanager
def file_lock(timeout=10, poll_interval=0.1):
    start = time.time()
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                raise TimeoutError("Timeout ao obter lock do arquivo de dados.")
            time.sleep(poll_interval)
    try:
        yield
    finally:
        try:
            os.remove(LOCK_FILE)
        except FileNotFoundError:
            pass

# ─── Persistence ───
def load_orders():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_orders(orders):
    tmp = DATA_FILE + ".tmp"
    with file_lock():
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DATA_FILE)

# ─── Utils ───
def format_duration(seconds):
    if seconds is None:
        return "--:--:--"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def step_index_by_key(step_key: str) -> int:
    for i, s in enumerate(STEPS):
        if s["key"] == step_key:
            return i
    return 0

def next_step_index_from_order(order) -> int:
    finished = len([s for s in order.get("steps", []) if s.get("endTime")])
    return min(finished, len(STEPS) - 1)

def find_open_order_by_number(orders, order_number: str):
    candidates = [o for o in orders if o.get("orderNumber") == order_number and not o.get("completedAt")]
    if not candidates:
        return None
    return sorted(candidates, key=lambda o: o.get("createdAt", 0))[-1]

# ─── Global Style (Fundo branco + estética) ───
st.markdown("""
<style>
/* Fundo branco em toda a aplicação */
html, body, [data-testid="stAppViewContainer"] {
    background: #FFFFFF !important;
}

/* Container principal com largura confortável */
.block-container {
    padding-top: 0.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Barra superior com logo */
.topbar {
    position: sticky;
    top: 0;
    z-index: 999;
    background: #FFFFFF;
    border-bottom: 1px solid #E5E7EB;
    padding: 0.4rem 0.2rem;
}
.topbar-inner {
    display: flex; align-items: center; gap: 12px;
}
.topbar-logo {
    height: 38px; /* ajuste fino aqui */
}
.topbar-title {
    font-weight: 800;
    letter-spacing: .08em;
    font-size: 0.9rem;
    color: #8B1A4A;
    text-transform: uppercase;
    margin: 0;
}

/* Badges de etapa */
.step-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    margin: 0 4px;
    border: 1px solid transparent;
}
.step-done {
    background: #ECFDF5; color: #065F46; border-color: #A7F3D0;
}
.step-current {
    background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE;
}
.step-pending {
    background: #F9FAFB; color: #6B7280; border-color: #E5E7EB;
}

/* Timer */
.timer-display {
    font-size: 3rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    text-align: center;
    padding: 0.5rem;
    font-weight: 800;
    color: #111827;
}

/* Número do pedido */
.order-number {
    font-size: 2.2rem;
    font-weight: 900;
    text-align: center;
    margin: 0.4rem 0 0.8rem;
    color: #111827;
}

/* Avatar operador */
.avatar {
    width: 40px; height: 40px; border-radius: 50%;
    display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:1.1rem;
}

/* Tipografia e textos auxiliares */
h2, h3, h4, h5 { color:#111827; }
.caption-muted { color:#6B7280; font-size:0.85rem; }

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    overflow: hidden;
}

/* Divisores */
hr, .stDivider { border-color: #F3F4F6 !important; }

/* Botões: reforço leve de altura e fonte */
button[kind="header"] { height: 2.2rem; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───
if "page" not in st.session_state:
    st.session_state.page = "login"
if "operator" not in st.session_state:
    st.session_state.operator = None
if "phase" not in st.session_state:
    st.session_state.phase = "input"
if "order_number" not in st.session_state:
    st.session_state.order_number = ""
if "current_step_idx" not in st.session_state:
    st.session_state.current_step_idx = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "current_order" not in st.session_state:
    st.session_state.current_order = None

# ─── Topbar (com logo) ───
def render_topbar(extra_right=None):
    with st.container():
        cols = st.columns([8, 4])
        with cols[0]:
            st.markdown(
                f"""
                <div class="topbar">
                    <div class="topbar-inner">
                        <img class="topbar-logo" src="{LOGO_URL}" alt="VI LINGERIE">
                        <p class="topbar-title">Apontamento de Produção</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with cols[1]:
            if extra_right:
                extra_right()

# ─── LOGIN PAGE ───
def login_page():
    render_topbar()

    st.markdown("### 🧑 Quem é você?")
    st.caption("Selecione seu nome para começar.")

    cols = st.columns(3)
    for i, op in enumerate(OPERATORS):
        col = cols[i % 3]
        if col.button(op, key=f"op_{op}", use_container_width=True):
            st.session_state.operator = op
            st.session_state.page = "operator"
            st.session_state.phase = "input"
            st.session_state.current_step_idx = 0
            st.session_state.current_order = None
            st.rerun()

    st.divider()
    if st.button("🔒 Acesso Gerência", use_container_width=True):
        st.session_state.page = "manager"
        st.rerun()

# ─── OPERATOR PAGE ───
def operator_page():
    if not st.session_state.operator:
        st.session_state.page = "login"
        st.rerun()

    operator = st.session_state.operator
    color = OPERATOR_COLORS.get(operator, "#666")

    def right_header():
        # Botão logout no cabeçalho
        col_a, col_b = st.columns([5, 1])
        with col_b:
            if st.button("🚪", key="logout", help="Sair"):
                st.session_state.page = "login"
                st.session_state.operator = None
                st.rerun()

    render_topbar(extra_right=right_header)

    # Header da estação
    col1, col2 = st.columns([1, 9])
    with col1:
        st.markdown(
            f'<div class="avatar" style="background:{color}; color:white;">{operator[0]}</div>',
            unsafe_allow_html=True
        )
    with col2:
        st.caption("ESTAÇÃO CENTRAL")
        st.markdown(f"### {operator}")

    # Estado atual
    phase = st.session_state.phase
    step_idx = st.session_state.current_step_idx
    current_step = STEPS[step_idx]

    # Step tracker
    if phase != "input":
        step_html = ""
        for i, step in enumerate(STEPS):
            if i < step_idx:
                step_html += f'<span class="step-badge step-done">✓ {step["label"]}</span>'
            elif i == step_idx:
                step_html += f'<span class="step-badge step-current">● {step["label"]}</span>'
            else:
                step_html += f'<span class="step-badge step-pending">{step["label"]}</span>'
        st.markdown(f'<div style="text-align:center; margin:0.5rem 0 1rem;">{step_html}</div>', unsafe_allow_html=True)

    # ─ INPUT PHASE ─
    if phase == "input":
        st.markdown("<div style='text-align:center; font-size:3rem; opacity:0.25;'>📦</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-weight:700;'>Bipar ou digitar pedido</p>", unsafe_allow_html=True)
        st.caption("Insira o número do pedido para iniciar", help=None)

        order_num = st.text_input("Número do pedido", placeholder="Ex: 12345", label_visibility="collapsed")
        if st.button("➡️ Confirmar Pedido", use_container_width=True, disabled=not order_num.strip()):
            order_num = order_num.strip()
            st.session_state.order_number = order_num

            orders = load_orders()
            existing = find_open_order_by_number(orders, order_num)

            if existing:
                # Verifica se há etapa aberta (sem endTime)
                open_step = next((s for s in existing.get("steps", []) if s.get("endTime") is None), None)
                if open_step:
                    owner = open_step.get("operatorId", "—")
                    st.error(f"Este pedido está com a etapa '{open_step['step'].upper()}' em andamento por {owner}. Aguarde a conclusão ou finalize na estação correta.")
                    st.stop()

                st.session_state.current_order = existing
                st.session_state.current_step_idx = next_step_index_from_order(existing)
                st.session_state.phase = "ready"
                st.rerun()
            else:
                st.session_state.current_order = {
                    "id": str(time.time()),
                    "orderNumber": order_num,
                    "steps": [],
                    "createdAt": time.time(),
                    "completedAt": None,
                }
                st.session_state.current_step_idx = 0
                st.session_state.phase = "ready"
                st.rerun()

    # ─ READY PHASE ─
    elif phase == "ready":
        st.markdown(f'<div class="order-number">#{st.session_state.order_number}</div>', unsafe_allow_html=True)
        if st.button(f"▶️ Iniciar {current_step['label']}", use_container_width=True, type="primary"):
            now = time.time()
            st.session_state.start_time = now
            order = st.session_state.current_order
            order["steps"].append({
                "step": current_step["key"],
                "operatorId": operator,
                "startTime": now,
                "endTime": None,
            })
            st.session_state.current_order = order
            st.session_state.phase = "running"
            st.rerun()

    # ─ RUNNING PHASE ─
    elif phase == "running":
        st.markdown(f'<div class="order-number">#{st.session_state.order_number}</div>', unsafe_allow_html=True)
        elapsed = time.time() - (st.session_state.start_time or time.time())
        st.markdown(f'<div class="timer-display">⏱ {format_duration(elapsed)}</div>', unsafe_allow_html=True)

        if st.button(f"⏹️ Concluir {current_step['label']}", use_container_width=True, type="primary"):
            now = time.time()
            order = st.session_state.current_order

            # Finaliza etapa atual
            for s in reversed(order["steps"]):
                if s["step"] == current_step["key"] and s["endTime"] is None:
                    s["endTime"] = now
                    break

            is_last = step_idx == len(STEPS) - 1
            orders = load_orders()

            # Atualiza/adiciona no JSON
            existing_idx = next((i for i, o in enumerate(orders) if o["id"] == order["id"]), None)
            if existing_idx is not None:
                orders[existing_idx] = order
            else:
                orders.append(order)

            if is_last:
                order["completedAt"] = now
                orders[existing_idx if existing_idx is not None else len(orders) - 1] = order
                save_orders(orders)
                st.session_state.phase = "done"
            else:
                save_orders(orders)
                st.session_state.current_order = order
                st.session_state.phase = "transition"

            st.rerun()

        # Atualiza timer a cada 1s
        time.sleep(1)
        st.rerun()

    # ─ TRANSITION PHASE ─
    elif phase == "transition":
        st.markdown(f'<div class="order-number">#{st.session_state.order_number}</div>', unsafe_allow_html=True)
        next_step = STEPS[step_idx + 1]
        st.success(f"✅ Etapa {current_step['label']} concluída!")
        st.markdown(f"**Quem fará a {next_step['label']}?**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧑 Eu mesmo", use_container_width=True, type="primary"):
                st.session_state.current_step_idx = step_idx + 1
                st.session_state.phase = "ready"
                st.rerun()
        with col2:
            if st.button("👥 Outro operador", use_container_width=True):
                orders = load_orders()
                order = st.session_state.current_order
                existing_idx = next((i for i, o in enumerate(orders) if o["id"] == order["id"]), None)
                if existing_idx is not None:
                    orders[existing_idx] = order
                else:
                    orders.append(order)
                save_orders(orders)

                st.session_state.page = "login"
                st.session_state.operator = None
                st.session_state.phase = "input"
                st.rerun()

    # ─ DONE PHASE ─
    elif phase == "done":
        st.markdown(f'<div class="order-number">#{st.session_state.order_number}</div>', unsafe_allow_html=True)
        st.success("✅ Pedido concluído! Todas as etapas foram finalizadas.")
        if st.button("📦 Novo Pedido", use_container_width=True, type="primary"):
            st.session_state.phase = "input"
            st.session_state.order_number = ""
            st.session_state.current_step_idx = 0
            st.session_state.current_order = None
            st.rerun()

# ─── MANAGER PAGE ───
def manager_page():
    def right_header():
        col_a, col_b = st.columns([5, 1])
        with col_b:
            if st.button("⬅️", help="Voltar"):
                st.session_state.page = "login"
                st.rerun()

    render_topbar(extra_right=right_header)
    st.markdown("### Painel de Gerência")

    orders = load_orders()
    completed = [o for o in orders if o.get("completedAt")]

    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Pedidos concluídos", len(completed))
    with col2:
        if completed:
            avg = sum((o["completedAt"] - o["createdAt"]) for o in completed) / len(completed)
            st.metric("⏱ Tempo médio total", format_duration(avg))
        else:
            st.metric("⏱ Tempo médio total", "--:--:--")
    with col3:
        since = time.time() - 8 * 3600
        active_ops = set()
        for o in orders:
            for s in o.get("steps", []):
                if s.get("endTime") and s["endTime"] >= since:
                    active_ops.add(s["operatorId"])
        st.metric("👥 Operadores ativos (8h)", len(active_ops))

    st.markdown("---")
    st.markdown("#### Desempenho por operador")
    op_stats = []
    for op in OPERATORS:
        steps = []
        for o in orders:
            for s in o.get("steps", []):
                if s["operatorId"] == op and s.get("endTime"):
                    steps.append(s)
        if steps:
            total_time = sum((s["endTime"] - s["startTime"]) for s in steps)
            avg_time = total_time / len(steps)
            op_stats.append({
                "Operador": op,
                "Etapas": len(steps),
                "Tempo Total": format_duration(total_time),
                "Média por etapa": format_duration(avg_time),
            })
    if op_stats:
        st.dataframe(op_stats, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado de operador ainda.")

    st.markdown("---")
    st.markdown("#### Pedidos recentes")
    if orders:
        table_data = []
        for o in reversed(orders[-20:]):
            row = {"Pedido": f"#{o['orderNumber']}"}
            for step_def in STEPS:
                step = next((s for s in o["steps"] if s["step"] == step_def["key"]), None)
                if step and step.get("endTime"):
                    dur = format_duration(step["endTime"] - step["startTime"])
                    row[step_def["label"]] = f"{step['operatorId']} ({dur})"
                elif step:
                    row[step_def["label"]] = f"{step['operatorId']} (…)".replace("..", "…")
                else:
                    row[step_def["label"]] = "—"
            row["Status"] = "✅ Concluído" if o.get("completedAt") else "🔄 Em andamento"
            table_data.append(row)
        st.dataframe(table_data, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum pedido registrado ainda.")

# ─── ROUTER ───
page = st.session_state.page
if page == "login":
    login_page()
elif page == "operator":
    operator_page()
elif page == "manager":
    manager_page()
