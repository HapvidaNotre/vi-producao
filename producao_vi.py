import streamlit as st
import sqlite3
import time
import base64
from datetime import datetime
from pathlib import Path
import csv, io
import streamlit.components.v1 as components
import pandas as pd
import re

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
ETAPAS      = ["Separacao","Mesa_Embalagem","Conferencia"]
ETAPAS_LBL  = ["Separação de Pedidos","Mesa de Embalagem","Conferência de Pedidos"]
ADMIN_SENHA = "vi2026"
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
    con.execute("""CREATE TABLE IF NOT EXISTS pedidos_base (
        numero TEXT PRIMARY KEY,
        cliente TEXT DEFAULT '',
        produto TEXT DEFAULT '',
        status TEXT DEFAULT 'aberto',
        importado_em TEXT DEFAULT '')""")
    con.commit(); con.close()

# ─── Pedidos base helpers ───
def importar_planilha(file_bytes, filename):
    """
    Parse the Vi Lingerie production spreadsheet.
    Col 'Pedido'  = order number (col A)
    Col '%.1'     = completion % — value 100 means done, anything else = open
    Col 'Cliente' = client name (optional display)
    Also supports generic xlsx/csv with auto-detection as fallback.
    """
    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
    except Exception as e:
        return False, f"Erro ao ler arquivo: {e}"

    cols_orig = list(df.columns)
    df.columns = [str(c).strip() for c in df.columns]

    # ── Detect numero column ──
    # Priority: exact 'Pedido', then fallback heuristic
    num_col = None
    for c in df.columns:
        if c.strip().lower() == "pedido":
            num_col = c; break
    if num_col is None:
        for c in df.columns:
            cl = c.lower()
            if any(k in cl for k in ["pedido","número","numero","order","cod"]):
                num_col = c; break
    if num_col is None:
        num_col = df.columns[0]  # last resort: first column

    # ── Detect percent/status column ──
    # Priority: exact '%.1' (Vi Lingerie format), then fallback
    pct_col = None
    for c in df.columns:
        if c.strip() == "%.1":
            pct_col = c; break
    if pct_col is None:
        for c in df.columns:
            cl = c.lower()
            if any(k in cl for k in ["% total","% pronto","progresso","status","situação","%"]):
                pct_col = c; break

    # ── Detect client column ──
    cli_col = next((c for c in df.columns if c.lower() in ("cliente","client","nome","comprador")), None)

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    con = sqlite3.connect(DB_PATH)
    count = 0
    skipped = 0
    for _, row in df.iterrows():
        num = str(row[num_col]).strip()
        if not num or num.lower() in ("nan","none","","pedido"):
            skipped += 1; continue

        # Determine status from % column
        if pct_col:
            try:
                pct_val = float(str(row[pct_col]).strip().replace(",","."))
                sta = "concluido" if pct_val >= 100.0 else "aberto"
            except:
                sta = "aberto"
        else:
            sta = "aberto"

        cli = ""
        if cli_col:
            raw = str(row[cli_col]).strip()
            cli = "" if raw.lower() in ("nan","none","") else raw

        con.execute("""INSERT INTO pedidos_base (numero,cliente,produto,status,importado_em)
            VALUES (?,?,?,?,?) ON CONFLICT(numero) DO UPDATE SET
            cliente=excluded.cliente,
            status=excluded.status,
            importado_em=excluded.importado_em""",
            (num, cli, "", sta, now_str))
        count += 1
    con.commit(); con.close()
    return True, count

def buscar_pedidos_base():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT numero,cliente,produto,status FROM pedidos_base ORDER BY numero").fetchall()
    con.close(); return rows

def status_pedido(numero):
    """Returns 'aberto','concluido','nao_encontrado'"""
    con = sqlite3.connect(DB_PATH)
    row = con.execute("SELECT status FROM pedidos_base WHERE numero=?", (numero,)).fetchone()
    con.close()
    if row is None: return "nao_encontrado"
    return row[0]

def cadastrar_pedido_avulso(numero):
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    con = sqlite3.connect(DB_PATH)
    con.execute("""INSERT OR IGNORE INTO pedidos_base (numero,cliente,produto,status,importado_em)
        VALUES (?,\'\',\'\','aberto',?)""", (numero, now_str))
    con.commit(); con.close()

def marcar_concluido(numero):
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE pedidos_base SET status=\'concluido\' WHERE numero=?", (numero,))
    con.commit(); con.close()

def verificar_etapa_registro(pedido, etapa_idx):
    """Verifica se esse pedido/etapa já tem registro. Retorna (existe, operador_anterior)."""
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT operador FROM registros WHERE pedido=? AND etapa_idx=? ORDER BY id DESC LIMIT 1",
        (pedido, etapa_idx)
    ).fetchone()
    con.close()
    if row: return True, row[0]
    return False, None

def pedido_em_andamento(pedido, etapa_idx):
    """Verifica se pedido está com timer ativo em outra sessão (via active_sessions table)."""
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS sessoes_ativas (
        pedido TEXT, etapa_idx INTEGER, operador TEXT, iniciado_em INTEGER,
        PRIMARY KEY (pedido, etapa_idx))""")
    row = con.execute(
        "SELECT operador, iniciado_em FROM sessoes_ativas WHERE pedido=? AND etapa_idx=?",
        (pedido, etapa_idx)
    ).fetchone()
    con.close()
    if row:
        # Considera ativa se foi iniciada há menos de 4 horas
        if int(time.time()) - row[1] < 14400:
            return True, row[0]
    return False, None

def registrar_sessao_ativa(pedido, etapa_idx, operador):
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS sessoes_ativas (
        pedido TEXT, etapa_idx INTEGER, operador TEXT, iniciado_em INTEGER,
        PRIMARY KEY (pedido, etapa_idx))""")
    con.execute("""INSERT OR REPLACE INTO sessoes_ativas VALUES (?,?,?,?)""",
        (pedido, etapa_idx, operador, int(time.time())))
    con.commit(); con.close()

def remover_sessao_ativa(pedido, etapa_idx):
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM sessoes_ativas WHERE pedido=? AND etapa_idx=?", (pedido, etapa_idx))
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
    "pedido_status":None, "pedido_confirm":False,
    # novo fluxo: etapa_escolhida → pedido → operador
    "etapa_escolhida":None, "duplicata_info":None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# (query param router removed — avatars now use native st.button)

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
.block-container {{ padding-top:1.8rem !important; padding-bottom:2rem !important; max-width:600px !important; margin: 0 auto !important; }}

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

def render_avatar_grid(on_click_key="home"):
    """Avatar grid — large photo-style cards, premium operador selection."""

    COLORS = [
        ("#C8566A","#FFF0F2","#7A2D3E"),
        ("#3B7DD8","#EEF4FF","#1a4fa0"),
        ("#4A7C59","#F0F7F3","#2a5038"),
        ("#E07B3A","#FFF4EE","#9a4a15"),
        ("#7C5CBF","#F4F0FF","#4a2e8a"),
        ("#C8566A","#FFF0F2","#7A2D3E"),
        ("#3B7DD8","#EEF4FF","#1a4fa0"),
        ("#4A7C59","#F0F7F3","#2a5038"),
        ("#E07B3A","#FFF4EE","#9a4a15"),
    ]

    # Global CSS for all cards
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap');
    .op-grid-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 4px; }

    div.op-btn-wrap > div[data-testid="stButton"] > button {
        font-family: 'Nunito', sans-serif !important;
        background: #FFFFFF !important;
        border: 2px solid #F0EBE5 !important;
        border-radius: 16px !important;
        height: 72px !important;
        width: 100% !important;
        padding: 0 16px 0 12px !important;
        text-align: left !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #1A1714 !important;
        letter-spacing: 0.2px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.055) !important;
        transition: all 0.15s ease !important;
        display: flex !important;
        align-items: center !important;
    }
    div.op-btn-wrap > div[data-testid="stButton"] > button:hover {
        transform: translateY(-3px) scale(1.01) !important;
    }
    div.op-btn-wrap > div[data-testid="stButton"] > button:active {
        transform: translateY(1px) scale(0.99) !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    cols_per_row = 2
    rows_ops = [OPERADORES[i:i+cols_per_row] for i in range(0, len(OPERADORES), cols_per_row)]

    for r_idx, row in enumerate(rows_ops):
        cols = st.columns(cols_per_row)
        for c_idx, (col, op) in enumerate(zip(cols, row)):
            op_idx = r_idx * cols_per_row + c_idx
            color, bg, dark = COLORS[op_idx % len(COLORS)]
            initials = (op[0] + op[1]).upper() if len(op) >= 2 else op[0].upper()

            with col:
                # Per-operator hover color
                st.markdown(f"""
                <style>
                div.op-btn-wrap-{op_idx} > div[data-testid="stButton"] > button {{
                    border-color: #F0EBE5 !important;
                }}
                div.op-btn-wrap-{op_idx} > div[data-testid="stButton"] > button:hover {{
                    background: {bg} !important;
                    border-color: {color} !important;
                    box-shadow: 0 8px 22px {color}33, 0 2px 6px rgba(0,0,0,0.06) !important;
                }}
                </style>""", unsafe_allow_html=True)

                # Circle initial badge above button
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:0;">'
                    f'<div style="width:42px;height:42px;border-radius:50%;flex-shrink:0;'
                    f'background:linear-gradient(135deg,{color},{dark});'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-family:Nunito,sans-serif;font-size:14px;font-weight:900;color:#fff;'
                    f'box-shadow:0 3px 10px {color}55;'
                    f'margin-right:-6px;position:relative;z-index:2;border:2px solid #fff;">'
                    f'{initials}</div></div>',
                    unsafe_allow_html=True
                )
                st.markdown(f'<div class="op-btn-wrap op-btn-wrap-{op_idx}">', unsafe_allow_html=True)
                if st.button(f"  {op}", key=f"av_{on_click_key}_{op}", use_container_width=True):
                    st.session_state.operador = op
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)


