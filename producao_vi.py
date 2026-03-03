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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: #F7F5F2 !important;
    font-family: 'DM Sans', sans-serif !important;
}}
[data-testid="stHeader"], [data-testid="stSidebar"], footer, #MainMenu {{ display:none !important; }}
.block-container {{ padding-top:1.8rem !important; padding-bottom:2rem !important; max-width:640px !important; }}

.logo-box {{ text-align:center; margin-bottom:1.6rem; }}
.logo-box img {{ height:54px; object-fit:contain; }}

.section-label {{
    font-size:11px; font-weight:600; letter-spacing:2px; text-transform:uppercase;
    color:#8C8480; margin-bottom:1.2rem; text-align:center;
}}

/* ── AVATAR GRID ── */
.ops-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px 18px;
    margin-bottom: 1.5rem;
}}
.op-wrap {{
    display: flex; flex-direction: column;
    align-items: center; gap: 9px;
    text-decoration: none;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
}}
.avatar {{
    width: 72px; height: 72px; border-radius: 50%;
    background: linear-gradient(145deg, #D9617A 0%, #A84055 55%, #7A2D3E 100%);
    box-shadow:
        0 6px 0 rgba(80,10,25,0.50),
        0 10px 24px rgba(158,63,82,0.38),
        inset 0 2px 5px rgba(255,255,255,0.20);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 700; color: #fff;
    text-shadow: 0 1px 4px rgba(0,0,0,0.28);
    transition: transform 0.20s ease, box-shadow 0.20s ease;
    position: relative; overflow: hidden;
    user-select: none;
}}
/* gloss */
.avatar::after {{
    content:''; position:absolute;
    top:8px; left:14px; width:36px; height:19px;
    background: radial-gradient(ellipse, rgba(255,255,255,0.24) 0%, transparent 75%);
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
    font-size: 12px; font-weight: 600; color: #1A1714;
    text-align: center; line-height: 1.3;
    text-decoration: none;
}}

/* ── STEPPER ── */
.stepper {{ display:flex; align-items:flex-start; margin-bottom:1.4rem; }}
.step {{ flex:1; display:flex; flex-direction:column; align-items:center; gap:5px; }}
.sdot {{
    width:28px; height:28px; border-radius:50%;
    border:2px solid #E8E3DC; background:#F0EDE8;
    display:flex; align-items:center; justify-content:center;
    font-size:11px; font-weight:700; color:#8C8480;
}}
.sdot.active {{ background:#C8566A; border-color:#C8566A; color:#fff; box-shadow:0 0 0 4px rgba(200,86,106,0.15); }}
.sdot.done   {{ background:#4A7C59; border-color:#4A7C59; color:#fff; }}
.slbl {{ font-size:10px; font-weight:600; letter-spacing:.8px; text-transform:uppercase; color:#8C8480; text-align:center; }}
.slbl.active {{ color:#C8566A; }} .slbl.done {{ color:#4A7C59; }}
.sline {{ flex:1; height:2px; background:#E8E3DC; margin-top:13px; }}
.sline.done {{ background:#4A7C59; }}

/* ── CARD ── */
.vi-card {{
    background:#fff; border:1.5px solid #E8E3DC; border-radius:14px;
    padding:24px; box-shadow:0 2px 14px rgba(0,0,0,0.05); margin-bottom:1rem;
}}

/* ── BADGE ── */
.badge-op {{
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 14px; border-radius:100px;
    background:#F5E8EB; color:#C8566A; font-size:12px; font-weight:600;
    margin-bottom:1rem;
}}

/* ── TIMER ── */
.timer-num {{
    font-family:'DM Mono',monospace; font-size:58px; font-weight:500;
    color:#C8566A; letter-spacing:-2px; line-height:1; text-align:center; padding:12px 0;
}}
.pedido-lbl {{ font-size:11px; font-weight:600; color:#8C8480; text-align:center; letter-spacing:1px; text-transform:uppercase; }}
.pedido-num {{ font-family:'DM Mono',monospace; font-size:22px; font-weight:500; color:#1A1714; text-align:center; margin-bottom:14px; }}
.etapa-lbl  {{ font-size:13px; color:#8C8480; text-align:center; margin-bottom:18px; }}

/* ── BUTTONS ── */
.stButton > button {{
    font-family:'DM Sans',sans-serif !important; font-weight:700 !important;
    border-radius:10px !important; transition:all .18s !important;
    height:50px !important; font-size:15px !important; letter-spacing:.4px !important;
}}
.btn-primary > button  {{ background:#C8566A !important; color:#fff !important; border:none !important; box-shadow:0 4px 14px rgba(200,86,106,.25) !important; }}
.btn-primary > button:hover {{ background:#b04560 !important; transform:translateY(-1px) !important; }}
.btn-dark > button    {{ background:#1A1714 !important; color:#fff !important; border:none !important; }}
.btn-dark > button:hover {{ background:#333 !important; }}
.btn-outline > button {{ background:transparent !important; color:#1A1714 !important; border:1.5px solid #E8E3DC !important; }}
.btn-outline > button:hover {{ border-color:#C8566A !important; color:#C8566A !important; }}
.btn-sm > button {{ height:38px !important; font-size:12px !important; }}

/* ── ADMIN ── */
.stat-box {{ background:#fff; border:1.5px solid #E8E3DC; border-radius:12px; padding:16px; text-align:center; }}
.stat-num {{ font-family:'DM Mono',monospace; font-size:30px; font-weight:500; color:#C8566A; }}
.stat-lbl {{ font-size:11px; font-weight:600; color:#8C8480; letter-spacing:.5px; margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
th {{ text-align:left; padding:9px 10px; font-size:10px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:#8C8480; border-bottom:1.5px solid #E8E3DC; }}
td {{ padding:10px 10px; border-bottom:1px solid #F0EDE8; color:#1A1714; }}
.tag {{ display:inline-block; padding:2px 8px; border-radius:100px; font-size:10px; font-weight:700; }}
.tag-sep {{ background:#EBF0FB; color:#3B5EC6; }}
.tag-conf {{ background:#FBF2E6; color:#C47B2A; }}
.tag-emb  {{ background:#E8F2EC; color:#4A7C59; }}

/* ── INPUT ── */
.stTextInput > div > div > input {{
    border:1.5px solid #E8E3DC !important; border-radius:10px !important;
    background:#F7F5F2 !important; font-family:'DM Sans',sans-serif !important;
    font-size:15px !important; padding:14px 16px !important; color:#1A1714 !important;
}}
.stTextInput > div > div > input:focus {{ border-color:#C8566A !important; box-shadow:none !important; }}
label {{ font-size:12px !important; font-weight:600 !important; color:#8C8480 !important; letter-spacing:.5px !important; }}
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
        st.markdown(f'<div style="font-size:13px;color:#8C8480;margin-bottom:8px;">Etapa atual: <strong>{etapa_lbl}</strong></div>', unsafe_allow_html=True)
        pedido_inp = st.text_input("NÚMERO DO PEDIDO", value=st.session_state.pedido or "", placeholder="Ex: #00123")
        if st.session_state.erro_pedido:
            st.markdown('<span style="color:#C8566A;font-size:12px;">⚠ Digite o número do pedido.</span>', unsafe_allow_html=True)

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("▶  INICIAR", use_container_width=True):
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
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("← Voltar", use_container_width=True):
                st.session_state.tela = "home"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Timer rodando ──
    elif st.session_state.rodando:
        elapsed = get_elapsed()
        h, rem = divmod(elapsed, 3600); m, s = divmod(rem, 60)
        st.markdown(f'<div class="pedido-lbl">PEDIDO</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pedido-num">{st.session_state.pedido}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="timer-num">{h:02d}:{m:02d}:{s:02d}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="etapa-lbl">Etapa: <strong>{etapa_lbl}</strong></div>', unsafe_allow_html=True)
        st.markdown('<div class="btn-dark">', unsafe_allow_html=True)
        if st.button("■  FINALIZAR", use_container_width=True):
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
