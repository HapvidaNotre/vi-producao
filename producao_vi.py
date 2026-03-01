import streamlit as st
import json
import time
from pathlib import Path

# ─── Config ───
st.set_page_config(page_title="VI LINGERIE", page_icon="✦", layout="wide")

DATA_FILE = "orders.json"

OPERATORS = [
    "Lucivanio", "Enagio", "Daniel", "Italo",
    "Cildenir", "Samya", "Neide", "Eduardo", "Talyson"
]

STEPS = [
    {"key": "separacao",  "label": "Separação",  "icon": "◈", "num": "01"},
    {"key": "embalagem",  "label": "Embalagem",  "icon": "◉", "num": "02"},
    {"key": "conferencia","label": "Conferência","icon": "◎", "num": "03"},
]

# Each operator gets a distinct, high-contrast color pair (bg, text)
OPERATOR_PALETTE = {
    "Lucivanio": {"bg": "#C0392B", "accent": "#FF6B5B"},   # vermelho
    "Enagio":    {"bg": "#1A6B3A", "accent": "#2ECC71"},   # verde escuro
    "Daniel":    {"bg": "#1A3A6B", "accent": "#5B9BFF"},   # azul marinho
    "Italo":     {"bg": "#6B1A6B", "accent": "#D45BFF"},   # roxo
    "Cildenir":  {"bg": "#6B4A1A", "accent": "#FFA845"},   # âmbar
    "Samya":     {"bg": "#1A6B6B", "accent": "#45FFE5"},   # teal
    "Neide":     {"bg": "#3A1A6B", "accent": "#8B6BFF"},   # índigo
    "Eduardo":   {"bg": "#6B1A1A", "accent": "#FF9B6B"},   # terracota
    "Talyson":   {"bg": "#1A4A6B", "accent": "#6BC5FF"},   # azul céu
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

def fmt_dur(seconds):
    if seconds is None:
        return "--:--:--"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ─── Global CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background: #0A0A0F !important;
    font-family: 'DM Sans', sans-serif;
    color: #F0EEE8;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp > div { background: transparent; }

/* ── Grain overlay ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 9999;
    opacity: 0.4;
}

/* ── Streamlit overrides ── */
.stButton > button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    height: auto !important;
    width: auto !important;
    line-height: 1 !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    color: inherit !important;
    font-family: inherit !important;
    transition: none !important;
    transform: none !important;
}
.stButton > button:hover {
    background: transparent !important;
    transform: none !important;
    box-shadow: none !important;
}
.stButton > button:focus { outline: none !important; box-shadow: none !important; }

