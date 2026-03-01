import streamlit as st
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# ─── Config ───
st.set_page_config(page_title="VI LINGERIE - Apontamento", page_icon="👙", layout="wide")

DATA_FILE = "orders.json"

OPERATORS = [
    "Lucivanio", "Enagio", "Daniel", "Italo",
    "Cildenir", "Samya", "Neide", "Eduardo", "Talyson"
]

STEPS = [
    {"key": "separacao", "label": "SEPARACAO", "icon": "📦"},
    {"key": "embalagem", "label": "EMBALAGEM", "icon": "📦"},
    {"key": "conferencia", "label": "CONFERENCIA", "icon": "📋"},
]

OPERATOR_COLORS = {
    "Lucivanio": "#7B2D8E",
    "Enagio": "#2E8B57",
    "Daniel": "#8B1A4A",
    "Italo": "#2563EB",
    "Cildenir": "#6B21A8",
    "Samya": "#1B5E20",
    "Neide": "#A0365A",
    "Eduardo": "#DC6B19",
    "Talyson": "#7C5CBF",
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
    /* Fundo branco global */
    .stApp {
        background-color: #F5F5F0;
    }
    
    /* Esconder elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Container principal */
    .main-container {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 1000px;
        margin: 2rem auto;
    }
    
    /* Logo header */
    .logo-header {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    
    .logo-header img {
        max-width: 300px;
        height: auto;
        margin-bottom: 1rem;
    }
    
    .logo-subtitle {
        font-size: 1.3rem;
        font-weight: 700;
        color: #2C3E50;
        margin: 0.5rem 0;
    }
    
    .logo-description {
        font-size: 0.95rem;
        color: #95A5A6;
        margin: 0.3rem 0;
    }
    
    /* Operator header */
    .operator-header {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .operator-info {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .operator-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.5rem;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    
    .operator-details {
        text-align: left;
    }
    
    .operator-label {
        font-size: 0.7rem;
        font-weight: bold;
        color: #95A5A6;
        letter-spacing: 2px;
        margin: 0;
        text-transform: uppercase;
    }
    
    .operator-name {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2C3E50;
        margin: 0;
    }
    
    /* Step badges com linha conectora */
    .step-tracker {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
        position: relative;
    }
    
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        flex: 1;
        max-width: 200px;
    }
    
    .step-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        z-index: 2;
        position: relative;
    }
    
    .step-done .step-circle {
        background: #2563EB;
        color: white;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    .step-current .step-circle {
        background: #7B2D8E;
        color: white;
        box-shadow: 0 4px 12px rgba(123, 45, 142, 0.3);
        animation: pulse 2s infinite;
    }
    
    .step-pending .step-circle {
        background: #E5E7EB;
        color: #9CA3AF;
    }
    
    .step-label {
        font-size: 0.85rem;
        font-weight: bold;
        color: #2C3E50;
        text-transform: uppercase;
    }
    
    .step-line {
        position: absolute;
        top: 30px;
        left: 50%;
        right: -50%;
        height: 3px;
        background: #E5E7EB;
        z-index: 1;
    }
    
    .step-done .step-line {
        background: #2563EB;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Order number */
    .order-number {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        margin: 2rem 0;
        color: #2C3E50;
    }
    
    /* Timer display */
    .timer-display {
        font-size: 3rem;
        font-family: 'Courier New', monospace;
        text-align: center;
        padding: 1.5rem;
        font-weight: bold;
        color: #2C3E50;
        margin: 1.5rem 0;
    }
    
    /* Input field customizado */
    .stTextInput > div > div > input {
        border: 3px solid #DC2626 !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        font-size: 1.2rem !important;
        text-align: center !important;
    }
    
    /* Botões */
    .stButton > button {
        border-radius: 16px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1rem 2rem !important;
        transition: all 0.3s !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important;
    }
    
    /* Operator grid */
    .operator-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .operator-card {
        background: #F8F9FA;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
        border: 2px solid transparent;
    }
    
    .operator-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    /* Success box */
    .success-box {
        background: #E8F4FD;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    
    .success-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2563EB;
        margin-bottom: 0.5rem;
    }
    
    .success-question {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2C3E50;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: #E5E7EB;
        margin: 2rem 0;
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
    st.markdown('''
    <div class="logo-header">
        <img src="https://raw.githubusercontent.com/HapvidaNotre/vi-producao/main/logo_vi.png" alt="VI Lingerie Logo">
        <p class="logo-subtitle">Apontamento de Producao</p>
        <p class="logo-description">Selecione seu nome para comecar</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.9rem; font-weight:bold; color:#95A5A6; letter-spacing:2px; text-transform:uppercase; margin-bottom:1.5rem;">QUEM E VOCE?</p>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    for i, op in enumerate(OPERATORS):
        col = cols[i % 3]
        color = OPERATOR_COLORS.get(op, "#666")
        with col:
            if st.button(f"{op[0]}\n\n{op}", key=f"op_{op}", use_container_width=True):
                st.session_state.operator = op
                st.session_state.page = "operator"
                st.session_state.phase = "input"
                st.session_state.current_step_idx = 0
                st.session_state.current_order = None
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔒 Acesso Gerencia", use_container_width=True):
            st.session_state.page = "manager"
            st.rerun()

# ─── OPERATOR PAGE ───
def operator_page():
    operator = st.session_state.operator
    color = OPERATOR_COLORS.get(operator, "#666")
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    current_step = STEPS[st.session_state.current_step_idx]
    step_label = current_step["label"] if st.session_state.phase != "input" else ""
    
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        st.markdown(f'''
        <div class="operator-info">
            <div class="operator-avatar" style="background:{color};">{operator[0]}</div>
            <div class="operator-details">
                <p class="operator-label">ESTACAO CENTRAL</p>
                <p class="operator-name">{operator}</p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        if st.session_state.phase != "input":
            st.markdown(f'<div style="text-align:center; padding:1rem;"><span style="background:#E8F4FD; color:#2563EB; padding:0.5rem 1.5rem; border-radius:20px; font-weight:bold; font-size:0.9rem;">{step_label}</span></div>', unsafe_allow_html=True)
    
    with col3:
        if st.button("🚪", key="logout", help="Sair"):
            st.session_state.page = "login"
            st.session_state.operator = None
            st.rerun()
    
    # Linha divisória com cor do operador
    st.markdown(f'<div style="height:3px; background:{color}; border-radius:2px; margin:1rem 0;"></div>', unsafe_allow_html=True)
    
    phase = st.session_state.phase
    step_idx = st.session_state.current_step_idx
    
    # Step tracker visual
    if phase != "input":
        step_html = '<div class="step-tracker">'
        for i, step in enumerate(STEPS):
            step_class = "step-done" if i < step_idx else ("step-current" if i == step_idx else "step-pending")
            icon = "✓" if i < step_idx else step["icon"]
            
            step_html += f'''
            <div class="step-item {step_class}">
                <div class="step-circle">{icon}</div>
                <div class="step-label">{step["label"]}</div>
                {f'<div class="step-line"></div>' if i < len(STEPS) - 1 else ''}
            </div>
            '''
        step_html += '</div>'
        st.markdown(step_html, unsafe_allow_html=True)
    
    # ─ INPUT PHASE ─
    if phase == "input":
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center; font-size:4rem; opacity:0.2; margin:2rem 0;">📦</div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-weight:bold; font-size:1.3rem; color:#2C3E50;">Bipar ou digitar pedido</p>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; font-size:0.95rem; color:#95A5A6; margin-bottom:2rem;">Insira o numero do pedido para iniciar</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            order_num = st.text_input("Numero do pedido", placeholder="Ex: 12345", label_visibility="collapsed", key="order_input")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("➡️", use_container_width=True, disabled=not order_num.strip() if 'order_num' in locals() else True, type="primary"):
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
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"▶ INICIAR {current_step['label']}", use_container_width=True, type="primary"):
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
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"⏹ CONCLUIR {current_step['label']}", use_container_width=True, type="primary"):
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
                    existing = [i for i, o in enumerate(orders) if o["id"] == order["id"]]
                    if existing:
                        orders[existing[0]] = order
                    else:
                        orders.append(order)
                    save_orders(orders)
                    st.session_state.current_order = order
                    st.session_state.phase = "transition"
                st.rerun()
        
        time.sleep(1)
        st.rerun()
    
    # ─ TRANSITION PHASE ─
    elif phase == "transition":
        st.markdown(f'<div class="order-number">#{st.session_state.order_number}</div>', unsafe_allow_html=True)
        next_step = STEPS[step_idx + 1]
        
        st.markdown(f'''
        <div class="success-box">
            <p class="success-title">Etapa anterior concluida!</p>
            <p class="success-question">Quem fara a {next_step["label"]}?</p>
        </div>
        ''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Eu mesmo", use_container_width=True, type="primary"):
                st.session_state.current_step_idx = step_idx + 1
                st.session_state.phase = "ready"
                st.rerun()
        with col2:
            if st.button("👥 Outro operador", use_container_width=True):
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
        st.success("✅ Pedido concluido! Todas as etapas foram finalizadas.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📦 Novo Pedido", use_container_width=True, type="primary"):
                st.session_state.phase = "input"
                st.session_state.order_number = ""
                st.session_state.current_step_idx = 0
                st.session_state.current_order = None
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ─── MANAGER PAGE ───
def manager_page():
    st.markdown('''
    <div class="logo-header">
        <img src="https://raw.githubusercontent.com/HapvidaNotre/vi-producao/main/logo_vi.png" alt="VI Lingerie Logo">
        <p class="logo-subtitle">Painel de Gerencia</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if st.button("⬅️ Voltar ao Login", key="back_to_login"):
        st.session_state.page = "login"
        st.rerun()
    
    orders = load_orders()
    completed = [o for o in orders if o.get("completedAt")]
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 PEDIDOS CONCLUIDOS", len(completed))
    with col2:
        if completed:
            avg = sum((o["completedAt"] - o["createdAt"]) for o in completed) / len(completed)
            st.metric("⏱ TEMPO MEDIO", format_duration(avg))
        else:
            st.metric("⏱ TEMPO MEDIO", "--:--:--")
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
                "Media": format_duration(avg_time),
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
            row["Status"] = "✅ Concluido" if o.get("completedAt") else "🔄 Em andamento"
            table_data.append(row)
        st.dataframe(table_data, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum pedido registrado ainda.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ─── ROUTER ───
page = st.session_state.page
if page == "login":
    login_page()
elif page == "operator":
    operator_page()
elif page == "manager":
    manager_page()
