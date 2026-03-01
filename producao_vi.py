import streamlit as st
import json
import time
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VI Lingerie · Produção",
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "orders.json"

OPERATORS = [
    ("Lucivanio", "L", "#E63946"),
    ("Enagio",    "E", "#2A9D8F"),
    ("Daniel",    "D", "#E76F51"),
    ("Italo",     "I", "#457B9D"),
    ("Cildenir",  "C", "#8338EC"),
    ("Samya",     "S", "#06D6A0"),
    ("Neide",     "N", "#FB8500"),
    ("Eduardo",   "Ed","#3A86FF"),
    ("Talyson",   "T", "#FF006E"),
]

STEPS = [
    {"key": "separacao",   "label": "Separação"},
    {"key": "embalagem",   "label": "Embalagem"},
    {"key": "conferencia", "label": "Conferência"},
]

# ── Persistence ──────────────────────────────────────────────────────
def load_orders():
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(DATA_FILE, "w") as f:
        json.dump(orders, f, indent=2)

def fmt(s):
    if s is None: return "--:--:--"
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}"

# ── CSS ──────────────────────────────────────────────────────────────
def inject_css(op_name=None, op_color=None):
    color = op_color or "#E63946"

    # Find operator color for current user
    op_color_map = {name: c for name, _, c in OPERATORS}

    # Build per-operator button styles for login grid
    op_btn_styles = ""
    for name, letter, clr in OPERATORS:
        key = f"op_{name}"
        r = int(clr[1:3], 16)
        g = int(clr[3:5], 16)
        b = int(clr[5:7], 16)
        op_btn_styles += f"""
        div[data-testid="stButton"]:has(button[data-testid="{key}"] ) button,
        button[key="{key}"] {{
            background: {clr} !important;
            box-shadow: 0 4px 24px rgba({r},{g},{b},0.45) !important;
        }}
        div[data-testid="stButton"]:has(> button[kind="secondary"]:nth-child(1)) button {{
        }}
        """

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ── Reset & base ── */
*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [class*="css"], .stApp {{
    font-family: 'Syne', sans-serif !important;
    background-color: #F7F4EF !important;
    color: #1A1A2E !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ 
    padding-top: 2rem !important; 
    padding-bottom: 4rem !important;
    max-width: 560px !important;
}}

/* ── All buttons base reset ── */
.stButton > button {{
    all: unset !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    font-family: 'Syne', sans-serif !important;
}}

/* ════════════════════════════════════════
   OPERATOR AVATAR BUTTONS  
   Invisible overlay on top of HTML avatar
════════════════════════════════════════ */
.op-btn {{
    position: relative !important;
    margin-top: -115px !important;  /* Pull up to overlap the avatar above */
}}

.op-btn .stButton {{
    position: relative !important;
}}

.op-btn .stButton > button {{
    width: 88px !important;
    height: 88px !important;
    border-radius: 50% !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    opacity: 0 !important;
    position: absolute !important;
    top: 0 !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    cursor: pointer !important;
    font-size: 0 !important;
}}

.op-btn .stButton > button:hover {{
    opacity: 0 !important;
    transform: translateX(-50%) !important;
}}

/* ════════════════════════════════════════
   PRIMARY ACTION BUTTON
════════════════════════════════════════ */
.btn-primary .stButton > button {{
    width: 100% !important;
    height: 60px !important;
    border-radius: 14px !important;
    background: {color} !important;
    color: #fff !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 20px {color}55 !important;
}}

.btn-primary .stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px {color}77 !important;
}}

.btn-primary .stButton > button:active {{
    transform: translateY(0px) !important;
}}

/* ════════════════════════════════════════
   SECONDARY BUTTON
════════════════════════════════════════ */
.btn-secondary .stButton > button {{
    width: 100% !important;
    height: 56px !important;
    border-radius: 14px !important;
    background: transparent !important;
    color: #1A1A2E !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border: 2px solid #D4CFC7 !important;
}}

.btn-secondary .stButton > button:hover {{
    border-color: {color} !important;
    color: {color} !important;
    background: {color}0D !important;
}}

/* ════════════════════════════════════════
   GHOST BUTTON (manager link, logout)
════════════════════════════════════════ */
.btn-ghost .stButton > button {{
    width: auto !important;
    height: 36px !important;
    border-radius: 8px !important;
    background: transparent !important;
    color: #999 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding: 0 1rem !important;
    border: 1px solid #E0DBD4 !important;
}}