.stTextInput > div > div > input {
    background: #13131A !important;
    border: 2px solid #2A2A38 !important;
    border-radius: 12px !important;
    color: #F0EEE8 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 2rem !important;
    font-weight: 500 !important;
    text-align: center !important;
    padding: 1.5rem !important;
    letter-spacing: 0.1em !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #E8B4A0 !important;
    box-shadow: 0 0 0 3px rgba(232,180,160,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: #444455 !important; }

.stMetric { background: #13131A; border-radius: 12px; padding: 1.2rem; border: 1px solid #1E1E2A; }
.stMetric label { color: #666 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 2px; }
.stMetric [data-testid="metric-container"] > div:last-child { color: #F0EEE8 !important; font-size: 2rem !important; font-weight: 700 !important; }

div[data-testid="stDataFrame"] { background: #13131A; border-radius: 12px; overflow: hidden; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0A0A0F; }
::-webkit-scrollbar-thumb { background: #2A2A38; border-radius: 3px; }

/* ══════════════════════════════════════════
   PAGE: LOGIN
══════════════════════════════════════════ */
.login-wrap {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 3rem 1.5rem 4rem;
}

.brand-mark {
    text-align: center;
    margin-bottom: 3.5rem;
}

.brand-mark .wordmark {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 900;
    letter-spacing: 0.25em;
    color: #F0EEE8;
    line-height: 1;
}

.brand-mark .tagline {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.4em;
    color: #444;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

.brand-mark .divider-line {
    width: 40px;
    height: 1px;
    background: #333;
    margin: 1.2rem auto 0;
}

.login-heading {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #555;
    text-align: center;
    margin-bottom: 2rem;
}

/* Operator profile grid */
.op-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.4rem;
    max-width: 540px;
    width: 100%;
    margin-bottom: 3rem;
}

.op-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
}

.op-card:hover { transform: translateY(-4px) scale(1.02); }
.op-card:active { transform: scale(0.97); }

.op-avatar {
    width: 88px;
    height: 88px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 900;
    color: #fff;
    position: relative;
    transition: box-shadow 0.2s;
}

.op-card:hover .op-avatar {
    box-shadow: 0 12px 40px rgba(0,0,0,0.5);
}

.op-avatar-ring {
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 1.5px solid transparent;
    transition: border-color 0.2s;
}

.op-card:hover .op-avatar-ring {
    border-color: rgba(255,255,255,0.25);
}

.op-name {
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #999;
    transition: color 0.2s;
}

.op-card:hover .op-name { color: #F0EEE8; }

.mgr-link {
    font-size: 0.75rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #333;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    transition: color 0.2s;
    margin-top: 0.5rem;
}

.mgr-link:hover { color: #666; }

/* ══════════════════════════════════════════
   PAGE: OPERATOR
══════════════════════════════════════════ */
.op-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Top bar */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.2rem 2rem;
    border-bottom: 1px solid #1A1A24;
    background: #0D0D14;
    position: sticky;
    top: 0;
    z-index: 100;
}

.topbar-brand {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: #F0EEE8;
}

.topbar-op {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.topbar-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.1rem;
    color: #fff;
}

.topbar-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: #F0EEE8;
}

.topbar-role {
    font-size: 0.68rem;
    color: #555;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.topbar-exit {
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #444;
    cursor: pointer;
    transition: color 0.2s;
    padding: 0.5rem 0.75rem;
    border: 1px solid #1E1E2A;
    border-radius: 8px;
}

.topbar-exit:hover { color: #F0EEE8; border-color: #333; }

/* Step progress bar */
.step-rail {
    display: flex;
    align-items: center;
    padding: 2rem 2.5rem;
    gap: 0;
    max-width: 600px;
    margin: 0 auto;
    width: 100%;
}

.step-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    flex: 0 0 auto;
    width: 80px;
}

.step-dot {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 700;
    transition: all 0.3s;
    border: 2px solid #1E1E2A;
    color: #333;
    background: #13131A;
}

.step-dot.done {
    background: #1A6B3A;
    border-color: #2ECC71;
    color: #fff;
}

.step-dot.active {
    background: #C0392B;
    border-color: #FF6B5B;
    color: #fff;
    box-shadow: 0 0 20px rgba(192,57,43,0.4);
    animation: glow 2s ease-in-out infinite;
}

@keyframes glow {
    0%, 100% { box-shadow: 0 0 20px rgba(192,57,43,0.4); }
    50% { box-shadow: 0 0 30px rgba(192,57,43,0.7); }
}

.step-label {
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #444;
    text-align: center;
    font-weight: 600;
}

.step-label.done { color: #2ECC71; }
.step-label.active { color: #FF6B5B; }

.step-connector {
    flex: 1;
    height: 1px;
    background: #1E1E2A;
    margin-bottom: 20px;
    transition: background 0.5s;
}

.step-connector.done { background: #1A6B3A; }

/* Content area */
.content-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 1.5rem 4rem;
    max-width: 560px;
    margin: 0 auto;
    width: 100%;
}

/* Phase: INPUT */
.input-phase-hint {
    font-size: 0.72rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 1.5rem;
    text-align: center;
}

.input-phase-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #F0EEE8;
    margin-bottom: 0.5rem;
    text-align: center;
}

.input-phase-sub {
    font-size: 0.9rem;
    color: #555;
    margin-bottom: 2.5rem;
    text-align: center;
}

.btn-primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 1.1rem 2rem;
    background: #F0EEE8;
    color: #0A0A0F;
    font-family: 'DM Sans', sans-serif;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    margin-top: 1rem;
}

.btn-primary:hover {
    background: #E8D8CC;
    transform: translateY(-1px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

.btn-primary:active { transform: translateY(0); }

.btn-secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 1rem 2rem;
    background: transparent;
    color: #F0EEE8;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #2A2A38;
}

.btn-secondary:hover { border-color: #555; background: #13131A; }

/* Phase: READY & RUNNING */
.order-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 0.5rem;
}

.order-number {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3rem, 12vw, 5.5rem);
    font-weight: 900;
    color: #F0EEE8;
    line-height: 1;
    margin-bottom: 2rem;
    letter-spacing: -0.02em;
}

.timer-block {
    background: #13131A;
    border: 1px solid #1E1E2A;
    border-radius: 16px;
    padding: 1.5rem 3rem;
    margin: 1.5rem 0 2rem;
    text-align: center;
}

.timer-label {
    font-size: 0.65rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #444;
    margin-bottom: 0.5rem;
}

.timer-value {
    font-family: 'DM Mono', monospace;
    font-size: 2.8rem;
    font-weight: 500;
    color: #F0EEE8;
    letter-spacing: 0.05em;
}

.timer-running .timer-value { color: #FF6B5B; }

/* Phase: TRANSITION */
.transition-card {
    background: #13131A;
    border: 1px solid #1E1E2A;
    border-radius: 20px;
    padding: 2.5rem;
    text-align: center;
    width: 100%;
    margin-bottom: 1.5rem;
}

.transition-check {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.transition-title {
    font-size: 0.72rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: #1A6B3A;
    margin-bottom: 0.75rem;
    font-weight: 600;
}

.transition-question {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #F0EEE8;
    margin-bottom: 0.5rem;
}

.transition-sub {
    font-size: 0.85rem;
    color: #555;
}

/* Phase: DONE */
.done-icon {
    font-size: 4rem;
    margin-bottom: 1.5rem;
    display: block;
    text-align: center;
}

.done-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #F0EEE8;
    text-align: center;
    margin-bottom: 0.5rem;
}

.done-sub {
    font-size: 0.9rem;
    color: #555;
    text-align: center;
    margin-bottom: 2rem;
}

/* Accent line */
.accent-line {
    width: 40px;
    height: 2px;
    border-radius: 2px;
    margin: 0 auto 2rem;
}

/* ══════════════════════════════════════════
   PAGE: MANAGER
══════════════════════════════════════════ */
.mgr-wrap {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
}

.mgr-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 3rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #1A1A24;
}

.mgr-title {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #F0EEE8;
}

.mgr-back {
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #444;
    cursor: pointer;
    transition: color 0.2s;
}

.mgr-back:hover { color: #F0EEE8; }

.section-title {
    font-size: 0.7rem;
    letter-spacing: 0.35em;
    text-transform: uppercase;
    color: #444;
    font-weight: 600;
    margin-bottom: 1.2rem;
    margin-top: 2.5rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───
for k, v in [
    ("page", "login"), ("operator", None), ("phase", "input"),
    ("order_number", ""), ("current_step_idx", 0),
    ("start_time", None), ("current_order", None)
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════
def login_page():
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)

    st.markdown('''
    <div class="brand-mark">
        <div class="wordmark">VI LINGERIE</div>
        <div class="tagline">Sistema de Apontamento</div>
        <div class="divider-line"></div>
    </div>
    <div class="login-heading">Quem é você?</div>
    ''', unsafe_allow_html=True)

    # Render operator grid
    st.markdown('<div class="op-grid">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, op in enumerate(OPERATORS):
        pal = OPERATOR_PALETTE.get(op, {"bg": "#333", "accent": "#888"})
        with cols[i % 3]:
            # HTML card rendering
            st.markdown(f'''
            <div class="op-card" id="op-{op}">
                <div class="op-avatar" style="background: radial-gradient(135deg at 30% 30%, {pal["accent"]}66 0%, {pal["bg"]} 100%); box-shadow: 0 8px 32px {pal["bg"]}88, inset 0 1px 0 rgba(255,255,255,0.15);">
                    <div class="op-avatar-ring"></div>
                    {op[0]}
                </div>
                <div class="op-name">{op}</div>
            </div>
            ''', unsafe_allow_html=True)
            # Invisible Streamlit button overlay
            if st.button(op, key=f"sel_{op}", use_container_width=True):
                st.session_state.operator = op
                st.session_state.page = "operator"
                st.session_state.phase = "input"
                st.session_state.current_step_idx = 0
                st.session_state.current_order = None
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Manager access
    if st.button("⬡ Acesso Gerência", key="mgr_btn"):
        st.session_state.page = "manager"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# OPERATOR PAGE
# ═══════════════════════════════════════════════
def operator_page():
    op = st.session_state.operator
    pal = OPERATOR_PALETTE.get(op, {"bg": "#333", "accent": "#888"})
    step_idx = st.session_state.current_step_idx
    phase = st.session_state.phase

    # ── TOP BAR ──
    col_a, col_b, col_c = st.columns([2, 3, 1])
    with col_a:
        st.markdown(f'''
        <div class="topbar-op" style="padding: 0.8rem 0;">
            <div class="topbar-avatar" style="background: {pal["bg"]};">{op[0]}</div>
            <div>
                <div class="topbar-name">{op}</div>
                <div class="topbar-role">Operador</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with col_b:
        st.markdown(f'<div style="padding:0.8rem 0; text-align:center; font-family:\'Playfair Display\',serif; font-size:1.05rem; letter-spacing:0.2em; color:#333; font-weight:700;">VI LINGERIE</div>', unsafe_allow_html=True)

    with col_c:
        if st.button("Sair →", key="exit_btn"):
            st.session_state.page = "login"
            st.session_state.operator = None
            st.session_state.phase = "input"
            st.rerun()

    st.markdown(f'<div style="height:2px; background: linear-gradient(90deg, {pal["bg"]}, {pal["accent"]}, {pal["bg"]}); margin-bottom: 0;"></div>', unsafe_allow_html=True)

    # ── STEP RAIL (show during non-input phases) ──
    if phase != "input":
        step_html = '<div class="step-rail">'
        for i, s in enumerate(STEPS):
            if i < step_idx:
                dot_cls, lbl_cls, symbol = "done", "done", "✓"
            elif i == step_idx:
                dot_cls, lbl_cls, symbol = "active", "active", s["num"]
            else:
                dot_cls, lbl_cls, symbol = "", "", s["num"]

            step_html += f'''
            <div class="step-node">
                <div class="step-dot {dot_cls}">{symbol}</div>
                <div class="step-label {lbl_cls}">{s["label"]}</div>
            </div>
            '''
            if i < len(STEPS) - 1:
                conn_cls = "done" if i < step_idx else ""
                step_html += f'<div class="step-connector {conn_cls}"></div>'

        step_html += '</div>'
        st.markdown(step_html, unsafe_allow_html=True)

    # ── CONTENT ──
    current_step = STEPS[step_idx]
    _, c, _ = st.columns([1, 3, 1])

    with c:
        # ─ INPUT ─
        if phase == "input":
            st.markdown('<div style="height:2.5rem;"></div>', unsafe_allow_html=True)
            st.markdown(f'''
            <div class="input-phase-hint">Novo pedido</div>
            <div class="input-phase-title">Bipe ou digite<br>o número do pedido</div>
            <div class="input-phase-sub">Insira o código e pressione confirmar</div>
            ''', unsafe_allow_html=True)

            order_num = st.text_input("Pedido", placeholder="00000", label_visibility="collapsed", key="order_input")

            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            if st.button("Confirmar pedido →", key="confirm_btn", use_container_width=True, type="primary"):
                if order_num.strip():
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

        # ─ READY ─
        elif phase == "ready":
            st.markdown(f'''
            <div style="text-align:center; padding-top:1rem;">
                <div class="order-badge">Pedido</div>
                <div class="order-number">#{st.session_state.order_number}</div>
            </div>
            <div class="accent-line" style="background:{pal['accent']};"></div>
            ''', unsafe_allow_html=True)

            st.markdown(f'''
            <div style="text-align:center; margin-bottom:2rem;">
                <div style="font-size:0.72rem; letter-spacing:0.3em; text-transform:uppercase; color:#555; margin-bottom:0.4rem;">Próxima etapa</div>
                <div style="font-family:\'Playfair Display\',serif; font-size:1.6rem; font-weight:700; color:#F0EEE8;">{current_step["label"]}</div>
            </div>
            ''', unsafe_allow_html=True)

            if st.button(f"▶ Iniciar {current_step['label']}", key="start_btn", use_container_width=True, type="primary"):
                now = time.time()
                st.session_state.start_time = now
                order = st.session_state.current_order
                order["steps"].append({
                    "step": current_step["key"],
                    "operatorId": op,
                    "startTime": now,
                    "endTime": None,
                })
                st.session_state.current_order = order
                st.session_state.phase = "running"
                st.rerun()

        # ─ RUNNING ─
        elif phase == "running":
            elapsed = time.time() - st.session_state.start_time
            st.markdown(f'''
            <div style="text-align:center; padding-top:1rem;">
                <div class="order-badge">Em andamento</div>
                <div class="order-number">#{st.session_state.order_number}</div>
            </div>
            <div class="accent-line" style="background:{pal['accent']};"></div>
            <div style="text-align:center; font-size:0.72rem; letter-spacing:0.25em; text-transform:uppercase; color:#555; margin-bottom:0.5rem;">{current_step["label"]}</div>
            <div class="timer-block timer-running">
                <div class="timer-label">Tempo decorrido</div>
                <div class="timer-value">{fmt_dur(elapsed)}</div>
            </div>
            ''', unsafe_allow_html=True)

            if st.button(f"⏹ Concluir {current_step['label']}", key="stop_btn", use_container_width=True, type="primary"):
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

        # ─ TRANSITION ─
        elif phase == "transition":
            next_step = STEPS[step_idx + 1]
            st.markdown(f'''
            <div class="transition-card">
                <div class="transition-check">✓</div>
                <div class="transition-title">Etapa concluída</div>
                <div class="transition-question">Quem fará<br>{next_step["label"]}?</div>
                <div class="transition-sub" style="margin-top:0.5rem;">Pedido #{st.session_state.order_number}</div>
            </div>
            ''', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Eu mesmo", key="self_btn", use_container_width=True, type="primary"):
                    st.session_state.current_step_idx = step_idx + 1
                    st.session_state.phase = "ready"
                    st.rerun()
            with col2:
                if st.button("Outro operador", key="other_btn", use_container_width=True):
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

        # ─ DONE ─
        elif phase == "done":
            st.markdown(f'''
            <div style="text-align:center; padding-top:1.5rem;">
                <div class="done-icon">✦</div>
                <div class="done-title">Pedido concluído!</div>
                <div class="done-sub">#{st.session_state.order_number} — todas as etapas finalizadas</div>
            </div>
            ''', unsafe_allow_html=True)

            if st.button("Novo pedido →", key="new_btn", use_container_width=True, type="primary"):
                st.session_state.phase = "input"
                st.session_state.order_number = ""
                st.session_state.current_step_idx = 0
                st.session_state.current_order = None
                st.rerun()


# ═══════════════════════════════════════════════
# MANAGER PAGE
# ═══════════════════════════════════════════════
def manager_page():
    st.markdown('<div class="mgr-wrap">', unsafe_allow_html=True)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="mgr-title">Painel de Gerência</div>', unsafe_allow_html=True)
    with col2:
        if st.button("← Voltar", key="back_btn"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown('<div style="height:1px; background:#1A1A24; margin: 1rem 0 2rem;"></div>', unsafe_allow_html=True)

    orders = load_orders()
    completed = [o for o in orders if o.get("completedAt")]

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pedidos concluídos", len(completed))
    with col2:
        if completed:
            avg = sum((o["completedAt"] - o["createdAt"]) for o in completed) / len(completed)
            st.metric("Tempo médio", fmt_dur(avg))
        else:
            st.metric("Tempo médio", "--:--:--")
    with col3:
        active_ops = set()
        for o in orders:
            for s in o.get("steps", []):
                if s.get("endTime"):
                    active_ops.add(s["operatorId"])
        st.metric("Operadores ativos", len(active_ops))

    # Operator performance
    st.markdown('<div class="section-title">Desempenho por operador</div>', unsafe_allow_html=True)
    op_stats = []
    for o in OPERATORS:
        steps = [s for ord_ in orders for s in ord_.get("steps", [])
                 if s["operatorId"] == o and s.get("endTime")]
        if steps:
            total = sum(s["endTime"] - s["startTime"] for s in steps)
            op_stats.append({
                "Operador": o,
                "Etapas": len(steps),
                "Tempo Total": fmt_dur(total),
                "Média por Etapa": fmt_dur(total / len(steps)),
            })
    if op_stats:
        st.dataframe(op_stats, use_container_width=True, hide_index=True)
    else:
        st.markdown('<p style="color:#444; font-size:0.9rem;">Nenhum dado ainda.</p>', unsafe_allow_html=True)

    # Recent orders
    st.markdown('<div class="section-title">Pedidos recentes</div>', unsafe_allow_html=True)
    if orders:
        table = []
        for o in reversed(orders[-20:]):
            row = {"Pedido": f"#{o['orderNumber']}"}
            for sd in STEPS:
                step = next((s for s in o["steps"] if s["step"] == sd["key"]), None)
                if step and step.get("endTime"):
                    dur = fmt_dur(step["endTime"] - step["startTime"])
                    row[sd["label"]] = f"{step['operatorId']} · {dur}"
                elif step:
                    row[sd["label"]] = f"{step['operatorId']} ···"
                else:
                    row[sd["label"]] = "—"
            row["Status"] = "✓ Concluído" if o.get("completedAt") else "⋯ Em andamento"
            table.append(row)
        st.dataframe(table, use_container_width=True, hide_index=True)
    else:
        st.markdown('<p style="color:#444; font-size:0.9rem;">Nenhum pedido registrado ainda.</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════
{
    "login": login_page,
    "operator": operator_page,
    "manager": manager_page,
}.get(st.session_state.page, login_page)()
