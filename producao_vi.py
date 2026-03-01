import streamlit as st
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
# ─── Config ───
st.set_page_config(page_title="VI LINGERIE - Apontamento", page_icon="👙", layout="wide")
DATA_FILE = "orders.json"
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
# ─── Persistence ───
def load_orders():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []
def save_orders(orders):
    with open(DATA_FILE, "w") as f:
        json.dump(orders, f, indent=2)
def format_duration(seconds):
    if seconds is None:
        return "--:--:--"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
# ─── Custom CSS ───
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .main-header h1 {
        color: #8B1A4A;
        font-size: 2.5rem;
        font-weight: 900;
        margin: 0;
    }
    .main-header p {
        color: #666;
        font-size: 0.9rem;
    }
    .operator-btn {
        border-radius: 12px;
        padding: 8px;
        text-align: center;
        cursor: pointer;
        font-weight: bold;
        color: white;
        margin: 4px;
    }
    .step-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        margin: 0 4px;
    }
    .step-done { background: #22c55e; color: white; }
    .step-current { background: #3b82f6; color: white; }
    .step-pending { background: #e5e7eb; color: #9ca3af; }
    .timer-display {
        font-size: 3rem;
        font-family: monospace;
        text-align: center;
        padding: 1rem;
        font-weight: bold;
    }
    .order-number {
        font-size: 2.5rem;
        font-weight: 900;
        text-align: center;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 900;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #666;
        text-transform: uppercase;
        font-weight: bold;
    }
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
# ─── LOGIN PAGE ───
def login_page():
    st.markdown('<div class="main-header"><h1>VI LINGERIE</h1><p>Apontamento de Produção</p><p style="font-size:0.8rem; color:#999;">Selecione seu nome para começar</p></div>', unsafe_allow_html=True)
    st.markdown("#### 🧑 QUEM É VOCÊ?")
    cols = st.columns(3)
    for i, op in enumerate(OPERATORS):
        col = cols[i % 3]
        color = OPERATOR_COLORS.get(op, "#666")
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
    operator = st.session_state.operator
    color = OPERATOR_COLORS.get(operator, "#666")
    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown(f'<div style="background:{color}; color:white; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:1.2rem;">{operator[0]}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='font-size:0.6rem; font-weight:bold; color:#999; letter-spacing:2px; margin:0;'>ESTAÇÃO CENTRAL</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-weight:bold; margin:0;'>{operator}</p>", unsafe_allow_html=True)
    with col3:
        if st.button("🚪", key="logout"):
            st.session_state.page = "login"
            st.session_state.operator = None
            st.rerun()
    st.markdown(f'<div style="height:4px; background:{color}; border-radius:2px;"></div>', unsafe_allow_html=True)
    phase = st.session_state.phase
    step_idx = st.session_state.current_step_idx
    # Step tracker
    step_html = ""
    for i, step in enumerate(STEPS):
        if i < step_idx:
            step_html += f'<span class="step-badge step-done">✓ {step["label"]}</span>'
        elif i == step_idx:
            step_html += f'<span class="step-badge step-current">● {step["label"]}</span>'
        else:
            step_html += f'<span class="step-badge step-pending">{step["label"]}</span>'
    if phase != "input":
        st.markdown(f'<div style="text-align:center; margin:1rem 0;">{step_html}</div>', unsafe_allow_html=True)
    current_step = STEPS[step_idx]
    # ─ INPUT PHASE ─
    if phase == "input":
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; font-size:3rem; opacity:0.3;'>📦</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-weight:bold;'>Bipar ou digitar pedido</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.85rem; color:#999;'>Insira o número do pedido para iniciar</p>", unsafe_allow_html=True)
        order_num = st.text_input("Número do pedido", placeholder="Ex: 12345", label_visibility="collapsed")
        if st.button("➡️ Confirmar Pedido", use_container_width=True, disabled=not order_num.strip()):
            st.session_state.order_number = order_num.strip()
            st.session_state.current_order = {
                "id": str(time.time()),
                "orderNumber": order_num.strip(),
                "steps": [],
                "createdAt": time.time(),
                "completedAt": None,
            }
            st.session_state.phase = "ready"
            st.rerun()
    # ─ READY PHASE ─
    elif phase == "ready":
        st.markdown(f'<div class="order-number">#{st.session_state.order_number}</div>', unsafe_allow_html=True)
        if st.button(f"▶️ INICIAR {current_step['label']}", use_container_width=True, type="primary"):
            st.session_state.start_time = time.time()
            now = time.time()
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
        elapsed = time.time() - st.session_state.start_time
        st.markdown(f'<div class="timer-display">⏱ {format_duration(elapsed)}</div>', unsafe_allow_html=True)
        if st.button(f"⏹️ CONCLUIR {current_step['label']}", use_container_width=True, type="primary"):
            now = time.time()
            order = st.session_state.current_order
            # Close current step
            for s in order["steps"]:
                if s["step"] == current_step["key"] and s["endTime"] is None:
                    s["endTime"] = now
                    break
            is_last = step_idx == len(STEPS) - 1
            if is_last:
                order["completedAt"] = now
                orders = load_orders()
                orders.append(order)
                save_orders(orders)
                st.session_state.phase = "done"
            else:
                orders = load_orders()
                # Update or append
                existing = [i for i, o in enumerate(orders) if o["id"] == order["id"]]
                if existing:
                    orders[existing[0]] = order
                else:
                    orders.append(order)
                save_orders(orders)
                st.session_state.current_order = order
                st.session_state.phase = "transition"
            st.rerun()
        # Auto-refresh timer
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
                # Save and go back to login
                orders = load_orders()
                order = st.session_state.current_order
                existing = [i for i, o in enumerate(orders) if o["id"] == order["id"]]
                if existing:
                    orders[existing[0]] = order
                else:
                    orders.append(order)
                save_orders(orders)
                st.session_state.current_step_idx = step_idx + 1
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
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("⬅️"):
            st.session_state.page = "login"
            st.rerun()
    with col2:
        st.markdown("<h2 style='color:#8B1A4A; margin:0;'>VI LINGERIE</h2>", unsafe_allow_html=True)
        st.caption("Painel de Gerência")
    orders = load_orders()
    completed = [o for o in orders if o.get("completedAt")]
    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 PEDIDOS CONCLUÍDOS", len(completed))
    with col2:
        if completed:
            avg = sum((o["completedAt"] - o["createdAt"]) for o in completed) / len(completed)
            st.metric("⏱ TEMPO MÉDIO", format_duration(avg))
        else:
            st.metric("⏱ TEMPO MÉDIO", "--:--:--")
    with col3:
        active_ops = set()
        for o in orders:
            for s in o.get("steps", []):
                if s.get("endTime"):
                    active_ops.add(s["operatorId"])
        st.metric("👥 OPERADORES ATIVOS", len(active_ops))
    # Operator performance
    st.markdown("---")
    st.markdown("##### DESEMPENHO POR OPERADOR")
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
                "Média": format_duration(avg_time),
            })
    if op_stats:
        st.dataframe(op_stats, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado de operador ainda.")
    # Recent orders
    st.markdown("---")
    st.markdown("##### PEDIDOS RECENTES")
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
                    row[step_def["label"]] = f"{step['operatorId']} (...)"
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