.btn-ghost .stButton > button:hover {{
    color: #1A1A2E !important;
    border-color: #1A1A2E !important;
}}

/* ════════════════════════════════════════
   TEXT INPUT
════════════════════════════════════════ */
.stTextInput label {{ display: none !important; }}
.stTextInput > div > div > input {{
    background: #fff !important;
    border: 2px solid #E0DBD4 !important;
    border-radius: 14px !important;
    color: #1A1A2E !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 1.2rem !important;
    letter-spacing: 0.15em !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05) !important;
    transition: border-color 0.2s !important;
}}

.stTextInput > div > div > input:focus {{
    border-color: {color} !important;
    box-shadow: 0 0 0 4px {color}22 !important;
    outline: none !important;
}}

.stTextInput > div > div > input::placeholder {{
    color: #C8C2BA !important;
    font-size: 1.8rem !important;
}}

/* ── HR ── */
hr {{ border: none; height: 1px; background: #E8E3DC; margin: 1.5rem 0; }}

/* ── Metric cards ── */
[data-testid="metric-container"] {{
    background: #fff;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    border: 1px solid #EAE5DE;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}}

[data-testid="metric-container"] label {{
    font-size: 0.65rem !important;
    letter-spacing: 0.25em !important;
    text-transform: uppercase !important;
    color: #999 !important;
    font-weight: 600 !important;
}}

[data-testid="metric-container"] [data-testid="metric-value"] {{
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #1A1A2E !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid #EAE5DE !important;
}}

/* ── Streamlit columns spacing ── */
[data-testid="column"] {{
    padding: 0.3rem !important;
}}

/* ── Success/Info ── */
.stSuccess, .stInfo {{
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
}}

</style>
""", unsafe_allow_html=True)


# ── Session state ────────────────────────────────────────────────────
for k, v in [
    ("page", "login"), ("operator", None), ("op_color", "#E63946"),
    ("phase", "input"), ("order_number", ""),
    ("current_step_idx", 0), ("start_time", None), ("current_order", None)
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════

def brand_header(subtitle="Sistema de Apontamento"):
    st.markdown(f"""
<div style="text-align:center; padding: 1.5rem 0 2.5rem;">
    <div style="font-size:0.65rem; letter-spacing:0.45em; text-transform:uppercase; 
                color:#B0A9A0; font-weight:600; margin-bottom:0.6rem;">
        Produção
    </div>
    <div style="font-family:'Syne',sans-serif; font-size:2.6rem; font-weight:800; 
                letter-spacing:0.08em; color:#1A1A2E; line-height:1;">
        VI LINGERIE
    </div>
    <div style="width:32px; height:3px; background:#1A1A2E; border-radius:2px; 
                margin:0.9rem auto;"></div>
    <div style="font-size:0.78rem; letter-spacing:0.2em; text-transform:uppercase; 
                color:#B0A9A0; font-weight:600;">
        {subtitle}
    </div>
</div>
""", unsafe_allow_html=True)


def step_bar(step_idx, color):
    steps = STEPS
    cols = st.columns(len(steps) * 2 - 1)
    col_positions = [0, 2, 4]  # columns for step circles

    for i, step in enumerate(steps):
        with cols[col_positions[i]]:
            if i < step_idx:
                # Done
                st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
    <div style="width:44px;height:44px;border-radius:50%;background:#1A1A2E;
                display:flex;align-items:center;justify-content:center;
                color:#F7F4EF;font-size:1.1rem;font-weight:700;">✓</div>
    <div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;
                color:#1A1A2E;font-weight:600;text-align:center;">{step['label']}</div>
</div>""", unsafe_allow_html=True)
            elif i == step_idx:
                # Active
                st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
    <div style="width:44px;height:44px;border-radius:50%;background:{color};
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-size:0.85rem;font-weight:800;
                box-shadow:0 4px 16px {color}55;
                animation:none;">0{i+1}</div>
    <div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;
                color:{color};font-weight:700;text-align:center;">{step['label']}</div>
</div>""", unsafe_allow_html=True)
            else:
                # Pending
                st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
    <div style="width:44px;height:44px;border-radius:50%;background:#EAE5DE;
                display:flex;align-items:center;justify-content:center;
                color:#C8C2BA;font-size:0.85rem;font-weight:700;">0{i+1}</div>
    <div style="font-size:0.62rem;letter-spacing:0.1em;text-transform:uppercase;
                color:#C8C2BA;font-weight:600;text-align:center;">{step['label']}</div>
</div>""", unsafe_allow_html=True)

        # Connector line between steps
        if i < len(steps) - 1:
            with cols[col_positions[i] + 1]:
                line_color = "#1A1A2E" if i < step_idx else "#E0DBD4"
                st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:center;height:44px;margin-top:0;">
    <div style="width:100%;height:2px;background:{line_color};border-radius:2px;"></div>
</div>""", unsafe_allow_html=True)


def order_display(number, color, label="Pedido"):
    st.markdown(f"""
<div style="text-align:center; padding: 1.5rem 0 1rem;">
    <div style="font-size:0.65rem;letter-spacing:0.35em;text-transform:uppercase;
                color:#B0A9A0;font-weight:600;margin-bottom:0.4rem;">{label}</div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:4rem;font-weight:700;
                color:#1A1A2E;line-height:1;letter-spacing:-0.02em;">#{number}</div>
    <div style="width:32px;height:3px;background:{color};border-radius:2px;
                margin:0.8rem auto 0;"></div>
</div>
""", unsafe_allow_html=True)


def op_topbar(op_name, op_color, op_letter):
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:0.5rem 0 1rem;">
    <div style="width:44px;height:44px;border-radius:50%;background:{op_color};
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-size:1.15rem;font-weight:800;
                box-shadow:0 4px 16px {op_color}55;flex-shrink:0;">
        {op_letter}
    </div>
    <div>
        <div style="font-size:0.6rem;letter-spacing:0.25em;text-transform:uppercase;
                    color:#B0A9A0;font-weight:600;">Operador</div>
        <div style="font-size:1.05rem;font-weight:700;color:#1A1A2E;line-height:1.2;">{op_name}</div>
    </div>
</div>
""", unsafe_allow_html=True)
    with col2:
        with st.container():
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("Sair", key="exit_btn"):
                st.session_state.page = "login"
                st.session_state.operator = None
                st.session_state.phase = "input"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="height:2px;background:{op_color};border-radius:2px;margin-bottom:1.5rem;opacity:0.6;"></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════
def login_page():
    inject_css()
    brand_header("Selecione seu perfil")

    # Operator grid — 3 columns
    rows = [OPERATORS[i:i+3] for i in range(0, len(OPERATORS), 3)]
    for row in rows:
        cols = st.columns(3)
        for j, (name, letter, color) in enumerate(row):
            with cols[j]:
                # Avatar label above
                st.markdown(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:10px;
            margin-bottom:0.5rem;">
    <div style="width:88px;height:88px;border-radius:50%;background:{color};
                display:flex;align-items:center;justify-content:center;
                color:#fff;font-size:2.1rem;font-weight:800;
                box-shadow:0 6px 24px {color}55;
                border:3px solid rgba(255,255,255,0.35);
                cursor:pointer;
                transition:transform 0.18s;">
        {letter}
    </div>
    <div style="font-size:0.8rem;font-weight:600;color:#1A1A2E;text-align:center;">
        {name}
    </div>
</div>
""", unsafe_allow_html=True)
                # The actual clickable button — styled to be invisible/overlay
                st.markdown(f'<div class="op-btn op-{name.lower()}">', unsafe_allow_html=True)
                if st.button(letter, key=f"op_{name}", use_container_width=True):
                    st.session_state.operator = name
                    st.session_state.op_color = color
                    st.session_state.page = "operator"
                    st.session_state.phase = "input"
                    st.session_state.current_step_idx = 0
                    st.session_state.current_order = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-bottom:1rem;"></div>', unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("⬡ Gerência", key="mgr_link", use_container_width=True):
            st.session_state.page = "manager"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  OPERATOR PAGE
# ══════════════════════════════════════════════════════════════════════
def operator_page():
    op_name = st.session_state.operator
    op_color = st.session_state.op_color
    op_letter = next((l for n, l, c in OPERATORS if n == op_name), op_name[0])

    inject_css(op_name, op_color)

    op_topbar(op_name, op_color, op_letter)

    step_idx = st.session_state.current_step_idx
    phase = st.session_state.phase
    current_step = STEPS[step_idx]

    # Show step bar if past input
    if phase != "input":
        step_bar(step_idx, op_color)
        st.markdown('<div style="margin-bottom:1.5rem;"></div>', unsafe_allow_html=True)

    # ─ INPUT ────────────────────────────────────────────────────────
    if phase == "input":
        st.markdown(f"""
<div style="text-align:center;padding:2rem 0 1.5rem;">
    <div style="font-size:3rem;margin-bottom:1rem;">📦</div>
    <div style="font-size:1.5rem;font-weight:800;color:#1A1A2E;margin-bottom:0.3rem;">
        Bipe o pedido
    </div>
    <div style="font-size:0.85rem;color:#B0A9A0;">
        Escaneie o código ou digite o número
    </div>
</div>
""", unsafe_allow_html=True)

        order_num = st.text_input("Pedido", placeholder="00000", key="order_input")
        st.markdown('<div style="margin-top:0.75rem;"></div>', unsafe_allow_html=True)

        if order_num.strip():
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button(f"Confirmar  →", key="confirm_btn", use_container_width=True):
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
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style="width:100%;height:60px;border-radius:14px;background:#EAE5DE;
            display:flex;align-items:center;justify-content:center;
            font-size:0.85rem;font-weight:700;letter-spacing:0.12em;
            text-transform:uppercase;color:#C8C2BA;margin-top:0.75rem;">
    Digite o número para continuar
</div>
""", unsafe_allow_html=True)

    # ─ READY ────────────────────────────────────────────────────────
    elif phase == "ready":
        order_display(st.session_state.order_number, op_color)

        st.markdown(f"""
<div style="text-align:center;padding:0.5rem 0 1.5rem;">
    <div style="display:inline-block;background:{op_color}15;color:{op_color};
                padding:0.4rem 1.2rem;border-radius:20px;font-size:0.75rem;
                font-weight:700;letter-spacing:0.15em;text-transform:uppercase;">
        Próxima etapa: {current_step['label']}
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button(f"▶  Iniciar {current_step['label']}", key="start_btn", use_container_width=True):
            now = time.time()
            st.session_state.start_time = now
            order = st.session_state.current_order
            order["steps"].append({
                "step": current_step["key"],
                "operatorId": op_name,
                "startTime": now,
                "endTime": None,
            })
            st.session_state.current_order = order
            st.session_state.phase = "running"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ─ RUNNING ──────────────────────────────────────────────────────
    elif phase == "running":
        elapsed = time.time() - st.session_state.start_time
        order_display(st.session_state.order_number, op_color, "Em andamento")

        st.markdown(f"""
<div style="background:#fff;border-radius:18px;padding:1.5rem;
            border:2px solid {op_color}33;text-align:center;margin-bottom:1.5rem;
            box-shadow:0 4px 20px {op_color}15;">
    <div style="font-size:0.65rem;letter-spacing:0.3em;text-transform:uppercase;
                color:#B0A9A0;font-weight:600;margin-bottom:0.5rem;">
        {current_step['label']} · Tempo decorrido
    </div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:3rem;font-weight:700;
                color:{op_color};letter-spacing:0.05em;line-height:1;">
        {fmt(elapsed)}
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button(f"⏹  Concluir {current_step['label']}", key="stop_btn", use_container_width=True):
            now = time.time()
            order = st.session_state.current_order
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
                found = [i for i, o in enumerate(orders) if o["id"] == order["id"]]
                if found:
                    orders[found[0]] = order
                else:
                    orders.append(order)
                save_orders(orders)
                st.session_state.current_order = order
                st.session_state.phase = "transition"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        time.sleep(1)
        st.rerun()

    # ─ TRANSITION ───────────────────────────────────────────────────
    elif phase == "transition":
        next_step = STEPS[step_idx + 1]
        order_display(st.session_state.order_number, op_color)

        st.markdown(f"""
<div style="background:#fff;border-radius:18px;padding:2rem;text-align:center;
            border:1px solid #EAE5DE;box-shadow:0 4px 16px rgba(0,0,0,0.05);
            margin-bottom:1.5rem;">
    <div style="font-size:2rem;margin-bottom:0.75rem;">✅</div>
    <div style="font-size:0.65rem;letter-spacing:0.3em;text-transform:uppercase;
                color:#2A9D8F;font-weight:700;margin-bottom:0.5rem;">
        Etapa concluída
    </div>
    <div style="font-size:1.3rem;font-weight:800;color:#1A1A2E;margin-bottom:0.3rem;">
        Quem fará a {next_step['label']}?
    </div>
    <div style="font-size:0.85rem;color:#B0A9A0;">Selecione abaixo para continuar</div>
</div>
""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Eu mesmo", key="self_btn", use_container_width=True):
                st.session_state.current_step_idx = step_idx + 1
                st.session_state.phase = "ready"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button("Outro operador", key="other_btn", use_container_width=True):
                orders = load_orders()
                order = st.session_state.current_order
                found = [i for i, o in enumerate(orders) if o["id"] == order["id"]]
                if found:
                    orders[found[0]] = order
                else:
                    orders.append(order)
                save_orders(orders)
                st.session_state.current_step_idx = step_idx + 1
                st.session_state.page = "login"
                st.session_state.operator = None
                st.session_state.phase = "input"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ─ DONE ─────────────────────────────────────────────────────────
    elif phase == "done":
        st.markdown(f"""
<div style="text-align:center;padding:2rem 0;">
    <div style="font-size:3.5rem;margin-bottom:1rem;">🎉</div>
    <div style="font-size:1.6rem;font-weight:800;color:#1A1A2E;margin-bottom:0.4rem;">
        Pedido concluído!
    </div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;
                color:{op_color};margin:1rem 0;">
        #{st.session_state.order_number}
    </div>
    <div style="font-size:0.85rem;color:#B0A9A0;margin-bottom:2rem;">
        Todas as etapas foram finalizadas com sucesso
    </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Novo pedido  →", key="new_btn", use_container_width=True):
            st.session_state.phase = "input"
            st.session_state.order_number = ""
            st.session_state.current_step_idx = 0
            st.session_state.current_order = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  MANAGER PAGE
# ══════════════════════════════════════════════════════════════════════
def manager_page():
    inject_css()

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
<div style="padding:1rem 0 0.5rem;">
    <div style="font-size:0.6rem;letter-spacing:0.35em;text-transform:uppercase;
                color:#B0A9A0;font-weight:600;">VI Lingerie</div>
    <div style="font-size:1.8rem;font-weight:800;color:#1A1A2E;">Painel de Gerência</div>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-ghost" style="padding-top:1.2rem;">', unsafe_allow_html=True)
        if st.button("← Voltar", key="back_btn", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr>', unsafe_allow_html=True)

    orders = load_orders()
    completed = [o for o in orders if o.get("completedAt")]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pedidos Concluídos", len(completed))
    with col2:
        if completed:
            avg = sum((o["completedAt"] - o["createdAt"]) for o in completed) / len(completed)
            st.metric("Tempo Médio", fmt(avg))
        else:
            st.metric("Tempo Médio", "--:--:--")
    with col3:
        active_ops = {s["operatorId"] for o in orders for s in o.get("steps", []) if s.get("endTime")}
        st.metric("Operadores Ativos", len(active_ops))

    st.markdown('<div style="margin-top:2rem;font-size:0.65rem;letter-spacing:0.3em;text-transform:uppercase;color:#B0A9A0;font-weight:600;margin-bottom:0.75rem;">Desempenho por operador</div>', unsafe_allow_html=True)

    op_stats = []
    for name, _, _ in OPERATORS:
        steps = [s for o in orders for s in o.get("steps", [])
                 if s["operatorId"] == name and s.get("endTime")]
        if steps:
            total = sum(s["endTime"] - s["startTime"] for s in steps)
            op_stats.append({
                "Operador": name,
                "Etapas": len(steps),
                "Tempo Total": fmt(total),
                "Média / Etapa": fmt(total / len(steps)),
            })

    if op_stats:
        st.dataframe(op_stats, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado disponível ainda.")

    st.markdown('<div style="margin-top:2rem;font-size:0.65rem;letter-spacing:0.3em;text-transform:uppercase;color:#B0A9A0;font-weight:600;margin-bottom:0.75rem;">Pedidos recentes</div>', unsafe_allow_html=True)

    if orders:
        table = []
        for o in reversed(orders[-20:]):
            row = {"Pedido": f"#{o['orderNumber']}"}
            for sd in STEPS:
                s = next((x for x in o["steps"] if x["step"] == sd["key"]), None)
                if s and s.get("endTime"):
                    row[sd["label"]] = f"{s['operatorId']} · {fmt(s['endTime']-s['startTime'])}"
                elif s:
                    row[sd["label"]] = f"{s['operatorId']} ···"
                else:
                    row[sd["label"]] = "—"
            row["Status"] = "✓ Concluído" if o.get("completedAt") else "⋯ Em andamento"
            table.append(row)
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum pedido registrado ainda.")


# ── Router ───────────────────────────────────────────────────────────
{
    "login":    login_page,
    "operator": operator_page,
    "manager":  manager_page,
}.get(st.session_state.page, login_page)()
