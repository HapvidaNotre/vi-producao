import streamlit as st
import sqlite3
import time
import base64
from datetime import datetime
from pathlib import Path
import csv, io

st.set_page_config(
    page_title="Vi Lingerie - Producao",
    page_icon="👗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────
OPERADORES  = ["Lucivanio","Enagio","Daniel","Italo","Cildenir","Samya","Neide","Eduardo","Talyson"]
ETAPAS      = ["Separacao","Conferencia","Embalagem"]
ETAPAS_LBL  = ["Separação","Conferência","Embalagem"]
ADMIN_SENHA = "vi2025"
DB_PATH     = Path(__file__).parent / "producao.db"

# ─────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido TEXT, operador TEXT, etapa TEXT,
        etapa_idx INTEGER, tempo_segundos INTEGER, data TEXT)""")
    con.commit(); con.close()

def salvar(pedido, operador, etapa, etapa_idx, tempo):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO registros VALUES (NULL,?,?,?,?,?,?)",
        (pedido, operador, etapa, etapa_idx, tempo, datetime.now().strftime("%d/%m/%Y %H:%M")))
    con.commit(); con.close()

def buscar():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT * FROM registros ORDER BY id DESC").fetchall()
    con.close(); return rows

def limpar():
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM registros")
    con.commit(); con.close()

init_db()

# ─────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────
def fmt(s):
    if s < 60: return f"{s}s"
    m, sec = divmod(s, 60)
    if m < 60: return f"{m}m {sec:02d}s"
    h, mi = divmod(m, 60)
    return f"{h}h {mi:02d}m"

def logo_b64():
    p = Path(__file__).parent / "logo_vi.png"
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else None

def media(lst): return int(sum(lst)/len(lst)) if lst else 0

def get_elapsed():
    if st.session_state.get("rodando") and st.session_state.get("inicio"):
        return st.session_state.acum + int(time.time() - st.session_state.inicio)
    return st.session_state.get("acum", 0)

# ─────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────
for k, v in {
    "tela":"home", "operador":None, "pedido":None,
    "etapa_idx":0, "rodando":False, "inicio":None,
    "acum":0, "modal":None,
    "pedido_prox":None, "etapa_prox":None,
    "erro_pedido":False, "erro_senha":False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────
#  QUERY PARAM ROUTER
#  Avatar clicks use <a href="?op=Name"> which sets a query param,
#  Streamlit detects it here, updates session_state, clears params, reruns.
# ─────────────────────────────────────
params = st.query_params
if "op" in params:
    op = params["op"]
    if op in OPERADORES:
        st.session_state.operador = op
        if st.session_state.pedido_prox:
            st.session_state.pedido    = st.session_state.pedido_prox
            st.session_state.etapa_idx = st.session_state.etapa_prox
            st.session_state.pedido_prox = None
            st.session_state.etapa_prox  = None
        else:
            st.session_state.pedido    = None
            st.session_state.etapa_idx = 0
        st.session_state.rodando = False
        st.session_state.inicio  = None
        st.session_state.acum    = 0
        st.session_state.modal   = None
        st.session_state.tela    = "producao"
    st.query_params.clear()
    st.rerun()

# ─────────────────────────────────────
#  CSS
# ─────────────────────────────────────
b64 = logo_b64()
logo_src = f"data:image/png;base64,{b64}" if b64 else ""

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&family=DM+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: #F7F5F2 !important;
    font-family: 'Nunito', sans-serif !important;
}}
[data-testid="stHeader"], [data-testid="stSidebar"], footer, #MainMenu {{ display:none !important; }}
.block-container {{ padding-top:1.8rem !important; padding-bottom:2rem !important; max-width:640px !important; }}

.logo-box {{ text-align:center; margin-bottom:1.6rem; }}
.logo-box img {{ height:56px; object-fit:contain; }}

.section-label {{
    font-size:11px; font-weight:800; letter-spacing:2.5px; text-transform:uppercase;
    color:#9C9490; margin-bottom:1.2rem; text-align:center;
}}

/* ── AVATAR GRID ── */
.ops-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px 20px;
    margin-bottom: 1.5rem;
}}
.op-wrap {{
    display: flex; flex-direction: column;
    align-items: center; gap: 10px;
    text-decoration: none !important;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
}}
.op-wrap:visited, .op-wrap:link, .op-wrap:hover, .op-wrap:active {{
    text-decoration: none !important;
}}
.avatar {{
    width: 74px; height: 74px; border-radius: 50%;
    background: linear-gradient(145deg, #D9617A 0%, #A84055 55%, #7A2D3E 100%);
    box-shadow:
        0 6px 0 rgba(80,10,25,0.50),
        0 10px 24px rgba(158,63,82,0.38),
        inset 0 2px 5px rgba(255,255,255,0.20);
    display: flex; align-items: center; justify-content: center;
    font-size: 28px; font-weight: 900; color: #fff;
    text-shadow: 0 1px 4px rgba(0,0,0,0.30);
    transition: transform 0.20s ease, box-shadow 0.20s ease;
    position: relative; overflow: hidden;
    user-select: none;
}}
.avatar::after {{
    content:''; position:absolute;
    top:8px; left:14px; width:36px; height:19px;
    background: radial-gradient(ellipse, rgba(255,255,255,0.26) 0%, transparent 75%);
    border-radius:50%; pointer-events:none;
}}
.op-wrap:hover .avatar {{
    transform: translateY(-7px) scale(1.07);
    box-shadow:
        0 13px 0 rgba(80,10,25,0.46),
        0 20px 36px rgba(158,63,82,0.46),
        inset 0 2px 5px rgba(255,255,255,0.22);
}}
.op-wrap:active .avatar {{
    transform: translateY(2px) scale(0.95) !important;
    box-shadow:
        0 2px 0 rgba(80,10,25,0.50),
        0 4px 10px rgba(158,63,82,0.28),
        inset 0 3px 8px rgba(0,0,0,0.22) !important;
    transition: transform 0.07s ease, box-shadow 0.07s ease !important;
}}
.op-name {{
    font-size: 13px; font-weight: 700; color: #2C2826;
    text-align: center; line-height: 1.3;
    text-decoration: none !important;
    letter-spacing: 0.1px;
}}

/* ── STEPPER ── */
.stepper {{ display:flex; align-items:flex-start; margin-bottom:1.6rem; }}
.step {{ flex:1; display:flex; flex-direction:column; align-items:center; gap:6px; }}
.sdot {{
    width:32px; height:32px; border-radius:50%;
    border:2px solid #E0DBD4; background:#EDE9E4;
    display:flex; align-items:center; justify-content:center;
    font-size:13px; font-weight:800; color:#A09890;
}}
.sdot.active {{ background:#C8566A; border-color:#C8566A; color:#fff; box-shadow:0 0 0 5px rgba(200,86,106,0.14); }}
.sdot.done   {{ background:#4A7C59; border-color:#4A7C59; color:#fff; }}
.slbl {{ font-size:10px; font-weight:800; letter-spacing:1px; text-transform:uppercase; color:#A09890; text-align:center; }}
.slbl.active {{ color:#C8566A; }} .slbl.done {{ color:#4A7C59; }}
.sline {{ flex:1; height:2px; background:#E0DBD4; margin-top:14px; }}
.sline.done {{ background:#4A7C59; }}

/* ── CARD ── */
.vi-card {{
    background:#fff; border:1.5px solid #E8E3DC; border-radius:16px;
    padding:28px; box-shadow:0 4px 20px rgba(0,0,0,0.06); margin-bottom:1rem;
}}

/* ── BADGE ── */
.badge-op {{
    display:inline-flex; align-items:center; gap:7px;
    padding:6px 16px; border-radius:100px;
    background:#F5E8EB; color:#C8566A;
    font-size:13px; font-weight:800; margin-bottom:1.2rem;
    letter-spacing:0.2px;
}}

/* ── ETAPA LABEL ── */
.etapa-info {{
    background: #F5E8EB;
    border-left: 4px solid #C8566A;
    border-radius: 0 10px 10px 0;
    padding: 10px 16px;
    margin-bottom: 20px;
    font-size: 14px; font-weight: 700; color: #1A1714;
}}

/* ── INPUT ── */
.stTextInput > div > div > input {{
    border: 2px solid #E0DBD4 !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    padding: 16px 18px !important;
    color: #1A1714 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    transition: border-color .2s, box-shadow .2s !important;
    height: 56px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #C8566A !important;
    box-shadow: 0 0 0 4px rgba(200,86,106,0.12) !important;
}}
.stTextInput > div > div > input::placeholder {{
    color: #C0BAB4 !important; font-weight: 600 !important;
}}
label {{
    font-family: 'Nunito', sans-serif !important;
    font-size: 11px !important; font-weight: 800 !important;
    color: #9C9490 !important; letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}}

/* ── BUTTONS ── */
.stButton > button {{
    font-family: 'Nunito', sans-serif !important;
    font-weight: 800 !important;
    border-radius: 12px !important;
    transition: all .18s ease !important;
    height: 54px !important;
    font-size: 15px !important;
    letter-spacing: .5px !important;
}}
/* INICIAR — verde escuro elegante */
.btn-iniciar > button {{
    background: linear-gradient(135deg, #2C6E49, #1E4D35) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 5px 0 rgba(20,50,30,0.45), 0 8px 20px rgba(44,110,73,0.30) !important;
}}
.btn-iniciar > button:hover {{
    background: linear-gradient(135deg, #357a54, #266040) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 0 rgba(20,50,30,0.40), 0 14px 28px rgba(44,110,73,0.35) !important;
}}
.btn-iniciar > button:active {{
    transform: translateY(2px) !important;
    box-shadow: 0 2px 0 rgba(20,50,30,0.45), 0 3px 8px rgba(44,110,73,0.20) !important;
}}
/* VOLTAR — cinza quente */
.btn-voltar > button {{
    background: #FFFFFF !important;
    color: #5C5450 !important;
    border: 2px solid #DDD8D2 !important;
    box-shadow: 0 3px 0 rgba(0,0,0,0.10), 0 4px 12px rgba(0,0,0,0.07) !important;
}}
.btn-voltar > button:hover {{
    border-color: #C8566A !important; color: #C8566A !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 5px 0 rgba(0,0,0,0.08), 0 8px 16px rgba(200,86,106,0.12) !important;
}}
/* FINALIZAR — vermelho */
.btn-finalizar > button {{
    background: linear-gradient(135deg, #C8566A, #9E3F52) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 5px 0 rgba(100,20,35,0.45), 0 8px 20px rgba(200,86,106,0.32) !important;
}}
.btn-finalizar > button:hover {{
    background: linear-gradient(135deg, #d9617a, #b04560) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 0 rgba(100,20,35,0.40), 0 14px 28px rgba(200,86,106,0.38) !important;
}}
.btn-finalizar > button:active {{
    transform: translateY(2px) !important;
    box-shadow: 0 2px 0 rgba(100,20,35,0.45) !important;
}}
/* PRIMARY (reutilizado) */
.btn-primary > button {{
    background: linear-gradient(135deg, #C8566A, #9E3F52) !important;
    color: #fff !important; border: none !important;
    box-shadow: 0 5px 0 rgba(100,20,35,0.40), 0 8px 18px rgba(200,86,106,0.28) !important;
}}
.btn-primary > button:hover {{
    background: linear-gradient(135deg, #d9617a, #b04560) !important;
    transform: translateY(-2px) !important;
}}
.btn-outline > button {{
    background: #fff !important; color: #5C5450 !important;
    border: 2px solid #DDD8D2 !important;
    box-shadow: 0 3px 0 rgba(0,0,0,0.08) !important;
}}
.btn-outline > button:hover {{ border-color:#C8566A !important; color:#C8566A !important; }}
.btn-sm > button {{ height:40px !important; font-size:12px !important; }}

/* ── TIMER ── */
.timer-wrap {{
    background: linear-gradient(135deg, #fff, #fdf5f7);
    border: 2px solid #F0E0E4;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(200,86,106,0.08);
}}
.timer-num {{
    font-family:'DM Mono',monospace; font-size:62px; font-weight:500;
    color:#C8566A; letter-spacing:-2px; line-height:1;
}}
.pedido-lbl {{ font-size:10px; font-weight:800; color:#9C9490; text-align:center; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }}
.pedido-num {{ font-family:'DM Mono',monospace; font-size:24px; font-weight:500; color:#1A1714; text-align:center; margin-bottom:6px; }}

/* ── ADMIN ── */
.stat-box {{ background:#fff; border:1.5px solid #E8E3DC; border-radius:14px; padding:18px; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.05); }}
.stat-num {{ font-family:'DM Mono',monospace; font-size:32px; font-weight:500; color:#C8566A; }}
.stat-lbl {{ font-size:11px; font-weight:800; color:#9C9490; letter-spacing:.8px; margin-top:5px; text-transform:uppercase; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; padding:10px 12px; font-size:10px; font-weight:800; letter-spacing:1.2px; text-transform:uppercase; color:#9C9490; border-bottom:2px solid #EDE9E4; }}
td {{ padding:11px 12px; border-bottom:1px solid #F2EEE9; color:#2C2826; font-weight:600; }}
.tag {{ display:inline-block; padding:3px 10px; border-radius:100px; font-size:10px; font-weight:800; letter-spacing:.5px; }}
.tag-sep {{ background:#EBF0FB; color:#3B5EC6; }}
.tag-conf {{ background:#FBF2E6; color:#C47B2A; }}
.tag-emb  {{ background:#E8F2EC; color:#4A7C59; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
#  RENDER HELPERS
# ─────────────────────────────────────
def render_logo():
    if logo_src:
        st.markdown(f'<div class="logo-box"><img src="{logo_src}"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-box" style="font-size:22px;font-weight:700;color:#C8566A;">Vi Lingerie</div>', unsafe_allow_html=True)

def render_stepper(idx):
    html = '<div class="stepper">'
    for i, lbl in enumerate(ETAPAS_LBL):
        dc = "done" if i < idx else ("active" if i == idx else "")
        html += f'<div class="step"><div class="sdot {dc}">{i+1}</div><div class="slbl {dc}">{lbl}</div></div>'
        if i < 2:
            html += f'<div class="sline {"done" if i < idx else ""}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_avatar_grid():
    """Clickable avatar links using query params — 100% reliable Streamlit navigation."""
    html = '<div class="ops-grid">'
    for op in OPERADORES:
        html += f"""
        <a class="op-wrap" href="?op={op}" target="_self">
          <div class="avatar">{op[0].upper()}</div>
          <div class="op-name">{op}</div>
        </a>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: HOME