def _go_producao(etapa_idx):
    """Helper: transition to production screen."""
    registrar_sessao_ativa(st.session_state.pedido, etapa_idx, st.session_state.operador)
    st.session_state.etapa_idx = etapa_idx
    st.session_state.rodando   = False
    st.session_state.inicio    = None
    st.session_state.acum      = 0
    st.session_state.modal     = None
    st.session_state.tela      = "producao"
    st.rerun()

# ─────────────────────────────────────
#  TELA: HOME  (fluxo: etapa → operador → pedido → INICIAR → volta home)
# ─────────────────────────────────────
def tela_home():
    render_logo()

    # ══════════════════════════════════
    #  PASSO 1 — Escolher a etapa
    # ══════════════════════════════════
    if st.session_state.etapa_escolhida is None:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:0 0 20px;">
            <div style="flex:1;height:1px;background:#EDE9E4;"></div>
            <div style="font-size:11px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;
                color:#9C9490;white-space:nowrap;">Em qual etapa vai trabalhar?</div>
            <div style="flex:1;height:1px;background:#EDE9E4;"></div>
        </div>
        """, unsafe_allow_html=True)

        ETAPA_CFG = [
            {"icon":"📦","color":"#C8566A","bg":"#FFF0F2","shadow":"rgba(200,86,106,0.22)",
             "desc":"Separar peças conforme localização no pedido","step":"01"},
            {"icon":"🗃️","color":"#3B7DD8","bg":"#F0F5FF","shadow":"rgba(59,125,216,0.22)",
             "desc":"Embalar conforme observação do pedido","step":"02"},
            {"icon":"✅","color":"#4A7C59","bg":"#F0F7F3","shadow":"rgba(74,124,89,0.22)",
             "desc":"Conferência via código de barras","step":"03"},
        ]
        st.markdown("""
        <style>
        .etapa-card > div[data-testid="stButton"] > button {
            background: #FFFFFF !important;
            border: 1.5px solid #EDE9E4 !important;
            border-radius: 18px !important;
            height: 86px !important;
            width: 100% !important;
            text-align: left !important;
            padding: 0 20px !important;
            font-family: 'Nunito', sans-serif !important;
            font-size: 16px !important;
            font-weight: 800 !important;
            color: #1A1714 !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05) !important;
            transition: all 0.18s ease !important;
        }
        .etapa-card > div[data-testid="stButton"] > button:active {
            transform: translateY(1px) !important;
        }
        </style>""", unsafe_allow_html=True)

        for i, lbl in enumerate(ETAPAS_LBL):
            cfg = ETAPA_CFG[i]
            st.markdown(f"""
            <style>
            .etapa-card-{i} > div[data-testid="stButton"] > button {{
                border-left: 5px solid {cfg["color"]} !important;
            }}
            .etapa-card-{i} > div[data-testid="stButton"] > button:hover {{
                background: {cfg["bg"]} !important;
                border-color: {cfg["color"]} !important;
                box-shadow: 0 8px 24px {cfg["shadow"]}, 0 2px 6px rgba(0,0,0,0.05) !important;
                transform: translateY(-3px) !important;
            }}
            </style>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;padding-left:4px;">
                <span style="background:{cfg["color"]};color:#fff;font-size:9px;font-weight:900;
                    letter-spacing:1.5px;padding:2px 8px;border-radius:20px;text-transform:uppercase;">
                    Etapa {cfg["step"]}
                </span>
                <span style="font-size:11px;color:#9C9490;font-weight:600;">{cfg["desc"]}</span>
            </div>""", unsafe_allow_html=True)
            st.markdown(f'<div class="etapa-card etapa-card-{i}">', unsafe_allow_html=True)
            if st.button(f'{cfg["icon"]}  {lbl}', use_container_width=True, key=f"etapa_btn_{i}"):
                st.session_state.etapa_escolhida = i
                st.session_state.operador = None
                st.session_state.pedido   = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            if i < 2: st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_c, _ = st.columns([2, 1, 2])
        with col_c:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("⚙ Admin", use_container_width=True):
                st.session_state.tela = "admin_login"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    etapa_idx = st.session_state.etapa_escolhida
    etapa_lbl = ETAPAS_LBL[etapa_idx]

    # ══════════════════════════════════
    #  PASSO 2 — Operador se identifica
    # ══════════════════════════════════
    if st.session_state.operador is None:
        render_stepper(etapa_idx)
        st.markdown(
            f'<div style="background:#F5E8EB;border-left:4px solid #C8566A;border-radius:0 10px 10px 0;'
            f'padding:10px 16px;margin-bottom:20px;font-size:14px;font-weight:700;color:#1A1714;">'
            f'Etapa: {etapa_lbl}</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
            <div style="flex:1;height:1px;background:#EDE9E4;"></div>
            <div style="font-size:11px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;
                color:#9C9490;white-space:nowrap;">Selecione o Operador</div>
            <div style="flex:1;height:1px;background:#EDE9E4;"></div>
        </div>
        """, unsafe_allow_html=True)

        render_avatar_grid(on_click_key="op")

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_v, _ = st.columns([2, 2, 2])
        with col_v:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("← Voltar", use_container_width=True, key="home_op_voltar"):
                st.session_state.etapa_escolhida = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ══════════════════════════════════
    #  PASSO 3 — Selecionar o pedido
    # ══════════════════════════════════
    render_stepper(etapa_idx)
    op = st.session_state.operador
    st.markdown(
        f'<div style="background:#F5E8EB;border-left:4px solid #C8566A;border-radius:0 10px 10px 0;'
        f'padding:10px 16px;margin-bottom:16px;font-size:14px;font-weight:700;color:#1A1714;">'
        f'<span style="color:#9C9490;font-weight:600;font-size:12px;">Operador</span><br>{op} &nbsp;·&nbsp; {etapa_lbl}'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-label">Selecione o pedido</div>', unsafe_allow_html=True)

    pedidos_db      = buscar_pedidos_base()
    pedidos_abertos = [p[0] for p in pedidos_db if p[3] == "aberto"]
    pedidos_info    = {p[0]: p[1] for p in pedidos_db if p[3] == "aberto"}
    has_base        = len(pedidos_db) > 0

    st.markdown("""
    <style>
    div[data-testid="stTextInput"] label { display:none !important; }
    div[data-testid="stSelectbox"] label { display:none !important; }
    </style>""", unsafe_allow_html=True)

    pedido_inp = ""

    if has_base and pedidos_abertos:
        def fmt_op_ped(n):
            cli = pedidos_info.get(n, "")
            return f"{n}  —  {cli}" if cli else n
        opcoes_disp = ["— Selecione ou digite —"] + [fmt_op_ped(n) for n in sorted(pedidos_abertos)]
        opcoes_map  = {"— Selecione ou digite —": ""} | {fmt_op_ped(n): n for n in sorted(pedidos_abertos)}
        _, col_sel, _ = st.columns([0.3, 4, 0.3])
        with col_sel:
            sel = st.selectbox("_sel", opcoes_disp, key="home_pedido_sel")
        pedido_inp = opcoes_map.get(sel, "")
        if pedido_inp:
            cli_nome = pedidos_info.get(pedido_inp, "")
            if cli_nome:
                import streamlit.components.v1 as _cv1
                _cv1.html(
                    f'<div style="background:#F0F7F3;border:1.5px solid #4A7C59;border-radius:10px;'
                    f'padding:10px 16px;font-family:sans-serif;display:flex;align-items:center;gap:10px;margin:6px 0;">'
                    f'<div style="font-size:18px;">🛍</div>'
                    f'<div><div style="font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#4A7C59;margin-bottom:2px;">Cliente</div>'
                    f'<div style="font-size:13px;font-weight:800;color:#1A1714;">{cli_nome}</div></div></div>',
                    height=58, scrolling=False
                )
        with st.expander("✏ Digitar número manualmente"):
            manual = st.text_input("Número manual", placeholder="Ex: 49735", key="home_pedido_manual")
            if manual.strip(): pedido_inp = manual.strip()
    else:
        _, col_inp, _ = st.columns([0.3, 4, 0.3])
        with col_inp:
            pedido_inp = st.text_input("_ped", placeholder="Ex: 49735", key="home_pedido_txt")
        if has_base and not pedidos_abertos:
            import streamlit.components.v1 as _cv1
            _cv1.html(
                '<div style="background:#FEF3C7;border:1px solid #F59E0B;border-radius:10px;'
                'padding:10px 14px;font-family:sans-serif;font-size:12px;font-weight:700;color:#92400E;text-align:center;">'
                '⚠ Nenhum pedido em aberto na base.</div>',
                height=50, scrolling=False
            )

    # ── Bloqueio: pedido concluído ──
    if st.session_state.pedido_status == "concluido":
        import streamlit.components.v1 as _cv1
        _cv1.html(
            '<div style="background:#FEF2F2;border:2px solid #FCA5A5;border-radius:14px;'
            'padding:16px 20px;font-family:sans-serif;text-align:center;margin:8px 0;">'
            '<div style="font-size:22px;margin-bottom:6px;">🔒</div>'
            '<div style="font-size:14px;font-weight:800;color:#991B1B;margin-bottom:4px;">Pedido Já Concluído</div>'
            '<div style="font-size:12px;color:#B91C1C;font-weight:600;">Este pedido já foi encerrado no sistema.</div>'
            '</div>',
            height=110, scrolling=False
        )
        if st.button("← Escolher outro pedido"):
            st.session_state.pedido_status = None; st.rerun()
        return

    # ── Pedido não encontrado: cadastrar? ──
    if st.session_state.pedido_status == "nao_encontrado":
        num_pend = st.session_state.get("_pedido_validando", "")
        import streamlit.components.v1 as _cv1
        _cv1.html(
            f'<div style="background:#FFFBEB;border:2px solid #FCD34D;border-radius:14px;'
            f'padding:16px 20px;font-family:sans-serif;text-align:center;margin:8px 0;">'
            f'<div style="font-size:22px;margin-bottom:6px;">❓</div>'
            f'<div style="font-size:14px;font-weight:800;color:#92400E;margin-bottom:4px;">Pedido Não Encontrado</div>'
            f'<div style="font-size:12px;color:#B45309;font-weight:600;">'
            f'Pedido <b>{num_pend}</b> não está na base. Deseja cadastrá-lo?</div>'
            f'</div>',
            height=115, scrolling=False
        )
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("✓ Cadastrar", use_container_width=True):
                cadastrar_pedido_avulso(num_pend)
                st.session_state.pedido_status = None
                st.session_state.pedido = num_pend
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with cc2:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("✕ Cancelar", use_container_width=True):
                st.session_state.pedido_status = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Popup duplicata ──
    if st.session_state.duplicata_info:
        info    = st.session_state.duplicata_info
        op_ant  = info["operador_anterior"]
        etl     = ETAPAS_LBL[etapa_idx]
        num     = info["pedido"]
        msg_tp  = "está sendo processado agora" if info["em_andamento"] else "já passou pela fase de"
        import streamlit.components.v1 as _cv1
        _cv1.html(
            f'<div style="background:#FFF7ED;border:2px solid #F97316;border-radius:14px;'
            f'padding:18px 22px;font-family:sans-serif;margin:8px 0;">'
            f'<div style="font-size:22px;text-align:center;margin-bottom:8px;">⚠️</div>'
            f'<div style="font-size:14px;font-weight:800;color:#9A3412;text-align:center;margin-bottom:8px;">Atenção — Pedido em Conflito</div>'
            f'<div style="font-size:13px;color:#7C2D12;font-weight:600;text-align:center;line-height:1.6;">'
            f'<b>{op}</b>, este pedido {msg_tp} <b>{etl}</b>'
            f'{(" (por " + op_ant + ")") if op_ant else ""}.<br><br>'
            f'Deseja mesmo assim realizar uma alteração nesta etapa?</div>'
            f'</div>',
            height=175, scrolling=False
        )
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("✓ Sim, prosseguir", use_container_width=True):
                st.session_state.pedido = info["pedido"]
                st.session_state.duplicata_info = None
                _go_producao(etapa_idx)
            st.markdown('</div>', unsafe_allow_html=True)
        with cc2:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("✕ Não", use_container_width=True):
                st.session_state.duplicata_info = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── BOTÃO INICIAR ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, _, c2 = st.columns([3, 0.3, 1.5])
    with c1:
        st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
        if st.button("▶  INICIAR", use_container_width=True, key="home_iniciar"):
            num = pedido_inp.strip() if isinstance(pedido_inp, str) else ""
            if not num:
                st.session_state.erro_pedido = True; st.rerun()
            st.session_state.erro_pedido = False
            pst = status_pedido(num)
            if pst == "concluido":
                st.session_state.pedido_status = "concluido"
                st.session_state._pedido_validando = num; st.rerun()
            elif pst == "nao_encontrado" and has_base:
                st.session_state.pedido_status = "nao_encontrado"
                st.session_state._pedido_validando = num; st.rerun()
            else:
                # Check duplicata
                em_and, op_and = pedido_em_andamento(num, etapa_idx)
                ja_reg, op_reg = verificar_etapa_registro(num, etapa_idx)
                op_ant = op_and or op_reg
                if em_and or ja_reg:
                    st.session_state._pedido_validando = num
                    st.session_state.duplicata_info = {
                        "pedido": num,
                        "operador_anterior": op_ant,
                        "em_andamento": em_and,
                    }
                    st.rerun()
                else:
                    st.session_state.pedido = num
                    st.session_state.pedido_status = None
                    _go_producao(etapa_idx)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True, key="home_ped_voltar"):
            st.session_state.operador = None
            st.session_state.pedido_status = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.erro_pedido:
        st.markdown(
            '<div style="text-align:center;color:#C8566A;font-size:13px;font-weight:800;margin-top:6px;">'
            '⚠ Selecione ou digite o número do pedido.</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────
#  TELA: PRODUÇÃO
# ─────────────────────────────────────
def tela_producao():
    render_logo()
    render_stepper(st.session_state.etapa_idx)

    op        = st.session_state.operador
    etapa_idx = st.session_state.etapa_idx
    etapa_lbl = ETAPAS_LBL[etapa_idx]

    st.markdown("<br style='line-height:0.5'>", unsafe_allow_html=True)

    # ── Pedido já definido pelo home — mostrar card info + botão INICIAR ──
    if not st.session_state.rodando and st.session_state.acum == 0 and not st.session_state.modal:
        pedido_val = st.session_state.pedido or ""
        initial    = op[0].upper()

        # Info card: etapa + operador + pedido
        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800;900&display=swap" rel="stylesheet">
        <style>* {{margin:0;padding:0;box-sizing:border-box;}}</style>
        </head><body style="background:transparent;font-family:Nunito,sans-serif;">
        <div style="background:linear-gradient(135deg,#C8566A 0%,#9E3F52 100%);border-radius:20px;
            box-shadow:0 8px 0 rgba(100,20,35,0.28),0 16px 36px rgba(200,86,106,0.28);
            overflow:hidden;position:relative;">
            <div style="position:absolute;right:-30px;top:-30px;width:140px;height:140px;border-radius:50%;background:rgba(255,255,255,0.07);"></div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:22px 28px;position:relative;z-index:1;">
                <div>
                    <div style="font-size:9px;font-weight:800;letter-spacing:2.5px;color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:4px;">Etapa Atual</div>
                    <div style="font-size:22px;font-weight:900;color:#fff;letter-spacing:-0.3px;">{etapa_lbl}</div>
                </div>
                <div style="width:1.5px;height:48px;background:rgba(255,255,255,0.2);border-radius:2px;margin:0 16px;flex-shrink:0;"></div>
                <div style="text-align:right;">
                    <div style="font-size:9px;font-weight:800;letter-spacing:2.5px;color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:4px;">Operador</div>
                    <div style="display:flex;align-items:center;gap:8px;justify-content:flex-end;">
                        <div style="width:32px;height:32px;border-radius:50%;background:rgba(255,255,255,0.20);border:2px solid rgba(255,255,255,0.35);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;color:#fff;">{initial}</div>
                        <span style="font-size:17px;font-weight:800;color:#fff;">{op}</span>
                    </div>
                </div>
            </div>
            <div style="background:rgba(0,0,0,0.15);padding:12px 28px;display:flex;align-items:center;gap:10px;">
                <div style="font-size:9px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,0.5);text-transform:uppercase;">Pedido</div>
                <div style="font-family:monospace;font-size:18px;font-weight:800;color:#fff;letter-spacing:1px;">{pedido_val}</div>
            </div>
        </div>
        </body></html>
        """, height=130, scrolling=False)

        st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)

        _, c1, _ = st.columns([0.3, 4, 0.3])
        with c1:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("▶  INICIAR CRONÔMETRO", use_container_width=True):
                st.session_state.rodando = True
                st.session_state.inicio  = time.time()
                st.session_state.acum    = 0
                registrar_sessao_ativa(pedido_val, etapa_idx, op)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _, c2, _ = st.columns([0.3, 4, 0.3])
        with c2:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("← Voltar ao Menu", use_container_width=True):
                remover_sessao_ativa(pedido_val, etapa_idx)
                st.session_state.pedido = None
                st.session_state.pedido_status = None
                st.session_state.operador = None
                st.session_state.etapa_escolhida = None
                st.session_state.tela = "home"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    # ── Timer rodando ──
    elif st.session_state.rodando:
        elapsed = get_elapsed()
        h, rem = divmod(elapsed, 3600); m, s = divmod(rem, 60)
        pedido_val = st.session_state.pedido
        initial = op[0].upper()
        timer_str = f"{h:02d}:{m:02d}:{s:02d}"
        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800;900&family=DM+Mono:wght@500&display=swap" rel="stylesheet">
        <style>* {{margin:0;padding:0;box-sizing:border-box;}}</style>
        </head><body style="background:transparent;font-family:Nunito,sans-serif;">
        <div style="background:linear-gradient(135deg,#C8566A 0%,#9E3F52 100%);border-radius:20px;padding:0;box-shadow:0 8px 0 rgba(100,20,35,0.28),0 16px 36px rgba(200,86,106,0.28);overflow:hidden;position:relative;">
            <div style="position:absolute;right:-30px;top:-30px;width:140px;height:140px;border-radius:50%;background:rgba(255,255,255,0.06);"></div>
            <div style="position:absolute;left:-20px;bottom:-40px;width:110px;height:110px;border-radius:50%;background:rgba(255,255,255,0.04);"></div>
            <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 28px 0;position:relative;z-index:1;">
                <div>
                    <div style="font-size:9px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:2px;">Pedido</div>
                    <div style="font-family:'DM Mono',monospace;font-size:18px;font-weight:500;color:#fff;">{pedido_val}</div>
                </div>
                <div style="width:1.5px;height:36px;background:rgba(255,255,255,0.2);border-radius:2px;margin:0 16px;flex-shrink:0;"></div>
                <div style="text-align:right;">
                    <div style="font-size:9px;font-weight:800;letter-spacing:2px;color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:2px;">Etapa · Operador</div>
                    <div style="font-size:15px;font-weight:800;color:#fff;">{etapa_lbl} · {op}</div>
                </div>
            </div>
            <div style="text-align:center;padding:18px 24px 24px;position:relative;z-index:1;">
                <div style="font-family:'DM Mono',monospace;font-size:70px;font-weight:500;color:#fff;letter-spacing:-3px;line-height:1;">{timer_str}</div>
                <div style="font-size:10px;font-weight:800;color:rgba(255,255,255,0.45);letter-spacing:2px;text-transform:uppercase;margin-top:8px;">cronômetro em execução</div>
            </div>
        </div>
        </body></html>
        """, height=200, scrolling=False)
        _, col_fin, _ = st.columns([0.5, 5, 0.5])
        with col_fin:
            st.markdown('<div class="btn-finalizar">', unsafe_allow_html=True)
            if st.button("■  FINALIZAR ETAPA", use_container_width=True):
                tempo = get_elapsed()
                st.session_state.acum = tempo; st.session_state.rodando = False; st.session_state.inicio = None
                salvar(st.session_state.pedido, op, ETAPAS[etapa_idx], etapa_idx, tempo)
                st.session_state.modal = "proxima" if etapa_idx < 2 else "concluido"
            if etapa_idx == 2:
                marcar_concluido(st.session_state.pedido)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        time.sleep(1); st.rerun()

    # ── Modal: etapa concluída → volta ao menu ──
    elif st.session_state.modal == "proxima":
        next_lbl   = ETAPAS_LBL[etapa_idx + 1]
        tempo_fmt  = fmt(st.session_state.acum)
        pedido_val = st.session_state.pedido
        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@800;900&family=DM+Mono:wght@500&display=swap" rel="stylesheet">
        <style>* {{margin:0;padding:0;box-sizing:border-box;}}</style>
        </head><body style="background:transparent;font-family:Nunito,sans-serif;">
        <div style="background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);border:1.5px solid #EDE9E4;">
            <div style="background:linear-gradient(135deg,#4A7C59,#2d5c3e);padding:24px;text-align:center;">
                <div style="width:56px;height:56px;background:rgba(255,255,255,0.2);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;border:2px solid rgba(255,255,255,0.35);">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                </div>
                <div style="font-size:20px;font-weight:900;color:#fff;margin-bottom:4px;">✅ Etapa Concluída!</div>
                <div style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.65);letter-spacing:1px;">{etapa_lbl} · {tempo_fmt}</div>
            </div>
            <div style="padding:20px 24px;text-align:center;">
                <div style="font-size:11px;font-weight:800;letter-spacing:2px;color:#9C9490;text-transform:uppercase;margin-bottom:6px;">Pedido {pedido_val}</div>
                <div style="font-size:14px;font-weight:600;color:#5C5450;line-height:1.6;">
                    Próxima etapa: <strong style="color:#1A1714;">{next_lbl}</strong><br>
                    <span style="font-size:12px;color:#9C9490;">O próximo operador iniciará no menu principal.</span>
                </div>
            </div>
        </div>
        </body></html>
        """, height=280, scrolling=False)
        st.markdown("<br style='line-height:0.2'>", unsafe_allow_html=True)
        st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
        if st.button("← Voltar ao Menu Principal", use_container_width=True, key="proxima_home"):
            st.session_state.modal = None; st.session_state.pedido = None
            st.session_state.etapa_idx = 0; st.session_state.acum = 0
            st.session_state.operador = None
            st.session_state.etapa_escolhida = None
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Modal: concluído ──
    elif st.session_state.modal == "concluido":
        pedido_val = st.session_state.pedido
        tempo_fmt = fmt(st.session_state.acum)
        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&display=swap" rel="stylesheet">
        <style>* {{margin:0;padding:0;box-sizing:border-box;}}</style>
        </head><body style="background:transparent;font-family:Nunito,sans-serif;">
        <div style="background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);border:1.5px solid #EDE9E4;">
            <div style="background:linear-gradient(135deg,#C8566A 0%,#9E3F52 100%);padding:28px;text-align:center;position:relative;overflow:hidden;">
                <div style="position:absolute;right:-20px;top:-20px;width:100px;height:100px;border-radius:50%;background:rgba(255,255,255,0.07);"></div>
                <div style="position:absolute;left:-10px;bottom:-30px;width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,0.05);"></div>
                <div style="width:60px;height:60px;background:rgba(255,255,255,0.18);border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto 14px;border:2px solid rgba(255,255,255,0.35);position:relative;z-index:1;">
                    <span style="font-size:28px;">🎉</span>
                </div>
                <div style="font-size:22px;font-weight:900;color:#fff;margin-bottom:4px;position:relative;z-index:1;">Pedido Concluído!</div>
                <div style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.65);letter-spacing:1px;position:relative;z-index:1;">Todas as etapas finalizadas</div>
            </div>
            <div style="padding:22px 28px;">
                <div style="display:flex;justify-content:space-between;align-items:center;background:#F7F5F2;border-radius:12px;padding:14px 18px;margin-bottom:10px;">
                    <span style="font-size:11px;font-weight:800;letter-spacing:1.5px;color:#9C9490;text-transform:uppercase;">Pedido</span>
                    <span style="font-family:monospace;font-size:17px;font-weight:800;color:#1A1714;">{pedido_val}</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;background:#F0F7F3;border-radius:12px;padding:14px 18px;">
                    <span style="font-size:11px;font-weight:800;letter-spacing:1.5px;color:#4A7C59;text-transform:uppercase;">Embalagem</span>
                    <span style="font-family:monospace;font-size:17px;font-weight:800;color:#4A7C59;">{tempo_fmt}</span>
                </div>
            </div>
        </div>
        </body></html>
        """, height=300, scrolling=False)
        st.markdown("<br style='line-height:0.2'>", unsafe_allow_html=True)
        st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
        if st.button("← Voltar ao Menu Principal", use_container_width=True):
            st.session_state.modal = None; st.session_state.pedido = None
            st.session_state.etapa_idx = 0; st.session_state.acum = 0
            st.session_state.operador = None
            st.session_state.etapa_escolhida = None
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: ADMIN LOGIN
# ─────────────────────────────────────
def tela_admin_login():
    render_logo()

    erro = st.session_state.erro_senha

    # Full premium admin login via components.html
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
      *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
      body { background:transparent; font-family:'Inter',sans-serif; }

      .card {
        background: linear-gradient(145deg, #1c1917 0%, #292524 50%, #1c1917 100%);
        border-radius: 24px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow:
          0 2px 0 rgba(255,255,255,0.04) inset,
          0 -1px 0 rgba(0,0,0,0.5) inset,
          0 20px 60px rgba(0,0,0,0.5),
          0 8px 20px rgba(0,0,0,0.3);
        position: relative;
      }

      /* Animated glow orb */
      .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.15;
        animation: pulse 4s ease-in-out infinite;
      }
      .orb-1 { width:220px; height:220px; background:#C8566A; top:-60px; right:-60px; animation-delay:0s; }
      .orb-2 { width:160px; height:160px; background:#9E3F52; bottom:-40px; left:-40px; animation-delay:2s; }
      @keyframes pulse {
        0%, 100% { opacity: 0.12; transform: scale(1); }
        50% { opacity: 0.22; transform: scale(1.1); }
      }

      .card-inner { position: relative; z-index: 1; padding: 36px 32px 32px; }

      /* Icon */
      .icon-wrap {
        width: 64px; height: 64px; border-radius: 18px;
        background: linear-gradient(145deg, #C8566A, #7A2D3E);
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 22px;
        box-shadow:
          0 0 0 1px rgba(200,86,106,0.3),
          0 8px 24px rgba(200,86,106,0.4),
          inset 0 1px 0 rgba(255,255,255,0.15);
        animation: icon-glow 3s ease-in-out infinite;
      }
      @keyframes icon-glow {
        0%, 100% { box-shadow: 0 0 0 1px rgba(200,86,106,0.3), 0 8px 24px rgba(200,86,106,0.4), inset 0 1px 0 rgba(255,255,255,0.15); }
        50% { box-shadow: 0 0 0 4px rgba(200,86,106,0.15), 0 8px 32px rgba(200,86,106,0.6), inset 0 1px 0 rgba(255,255,255,0.15); }
      }

      .title-area { text-align: center; margin-bottom: 28px; }
      .eyebrow {
        font-size: 10px; font-weight: 700; letter-spacing: 3px;
        text-transform: uppercase; color: rgba(255,255,255,0.35);
        margin-bottom: 6px;
      }
      .title {
        font-size: 26px; font-weight: 800; color: #fff;
        letter-spacing: -0.5px; line-height: 1.1;
      }
      .subtitle { font-size: 13px; color: rgba(255,255,255,0.4); margin-top: 6px; font-weight: 500; }

      /* Divider */
      .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(200,86,106,0.4), rgba(255,255,255,0.08), transparent);
        margin-bottom: 24px;
      }

      /* Status bar */
      .status-bar {
        display: flex; align-items: center; justify-content: center; gap: 20px;
        padding: 12px 0 4px;
      }
      .status-item { display:flex; align-items:center; gap:6px; }
      .dot {
        width: 7px; height: 7px; border-radius: 50%;
        animation: blink 2s ease-in-out infinite;
      }
      .dot-green { background: #4ade80; box-shadow: 0 0 8px #4ade80; }
      .dot-amber { background: #C8566A; animation-delay: 1s; }
      @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
      }
      .status-text { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.35); letter-spacing: 0.5px; }

      /* Scan line effect */
      .scanline {
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: repeating-linear-gradient(
          0deg,
          transparent,
          transparent 2px,
          rgba(255,255,255,0.01) 2px,
          rgba(255,255,255,0.01) 4px
        );
        pointer-events: none; border-radius: 24px; z-index: 0;
      }
    </style>
    </head>
    <body>
    <div class="card">
      <div class="scanline"></div>
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="card-inner">
        <div class="icon-wrap">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
        </div>
        <div class="title-area">
          <div class="eyebrow">Acesso Restrito</div>
          <div class="title">Painel Administrativo</div>
          <div class="subtitle">Vi Lingerie · Sistema de Produção</div>
        </div>
        <div class="divider"></div>
        <div class="status-bar">
          <div class="status-item">
            <div class="dot dot-green"></div>
            <span class="status-text">Sistema Online</span>
          </div>
          <div class="status-item">
            <div class="dot dot-amber"></div>
            <span class="status-text">Autenticação Necessária</span>
          </div>
        </div>
      </div>
    </div>
    </body>
    </html>
    """, height=330, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # Password field styling
    border_color = "#C8566A" if erro else "#E0DBD4"
    shadow = "0 0 0 4px rgba(200,86,106,0.12)" if erro else "0 3px 12px rgba(0,0,0,0.06)"

    st.markdown(f"""
    <style>
    div[data-testid="stTextInput"] label {{ display:none !important; }}
    div[data-testid="stTextInput"] input {{
        text-align: center !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        letter-spacing: 8px !important;
        color: #1A1714 !important;
        height: 62px !important;
        border: 2px solid {border_color} !important;
        border-radius: 14px !important;
        background: #fff !important;
        box-shadow: {shadow} !important;
        padding: 0 20px !important;
        font-family: 'DM Mono', monospace !important;
        transition: all .2s ease !important;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: #1A1714 !important;
        box-shadow: 0 0 0 4px rgba(26,23,20,0.08), 0 4px 16px rgba(0,0,0,0.08) !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color: #D0CAC4 !important;
        font-weight: 500 !important;
        letter-spacing: 4px !important;
        font-size: 18px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:10px;font-weight:700;letter-spacing:2.5px;color:#9C9490;
                text-transform:uppercase;margin-bottom:10px;text-align:center;">
        Senha de Acesso
    </div>
    """, unsafe_allow_html=True)

    _, col_inp, _ = st.columns([0.3, 5, 0.3])
    with col_inp:
        senha = st.text_input("_", type="password", placeholder="· · · · · · · ·")

    if erro:
        st.markdown("""
        <div style="text-align:center;margin-top:8px;">
          <span style="display:inline-flex;align-items:center;gap:6px;background:#FEF2F2;
                 border:1px solid #FECACA;border-radius:8px;padding:6px 14px;
                 color:#C8566A;font-size:12px;font-weight:700;">
            ⚠ Credenciais inválidas. Tente novamente.
          </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _, c1, gap, c2, _ = st.columns([0.3, 1.4, 0.3, 3, 0.3])
    with c1:
        st.markdown("""
        <style>
        .btn-ghost > button {
            background: transparent !important;
            color: #5C5450 !important;
            border: 1.5px solid #DDD8D2 !important;
            font-size: 13px !important;
        }
        .btn-ghost > button:hover { border-color: #9C9490 !important; color: #1A1714 !important; }
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True):
            st.session_state.erro_senha = False; st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <style>
        .btn-admin-dark > button {
            background: linear-gradient(135deg, #1c1917, #292524) !important;
            color: #fff !important; border: none !important;
            box-shadow: 0 5px 0 rgba(0,0,0,0.50), 0 10px 24px rgba(0,0,0,0.25) !important;
            font-size: 14px !important; letter-spacing: 0.8px !important;
            border-top: 1px solid rgba(255,255,255,0.08) !important;
        }
        .btn-admin-dark > button:hover {
            background: linear-gradient(135deg, #292524, #3d3530) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 0 rgba(0,0,0,0.45), 0 16px 32px rgba(0,0,0,0.30) !important;
        }
        .btn-admin-dark > button:active {
            transform: translateY(3px) !important;
            box-shadow: 0 2px 0 rgba(0,0,0,0.50) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="btn-admin-dark">', unsafe_allow_html=True)
        if st.button("🔓  Acessar Painel", use_container_width=True):
            if senha == ADMIN_SENHA:
                st.session_state.erro_senha = False; st.session_state.tela = "admin"; st.rerun()
            else:
                st.session_state.erro_senha = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
# ─────────────────────────────────────
#  TELA: ADMIN PANEL
# ─────────────────────────────────────
def gerar_pdf(regs, op_map, ped_comp, ops_ativ, avg):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    ROSA      = colors.HexColor("#C8566A")
    ESCURO    = colors.HexColor("#1A1714")
    CLARO     = colors.HexColor("#F7F5F2")
    CINZA     = colors.HexColor("#8C8480")
    VERDE     = colors.HexColor("#4A7C59")
    BEGE      = colors.HexColor("#EDE9E4")
    BRANCO    = colors.white

    styles = getSampleStyleSheet()

    def sty(name, **kw):
        s = ParagraphStyle(name, **kw)
        return s

    S_TITLE    = sty("t", fontName="Helvetica-Bold", fontSize=22, textColor=ESCURO, spaceAfter=2)
    S_SUB      = sty("s", fontName="Helvetica",      fontSize=10, textColor=CINZA,  spaceAfter=0)
    S_SECTION  = sty("sc",fontName="Helvetica-Bold", fontSize=9,  textColor=CINZA,
                     spaceAfter=6, spaceBefore=16, letterSpacing=1.5)
    S_FOOTER   = sty("f", fontName="Helvetica",      fontSize=8,  textColor=CINZA, alignment=TA_CENTER)

    story = []
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # ── Header ──
    header_data = [[
        Paragraph("<b><font color='#C8566A' size='18'>Vi</font> LINGERIE</b>", styles["Normal"]),
        Paragraph(f"<font color='#8C8480' size='8'>Gerado em {now_str}</font>", ParagraphStyle("r", alignment=TA_RIGHT))
    ]]
    header_tbl = Table(header_data, colWidths=["60%","40%"])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=2, color=ROSA, spaceAfter=14))

    story.append(Paragraph("Relatório de Produção", S_TITLE))
    story.append(Paragraph("Desempenho de operadores por etapa do processo produtivo", S_SUB))
    story.append(Spacer(1, 18))

    # ── KPI cards ──
    story.append(Paragraph("RESUMO GERAL", S_SECTION))
    kpi_data = [
        [Paragraph(f"<b><font size='22' color='#C8566A'>{len(ped_comp)}</font></b><br/><font size='8' color='#8C8480'>PEDIDOS CONCLUÍDOS</font>", styles["Normal"]),
         Paragraph(f"<b><font size='22' color='#C8566A'>{len(ops_ativ)}</font></b><br/><font size='8' color='#8C8480'>OPERADORES ATIVOS</font>", styles["Normal"]),
         Paragraph(f"<b><font size='22' color='#C8566A'>{avg}m</font></b><br/><font size='8' color='#8C8480'>TEMPO MÉDIO</font>", styles["Normal"]),
         Paragraph(f"<b><font size='22' color='#C8566A'>{len(regs)}</font></b><br/><font size='8' color='#8C8480'>REGISTROS TOTAIS</font>", styles["Normal"])],
    ]
    kpi_tbl = Table(kpi_data, colWidths=["25%","25%","25%","25%"])
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), CLARO),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [CLARO]),
        ("BOX",           (0,0), (0,0),   0.8, BEGE),
        ("BOX",           (1,0), (1,0),   0.8, BEGE),
        ("BOX",           (2,0), (2,0),   0.8, BEGE),
        ("BOX",           (3,0), (3,0),   0.8, BEGE),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (-1,-1), 14),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 20))

    # ── Operator performance ──
    if op_map:
        story.append(Paragraph("DESEMPENHO POR OPERADOR", S_SECTION))
        op_header = [
            Paragraph("<b>OPERADOR</b>", ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO)),
            Paragraph("<b>PEDIDOS</b>",  ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>SEPARAÇÃO</b>",ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>CONFERÊNCIA</b>",ParagraphStyle("h",fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>EMBALAGEM</b>",ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
        ]
        op_rows = [op_header]
        for i, (op, d) in enumerate(op_map.items()):
            bg = CLARO if i % 2 == 0 else BRANCO
            op_rows.append([
                Paragraph(f"<b>{op}</b>", ParagraphStyle("o", fontName="Helvetica-Bold", fontSize=9, textColor=ESCURO)),
                Paragraph(str(len(d["p"])), ParagraphStyle("c", fontSize=9, textColor=ESCURO, alignment=TA_CENTER)),
                Paragraph(fmt(media(d["sep"])) if d["sep"] else "—", ParagraphStyle("c", fontSize=9, textColor=ESCURO, alignment=TA_CENTER)),
                Paragraph(fmt(media(d["conf"])) if d["conf"] else "—", ParagraphStyle("c", fontSize=9, textColor=ESCURO, alignment=TA_CENTER)),
                Paragraph(fmt(media(d["emb"])) if d["emb"] else "—", ParagraphStyle("c", fontSize=9, textColor=VERDE, alignment=TA_CENTER, fontName="Helvetica-Bold")),
            ])

        op_tbl = Table(op_rows, colWidths=["30%","14%","18%","20%","18%"])
        row_bgs = [ROSA] + [CLARO if i%2==0 else BRANCO for i in range(len(op_rows)-1)]
        op_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), ROSA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [CLARO, BRANCO]),
            ("GRID",          (0,0), (-1,-1), 0.4, BEGE),
            ("TOPPADDING",    (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,-1), 9),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("LINEBELOW",     (0,0), (-1,0), 0, colors.transparent),
        ]))
        story.append(op_tbl)
        story.append(Spacer(1, 20))

    # ── History ──
    if regs:
        story.append(Paragraph("HISTÓRICO DE PEDIDOS", S_SECTION))
        ETAPA_CORES = {"Separacao": colors.HexColor("#3B5EC6"),
                       "Conferencia": colors.HexColor("#C47B2A"),
                       "Embalagem": colors.HexColor("#4A7C59")}
        ETAPA_NOMES = {"Separacao":"Separação","Conferencia":"Conferência","Embalagem":"Embalagem"}
        hist_header = [
            Paragraph("<b>PEDIDO</b>",   ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=8,textColor=BRANCO)),
            Paragraph("<b>OPERADOR</b>", ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=8,textColor=BRANCO)),
            Paragraph("<b>ETAPA</b>",    ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=8,textColor=BRANCO,alignment=TA_CENTER)),
            Paragraph("<b>TEMPO</b>",    ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=8,textColor=BRANCO,alignment=TA_CENTER)),
            Paragraph("<b>DATA</b>",     ParagraphStyle("h",fontName="Helvetica-Bold",fontSize=8,textColor=BRANCO,alignment=TA_CENTER)),
        ]
        hist_rows = [hist_header]
        for i, r in enumerate(regs[:80]):
            cor_etapa = ETAPA_CORES.get(r[3], CINZA)
            hist_rows.append([
                Paragraph(f"<font name='Courier-Bold' size='8'>{r[1]}</font>", styles["Normal"]),
                Paragraph(f"<font size='8'>{r[2]}</font>", styles["Normal"]),
                Paragraph(ETAPA_NOMES.get(r[3], r[3]), styles["Normal"]),
                Paragraph(f"<font name='Courier' size='8'>{fmt(r[5])}</font>", ParagraphStyle("c",fontSize=8,alignment=TA_CENTER)),
                Paragraph(f"<font size='7' color='#8C8480'>{r[6]}</font>", ParagraphStyle("c",fontSize=7,alignment=TA_CENTER)),
            ])

        hist_tbl = Table(hist_rows, colWidths=["18%","22%","22%","16%","22%"])
        hist_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), ESCURO),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [CLARO, BRANCO]),
            ("GRID",          (0,0), (-1,-1), 0.3, BEGE),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(hist_tbl)

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BEGE, spaceAfter=8))
    story.append(Paragraph(f"Vi Lingerie · Relatório gerado automaticamente em {now_str} · Sistema de Produção", S_FOOTER))

    doc.build(story)
    return buf.getvalue()


def tela_admin():
    render_logo()

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("""
        <div style="margin-bottom:1.2rem;">
            <div style="font-size:10px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;color:#9C9490;margin-bottom:4px;">Painel Administrativo</div>
            <div style="font-size:24px;font-weight:900;color:#1A1714;letter-spacing:-0.3px;">Visão Geral da Produção</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-voltar btn-sm">', unsafe_allow_html=True)
        if st.button("← Sair", use_container_width=True):
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Upload planilha ──
    # Toggle state
    if "show_upload" not in st.session_state:
        st.session_state.show_upload = False

    # Header button to toggle
    st.markdown("""
    <style>
    .btn-upload > button {
        background: linear-gradient(135deg,#1A1714,#2e2825) !important;
        color:#fff !important; border:none !important;
        box-shadow: 0 5px 0 rgba(0,0,0,0.45), 0 8px 20px rgba(0,0,0,0.20) !important;
        font-size:14px !important; font-weight:800 !important; letter-spacing:.5px !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
    }
    .btn-upload > button:hover {
        background: linear-gradient(135deg,#2e2825,#3d3530) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_up1, col_up2 = st.columns([3,1])
    with col_up1:
        pedidos_base_count = len(buscar_pedidos_base())
        if pedidos_base_count > 0:
            abertos_c   = sum(1 for p in buscar_pedidos_base() if p[3]=="aberto")
            concl_c     = pedidos_base_count - abertos_c
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:14px;padding:12px 0;">
                <div style="width:10px;height:10px;border-radius:50%;background:#4A7C59;
                            box-shadow:0 0 8px #4A7C59;flex-shrink:0;"></div>
                <div style="font-size:13px;font-weight:700;color:#5C5450;">
                    Base carregada: <strong style="color:#1A1714;">{pedidos_base_count}</strong> pedidos
                    &nbsp;·&nbsp; <span style="color:#4A7C59;">{abertos_c} abertos</span>
                    &nbsp;·&nbsp; <span style="color:#C8566A;">{concl_c} concluídos</span>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:14px;padding:12px 0;">
                <div style="width:10px;height:10px;border-radius:50%;background:#C8566A;
                            box-shadow:0 0 8px rgba(200,86,106,0.6);flex-shrink:0;"></div>
                <div style="font-size:13px;font-weight:700;color:#C8566A;">
                    Nenhuma planilha carregada ainda
                </div>
            </div>""", unsafe_allow_html=True)
    with col_up2:
        label = "✕ Fechar" if st.session_state.show_upload else "📂 Carregar Planilha"
        st.markdown('<div class="btn-upload">', unsafe_allow_html=True)
        if st.button(label, use_container_width=True):
            st.session_state.show_upload = not st.session_state.show_upload
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.show_upload:
        components.html("""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
        <style>*{margin:0;padding:0;box-sizing:border-box;}</style>
        </head><body style="background:transparent;font-family:Nunito,sans-serif;">
        <div style="background:linear-gradient(135deg,#1c1917,#292524);border-radius:16px;padding:20px 24px;
                    border:1px solid rgba(255,255,255,0.07);box-shadow:0 6px 24px rgba(0,0,0,0.25);
                    position:relative;overflow:hidden;">
            <div style="position:absolute;right:-20px;top:-20px;width:120px;height:120px;border-radius:50%;
                        background:rgba(200,86,106,0.08);"></div>
            <div style="display:flex;align-items:flex-start;gap:16px;position:relative;z-index:1;">
                <div style="width:44px;height:44px;border-radius:12px;flex-shrink:0;
                            background:linear-gradient(135deg,#C8566A,#9E3F52);
                            display:flex;align-items:center;justify-content:center;
                            box-shadow:0 4px 14px rgba(200,86,106,0.4);">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="12" y1="18" x2="12" y2="12"></line>
                        <line x1="9" y1="15" x2="15" y2="15"></line>
                    </svg>
                </div>
                <div>
                    <div style="font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;
                                color:rgba(255,255,255,0.4);margin-bottom:4px;">Instruções</div>
                    <div style="font-size:13px;font-weight:700;color:rgba(255,255,255,0.85);line-height:1.7;">
                        Suba a planilha <b style="color:#C8566A;">.xlsx</b> exportada do sistema interno.<br>
                        O sistema lê a coluna <b style="color:#C8566A;">Pedido</b> e a coluna <b style="color:#C8566A;">%.1</b>
                        (100% = concluído, qualquer outro valor = em aberto).<br>
                        Pedidos concluídos ficam <b>bloqueados</b> para produção.
                    </div>
                </div>
            </div>
        </div>
        </body></html>""", height=130, scrolling=False)

        st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Selecione a planilha (.xlsx ou .csv)",
            type=["xlsx","xls","csv"],
        )
        if uploaded:
            ok, result = importar_planilha(uploaded.read(), uploaded.name)
            if ok:
                components.html(f"""<div style="background:#E8F2EC;border:2px solid #4A7C59;border-radius:12px;
                    padding:14px 20px;font-family:sans-serif;font-size:14px;font-weight:800;
                    color:#2d5a3d;text-align:center;margin-top:8px;">
                    ✅ {result} pedidos importados com sucesso de <b>{uploaded.name}</b>
                </div>""", height=60, scrolling=False)
                st.session_state.show_upload = False
                st.rerun()
            else:
                components.html(f"""<div style="background:#FEF2F2;border:2px solid #C8566A;border-radius:12px;
                    padding:14px 20px;font-family:sans-serif;font-size:14px;font-weight:800;
                    color:#991B1B;text-align:center;margin-top:8px;">
                    ❌ {result}
                </div>""", height=60, scrolling=False)

    st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)
    regs     = buscar()
    ped_comp = list({r[1] for r in regs if r[4] == 2})
    ops_ativ = list({r[2] for r in regs})
    avg      = media([r[5] for r in regs]) // 60 if regs else 0
    total_r  = len(regs)

    # ── KPI Cards via components ──
    kpi_html = f"""
    <!DOCTYPE html><html><head>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:transparent;font-family:Nunito,sans-serif;}}
    .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}}
    .card{{background:#fff;border-radius:16px;padding:18px 16px 14px;
           border:1.5px solid #EDE9E4;box-shadow:0 2px 12px rgba(0,0,0,0.05);
           position:relative;overflow:hidden;}}
    .card-icon{{position:absolute;top:-6px;right:4px;font-size:44px;opacity:0.07;line-height:1;}}
    .card-lbl{{font-size:9px;font-weight:800;letter-spacing:1.8px;text-transform:uppercase;color:#9C9490;margin-bottom:8px;}}
    .card-num{{font-family:"DM Mono",monospace;font-size:32px;font-weight:500;letter-spacing:-1px;}}
    .card-bar{{height:3px;border-radius:2px;margin-top:12px;opacity:0.3;}}
    </style></head><body>
    <div class="grid">
      <div class="card">
        <div class="card-icon">📦</div>
        <div class="card-lbl">Pedidos Concluídos</div>
        <div class="card-num" style="color:#C8566A;">{len(ped_comp)}</div>
        <div class="card-bar" style="background:#C8566A;"></div>
      </div>
      <div class="card">
        <div class="card-icon">👥</div>
        <div class="card-lbl">Operadores Ativos</div>
        <div class="card-num" style="color:#4A7C59;">{len(ops_ativ)}</div>
        <div class="card-bar" style="background:#4A7C59;"></div>
      </div>
      <div class="card">
        <div class="card-icon">⏱</div>
        <div class="card-lbl">Tempo Médio</div>
        <div class="card-num" style="color:#3B5EC6;">{avg}m</div>
        <div class="card-bar" style="background:#3B5EC6;"></div>
      </div>
      <div class="card">
        <div class="card-icon">📊</div>
        <div class="card-lbl">Total Registros</div>
        <div class="card-num" style="color:#C47B2A;">{total_r}</div>
        <div class="card-bar" style="background:#C47B2A;"></div>
      </div>
    </div>
    </body></html>"""
    components.html(kpi_html, height=115, scrolling=False)

    # ── Build op_map ──
    op_map = {}
    for r in regs:
        op = r[2]
        if op not in op_map: op_map[op] = {"p":set(),"sep":[],"conf":[],"emb":[]}
        op_map[op]["p"].add(r[1])
        if r[4]==0: op_map[op]["sep"].append(r[5])
        if r[4]==1: op_map[op]["conf"].append(r[5])
        if r[4]==2: op_map[op]["emb"].append(r[5])

    st.markdown("<br style='line-height:0.4'>", unsafe_allow_html=True)

    # ── Operator table via components ──
    if op_map:
        op_rows = ""
        for op, d in op_map.items():
            sep_t  = fmt(media(d["sep"]))  if d["sep"]  else "—"
            conf_t = fmt(media(d["conf"])) if d["conf"] else "—"
            emb_t  = fmt(media(d["emb"]))  if d["emb"]  else "—"
            ini    = op[0].upper()
            op_rows += f"""<tr>
              <td style="padding:13px 16px;vertical-align:middle;">
                <div style="display:flex;align-items:center;gap:10px;">
                  <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
                       background:linear-gradient(135deg,#D9617A,#9E3F52);
                       display:flex;align-items:center;justify-content:center;
                       font-size:15px;font-weight:900;color:#fff;">{ini}</div>
                  <span style="font-weight:800;font-size:14px;color:#1A1714;">{op}</span>
                </div>
              </td>
              <td style="padding:13px 10px;text-align:center;vertical-align:middle;">
                <span style="background:#F5E8EB;color:#C8566A;font-weight:800;font-size:13px;
                             padding:4px 14px;border-radius:100px;">{len(d["p"])}</span>
              </td>
              <td style="padding:13px 10px;text-align:center;font-family:monospace;font-size:13px;color:#3B5EC6;font-weight:700;vertical-align:middle;">{sep_t}</td>
              <td style="padding:13px 10px;text-align:center;font-family:monospace;font-size:13px;color:#C47B2A;font-weight:700;vertical-align:middle;">{conf_t}</td>
              <td style="padding:13px 10px;text-align:center;font-family:monospace;font-size:13px;color:#4A7C59;font-weight:700;vertical-align:middle;">{emb_t}</td>
            </tr>"""

        n_ops = len(op_map)
        op_height = 56 + (n_ops * 62) + 20

        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
        <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:transparent;font-family:Nunito,sans-serif;}}
        .lbl{{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#9C9490;margin-bottom:10px;}}
        .wrap{{background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;
               overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.05);}}
        table{{width:100%;border-collapse:collapse;}}
        thead tr{{background:#1A1714;}}
        th{{padding:12px 10px;font-size:9px;font-weight:800;letter-spacing:1.5px;
            text-transform:uppercase;text-align:center;}}
        th:first-child{{text-align:left;padding-left:16px;}}
        tbody tr{{border-bottom:1px solid #F2EEE9;transition:background .15s;}}
        tbody tr:last-child{{border-bottom:none;}}
        tbody tr:hover{{background:#FDFAF9;}}
        </style></head><body>
        <div class="lbl">Desempenho por Operador</div>
        <div class="wrap">
          <table>
            <thead>
              <tr>
                <th style="color:rgba(255,255,255,0.45);">Operador</th>
                <th style="color:rgba(255,255,255,0.45);">Pedidos</th>
                <th style="color:#7B9FE0;">Separação</th>
                <th style="color:#D4A45A;">Conferência</th>
                <th style="color:#7AB895;">Embalagem</th>
              </tr>
            </thead>
            <tbody>{op_rows}</tbody>
          </table>
        </div>
        </body></html>
        """, height=op_height, scrolling=False)
    else:
        components.html("""
        <!DOCTYPE html><html><body style="background:transparent;font-family:sans-serif;">
        <div style="background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;
                    padding:40px;text-align:center;color:#9C9490;font-size:14px;font-weight:600;">
            Nenhum registro ainda.
        </div></body></html>""", height=120, scrolling=False)

    st.markdown("<br style='line-height:0.4'>", unsafe_allow_html=True)

    # ── History header ──
    h1, h2 = st.columns([3, 1])
    with h2:
        if st.button("🗑 Limpar dados", use_container_width=True):
            limpar(); st.rerun()

    tag_html = {
        0: '<span style="background:#EBF0FB;color:#3B5EC6;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:800;">Separação</span>',
        1: '<span style="background:#FBF2E6;color:#C47B2A;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:800;">Conferência</span>',
        2: '<span style="background:#E8F2EC;color:#4A7C59;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:800;">Embalagem</span>',
    }

    if regs:
        hist_rows = ""
        for r in regs[:80]:
            hist_rows += f"""<tr>
              <td style="padding:11px 16px;font-family:monospace;font-size:12px;font-weight:700;color:#1A1714;">{r[1]}</td>
              <td style="padding:11px 10px;font-size:13px;font-weight:700;color:#1A1714;">{r[2]}</td>
              <td style="padding:11px 10px;">{tag_html.get(r[4], r[3])}</td>
              <td style="padding:11px 10px;font-family:monospace;font-size:12px;font-weight:700;color:#4A7C59;text-align:center;">{fmt(r[5])}</td>
              <td style="padding:11px 10px;font-size:11px;color:#9C9490;text-align:center;">{r[6]}</td>
            </tr>"""

        n_hist = min(len(regs), 80)
        hist_height = 56 + (n_hist * 46) + 20

        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
        <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:transparent;font-family:Nunito,sans-serif;}}
        .lbl{{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#9C9490;margin-bottom:10px;}}
        .wrap{{background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;
               overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.05);}}
        table{{width:100%;border-collapse:collapse;}}
        thead tr{{background:#1A1714;}}
        th{{padding:12px 10px;font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.45);text-align:center;}}
        th:first-child{{text-align:left;padding-left:16px;}}
        th:nth-child(2){{text-align:left;}}
        tbody tr{{border-bottom:1px solid #F2EEE9;}}
        tbody tr:last-child{{border-bottom:none;}}
        tbody tr:hover{{background:#FDFAF9;}}
        </style></head><body>
        <div class="lbl">Histórico de Pedidos</div>
        <div class="wrap">
          <table>
            <thead>
              <tr>
                <th>Pedido</th><th>Operador</th><th>Etapa</th><th>Tempo</th><th>Data</th>
              </tr>
            </thead>
            <tbody>{hist_rows}</tbody>
          </table>
        </div>
        </body></html>
        """, height=min(hist_height, 600), scrolling=hist_height > 600)
    else:
        components.html("""
        <!DOCTYPE html><html><body style="background:transparent;font-family:sans-serif;">
        <div style="background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;
                    padding:40px;text-align:center;color:#9C9490;font-size:14px;font-weight:600;">
            Nenhum registro ainda.
        </div></body></html>""", height=120, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Export buttons ──
    if regs:
        st.markdown("""
        <style>
        .btn-pdf > button {
            background: linear-gradient(135deg,#C8566A,#9E3F52) !important;
            color:#fff !important; border:none !important;
            box-shadow: 0 5px 0 rgba(100,20,35,0.40), 0 8px 20px rgba(200,86,106,0.28) !important;
            font-weight:800 !important; height:54px !important;
        }
        .btn-pdf > button:hover { transform:translateY(-2px) !important; }
        .btn-xml > button {
            background: linear-gradient(135deg,#3B5EC6,#2a469e) !important;
            color:#fff !important; border:none !important;
            box-shadow: 0 5px 0 rgba(20,30,100,0.40), 0 8px 20px rgba(59,94,198,0.28) !important;
            font-weight:800 !important; height:54px !important;
        }
        .btn-xml > button:hover { transform:translateY(-2px) !important; }
        </style>
        """, unsafe_allow_html=True)

        # ── Build exports ──
        ts = datetime.now().strftime("%Y%m%d_%H%M")

        # CSV
        buf_csv = io.StringIO()
        csv.writer(buf_csv).writerows(
            [["ID","Pedido","Operador","Etapa","EtapaIdx","Tempo(s)","Data"]] + list(regs))

        # PDF
        pdf_bytes = gerar_pdf(regs, op_map, ped_comp, ops_ativ, avg)

        # XML
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        root = ET.Element("RelatorioProducao")
        root.set("gerado_em", datetime.now().strftime("%d/%m/%Y %H:%M"))
        root.set("total_registros", str(len(regs)))
        summary = ET.SubElement(root, "Resumo")
        ET.SubElement(summary, "PedidosConcluidos").text = str(len(ped_comp))
        ET.SubElement(summary, "OperadoresAtivos").text = str(ops_ativ)
        ET.SubElement(summary, "TempoMedioSegundos").text = str(avg)
        registros_el = ET.SubElement(root, "Registros")
        for r in regs:
            reg = ET.SubElement(registros_el, "Registro")
            reg.set("id", str(r[0]))
            ET.SubElement(reg, "Pedido").text    = str(r[1])
            ET.SubElement(reg, "Operador").text  = str(r[2])
            ET.SubElement(reg, "Etapa").text     = str(r[3])
            ET.SubElement(reg, "EtapaIdx").text  = str(r[4])
            ET.SubElement(reg, "TempoSegundos").text = str(r[5])
            ET.SubElement(reg, "TempoFormatado").text = fmt(r[5])
            ET.SubElement(reg, "Data").text      = str(r[6])
        xml_str = minidom.parseString(ET.tostring(root, encoding="unicode")).toprettyxml(indent="  ")
        xml_bytes = xml_str.encode("utf-8")

        # ── Layout: 3 colunas ──
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            st.download_button(
                label="⬇  Exportar CSV",
                data=buf_csv.getvalue().encode(),
                file_name=f"vi_producao_{ts}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-xml">', unsafe_allow_html=True)
            st.download_button(
                label="🗂  Exportar XML",
                data=xml_bytes,
                file_name=f"vi_producao_{ts}.xml",
                mime="application/xml",
                use_container_width=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button(
                label="📄  Exportar PDF",
                data=pdf_bytes,
                file_name=f"vi_relatorio_{ts}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)
# ─────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────
{
    "home":        tela_home,
    "producao":    tela_producao,
    "admin_login": tela_admin_login,
    "admin":       tela_admin,
}.get(st.session_state.tela, tela_home)()