# ─────────────────────────────────────
def tela_home():
    render_logo()
    st.markdown('<div class="section-label">Selecione o Operador</div>', unsafe_allow_html=True)

    if st.session_state.pedido_prox:
        st.info(f"📦 Pedido **{st.session_state.pedido_prox}** aguardando: **{ETAPAS_LBL[st.session_state.etapa_prox]}**")

    render_avatar_grid()

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([2, 1, 2])
    with col_c:
        st.markdown('<div class="btn-outline btn-sm">', unsafe_allow_html=True)
        if st.button("⚙ Admin", use_container_width=True):
            st.session_state.tela = "admin_login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: PRODUÇÃO
# ─────────────────────────────────────
def tela_producao():
    render_logo()
    render_stepper(st.session_state.etapa_idx)

    op        = st.session_state.operador
    etapa_idx = st.session_state.etapa_idx
    etapa_lbl = ETAPAS_LBL[etapa_idx]

    st.markdown(f'<div class="badge-op">● {op}</div>', unsafe_allow_html=True)

    # ── Input de pedido ──
    if not st.session_state.rodando and st.session_state.acum == 0 and not st.session_state.modal:

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #C8566A 0%, #9E3F52 100%);
            border-radius: 18px;
            padding: 20px 28px;
            margin-bottom: 24px;
            box-shadow: 0 8px 0 rgba(100,20,35,0.30), 0 14px 32px rgba(200,86,106,0.30);
        ">
            <div style="font-size:10px;font-weight:800;letter-spacing:2.5px;color:rgba(255,255,255,0.65);text-transform:uppercase;margin-bottom:5px;">Etapa Atual</div>
            <div style="font-size:24px;font-weight:900;color:#fff;letter-spacing:0.2px;">{etapa_lbl}</div>
        </div>
        """, unsafe_allow_html=True)

        # Label grande
        st.markdown("""
        <div style="font-size:14px;font-weight:800;letter-spacing:1.5px;color:#5C5450;
                    text-transform:uppercase;margin-bottom:8px;">
            Número do Pedido
        </div>
        """, unsafe_allow_html=True)

        _, col_inp, _ = st.columns([0.3, 5, 0.3])
        with col_inp:
            st.markdown("""
            <style>
            div[data-testid="stTextInput"] label { display:none !important; }
            div[data-testid="stTextInput"] input {
                text-align: center !important;
                font-size: 18px !important;
                font-weight: 800 !important;
                letter-spacing: 2px !important;
                color: #1A1714 !important;
                height: 50px !important;
                border: 2px solid #E0DBD4 !important;
                border-radius: 12px !important;
                background: #fff !important;
                box-shadow: 0 3px 10px rgba(0,0,0,0.05) !important;
                padding: 0 16px !important;
            }
            div[data-testid="stTextInput"] input:focus {
                border-color: #C8566A !important;
                box-shadow: 0 0 0 4px rgba(200,86,106,0.12), 0 3px 10px rgba(0,0,0,0.05) !important;
            }
            div[data-testid="stTextInput"] input::placeholder {
                color: #CCC6BF !important; font-weight:600 !important; font-size:15px !important; letter-spacing:1px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            pedido_inp = st.text_input("_", value=st.session_state.pedido or "", placeholder="Ex: #00123")

        if st.session_state.erro_pedido:
            st.markdown('<div style="text-align:center;color:#C8566A;font-size:13px;font-weight:800;margin-top:6px;">⚠ Digite o número do pedido.</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        _, c1, gap, c2, _ = st.columns([0.3, 3.5, 0.4, 1.5, 0.3])
        with c1:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("▶  INICIAR CRONÔMETRO", use_container_width=True):
                if not pedido_inp.strip():
                    st.session_state.erro_pedido = True; st.rerun()
                st.session_state.erro_pedido = False
                st.session_state.pedido  = pedido_inp.strip()
                st.session_state.rodando = True
                st.session_state.inicio  = time.time()
                st.session_state.acum    = 0
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("← Voltar", use_container_width=True):
                st.session_state.tela = "home"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Timer rodando ──
    elif st.session_state.rodando:
        elapsed = get_elapsed()
        h, rem = divmod(elapsed, 3600); m, s = divmod(rem, 60)
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #C8566A 0%, #9E3F52 100%);
            border-radius: 20px;
            padding: 28px 24px 24px;
            text-align: center;
            box-shadow: 0 8px 0 rgba(100,20,35,0.30), 0 16px 36px rgba(200,86,106,0.32);
            margin-bottom: 20px;
        ">
            <div style="font-size:10px;font-weight:800;letter-spacing:3px;color:rgba(255,255,255,0.60);text-transform:uppercase;margin-bottom:4px;">Pedido</div>
            <div style="font-family:'DM Mono',monospace;font-size:26px;font-weight:500;color:#fff;margin-bottom:16px;letter-spacing:1px;">{st.session_state.pedido}</div>
            <div style="font-family:'DM Mono',monospace;font-size:68px;font-weight:500;color:#fff;letter-spacing:-3px;line-height:1;">{h:02d}:{m:02d}:{s:02d}</div>
            <div style="font-size:11px;font-weight:800;color:rgba(255,255,255,0.55);margin-top:14px;letter-spacing:2px;text-transform:uppercase;">Etapa: {etapa_lbl}</div>
        </div>
        """, unsafe_allow_html=True)
        _, col_fin, _ = st.columns([0.5, 5, 0.5])
        with col_fin:
            st.markdown('<div class="btn-finalizar">', unsafe_allow_html=True)
            if st.button("■  FINALIZAR ETAPA", use_container_width=True):
                tempo = get_elapsed()
                st.session_state.acum = tempo; st.session_state.rodando = False; st.session_state.inicio = None
                salvar(st.session_state.pedido, op, ETAPAS[etapa_idx], etapa_idx, tempo)
                st.session_state.modal = "proxima" if etapa_idx < 2 else "concluido"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        time.sleep(1); st.rerun()

    # ── Modal: próxima etapa? ──
    elif st.session_state.modal == "proxima":
        next_lbl = ETAPAS_LBL[etapa_idx + 1]
        st.markdown(f"""<div class="vi-card" style="text-align:center;">
          <div style="font-size:38px;margin-bottom:10px;">✅</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;">Etapa Concluída!</div>
          <div style="font-size:14px;color:#8C8480;line-height:1.6;">
            <strong>{etapa_lbl}</strong> finalizada em <strong>{fmt(st.session_state.acum)}</strong>.<br>
            Deseja ir para <strong>{next_lbl}</strong>?
          </div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button(f"Sim → {next_lbl}", use_container_width=True):
                st.session_state.modal = "quem"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("Encerrar pedido", use_container_width=True):
                st.session_state.modal = None; st.session_state.pedido = None
                st.session_state.etapa_idx = 0; st.session_state.acum = 0
                st.session_state.tela = "home"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Modal: quem faz? ──
    elif st.session_state.modal == "quem":
        next_lbl = ETAPAS_LBL[etapa_idx + 1]
        st.markdown(f"""<div class="vi-card" style="text-align:center;">
          <div style="font-size:38px;margin-bottom:10px;">👤</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;">Quem faz a próxima etapa?</div>
          <div style="font-size:14px;color:#8C8480;">{etapa_lbl} → <strong>{next_lbl}</strong></div>
        </div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Eu mesmo", use_container_width=True):
                st.session_state.etapa_idx += 1; st.session_state.acum = 0
                st.session_state.modal = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("Outro operador", use_container_width=True):
                st.session_state.pedido_prox = st.session_state.pedido
                st.session_state.etapa_prox  = etapa_idx + 1
                st.session_state.pedido = None; st.session_state.etapa_idx = 0
                st.session_state.acum = 0; st.session_state.modal = None
                st.session_state.tela = "home"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Modal: concluído ──
    elif st.session_state.modal == "concluido":
        st.markdown(f"""<div class="vi-card" style="text-align:center;">
          <div style="font-size:42px;margin-bottom:10px;">🎉</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;">Pedido Concluído!</div>
          <div style="font-size:14px;color:#8C8480;line-height:1.6;">
            Pedido <strong>{st.session_state.pedido}</strong> finalizado!<br>
            Embalagem: <strong>{fmt(st.session_state.acum)}</strong>
          </div></div>""", unsafe_allow_html=True)
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Voltar ao início", use_container_width=True):
            st.session_state.modal = None; st.session_state.pedido = None
            st.session_state.etapa_idx = 0; st.session_state.acum = 0
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: ADMIN LOGIN
# ─────────────────────────────────────
def tela_admin_login():
    render_logo()
    st.markdown('<div class="section-label">Área Administrativa</div>', unsafe_allow_html=True)
    st.markdown('<div class="vi-card">', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;font-size:32px;margin-bottom:8px;">🔐</div>', unsafe_allow_html=True)
    senha = st.text_input("SENHA", type="password", placeholder="Digite a senha")
    if st.session_state.erro_senha:
        st.markdown('<span style="color:#C8566A;font-size:12px;">⚠ Senha incorreta.</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True):
            st.session_state.erro_senha = False; st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Entrar", use_container_width=True):
            if senha == ADMIN_SENHA:
                st.session_state.erro_senha = False; st.session_state.tela = "admin"; st.rerun()
            else:
                st.session_state.erro_senha = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: ADMIN PANEL
# ─────────────────────────────────────
def tela_admin():
    render_logo()
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="section-label" style="text-align:left;margin-bottom:2px;">Painel Administrativo</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:20px;font-weight:700;margin-bottom:1rem;">Visão Geral</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-outline btn-sm">', unsafe_allow_html=True)
        if st.button("← Voltar"):
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    regs = buscar()
    ped_comp  = list({r[1] for r in regs if r[4] == 2})
    ops_ativ  = list({r[2] for r in regs})
    avg       = media([r[5] for r in regs]) // 60 if regs else 0

    for col, num, lbl in zip(st.columns(3),
        [len(ped_comp), len(ops_ativ), f"{avg}m"],
        ["Pedidos Concluídos","Operadores Ativos","Tempo Médio"]):
        with col:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{num}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:13px;font-weight:700;margin-bottom:8px;">Desempenho por Operador</div>', unsafe_allow_html=True)

    op_map = {}
    for r in regs:
        op = r[2]
        if op not in op_map: op_map[op] = {"p":set(),"sep":[],"conf":[],"emb":[]}
        op_map[op]["p"].add(r[1])
        if r[4]==0: op_map[op]["sep"].append(r[5])
        if r[4]==1: op_map[op]["conf"].append(r[5])
        if r[4]==2: op_map[op]["emb"].append(r[5])

    rows = "".join(f"<tr><td><b>{op}</b></td><td>{len(d['p'])}</td><td>{fmt(media(d['sep'])) if d['sep'] else '—'}</td><td>{fmt(media(d['conf'])) if d['conf'] else '—'}</td><td>{fmt(media(d['emb'])) if d['emb'] else '—'}</td></tr>"
        for op, d in op_map.items()) or '<tr><td colspan="5" style="text-align:center;color:#ccc;padding:20px">Sem dados</td></tr>'

    st.markdown(f'<div class="vi-card"><table><thead><tr><th>Operador</th><th>Pedidos</th><th>Separação</th><th>Conferência</th><th>Embalagem</th></tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    h1, h2 = st.columns([3, 1])
    with h1: st.markdown('<div style="font-size:13px;font-weight:700;margin-bottom:8px;">Histórico de Pedidos</div>', unsafe_allow_html=True)
    with h2:
        if st.button("🗑 Limpar"): limpar(); st.rerun()

    tag_cls = ["tag-sep","tag-conf","tag-emb"]
    hist = "".join(f"<tr><td style=\"font-family:'DM Mono',monospace;font-size:12px\">{r[1]}</td><td>{r[2]}</td><td><span class=\"tag {tag_cls[r[4]]}\">{r[3]}</span></td><td style=\"font-family:'DM Mono',monospace;font-size:12px\">{fmt(r[5])}</td><td style=\"color:#8C8480;font-size:12px\">{r[6]}</td></tr>"
        for r in regs[:60]) or '<tr><td colspan="5" style="text-align:center;color:#ccc;padding:20px">Sem dados</td></tr>'

    st.markdown(f'<div class="vi-card"><table><thead><tr><th>Pedido</th><th>Operador</th><th>Etapa</th><th>Tempo</th><th>Data</th></tr></thead><tbody>{hist}</tbody></table></div>', unsafe_allow_html=True)

    if regs:
        st.markdown("<br>", unsafe_allow_html=True)
        buf = io.StringIO()
        csv.writer(buf).writerows([["ID","Pedido","Operador","Etapa","EtapaIdx","Tempo(s)","Data"]] + list(regs))
        st.download_button("⬇  Exportar CSV", buf.getvalue().encode(),
            f"vi_producao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv", use_container_width=True)

# ─────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────
{
    "home":        tela_home,
    "producao":    tela_producao,
    "admin_login": tela_admin_login,
    "admin":       tela_admin,
}.get(st.session_state.tela, tela_home)()
