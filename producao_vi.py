import streamlit as st
import time
import base64
from datetime import datetime
from pathlib import Path
import csv, io
import streamlit.components.v1 as components
import pandas as pd
import re
import requests
import json

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

# ─────────────────────────────────────
#  SUPABASE CONFIG
# ─────────────────────────────────────
try:
    SB_URL = st.secrets["SUPABASE_URL"]
    SB_KEY = st.secrets["SUPABASE_KEY"]
except:
    SB_URL = "https://uiybrhaqtcwejtbbctge.supabase.co"
    SB_KEY = "sb_publishable_oIpsQMjK3QGL6IPkccJHqQ_OQCfrJf0"

def _sb_headers():
    return {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _get(table, params=""):
    r = requests.get(f"{SB_URL}/rest/v1/{table}?{params}", headers=_sb_headers(), timeout=10)
    return r.json() if r.ok else []

def _post(table, data):
    r = requests.post(f"{SB_URL}/rest/v1/{table}", headers=_sb_headers(),
                      data=json.dumps(data), timeout=10)
    return r.ok

def _patch(table, match_params, data):
    r = requests.patch(f"{SB_URL}/rest/v1/{table}?{match_params}",
                       headers={**_sb_headers(), "Prefer": "return=minimal"},
                       data=json.dumps(data), timeout=10)
    return r.ok

def _delete(table, params):
    r = requests.delete(f"{SB_URL}/rest/v1/{table}?{params}",
                        headers=_sb_headers(), timeout=10)
    return r.ok

def _upsert(table, data, on_conflict):
    h = {**_sb_headers(), "Prefer": f"resolution=merge-duplicates,return=minimal"}
    r = requests.post(f"{SB_URL}/rest/v1/{table}?on_conflict={on_conflict}",
                      headers=h, data=json.dumps(data), timeout=10)
    return r.ok

# ─────────────────────────────────────
#  DATABASE — Supabase REST API
# ─────────────────────────────────────
def init_db():
    pass  # Tables created via supabase_setup.sql

# ─── Planilha / Pedidos base ───
def buscar_pedidos_base():
    rows = _get("pedidos_base", "select=numero,cliente,produto,status&order=numero.asc")
    if isinstance(rows, list):
        return [(r["numero"], r.get("cliente",""), r.get("produto",""), r.get("status","aberto"))
                for r in rows]
    return []

def status_pedido(numero):
    rows = _get("pedidos_base", f"numero=eq.{numero}&select=status")
    if not rows: return "nao_encontrado"
    return rows[0].get("status", "nao_encontrado")

def cadastrar_pedido_avulso(numero):
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    _upsert("pedidos_base",
            {"numero": numero, "cliente": "", "produto": "",
             "status": "aberto", "importado_em": now_str},
            "numero")

def marcar_concluido(numero):
    _patch("pedidos_base", f"numero=eq.{numero}", {"status": "concluido"})

def verificar_etapa_registro(pedido, etapa_idx):
    rows = _get("registros",
        f"pedido=eq.{pedido}&etapa_idx=eq.{etapa_idx}&select=operador&order=id.desc&limit=1")
    if rows: return True, rows[0].get("operador")
    return False, None

def pedido_em_andamento(pedido, etapa_idx):
    rows = _get("sessoes_ativas",
        f"pedido=eq.{pedido}&etapa_idx=eq.{etapa_idx}&select=operador,iniciado_em")
    if rows:
        r = rows[0]
        if int(time.time()) - int(r.get("iniciado_em", 0)) < 14400:
            return True, r.get("operador")
    return False, None

def registrar_sessao_ativa(pedido, etapa_idx, operador):
    _upsert("sessoes_ativas",
            {"pedido": pedido, "etapa_idx": etapa_idx,
             "operador": operador, "iniciado_em": int(time.time())},
            "pedido,etapa_idx")

def remover_sessao_ativa(pedido, etapa_idx):
    _delete("sessoes_ativas", f"pedido=eq.{pedido}&etapa_idx=eq.{etapa_idx}")

def buscar_pedidos_por_etapa(etapa_idx):
    pedidos_rows = _get("pedidos_base", "select=numero,cliente&status=eq.aberto&order=numero.asc")
    if not isinstance(pedidos_rows, list):
        return []
    regs_rows = _get("registros", "select=pedido,etapa_idx")
    if not isinstance(regs_rows, list):
        regs_rows = []
    etapas_feitas = {}
    for r in regs_rows:
        p = r.get("pedido"); e = r.get("etapa_idx")
        if p not in etapas_feitas: etapas_feitas[p] = set()
        if e is not None: etapas_feitas[p].add(int(e))
    resultado = []
    for p in pedidos_rows:
        num = p["numero"]; cli = p.get("cliente", "")
        feitas = etapas_feitas.get(num, set())
        if etapa_idx == 0 and 0 not in feitas:
            resultado.append((num, cli))
        elif etapa_idx == 1 and 0 in feitas and 1 not in feitas:
            resultado.append((num, cli))
        elif etapa_idx == 2 and 1 in feitas and 2 not in feitas:
            resultado.append((num, cli))
    return resultado

def buscar_todas_sessoes_ativas():
    rows = _get("sessoes_ativas", "select=*&order=iniciado_em.asc")
    return rows if isinstance(rows, list) else []

def buscar_status_completo_pedido(numero):
    """
    Retorna dict com o status detalhado de cada etapa do pedido:
    {
      "base_status": "aberto"|"concluido"|"nao_encontrado",
      "etapas": [
        {"idx":0, "label":"Separação", "feita":True/False, "em_andamento":False,
         "operador":"...", "tempo":120, "data":"..."},
        ...
      ]
    }
    """
    # Status base
    base_rows = _get("pedidos_base", f"numero=eq.{numero}&select=status,cliente")
    if not base_rows:
        return {"base_status": "nao_encontrado", "cliente": "", "etapas": []}
    base_status = base_rows[0].get("status", "aberto")
    cliente     = base_rows[0].get("cliente", "")

    # Registros finalizados por etapa
    reg_rows = _get("registros",
        f"pedido=eq.{numero}&select=etapa_idx,operador,tempo_segundos,data&order=id.asc")
    regs_por_etapa = {}
    if isinstance(reg_rows, list):
        for r in reg_rows:
            ei = r.get("etapa_idx")
            if ei is not None:
                regs_por_etapa[int(ei)] = r

    # Sessões ativas (em andamento agora)
    sess_rows = _get("sessoes_ativas",
        f"pedido=eq.{numero}&select=etapa_idx,operador,iniciado_em")
    sess_por_etapa = {}
    if isinstance(sess_rows, list):
        for r in sess_rows:
            ei = r.get("etapa_idx")
            if ei is not None:
                sess_por_etapa[int(ei)] = r

    etapas = []
    for idx, lbl in enumerate(ETAPAS_LBL):
        reg  = regs_por_etapa.get(idx)
        sess = sess_por_etapa.get(idx)
        etapas.append({
            "idx":          idx,
            "label":        lbl,
            "feita":        reg is not None,
            "em_andamento": sess is not None,
            "operador":     (reg or sess or {}).get("operador", ""),
            "tempo":        (reg or {}).get("tempo_segundos"),
            "data":         (reg or {}).get("data", ""),
            "iniciado_em":  (sess or {}).get("iniciado_em"),
        })

    return {
        "base_status": base_status,
        "cliente":     cliente,
        "etapas":      etapas,
    }

def finalizar_pip(pedido, etapa_idx, operador, iniciado_em):
    tempo = max(int(time.time()) - int(iniciado_em), 1)
    salvar(pedido, operador, ETAPAS[etapa_idx], etapa_idx, tempo)
    remover_sessao_ativa(pedido, etapa_idx)
    if etapa_idx == 2:
        marcar_concluido(pedido)

def salvar(pedido, operador, etapa, etapa_idx, tempo):
    _post("registros", {
        "pedido": pedido, "operador": operador, "etapa": etapa,
        "etapa_idx": etapa_idx, "tempo_segundos": tempo,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
    })

def buscar():
    rows = _get("registros", "select=*&order=id.desc")
    if isinstance(rows, list):
        return [(r.get("id"), r.get("pedido"), r.get("operador"), r.get("etapa"),
                 r.get("etapa_idx"), r.get("tempo_segundos"), r.get("data"))
                for r in rows]
    return []

def limpar():
    _delete("registros", "id=gte.0")

def limpar_sessoes_ativas():
    """Remove todas as sessões ativas buscando e deletando uma a uma."""
    rows = _get("sessoes_ativas", "select=pedido,etapa_idx")
    if isinstance(rows, list):
        for r in rows:
            ped = r.get("pedido", "")
            eta = r.get("etapa_idx", 0)
            if ped != "":
                _delete("sessoes_ativas", f"pedido=eq.{ped}&etapa_idx=eq.{eta}")
    # fallback: deleta por campo operador sempre preenchido
    _delete("sessoes_ativas", "operador=neq.___x___")

def buscar_pedidos_avulsos():
    rows = _get(
        "pedidos_base",
        "select=numero,status,importado_em"
        "&cliente=eq."
        "&percentual=is.null"
        "&order=importado_em.desc"
    )
    if isinstance(rows, list):
        return [(r["numero"], r.get("status","aberto"), r.get("importado_em",""))
                for r in rows]
    return []

def excluir_pedido_avulso(numero):
    _delete("sessoes_ativas", f"pedido=eq.{numero}")
    _delete("registros",      f"pedido=eq.{numero}")
    _delete("pedidos_base",   f"numero=eq.{numero}")

init_db()

# ── Limpeza automática de sessões expiradas (>12h) ──
def _limpar_sessoes_expiradas():
    """Remove sessões com mais de 12h buscando e deletando individualmente."""
    limite = int(time.time()) - 43200
    rows = _get("sessoes_ativas", "select=pedido,etapa_idx,iniciado_em")
    if isinstance(rows, list):
        for r in rows:
            try:
                if int(r.get("iniciado_em", 0)) < limite:
                    ped = r.get("pedido", "")
                    eta = r.get("etapa_idx", 0)
                    if ped:
                        _delete("sessoes_ativas", f"pedido=eq.{ped}&etapa_idx=eq.{eta}")
            except Exception:
                pass

_limpar_sessoes_expiradas()

# ─────────────────────────────────────
#  QUERY PARAM — PiP FINALIZAR
# ─────────────────────────────────────
_qp = st.query_params
_pip_action = _qp.get("pip_action", "")

if _pip_action == "finalizar":
    try:
        _ped = _qp.get("pedido", "")
        _eta = int(_qp.get("etapa", 0))
        _op  = _qp.get("operador", "")
        _ini = int(_qp.get("iniciado_em", 0))
        if _ped and _op and _ini:
            finalizar_pip(_ped, _eta, _op, _ini)
    except Exception:
        pass
    st.query_params.clear()
    st.rerun()

elif _pip_action == "fechar":
    # Fecha o PiP sem salvar o tempo — apenas remove a sessão ativa
    try:
        _ped = _qp.get("pedido", "")
        _eta = int(_qp.get("etapa", 0))
        if _ped:
            remover_sessao_ativa(_ped, _eta)
    except Exception:
        pass
    st.query_params.clear()
    st.rerun()

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
    "etapa_escolhida":None, "duplicata_info":None,
    "pedido_validado":False,
    "op_filtro_andamento": "Todos",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
    import streamlit.components.v1 as _cv1

    COLORS = [
        "#C8566A","#3B7DD8","#4A7C59","#E07B3A",
        "#7C5CBF","#B85C38","#2E9E8F","#8E6BBF","#C8566A",
    ]

    selecionado = st.session_state.get("operador")
    if selecionado and selecionado in OPERADORES:
        idx_op = OPERADORES.index(selecionado)
        cor    = COLORS[idx_op % len(COLORS)]
        ini    = (selecionado[0]+selecionado[1]).upper()
    else:
        cor, ini = "#9C9490", "?"

    _cv1.html(f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;font-family:'Nunito',sans-serif;overflow:visible;}}
.card{{
    display:flex;align-items:center;gap:14px;
    background:#fff;border:2px solid #E8E2DC;
    border-radius:16px 16px 0 0;
    padding:14px 18px 12px;
    box-shadow:0 2px 12px rgba(0,0,0,.06);
    border-bottom: none;
}}
.av{{width:44px;height:44px;border-radius:50%;flex-shrink:0;
    background:linear-gradient(145deg,{cor},{cor}bb);
    display:flex;align-items:center;justify-content:center;
    font-size:15px;font-weight:900;color:#fff;
    box-shadow:0 3px 10px rgba(0,0,0,.20);}}
.label{{font-size:10px;font-weight:800;letter-spacing:1.8px;
    text-transform:uppercase;color:#9C9490;margin-bottom:3px;}}
.value{{font-size:16px;font-weight:900;color:#1A1714;}}
.hint{{font-size:11px;color:#9C9490;margin-top:2px;font-weight:600;}}
.arrow{{margin-left:auto;font-size:18px;color:#C8566A;}}
</style></head>
<body>
<div class="card">
    <div class="av">{ini}</div>
    <div>
        <div class="label">Operador</div>
        <div class="value">{"Nenhum selecionado" if not selecionado else selecionado}</div>
        <div class="hint">{"Escolha abaixo ↓" if not selecionado else "✓ Selecionado"}</div>
    </div>
    <div class="arrow">⌄</div>
</div>
</body></html>""", height=96, scrolling=False)

    st.markdown("""
    <style>
    div[data-testid="stSelectbox"] label { display:none !important; }
    div[data-testid="stSelectbox"] > div > div {
        border: 2px solid #E8E2DC !important;
        border-top: none !important;
        border-radius: 0 0 16px 16px !important;
        background: #fff !important;
        padding: 4px 8px !important;
        font-family: 'Nunito', sans-serif !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        color: #1A1714 !important;
        box-shadow: 0 8px 24px rgba(0,0,0,.08) !important;
        margin-top: -2px !important;
    }
    div[data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #C8566A !important;
        box-shadow: 0 8px 24px rgba(200,86,106,.12) !important;
    }
    div[data-testid="stSelectbox"] ul {
        background: #fff !important;
        border: 2px solid #C8566A !important;
        border-radius: 12px !important;
        padding: 6px !important;
        box-shadow: 0 16px 40px rgba(0,0,0,.14) !important;
        font-family: 'Nunito', sans-serif !important;
    }
    div[data-testid="stSelectbox"] ul li {
        border-radius: 8px !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        padding: 10px 14px !important;
    }
    div[data-testid="stSelectbox"] ul li:hover {
        background: #FFF0F2 !important;
        color: #C8566A !important;
    }
    </style>
    """, unsafe_allow_html=True)

    opcoes  = ["— Selecione o operador —"] + OPERADORES
    idx_cur = 0
    if selecionado and selecionado in OPERADORES:
        idx_cur = OPERADORES.index(selecionado) + 1

    escolha = st.selectbox("op", opcoes,
                           index=idx_cur,
                           key=f"op_sel_{on_click_key}",
                           label_visibility="collapsed")

    if escolha and escolha != "— Selecione o operador —":
        if st.session_state.get("operador") != escolha:
            st.session_state.operador = escolha
            st.rerun()


# ─────────────────────────────────────
#  PiP — JANELA FLUTUANTE
# ─────────────────────────────────────
ETAPA_CORES = ["#C8566A", "#3B7DD8", "#4A7C59"]
ETAPA_ICONS = ["📦", "🗃️", "✅"]

def render_pip():
    """Renderiza janelas PiP flutuantes — só aparece para sessões com cronômetro ativo."""
    sessoes = buscar_todas_sessoes_ativas()
    if not sessoes:
        return

    cards_html = ""
    cards_js   = ""

    for s in sessoes:
        ped     = s.get("pedido", "")
        op      = s.get("operador", "")
        eta_idx = int(s.get("etapa_idx", 0))
        ini     = int(s.get("iniciado_em", 0))
        cor     = ETAPA_CORES[eta_idx]
        icon    = ETAPA_ICONS[eta_idx]
        lbl     = ETAPAS_LBL[eta_idx]
        uid     = f"{ped}_{eta_idx}"

        cards_html += f"""
        <div class="pip-card" id="pip-card-{uid}" style="border-top:3px solid {cor};">
          <!-- Header -->
          <div class="pip-drag-handle" id="pip-handle-{uid}">
            <span style="font-size:11px;opacity:0.5;flex-shrink:0;">⠿</span>
            <span style="font-size:10px;font-weight:800;letter-spacing:1px;opacity:0.7;flex:1;text-align:center;text-transform:uppercase;">{icon} {lbl}</span>
            <span class="pip-minimize" onclick="togglePip('{uid}')" title="Minimizar">─</span>
            <span class="pip-close-btn" onclick="pedirFechamento('{uid}','{ped}',{eta_idx},'{op}',{ini})" title="Fechar PiP">✕</span>
          </div>
          <!-- Body normal -->
          <div class="pip-body" id="pip-body-{uid}">
            <div style="font-size:11px;opacity:0.6;margin-bottom:2px;">Pedido <strong style="opacity:1;color:#fff;">{ped}</strong> · {op}</div>
            <div class="pip-timer" id="pip-timer-{uid}">00:00:00</div>
            <button class="pip-btn-fin" onclick="finalizarPip('{ped}',{eta_idx},'{op}',{ini})">&#9632; FINALIZAR</button>
          </div>
          <!-- Popup de confirmação (oculto por padrão) -->
          <div class="pip-confirm" id="pip-confirm-{uid}">
            <div class="pip-confirm-icon">⚠️</div>
            <div class="pip-confirm-msg">Fechar o PiP <strong>descarta o tempo</strong> sem salvar.<br>Tem certeza?</div>
            <div class="pip-confirm-btns">
              <button class="pip-confirm-yes" onclick="fecharPip('{uid}','{ped}',{eta_idx})">Sim, fechar</button>
              <button class="pip-confirm-no"  onclick="cancelarFechamento('{uid}')">Cancelar</button>
            </div>
          </div>
        </div>"""

        cards_js += f"startTimer('{uid}', {ini});\n"

    components.html(f"""
    <script>
    (function() {{
        var pd = window.parent.document;

        if (pd.getElementById('pip-container')) {{
            pd.getElementById('pip-container').remove();
        }}
        if (pd.getElementById('pip-styles')) {{
            pd.getElementById('pip-styles').remove();
        }}

        var style = pd.createElement('style');
        style.id = 'pip-styles';
        style.textContent = `
            #pip-container {{
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                pointer-events: none;
            }}
            .pip-card {{
                pointer-events: all;
                background: rgba(26,23,20,0.94);
                border-radius: 14px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.45);
                overflow: hidden;
                resize: both;
                min-width: 210px;
                min-height: 110px;
                width: 260px;
                backdrop-filter: blur(8px);
            }}
            .pip-drag-handle {{
                padding: 8px 12px;
                background: rgba(255,255,255,0.06);
                cursor: grab;
                display: flex;
                align-items: center;
                gap: 6px;
                color: rgba(255,255,255,0.65);
                user-select: none;
                font-family: 'Nunito', sans-serif;
            }}
            .pip-drag-handle:active {{ cursor: grabbing; }}
            .pip-minimize {{
                cursor: pointer;
                font-size: 14px;
                padding: 0 4px;
                opacity: 0.6;
            }}
            .pip-minimize:hover {{ opacity: 1; }}
            .pip-body {{
                padding: 10px 14px 14px;
                font-family: 'Nunito', sans-serif;
                color: #fff;
            }}
            .pip-timer {{
                font-family: 'DM Mono', 'Courier New', monospace;
                font-size: 34px;
                font-weight: 500;
                color: #fff;
                letter-spacing: -1px;
                margin: 6px 0 10px;
                line-height: 1;
            }}
            .pip-btn-fin {{
                width: 100%;
                background: #C8566A;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 9px 0;
                font-family: 'Nunito', sans-serif;
                font-size: 13px;
                font-weight: 800;
                cursor: pointer;
                letter-spacing: 0.5px;
            }}
            .pip-btn-fin:hover {{ background: #a83050; }}

            /* ── Botão X fechar ── */
            .pip-close-btn {{
                cursor: pointer;
                font-size: 13px;
                padding: 0 2px 0 6px;
                opacity: 0.45;
                color: #fff;
                flex-shrink: 0;
                line-height: 1;
                transition: opacity .15s, color .15s;
            }}
            .pip-close-btn:hover {{ opacity: 1; color: #FF6B6B; }}

            /* ── Popup de confirmação ── */
            .pip-confirm {{
                display: none;
                padding: 16px 14px 14px;
                font-family: 'Nunito', sans-serif;
                color: #fff;
                text-align: center;
                animation: fadeIn .15s ease;
            }}
            @keyframes fadeIn {{ from{{opacity:0;transform:translateY(4px)}} to{{opacity:1;transform:translateY(0)}} }}
            .pip-confirm-icon {{ font-size: 26px; margin-bottom: 8px; }}
            .pip-confirm-msg {{
                font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.8);
                line-height: 1.55; margin-bottom: 14px;
            }}
            .pip-confirm-msg strong {{ color: #FF6B6B; }}
            .pip-confirm-btns {{ display: flex; gap: 8px; }}
            .pip-confirm-yes {{
                flex: 1; background: rgba(200,86,106,0.25); color: #FF8FA3;
                border: 1.5px solid rgba(200,86,106,0.5); border-radius: 8px;
                padding: 8px 0; font-family: 'Nunito', sans-serif;
                font-size: 12px; font-weight: 800; cursor: pointer;
                transition: background .15s;
            }}
            .pip-confirm-yes:hover {{ background: #C8566A; color: #fff; border-color: #C8566A; }}
            .pip-confirm-no {{
                flex: 1; background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.65);
                border: 1.5px solid rgba(255,255,255,0.15); border-radius: 8px;
                padding: 8px 0; font-family: 'Nunito', sans-serif;
                font-size: 12px; font-weight: 800; cursor: pointer;
                transition: background .15s;
            }}
            .pip-confirm-no:hover {{ background: rgba(255,255,255,0.14); color: #fff; }}
        `;
        pd.head.appendChild(style);

        var container = pd.createElement('div');
        container.id = 'pip-container';
        container.innerHTML = `{cards_html}`;
        pd.body.appendChild(container);

        window.parent.startTimer = function(uid, iniciado_em) {{
            var el = pd.getElementById('pip-timer-' + uid);
            if (!el) return;
            function update() {{
                var elapsed = Math.floor(Date.now() / 1000) - iniciado_em;
                var h = Math.floor(elapsed / 3600);
                var m = Math.floor((elapsed % 3600) / 60);
                var s = elapsed % 60;
                el.textContent =
                    String(h).padStart(2,'0') + ':' +
                    String(m).padStart(2,'0') + ':' +
                    String(s).padStart(2,'0');
            }}
            update();
            setInterval(update, 1000);
        }};

        window.parent.finalizarPip = function(pedido, etapa, operador, iniciado_em) {{
            var url = new URL(window.parent.location.href);
            url.searchParams.set('pip_action', 'finalizar');
            url.searchParams.set('pedido', pedido);
            url.searchParams.set('etapa', etapa);
            url.searchParams.set('operador', operador);
            url.searchParams.set('iniciado_em', iniciado_em);
            window.parent.location.href = url.toString();
        }};

        window.parent.togglePip = function(uid) {{
            var body = pd.getElementById('pip-body-' + uid);
            if (!body) return;
            body.style.display = body.style.display === 'none' ? 'block' : 'none';
        }};

        /* Abre o popup de confirmação de fechamento */
        window.parent.pedirFechamento = function(uid, pedido, etapa, operador, iniciado_em) {{
            var body    = pd.getElementById('pip-body-' + uid);
            var confirm = pd.getElementById('pip-confirm-' + uid);
            if (!body || !confirm) return;
            body.style.display    = 'none';
            confirm.style.display = 'block';
        }};

        /* Usuário confirmou — remove do DOM + chama endpoint para deletar sessão */
        window.parent.fecharPip = function(uid, pedido, etapa) {{
            var card = pd.getElementById('pip-card-' + uid);
            if (card) {{
                card.style.transition = 'opacity .2s, transform .2s';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.92)';
                setTimeout(function() {{ if (card) card.remove(); }}, 220);
            }}
            // Redireciona com ação de fechar (sem salvar tempo)
            var url = new URL(window.parent.location.href);
            url.searchParams.set('pip_action', 'fechar');
            url.searchParams.set('pedido', pedido);
            url.searchParams.set('etapa', etapa);
            window.parent.location.href = url.toString();
        }};

        /* Usuário cancelou — volta ao body normal */
        window.parent.cancelarFechamento = function(uid) {{
            var body    = pd.getElementById('pip-body-' + uid);
            var confirm = pd.getElementById('pip-confirm-' + uid);
            if (!body || !confirm) return;
            confirm.style.display = 'none';
            body.style.display    = 'block';
        }};

        pd.querySelectorAll('.pip-drag-handle').forEach(function(handle) {{
            var card = handle.closest('.pip-card');
            var dragging = false, sx, sy, ox, oy;
            handle.addEventListener('mousedown', function(e) {{
                dragging = true;
                sx = e.clientX; sy = e.clientY;
                var rect = card.getBoundingClientRect();
                ox = rect.left; oy = rect.top;
                card.style.position = 'fixed';
                card.style.left = ox + 'px';
                card.style.top  = oy + 'px';
                card.style.margin = '0';
                e.preventDefault();
            }});
            pd.addEventListener('mousemove', function(e) {{
                if (!dragging) return;
                card.style.left = (ox + e.clientX - sx) + 'px';
                card.style.top  = (oy + e.clientY - sy) + 'px';
            }});
            pd.addEventListener('mouseup', function() {{ dragging = false; }});
        }});

        pd.querySelectorAll('.pip-drag-handle').forEach(function(handle) {{
            var card = handle.closest('.pip-card');
            var ox, oy, sx, sy;
            handle.addEventListener('touchstart', function(e) {{
                var t = e.touches[0];
                sx = t.clientX; sy = t.clientY;
                var rect = card.getBoundingClientRect();
                ox = rect.left; oy = rect.top;
                card.style.position = 'fixed';
                card.style.left = ox + 'px';
                card.style.top  = oy + 'px';
                card.style.margin = '0';
            }}, {{passive:true}});
            handle.addEventListener('touchmove', function(e) {{
                var t = e.touches[0];
                card.style.left = (ox + t.clientX - sx) + 'px';
                card.style.top  = (oy + t.clientY - sy) + 'px';
                e.preventDefault();
            }}, {{passive:false}});
        }});

        {cards_js}
    }})();
    </script>
    """, height=0, scrolling=False)


# ─────────────────────────────────────
#  TELA: HOME
# ─────────────────────────────────────
def _render_status_pedido(num, status, etapa_idx):
    num    = st.session_state.get("_pedido_validando", "")
    status = st.session_state.get("_status_cache") or buscar_status_completo_pedido(num)
    render_stepper(etapa_idx)

    base_st   = status["base_status"]
    cliente   = status.get("cliente", "")
    etapas    = status["etapas"]
    etapa_lbl = ETAPAS_LBL[etapa_idx]
    etapa_info = etapas[etapa_idx]  # dados da etapa que foi selecionada

    COR = ["#C8566A", "#3B7DD8", "#4A7C59"]

    # ── Header do pedido ─────────────────────────────────────────────────
    cor_h = COR[etapa_idx]
    import streamlit.components.v1 as _cv1
    _cv1.html(f"""
    <style>*{{margin:0;padding:0;box-sizing:border-box;}}
    body{{font-family:'Nunito',sans-serif;background:transparent;}}</style>
    <div style="background:linear-gradient(135deg,{cor_h},{cor_h}bb);
                border-radius:14px;padding:14px 18px;display:flex;
                align-items:center;gap:14px;">
      <div>
        <div style="font-size:9px;font-weight:800;letter-spacing:2px;
             color:rgba(255,255,255,0.55);text-transform:uppercase;">Pedido</div>
        <div style="font-size:22px;font-weight:900;color:#fff;
             font-family:monospace;">#{num}</div>
        {(f'<div style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:1px;">{cliente}</div>') if cliente else ""}
      </div>
      <div style="margin-left:auto;text-align:right;">
        <div style="font-size:9px;font-weight:800;letter-spacing:2px;
             color:rgba(255,255,255,0.55);text-transform:uppercase;">Etapa atual</div>
        <div style="font-size:14px;font-weight:800;color:#fff;">{etapa_lbl}</div>
      </div>
    </div>""", height=74, scrolling=False)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── CASO 1: Pedido não encontrado ────────────────────────────────────
    if base_st == "nao_encontrado":
        _cv1.html("""
        <div style="background:#FFFBEB;border:2px solid #F59E0B;border-radius:14px;
                    padding:20px;text-align:center;font-family:sans-serif;">
          <div style="font-size:28px;margin-bottom:8px;">❓</div>
          <div style="font-size:14px;font-weight:800;color:#92400E;">Pedido não encontrado na base</div>
          <div style="font-size:12px;color:#B45309;margin-top:4px;font-weight:600;">
            Deseja cadastrá-lo como pedido avulso?</div>
        </div>""", height=110, scrolling=False)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("✓ Cadastrar e Continuar", use_container_width=True):
                cadastrar_pedido_avulso(num)
                st.session_state.pedido          = num
                st.session_state.pedido_status   = None
                st.session_state.pedido_validado = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("✕ Cancelar", use_container_width=True):
                st.session_state.pedido_status = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Timeline resumida das 3 etapas ───────────────────────────────────
    tl_html = '<div style="display:flex;gap:0;margin-bottom:12px;">'
    for e in etapas:
        if e["feita"]:
            bg_c, txt_c, ic = "#4A7C59", "#fff", "✓"
        elif e["em_andamento"]:
            bg_c, txt_c, ic = "#E07B3A", "#fff", "⏱"
        else:
            bg_c, txt_c, ic = "#EDE9E4", "#9C9490", str(e["idx"]+1)
        brd = "3px solid #1A1714" if e["idx"] == etapa_idx else "none"
        tl_html += f'''<div style="flex:1;background:{bg_c};padding:8px 4px;
            text-align:center;outline:{brd};position:relative;">
          <div style="font-size:16px;">{ic}</div>
          <div style="font-size:9px;font-weight:800;color:{txt_c};
               opacity:0.85;margin-top:2px;letter-spacing:.5px;">{e["label"].split()[0].upper()}</div>
        </div>'''
    tl_html += '</div>'
    _cv1.html(f"""<style>*{{margin:0;padding:0;box-sizing:border-box;}}
    body{{font-family:sans-serif;background:transparent;}}</style>
    <div style="border-radius:12px;overflow:hidden;border:1.5px solid #EDE9E4;">
      {tl_html}
    </div>""", height=68, scrolling=False)

    # ── CASO 2: Pedido totalmente concluído ──────────────────────────────
    if base_st == "concluido":
        _cv1.html("""
        <div style="background:#F0F7F3;border:2px solid #4A7C59;border-radius:14px;
                    padding:20px;text-align:center;font-family:sans-serif;">
          <div style="font-size:28px;margin-bottom:8px;">🎉</div>
          <div style="font-size:14px;font-weight:800;color:#2d5a3d;">Pedido totalmente concluído!</div>
          <div style="font-size:12px;color:#4A7C59;margin-top:4px;font-weight:600;">
            Todas as 3 etapas foram finalizadas com sucesso.</div>
        </div>""", height=110, scrolling=False)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("← Buscar outro pedido", use_container_width=True):
            st.session_state.pedido_status = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── CASO 3: Esta etapa está EM ANDAMENTO agora ───────────────────────
    if etapa_info["em_andamento"]:
        op_and     = etapa_info["operador"]
        ini_ts     = etapa_info["iniciado_em"]
        elapsed, _ = fmt_elapsed(ini_ts) if ini_ts else ("--:--:--", 0)
        _cv1.html(f"""
        <style>*{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:'Nunito',sans-serif;background:transparent;}}</style>
        <div style="background:#FFF8F0;border:2px solid #E07B3A;border-radius:14px;padding:18px 20px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <div style="font-size:24px;">⏱</div>
            <div>
              <div style="font-size:14px;font-weight:900;color:#9A3412;">Em andamento agora</div>
              <div style="font-size:12px;color:#C2410C;font-weight:600;">
                Etapa: <strong>{etapa_lbl}</strong> &nbsp;·&nbsp; Operador: <strong>{op_and}</strong></div>
            </div>
            <div style="margin-left:auto;font-family:monospace;font-size:26px;
                 font-weight:500;color:#E07B3A;">{elapsed}</div>
          </div>
          <div style="font-size:13px;color:#7C2D12;font-weight:700;text-align:center;
               background:rgba(224,123,58,0.08);border-radius:8px;padding:8px;">
            Deseja finalizar o temporizador deste pedido?
          </div>
        </div>""", height=130, scrolling=False)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="btn-finalizar">', unsafe_allow_html=True)
            if st.button("■  Sim, Finalizar", use_container_width=True):
                tempo = max(int(time.time()) - int(ini_ts), 1)
                salvar(num, op_and, ETAPAS[etapa_idx], etapa_idx, tempo)
                remover_sessao_ativa(num, etapa_idx)
                if etapa_idx == 2:
                    marcar_concluido(num)
                st.toast(f"✅ {op_and} · Pedido #{num} finalizado em {fmt(tempo)}!", icon="🎉")
                st.session_state.pedido_status = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("✕ Não", use_container_width=True):
                st.session_state.pedido_status = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── CASO 4: Esta etapa já foi finalizada ─────────────────────────────
    if etapa_info["feita"]:
        op_fin   = etapa_info["operador"]
        tempo_fin = fmt(etapa_info["tempo"]) if etapa_info["tempo"] else "—"
        data_fin  = etapa_info["data"] or ""
        prox_idx  = etapa_idx + 1
        tem_prox  = prox_idx < len(ETAPAS_LBL)
        prox_lbl  = ETAPAS_LBL[prox_idx] if tem_prox else ""
        _cv1.html(f"""
        <style>*{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:'Nunito',sans-serif;background:transparent;}}</style>
        <div style="background:#F0F7F3;border:2px solid #4A7C59;border-radius:14px;padding:18px 20px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <div style="font-size:24px;">✅</div>
            <div>
              <div style="font-size:14px;font-weight:900;color:#2d5a3d;">Etapa já finalizada</div>
              <div style="font-size:12px;color:#4A7C59;font-weight:600;">
                <strong>{etapa_lbl}</strong> &nbsp;·&nbsp; por <strong>{op_fin}</strong>
                &nbsp;·&nbsp; {tempo_fin}</div>
            </div>
            <div style="margin-left:auto;font-size:11px;color:#9C9490;text-align:right;">{data_fin}</div>
          </div>
          {(f'<div style="font-size:13px;color:#2d5a3d;font-weight:700;text-align:center;background:rgba(74,124,89,0.08);border-radius:8px;padding:8px;">Deseja ir para a próxima etapa: <strong>{prox_lbl}</strong>?</div>') if tem_prox else
           '<div style="font-size:13px;color:#2d5a3d;font-weight:700;text-align:center;background:rgba(74,124,89,0.08);border-radius:8px;padding:8px;">Este pedido já passou por todas as etapas.</div>'}
        </div>""", height=130, scrolling=False)
        if tem_prox:
            ca, cb = st.columns(2)
            with ca:
                st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
                if st.button(f"▶  Sim, ir para {prox_lbl}", use_container_width=True):
                    st.session_state.etapa_escolhida = prox_idx
                    st.session_state.pedido          = num
                    st.session_state.pedido_status   = None
                    st.session_state.pedido_validado = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with cb:
                st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
                if st.button("✕ Não", use_container_width=True):
                    st.session_state.pedido_status = None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("← Buscar outro pedido", use_container_width=True):
                st.session_state.pedido_status = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── CASO 5: Etapa anterior não concluída ─────────────────────────────
    if etapa_idx > 0 and not etapas[etapa_idx - 1]["feita"] and not etapas[etapa_idx - 1]["em_andamento"]:
        et_ant = ETAPAS_LBL[etapa_idx - 1]
        _cv1.html(f"""
        <div style="background:#FEF2F2;border:2px solid #FCA5A5;border-radius:14px;
                    padding:20px;text-align:center;font-family:sans-serif;">
          <div style="font-size:28px;margin-bottom:8px;">🔒</div>
          <div style="font-size:14px;font-weight:800;color:#991B1B;">Etapa bloqueada</div>
          <div style="font-size:12px;color:#B91C1C;margin-top:4px;font-weight:600;">
            A etapa anterior (<strong>{et_ant}</strong>) ainda não foi concluída.</div>
        </div>""", height=110, scrolling=False)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True):
            st.session_state.pedido_status = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── CASO 6: Pronto para iniciar ──────────────────────────────────────
    _cv1.html(f"""
    <div style="background:#F0F7F3;border:2px solid #4A7C59;border-radius:14px;
                padding:16px 20px;text-align:center;font-family:sans-serif;">
      <div style="font-size:24px;margin-bottom:6px;">✅</div>
      <div style="font-size:14px;font-weight:800;color:#2d5a3d;">
        Pedido pronto para <strong>{etapa_lbl}</strong></div>
      <div style="font-size:12px;color:#4A7C59;margin-top:4px;font-weight:600;">
        Selecione o operador e inicie o processo.</div>
    </div>""", height=100, scrolling=False)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
        if st.button("▶  Continuar", use_container_width=True):
            st.session_state.pedido          = num
            st.session_state.pedido_status   = None
            st.session_state.pedido_validado = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with cb:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True):
            st.session_state.pedido_status = None; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    return


def tela_home():
    render_logo()

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

        # ── Botão de Operações em Andamento ──────────────────────────────────
        sessoes_ativas_agora = buscar_todas_sessoes_ativas()
        n_sess = len(sessoes_ativas_agora)
        if n_sess > 0:
            st.markdown(f"""
            <style>
            .btn-andamento > button {{
                background: linear-gradient(135deg, #1c1917, #2d2925) !important;
                color: #fff !important; border: none !important;
                border-radius: 14px !important; height: 64px !important;
                font-size: 15px !important; font-weight: 800 !important;
                box-shadow: 0 5px 0 rgba(0,0,0,0.40), 0 8px 20px rgba(0,0,0,0.20) !important;
                position: relative !important;
            }}
            .btn-andamento > button:hover {{
                background: linear-gradient(135deg, #292524, #3d3530) !important;
                transform: translateY(-2px) !important;
            }}
            </style>
            <div style="position:relative;margin-bottom:8px;">
              <div style="position:absolute;top:-10px;right:12px;z-index:10;
                background:#C8566A;color:#fff;font-size:11px;font-weight:900;
                padding:3px 10px;border-radius:20px;border:2px solid #F7F5F2;
                letter-spacing:.5px;">
                {n_sess} em andamento
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown('<div class="btn-andamento">', unsafe_allow_html=True)
            if st.button("⏱  Ver Operações em Andamento", use_container_width=True):
                st.session_state.tela = "operacoes"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        _, col_c, _ = st.columns([2, 1, 2])
        with col_c:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("⚙ Admin", use_container_width=True):
                st.session_state.tela = "admin_login"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    etapa_idx = st.session_state.etapa_escolhida
    etapa_lbl = ETAPAS_LBL[etapa_idx]

    # ── PASSO 2: Digitar Pedido + BUSCAR ─────────────────────────────────────
    if not st.session_state.pedido_validado:

        # ── Se status já foi carregado, renderiza painel e sai ──────────────
        if st.session_state.pedido_status in ("mostrar_status", "mostrar_status_ok"):
            num    = st.session_state.get("_pedido_validando", "")
            # Garante que os dados estão carregados
            if st.session_state.pedido_status == "mostrar_status":
                st.session_state["_status_cache"] = buscar_status_completo_pedido(num)
                st.session_state.pedido_status    = "mostrar_status_ok"
            status = st.session_state.get("_status_cache") or buscar_status_completo_pedido(num)
            _render_status_pedido(num, status, etapa_idx)
            return

        render_stepper(etapa_idx)
        st.markdown(
            f'<div style="background:#F5E8EB;border-left:4px solid #C8566A;border-radius:0 10px 10px 0;'
            f'padding:10px 16px;margin-bottom:20px;font-size:14px;font-weight:700;color:#1A1714;">'
            f'Etapa selecionada: <strong>{etapa_lbl}</strong></div>',
            unsafe_allow_html=True
        )
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <div style="flex:1;height:1px;background:#EDE9E4;"></div>
            <div style="font-size:11px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;
                color:#9C9490;white-space:nowrap;">Nº do Pedido</div>
            <div style="flex:1;height:1px;background:#EDE9E4;"></div>
        </div>
        """, unsafe_allow_html=True)

        pedidos_etapa   = buscar_pedidos_por_etapa(etapa_idx)
        pedidos_abertos = [p[0] for p in pedidos_etapa]
        pedidos_info    = {p[0]: p[1] for p in pedidos_etapa}
        has_base        = len(pedidos_etapa) > 0

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
            if not pedidos_abertos:
                import streamlit.components.v1 as _cv1
                _cv1.html(
                    f'<div style="background:#FEF3C7;border:1px solid #F59E0B;border-radius:10px;'
                    f'padding:10px 14px;font-family:sans-serif;font-size:12px;font-weight:700;color:#92400E;text-align:center;">'
                    f'⚠ Nenhum pedido aguardando {etapa_lbl} no momento.</div>',
                    height=50, scrolling=False
                )

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
            if st.button("← Buscar outro pedido"):
                st.session_state.pedido_status = None; st.rerun()
            return

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
                    st.session_state.pedido_status  = None
                    st.session_state.pedido         = num_pend
                    st.session_state.pedido_validado = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with cc2:
                st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
                if st.button("✕ Cancelar", use_container_width=True):
                    st.session_state.pedido_status = None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            return

        if st.session_state.duplicata_info:
            info   = st.session_state.duplicata_info
            op_ant = info["operador_anterior"]
            etl    = ETAPAS_LBL[etapa_idx]
            msg_tp = "está sendo processado agora" if info["em_andamento"] else "já passou pela fase de"
            import streamlit.components.v1 as _cv1
            _cv1.html(
                f'<div style="background:#FFF7ED;border:2px solid #F97316;border-radius:14px;'
                f'padding:18px 22px;font-family:sans-serif;margin:8px 0;">'
                f'<div style="font-size:22px;text-align:center;margin-bottom:8px;">⚠️</div>'
                f'<div style="font-size:14px;font-weight:800;color:#9A3412;text-align:center;margin-bottom:8px;">Atenção — Pedido em Conflito</div>'
                f'<div style="font-size:13px;color:#7C2D12;font-weight:600;text-align:center;line-height:1.6;">'
                f'Pedido {info["pedido"]} {msg_tp} <b>{etl}</b>'
                f'{(" (por " + op_ant + ")") if op_ant else ""}.<br><br>'
                f'Deseja mesmo assim prosseguir?</div>'
                f'</div>',
                height=175, scrolling=False
            )
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
                if st.button("✓ Sim, prosseguir", use_container_width=True):
                    st.session_state.pedido          = info["pedido"]
                    st.session_state.duplicata_info  = None
                    st.session_state.pedido_validado = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with cc2:
                st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
                if st.button("✕ Não", use_container_width=True):
                    st.session_state.duplicata_info = None; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            return

        st.markdown("<br>", unsafe_allow_html=True)
        c1, _, c2 = st.columns([3, 0.3, 1.5])
        with c1:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("🔍  BUSCAR", use_container_width=True, key="home_buscar"):
                num = pedido_inp.strip() if isinstance(pedido_inp, str) else ""
                if not num:
                    st.session_state.erro_pedido = True; st.rerun()
                st.session_state.erro_pedido       = False
                st.session_state._pedido_validando = num
                st.session_state.pedido_status     = "mostrar_status"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("← Voltar", use_container_width=True, key="home_ped_voltar"):
                st.session_state.etapa_escolhida = None
                st.session_state.pedido_status   = None; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.erro_pedido:
            st.markdown(
                '<div style="text-align:center;color:#C8566A;font-size:13px;font-weight:800;margin-top:6px;">'
                '⚠ Selecione ou digite o número do pedido.</div>',
                unsafe_allow_html=True
            )
        return


    # ── PASSO 3: Selecionar Operador ─────────────────────────────────────────
    pedido_val   = st.session_state.pedido
    pedidos_etapa = buscar_pedidos_por_etapa(etapa_idx)
    pedidos_info  = {p[0]: p[1] for p in pedidos_etapa}
    if pedido_val not in pedidos_info:
        _rows = _get("pedidos_base", f"numero=eq.{pedido_val}&select=cliente")
        if _rows: pedidos_info[pedido_val] = _rows[0].get("cliente", "")
    cli_nome = pedidos_info.get(pedido_val, "")

    render_stepper(etapa_idx)

    import streamlit.components.v1 as _cv1
    _cv1.html(
        f'<div style="background:#F0F7F3;border:1.5px solid #4A7C59;border-radius:12px;'
        f'padding:12px 18px;font-family:sans-serif;display:flex;align-items:center;gap:14px;margin-bottom:4px;">'
        f'<div style="width:38px;height:38px;border-radius:50%;background:#4A7C59;flex-shrink:0;'
        f'display:flex;align-items:center;justify-content:center;font-size:18px;">✓</div>'
        f'<div>'
        f'<div style="font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#4A7C59;margin-bottom:2px;">Pedido Encontrado</div>'
        f'<div style="font-size:16px;font-weight:900;color:#1A1714;font-family:monospace;">{pedido_val}'
        f'{"  · " + cli_nome if cli_nome else ""}</div>'
        f'<div style="font-size:11px;color:#9C9490;margin-top:2px;">Etapa: {etapa_lbl}</div>'
        f'</div></div>',
        height=80, scrolling=False
    )

    st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <div style="flex:1;height:1px;background:#EDE9E4;"></div>
        <div style="font-size:11px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;
            color:#9C9490;white-space:nowrap;">Identificar Operador</div>
        <div style="flex:1;height:1px;background:#EDE9E4;"></div>
    </div>
    """, unsafe_allow_html=True)

    render_avatar_grid(on_click_key="op_step3")

    if st.session_state.operador:
        st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)
        _, col_ini, _ = st.columns([0.3, 4, 0.3])
        with col_ini:
            st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
            if st.button("▶  INICIAR OPERAÇÃO", use_container_width=True, key="home_iniciar_op"):
                # ✅ CORREÇÃO: NÃO registra sessão ativa aqui.
                # A sessão só é registrada quando o operador clicar em
                # "INICIAR CRONÔMETRO" na tela de produção.
                # Isso garante que o PiP só aparece com o cronômetro rodando.
                st.session_state.etapa_idx       = etapa_idx
                st.session_state.rodando         = False
                st.session_state.inicio          = None
                st.session_state.acum            = 0
                st.session_state.modal           = None
                st.session_state.tela            = "producao"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    _, col_v, _ = st.columns([2, 2, 2])
    with col_v:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True, key="home_op_voltar"):
            st.session_state.pedido_validado = False
            st.session_state.pedido          = None
            st.session_state.operador        = None; st.rerun()
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

    st.markdown("<br style='line-height:0.5'>", unsafe_allow_html=True)

    # ── Card info + botão INICIAR CRONÔMETRO ──
    if not st.session_state.rodando and st.session_state.acum == 0 and not st.session_state.modal:
        pedido_val = st.session_state.pedido or ""
        initial    = op[0].upper()

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
                # ✅ SESSÃO REGISTRADA AQUI — único momento correto.
                # O PiP só aparece a partir deste ponto.
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
                # Sem sessão ativa registrada, nada para remover.
                # Limpa estado e volta ao lobby.
                st.session_state.pedido          = None
                st.session_state.pedido_status   = None
                st.session_state.pedido_validado = False
                st.session_state.operador        = None
                st.session_state.etapa_escolhida = None
                st.session_state.tela            = "home"
                st.rerun()
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

        # ── Botões: Voltar ao painel / Finalizar ──
        col_back, col_fin2 = st.columns([1, 2])
        with col_back:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("⊞  Painel", use_container_width=True,
                         help="Volta ao painel sem perder o cronômetro"):
                # Mantém sessão ativa — aparece no painel de operações
                st.session_state.rodando         = False
                st.session_state.inicio          = None
                st.session_state.acum            = 0
                st.session_state.pedido          = None
                st.session_state.pedido_validado = False
                st.session_state.operador        = None
                st.session_state.etapa_escolhida = None
                st.session_state.tela            = "operacoes"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        _, col_fin, _ = st.columns([0.5, 5, 0.5])
        with col_fin:
            st.markdown('<div class="btn-finalizar">', unsafe_allow_html=True)
            if st.button("■  FINALIZAR ETAPA", use_container_width=True):
                tempo = get_elapsed()
                st.session_state.acum    = tempo
                st.session_state.rodando = False
                st.session_state.inicio  = None
                salvar(st.session_state.pedido, op, ETAPAS[etapa_idx], etapa_idx, tempo)
                remover_sessao_ativa(st.session_state.pedido, etapa_idx)
                if etapa_idx == 2:
                    marcar_concluido(st.session_state.pedido)
                    st.session_state.modal = "concluido"
                else:
                    st.session_state.modal = "proxima"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        _, col_menu, _ = st.columns([0.5, 5, 0.5])
        with col_menu:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            if st.button("← Voltar ao Menu", use_container_width=True, key="voltar_menu_rodando"):
                # Remove sessão ativa e volta ao menu principal
                remover_sessao_ativa(st.session_state.pedido, etapa_idx)
                st.session_state.rodando         = False
                st.session_state.inicio          = None
                st.session_state.acum            = 0
                st.session_state.pedido          = None
                st.session_state.pedido_status   = None
                st.session_state.pedido_validado = False
                st.session_state.operador        = None
                st.session_state.etapa_escolhida = None
                st.session_state.tela            = "home"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        time.sleep(1); st.rerun()

    # ── Modal: próxima etapa ──
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
        if st.button("▶  Próximo Pedido", use_container_width=True, key="proxima_home"):
            st.session_state.modal          = None
            st.session_state.pedido         = None
            st.session_state.pedido_validado = False
            st.session_state.etapa_idx      = 0
            st.session_state.acum           = 0
            st.session_state.tela           = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Modal: pedido concluído ──
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
                    <span style="font-size:11px;font-weight:800;letter-spacing:1.5px;color:#4A7C59;text-transform:uppercase;">Conferência</span>
                    <span style="font-family:monospace;font-size:17px;font-weight:800;color:#4A7C59;">{tempo_fmt}</span>
                </div>
            </div>
        </div>
        </body></html>
        """, height=300, scrolling=False)
        st.markdown("<br style='line-height:0.2'>", unsafe_allow_html=True)
        st.markdown('<div class="btn-iniciar">', unsafe_allow_html=True)
        if st.button("▶  Próximo Pedido", use_container_width=True):
            st.session_state.modal          = None
            st.session_state.pedido         = None
            st.session_state.pedido_validado = False
            st.session_state.etapa_idx      = 0
            st.session_state.acum           = 0
            st.session_state.tela           = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────
#  TELA: ADMIN LOGIN
# ─────────────────────────────────────
def tela_admin_login():
    render_logo()

    erro = st.session_state.erro_senha

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
        border-radius: 24px; overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 2px 0 rgba(255,255,255,0.04) inset, 0 -1px 0 rgba(0,0,0,0.5) inset,
                    0 20px 60px rgba(0,0,0,0.5), 0 8px 20px rgba(0,0,0,0.3);
        position: relative;
      }
      .orb { position:absolute; border-radius:50%; filter:blur(60px); opacity:0.15; animation:pulse 4s ease-in-out infinite; }
      .orb-1 { width:220px; height:220px; background:#C8566A; top:-60px; right:-60px; animation-delay:0s; }
      .orb-2 { width:160px; height:160px; background:#9E3F52; bottom:-40px; left:-40px; animation-delay:2s; }
      @keyframes pulse { 0%,100%{opacity:.12;transform:scale(1);} 50%{opacity:.22;transform:scale(1.1);} }
      .card-inner { position:relative; z-index:1; padding:36px 32px 32px; }
      .icon-wrap {
        width:64px; height:64px; border-radius:18px;
        background:linear-gradient(145deg,#C8566A,#7A2D3E);
        display:flex; align-items:center; justify-content:center;
        margin:0 auto 22px;
        box-shadow: 0 0 0 1px rgba(200,86,106,0.3), 0 8px 24px rgba(200,86,106,0.4), inset 0 1px 0 rgba(255,255,255,0.15);
        animation:icon-glow 3s ease-in-out infinite;
      }
      @keyframes icon-glow {
        0%,100%{box-shadow:0 0 0 1px rgba(200,86,106,0.3),0 8px 24px rgba(200,86,106,0.4),inset 0 1px 0 rgba(255,255,255,0.15);}
        50%{box-shadow:0 0 0 4px rgba(200,86,106,0.15),0 8px 32px rgba(200,86,106,0.6),inset 0 1px 0 rgba(255,255,255,0.15);}
      }
      .title-area { text-align:center; margin-bottom:28px; }
      .eyebrow { font-size:10px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:rgba(255,255,255,0.35); margin-bottom:6px; }
      .title { font-size:26px; font-weight:800; color:#fff; letter-spacing:-0.5px; line-height:1.1; }
      .subtitle { font-size:13px; color:rgba(255,255,255,0.4); margin-top:6px; font-weight:500; }
      .divider { height:1px; background:linear-gradient(90deg,transparent,rgba(200,86,106,0.4),rgba(255,255,255,0.08),transparent); margin-bottom:24px; }
      .status-bar { display:flex; align-items:center; justify-content:center; gap:20px; padding:12px 0 4px; }
      .status-item { display:flex; align-items:center; gap:6px; }
      .dot { width:7px; height:7px; border-radius:50%; animation:blink 2s ease-in-out infinite; }
      .dot-green { background:#4ade80; box-shadow:0 0 8px #4ade80; }
      .dot-amber { background:#C8566A; animation-delay:1s; }
      @keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
      .status-text { font-size:11px; font-weight:600; color:rgba(255,255,255,0.35); letter-spacing:0.5px; }
      .scanline { position:absolute; top:0; left:0; right:0; bottom:0;
        background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,0.01) 2px,rgba(255,255,255,0.01) 4px);
        pointer-events:none; border-radius:24px; z-index:0; }
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
          <div class="status-item"><div class="dot dot-green"></div><span class="status-text">Sistema Online</span></div>
          <div class="status-item"><div class="dot dot-amber"></div><span class="status-text">Autenticação Necessária</span></div>
        </div>
      </div>
    </div>
    </body>
    </html>
    """, height=330, scrolling=False)

    st.markdown("<br>", unsafe_allow_html=True)

    border_color = "#C8566A" if erro else "#E0DBD4"
    shadow = "0 0 0 4px rgba(200,86,106,0.12)" if erro else "0 3px 12px rgba(0,0,0,0.06)"

    st.markdown(f"""
    <style>
    div[data-testid="stTextInput"] label {{ display:none !important; }}
    div[data-testid="stTextInput"] input {{
        text-align:center !important; font-size:22px !important; font-weight:700 !important;
        letter-spacing:8px !important; color:#1A1714 !important; height:62px !important;
        border:2px solid {border_color} !important; border-radius:14px !important;
        background:#fff !important; box-shadow:{shadow} !important;
        padding:0 20px !important; font-family:'DM Mono',monospace !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color:#D0CAC4 !important; font-weight:500 !important;
        letter-spacing:4px !important; font-size:18px !important;
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
        .btn-ghost > button { background:transparent !important; color:#5C5450 !important;
            border:1.5px solid #DDD8D2 !important; font-size:13px !important; }
        .btn-ghost > button:hover { border-color:#9C9490 !important; color:#1A1714 !important; }
        </style>""", unsafe_allow_html=True)
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=True):
            st.session_state.erro_senha = False; st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <style>
        .btn-admin-dark > button {
            background:linear-gradient(135deg,#1c1917,#292524) !important;
            color:#fff !important; border:none !important;
            box-shadow:0 5px 0 rgba(0,0,0,0.50),0 10px 24px rgba(0,0,0,0.25) !important;
            font-size:14px !important; letter-spacing:0.8px !important;
            border-top:1px solid rgba(255,255,255,0.08) !important;
        }
        .btn-admin-dark > button:hover {
            background:linear-gradient(135deg,#292524,#3d3530) !important;
            transform:translateY(-2px) !important;
        }
        .btn-admin-dark > button:active { transform:translateY(3px) !important; }
        </style>""", unsafe_allow_html=True)
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

    ROSA   = colors.HexColor("#C8566A")
    ESCURO = colors.HexColor("#1A1714")
    CLARO  = colors.HexColor("#F7F5F2")
    CINZA  = colors.HexColor("#8C8480")
    VERDE  = colors.HexColor("#4A7C59")
    BEGE   = colors.HexColor("#EDE9E4")
    BRANCO = colors.white

    styles = getSampleStyleSheet()

    def sty(name, **kw):
        return ParagraphStyle(name, **kw)

    S_TITLE   = sty("t",  fontName="Helvetica-Bold", fontSize=22, textColor=ESCURO, spaceAfter=2)
    S_SUB     = sty("s",  fontName="Helvetica",      fontSize=10, textColor=CINZA,  spaceAfter=0)
    S_SECTION = sty("sc", fontName="Helvetica-Bold", fontSize=9,  textColor=CINZA,
                    spaceAfter=6, spaceBefore=16, letterSpacing=1.5)
    S_FOOTER  = sty("f",  fontName="Helvetica",      fontSize=8,  textColor=CINZA, alignment=TA_CENTER)

    story = []
    now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")

    header_data = [[
        Paragraph("<b><font color='#C8566A' size='18'>Vi</font> LINGERIE</b>", styles["Normal"]),
        Paragraph(f"<font color='#8C8480' size='8'>Gerado em {now_str}</font>",
                  ParagraphStyle("r", alignment=TA_RIGHT))
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

    story.append(Paragraph("RESUMO GERAL", S_SECTION))
    kpi_data = [[
        Paragraph(f"<b><font size='22' color='#C8566A'>{len(ped_comp)}</font></b><br/><font size='8' color='#8C8480'>PEDIDOS CONCLUÍDOS</font>", styles["Normal"]),
        Paragraph(f"<b><font size='22' color='#C8566A'>{len(ops_ativ)}</font></b><br/><font size='8' color='#8C8480'>OPERADORES ATIVOS</font>", styles["Normal"]),
        Paragraph(f"<b><font size='22' color='#C8566A'>{avg}m</font></b><br/><font size='8' color='#8C8480'>TEMPO MÉDIO</font>", styles["Normal"]),
        Paragraph(f"<b><font size='22' color='#C8566A'>{len(regs)}</font></b><br/><font size='8' color='#8C8480'>REGISTROS TOTAIS</font>", styles["Normal"]),
    ]]
    kpi_tbl = Table(kpi_data, colWidths=["25%","25%","25%","25%"])
    kpi_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), CLARO),
        ("TOPPADDING",    (0,0), (-1,-1), 14), ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (-1,-1), 14), ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(kpi_tbl)
    story.append(Spacer(1, 20))

    if op_map:
        story.append(Paragraph("DESEMPENHO POR OPERADOR", S_SECTION))
        op_header = [
            Paragraph("<b>OPERADOR</b>",    ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO)),
            Paragraph("<b>PEDIDOS</b>",     ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>SEPARAÇÃO</b>",   ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>CONFERÊNCIA</b>", ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>EMBALAGEM</b>",   ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
        ]
        op_rows = [op_header]
        for i, (op, d) in enumerate(op_map.items()):
            op_rows.append([
                Paragraph(f"<b>{op}</b>", ParagraphStyle("o", fontName="Helvetica-Bold", fontSize=9, textColor=ESCURO)),
                Paragraph(str(len(d["p"])), ParagraphStyle("c", fontSize=9, textColor=ESCURO, alignment=TA_CENTER)),
                Paragraph(fmt(media(d["sep"]))  if d["sep"]  else "—", ParagraphStyle("c", fontSize=9, textColor=ESCURO, alignment=TA_CENTER)),
                Paragraph(fmt(media(d["conf"])) if d["conf"] else "—", ParagraphStyle("c", fontSize=9, textColor=ESCURO, alignment=TA_CENTER)),
                Paragraph(fmt(media(d["emb"]))  if d["emb"]  else "—", ParagraphStyle("c", fontSize=9, textColor=VERDE,  alignment=TA_CENTER, fontName="Helvetica-Bold")),
            ])
        op_tbl = Table(op_rows, colWidths=["30%","14%","18%","20%","18%"])
        op_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), ROSA),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [CLARO, BRANCO]),
            ("GRID",          (0,0), (-1,-1), 0.4, BEGE),
            ("TOPPADDING",    (0,0), (-1,-1), 9),  ("BOTTOMPADDING", (0,0), (-1,-1), 9),
            ("LEFTPADDING",   (0,0), (-1,-1), 10), ("RIGHTPADDING",  (0,0), (-1,-1), 10),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(op_tbl)
        story.append(Spacer(1, 20))

    if regs:
        story.append(Paragraph("HISTÓRICO DE PEDIDOS", S_SECTION))
        ETAPA_NOMES = {"Separacao":"Separação","Conferencia":"Conferência","Embalagem":"Embalagem"}
        hist_header = [
            Paragraph("<b>PEDIDO</b>",   ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO)),
            Paragraph("<b>OPERADOR</b>", ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO)),
            Paragraph("<b>ETAPA</b>",    ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>TEMPO</b>",    ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
            Paragraph("<b>DATA</b>",     ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8, textColor=BRANCO, alignment=TA_CENTER)),
        ]
        hist_rows = [hist_header]
        for r in regs[:80]:
            hist_rows.append([
                Paragraph(f"<font name='Courier-Bold' size='8'>{r[1]}</font>", styles["Normal"]),
                Paragraph(f"<font size='8'>{r[2]}</font>", styles["Normal"]),
                Paragraph(ETAPA_NOMES.get(r[3], r[3]), styles["Normal"]),
                Paragraph(f"<font name='Courier' size='8'>{fmt(r[5])}</font>", ParagraphStyle("c", fontSize=8, alignment=TA_CENTER)),
                Paragraph(f"<font size='7' color='#8C8480'>{r[6]}</font>", ParagraphStyle("c", fontSize=7, alignment=TA_CENTER)),
            ])
        hist_tbl = Table(hist_rows, colWidths=["18%","22%","22%","16%","22%"])
        hist_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), ESCURO),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [CLARO, BRANCO]),
            ("GRID",          (0,0), (-1,-1), 0.3, BEGE),
            ("TOPPADDING",    (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 8), ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
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

    pedidos_base_count = len(buscar_pedidos_base())
    if pedidos_base_count > 0:
        pb = buscar_pedidos_base()
        abertos_c = sum(1 for p in pb if p[3] == "aberto")
        concl_c   = pedidos_base_count - abertos_c
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;background:#F0F7F3;
                    border:1.5px solid #4A7C59;border-radius:12px;padding:14px 20px;margin-bottom:1rem;">
            <div style="width:10px;height:10px;border-radius:50%;background:#4A7C59;
                        box-shadow:0 0 8px #4A7C59;flex-shrink:0;"></div>
            <div style="font-size:13px;font-weight:700;color:#2d5a3d;">
                Base sincronizada via <strong>Programa A</strong>:
                <strong style="color:#1A1714;">{pedidos_base_count}</strong> pedidos
                &nbsp;·&nbsp; <span style="color:#4A7C59;">{abertos_c} abertos</span>
                &nbsp;·&nbsp; <span style="color:#C8566A;">{concl_c} concluídos</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:14px;background:#FFFBEB;
                    border:1.5px solid #F59E0B;border-radius:12px;padding:14px 20px;margin-bottom:1rem;">
            <div style="width:10px;height:10px;border-radius:50%;background:#F59E0B;flex-shrink:0;"></div>
            <div style="font-size:13px;font-weight:700;color:#92400E;">
                Nenhuma planilha carregada. Acesse o <strong>Programa A</strong> (Dashboard do Gestor) para importar a carteira de pedidos.
            </div>
        </div>
        """, unsafe_allow_html=True)

    avulsos = buscar_pedidos_avulsos()

    with st.expander(
        f"🗑️ Gerenciar Pedidos Avulsos  {'— ' + str(len(avulsos)) + ' encontrado(s)' if avulsos else '— nenhum cadastrado'}",
        expanded=bool(avulsos)
    ):
        if not avulsos:
            components.html("""
            <!DOCTYPE html><html><body style="background:transparent;font-family:sans-serif;">
            <div style="background:#F0F7F3;border:1.5px solid #4A7C59;border-radius:12px;
                        padding:18px 20px;text-align:center;">
                <div style="font-size:22px;margin-bottom:6px;">✅</div>
                <div style="font-size:13px;font-weight:700;color:#2d5a3d;">
                    Nenhum pedido avulso cadastrado.</div>
                <div style="font-size:11px;color:#4A7C59;margin-top:4px;font-weight:600;">
                    Todos os pedidos vieram da planilha do Programa A.</div>
            </div></body></html>""", height=100, scrolling=False)
        else:
            st.markdown("""
            <div style="background:#FFFBEB;border:1.5px solid #F59E0B;border-radius:10px;
                        padding:12px 16px;font-size:12px;font-weight:700;color:#92400E;margin-bottom:12px;">
                ⚠️ Pedidos avulsos são cadastros manuais feitos durante a operação que
                <strong>não existem na planilha</strong>. Exclua apenas os que foram
                digitados por engano.
            </div>
            """, unsafe_allow_html=True)

            if "confirm_excluir" not in st.session_state:
                st.session_state.confirm_excluir = {}

            for numero, status, importado_em in avulsos:
                regs_vinculados = _get("registros", f"pedido=eq.{numero}&select=id")
                tem_registros   = isinstance(regs_vinculados, list) and len(regs_vinculados) > 0
                cor_status      = "#4A7C59" if status == "aberto" else "#C8566A"
                lbl_status      = "aberto" if status == "aberto" else "concluído"

                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    aviso_reg = (
                        f' &nbsp;·&nbsp; <span style="color:#C47B2A;font-size:10px;">'
                        f'⚠ {len(regs_vinculados)} registro(s) de produção serão removidos</span>'
                        if tem_registros else ""
                    )
                    st.markdown(f"""
                    <div style="background:#fff;border:1.5px solid #EDE9E4;border-radius:10px;
                                padding:11px 16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span style="font-family:monospace;font-size:14px;font-weight:800;
                                     color:#1A1714;">{numero}</span>
                        <span style="background:{cor_status}22;color:{cor_status};font-size:10px;
                                     font-weight:800;padding:2px 10px;border-radius:20px;
                                     text-transform:uppercase;">{lbl_status}</span>
                        <span style="font-size:11px;color:#9C9490;">
                            Cadastrado em: {importado_em or "—"}</span>
                        {aviso_reg}
                    </div>
                    """, unsafe_allow_html=True)

                with col_btn:
                    em_confirmacao = st.session_state.confirm_excluir.get(numero, False)

                    if not em_confirmacao:
                        st.markdown("""
                        <style>
                        .btn-del > button {
                            background:#FEF2F2 !important; color:#C8566A !important;
                            border:1.5px solid #FECACA !important; border-radius:10px !important;
                            font-size:12px !important; font-weight:800 !important;
                            height:46px !important;
                        }
                        .btn-del > button:hover {
                            background:#C8566A !important; color:#fff !important;
                            border-color:#C8566A !important;
                        }
                        </style>""", unsafe_allow_html=True)
                        st.markdown('<div class="btn-del">', unsafe_allow_html=True)
                        if st.button("🗑 Excluir", key=f"del_{numero}", use_container_width=True):
                            st.session_state.confirm_excluir[numero] = True
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="font-size:10px;font-weight:800;color:#C8566A;
                                    text-align:center;margin-bottom:4px;">Confirmar?</div>
                        """, unsafe_allow_html=True)
                        ca, cb = st.columns(2)
                        with ca:
                            st.markdown("""
                            <style>
                            .btn-sim > button {
                                background:#C8566A !important; color:#fff !important;
                                border:none !important; border-radius:8px !important;
                                font-size:11px !important; font-weight:800 !important;
                                height:38px !important;
                            }
                            </style>""", unsafe_allow_html=True)
                            st.markdown('<div class="btn-sim">', unsafe_allow_html=True)
                            if st.button("✓ Sim", key=f"sim_{numero}", use_container_width=True):
                                excluir_pedido_avulso(numero)
                                st.session_state.confirm_excluir.pop(numero, None)
                                st.toast(f"✅ Pedido {numero} excluído com sucesso.", icon="🗑️")
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                        with cb:
                            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
                            if st.button("✕", key=f"nao_{numero}", use_container_width=True):
                                st.session_state.confirm_excluir[numero] = False
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)

    regs     = buscar()
    ped_comp = list({r[1] for r in regs if r[4] == 2})
    ops_ativ = list({r[2] for r in regs})
    avg      = media([r[5] for r in regs]) // 60 if regs else 0
    total_r  = len(regs)

    kpi_html = f"""
    <!DOCTYPE html><html><head>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:transparent;font-family:Nunito,sans-serif;}}
    .grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}}
    .card{{background:#fff;border-radius:16px;padding:18px 16px 14px;
           border:1.5px solid #EDE9E4;box-shadow:0 2px 12px rgba(0,0,0,0.05);position:relative;overflow:hidden;}}
    .card-icon{{position:absolute;top:-6px;right:4px;font-size:44px;opacity:0.07;line-height:1;}}
    .card-lbl{{font-size:9px;font-weight:800;letter-spacing:1.8px;text-transform:uppercase;color:#9C9490;margin-bottom:8px;}}
    .card-num{{font-family:"DM Mono",monospace;font-size:32px;font-weight:500;letter-spacing:-1px;}}
    .card-bar{{height:3px;border-radius:2px;margin-top:12px;opacity:0.3;}}
    </style></head><body>
    <div class="grid">
      <div class="card"><div class="card-icon">📦</div><div class="card-lbl">Pedidos Concluídos</div><div class="card-num" style="color:#C8566A;">{len(ped_comp)}</div><div class="card-bar" style="background:#C8566A;"></div></div>
      <div class="card"><div class="card-icon">👥</div><div class="card-lbl">Operadores Ativos</div><div class="card-num" style="color:#4A7C59;">{len(ops_ativ)}</div><div class="card-bar" style="background:#4A7C59;"></div></div>
      <div class="card"><div class="card-icon">⏱</div><div class="card-lbl">Tempo Médio</div><div class="card-num" style="color:#3B5EC6;">{avg}m</div><div class="card-bar" style="background:#3B5EC6;"></div></div>
      <div class="card"><div class="card-icon">📊</div><div class="card-lbl">Total Registros</div><div class="card-num" style="color:#C47B2A;">{total_r}</div><div class="card-bar" style="background:#C47B2A;"></div></div>
    </div>
    </body></html>"""
    components.html(kpi_html, height=115, scrolling=False)

    op_map = {}
    for r in regs:
        op = r[2]
        if op not in op_map: op_map[op] = {"p":set(),"sep":[],"conf":[],"emb":[]}
        op_map[op]["p"].add(r[1])
        if r[4]==0: op_map[op]["sep"].append(r[5])
        if r[4]==1: op_map[op]["conf"].append(r[5])
        if r[4]==2: op_map[op]["emb"].append(r[5])

    st.markdown("<br style='line-height:0.3'>", unsafe_allow_html=True)

    todas_datas_regs = sorted({
        r[6].split(" ")[0] for r in regs if r[6] and " " in str(r[6])
    }, reverse=True) if regs else []
    todos_ops_regs = sorted({r[2] for r in regs if r[2]}) if regs else []

    fc1, fc2 = st.columns(2)
    with fc1:
        opcoes_data = ["Todos os dias"] + todas_datas_regs
        filtro_data = st.selectbox("📅 Filtrar por dia", opcoes_data, key="admin_filtro_data")
    with fc2:
        opcoes_op = ["Todos os operadores"] + todos_ops_regs
        filtro_op = st.selectbox("👤 Filtrar por operador", opcoes_op, key="admin_filtro_op")

    regs_filtrados = regs
    if filtro_data != "Todos os dias":
        regs_filtrados = [r for r in regs_filtrados if str(r[6]).startswith(filtro_data)]
    if filtro_op != "Todos os operadores":
        regs_filtrados = [r for r in regs_filtrados if r[2] == filtro_op]

    tem_filtro = filtro_data != "Todos os dias" or filtro_op != "Todos os operadores"
    if tem_filtro:
        partes_filtro = []
        if filtro_data != "Todos os dias": partes_filtro.append(f"📅 {filtro_data}")
        if filtro_op   != "Todos os operadores": partes_filtro.append(f"👤 {filtro_op}")
        ped_filt = len({r[1] for r in regs_filtrados})
        st.markdown(
            f'<div style="background:#F0F7F3;border:1.5px solid #4A7C59;border-radius:10px;'
            f'padding:10px 16px;font-size:13px;font-weight:700;color:#2d5a3d;margin-bottom:4px;">'
            f'Filtro ativo: {" · ".join(partes_filtro)} &nbsp;→&nbsp; '
            f'<strong>{ped_filt} pedido(s)</strong> · {len(regs_filtrados)} registro(s)</div>',
            unsafe_allow_html=True
        )

    regs_para_tabela = regs_filtrados

    op_map = {}
    for r in regs_filtrados:
        op = r[2]
        if op not in op_map: op_map[op] = {"p":set(),"sep":[],"conf":[],"emb":[]}
        op_map[op]["p"].add(r[1])
        if r[4]==0: op_map[op]["sep"].append(r[5])
        if r[4]==1: op_map[op]["conf"].append(r[5])
        if r[4]==2: op_map[op]["emb"].append(r[5])

    st.markdown("<br style='line-height:0.4'>", unsafe_allow_html=True)

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
                <span style="background:#F5E8EB;color:#C8566A;font-weight:800;font-size:13px;padding:4px 14px;border-radius:100px;">{len(d["p"])}</span>
              </td>
              <td style="padding:13px 10px;text-align:center;font-family:monospace;font-size:13px;color:#3B5EC6;font-weight:700;vertical-align:middle;">{sep_t}</td>
              <td style="padding:13px 10px;text-align:center;font-family:monospace;font-size:13px;color:#C47B2A;font-weight:700;vertical-align:middle;">{conf_t}</td>
              <td style="padding:13px 10px;text-align:center;font-family:monospace;font-size:13px;color:#4A7C59;font-weight:700;vertical-align:middle;">{emb_t}</td>
            </tr>"""

        n_ops = len(op_map)
        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
        <style>
        *{{margin:0;padding:0;box-sizing:border-box;}} body{{background:transparent;font-family:Nunito,sans-serif;}}
        .lbl{{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#9C9490;margin-bottom:10px;}}
        .wrap{{background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.05);}}
        table{{width:100%;border-collapse:collapse;}} thead tr{{background:#1A1714;}}
        th{{padding:12px 10px;font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;text-align:center;}}
        th:first-child{{text-align:left;padding-left:16px;}}
        tbody tr{{border-bottom:1px solid #F2EEE9;transition:background .15s;}}
        tbody tr:last-child{{border-bottom:none;}} tbody tr:hover{{background:#FDFAF9;}}
        </style></head><body>
        <div class="lbl">Desempenho por Operador{" · " + filtro_data if filtro_data != "Todos os dias" else ""}</div>
        <div class="wrap"><table><thead><tr>
          <th style="color:rgba(255,255,255,0.45);">Operador</th>
          <th style="color:rgba(255,255,255,0.45);">Pedidos</th>
          <th style="color:#7B9FE0;">Separação</th>
          <th style="color:#D4A45A;">Conferência</th>
          <th style="color:#7AB895;">Embalagem</th>
        </tr></thead><tbody>{op_rows}</tbody></table></div>
        </body></html>
        """, height=56 + (n_ops * 62) + 20, scrolling=False)
    else:
        components.html("""<!DOCTYPE html><html><body style="background:transparent;font-family:sans-serif;">
        <div style="background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;
                    padding:40px;text-align:center;color:#9C9490;font-size:14px;font-weight:600;">
            Nenhum registro encontrado para o filtro selecionado.</div></body></html>""", height=120, scrolling=False)

    st.markdown("<br style='line-height:0.4'>", unsafe_allow_html=True)

    h1, h2, h3 = st.columns([2, 1.2, 1.2])
    with h2:
        st.markdown("""
        <style>
        .btn-warn > button {
            background:#FEF3C7 !important; color:#92400E !important;
            border:1.5px solid #F59E0B !important; border-radius:10px !important;
            font-size:12px !important; font-weight:800 !important; height:40px !important;
        }
        .btn-warn > button:hover { background:#F59E0B !important; color:#fff !important; }
        </style>""", unsafe_allow_html=True)
        st.markdown('<div class="btn-warn">', unsafe_allow_html=True)
        if st.button("⊘  Limpar PIPs", use_container_width=True, help="Remove todos os PIPs/sessões ativas fantasmas"):
            limpar_sessoes_ativas(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with h3:
        if st.button("🗑 Limpar dados", use_container_width=True):
            limpar(); st.rerun()

    tag_html = {
        0: '<span style="background:#EBF0FB;color:#3B5EC6;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:800;">Separação</span>',
        1: '<span style="background:#FBF2E6;color:#C47B2A;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:800;">Conferência</span>',
        2: '<span style="background:#E8F2EC;color:#4A7C59;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:800;">Embalagem</span>',
    }

    if regs_para_tabela:
        hist_rows = ""
        for r in regs_para_tabela[:80]:
            hist_rows += f"""<tr>
              <td style="padding:11px 16px;font-family:monospace;font-size:12px;font-weight:700;color:#1A1714;">{r[1]}</td>
              <td style="padding:11px 10px;font-size:13px;font-weight:700;color:#1A1714;">{r[2]}</td>
              <td style="padding:11px 10px;">{tag_html.get(r[4], r[3])}</td>
              <td style="padding:11px 10px;font-family:monospace;font-size:12px;font-weight:700;color:#4A7C59;text-align:center;">{fmt(r[5])}</td>
              <td style="padding:11px 10px;font-size:11px;color:#9C9490;text-align:center;">{r[6]}</td>
            </tr>"""

        n_hist = min(len(regs_para_tabela), 80)
        hist_height = 56 + (n_hist * 46) + 20

        components.html(f"""
        <!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&display=swap" rel="stylesheet">
        <style>
        *{{margin:0;padding:0;box-sizing:border-box;}} body{{background:transparent;font-family:Nunito,sans-serif;}}
        .lbl{{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#9C9490;margin-bottom:10px;}}
        .wrap{{background:#fff;border-radius:16px;border:1.5px solid #EDE9E4;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.05);}}
        table{{width:100%;border-collapse:collapse;}} thead tr{{background:#1A1714;}}
        th{{padding:12px 10px;font-size:9px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.45);text-align:center;}}
        th:first-child{{text-align:left;padding-left:16px;}} th:nth-child(2){{text-align:left;}}
        tbody tr{{border-bottom:1px solid #F2EEE9;}} tbody tr:last-child{{border-bottom:none;}}
        tbody tr:hover{{background:#FDFAF9;}}
        </style></head><body>
        <div class="lbl">Histórico de Pedidos</div>
        <div class="wrap"><table><thead><tr>
          <th>Pedido</th><th>Operador</th><th>Etapa</th><th>Tempo</th><th>Data</th>
        </tr></thead><tbody>{hist_rows}</tbody></table></div>
        </body></html>
        """, height=min(hist_height, 600), scrolling=hist_height > 600)

    st.markdown("<br>", unsafe_allow_html=True)

    if regs:
        st.markdown("""
        <style>
        .btn-pdf > button { background:linear-gradient(135deg,#C8566A,#9E3F52) !important; color:#fff !important; border:none !important;
            box-shadow:0 5px 0 rgba(100,20,35,0.40),0 8px 20px rgba(200,86,106,0.28) !important; font-weight:800 !important; height:54px !important; }
        .btn-pdf > button:hover { transform:translateY(-2px) !important; }
        .btn-xml > button { background:linear-gradient(135deg,#3B5EC6,#2a469e) !important; color:#fff !important; border:none !important;
            box-shadow:0 5px 0 rgba(20,30,100,0.40),0 8px 20px rgba(59,94,198,0.28) !important; font-weight:800 !important; height:54px !important; }
        .btn-xml > button:hover { transform:translateY(-2px) !important; }
        </style>
        """, unsafe_allow_html=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M")

        buf_csv = io.StringIO()
        csv.writer(buf_csv).writerows(
            [["ID","Pedido","Operador","Etapa","EtapaIdx","Tempo(s)","Data"]] + list(regs))

        pdf_bytes = gerar_pdf(regs, op_map, ped_comp, ops_ativ, avg)

        # ── Gerar XLS ──
        df_xls = pd.DataFrame(list(regs), columns=["ID","Pedido","Operador","Etapa","EtapaIdx","Tempo(s)","Data"])
        buf_xls = io.BytesIO()
        with pd.ExcelWriter(buf_xls, engine="openpyxl") as writer:
            df_xls.to_excel(writer, index=False, sheet_name="Producao")
        buf_xls.seek(0)
        xls_bytes = buf_xls.read()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
            st.download_button("⬇  Exportar CSV", data=buf_csv.getvalue().encode(),
                file_name=f"vi_producao_{ts}.csv", mime="text/csv", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="btn-xml">', unsafe_allow_html=True)
            st.download_button("📊  Exportar XLS", data=xls_bytes,
                file_name=f"vi_producao_{ts}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button("📄  Exportar PDF", data=pdf_bytes,
                file_name=f"vi_relatorio_{ts}.pdf", mime="application/pdf", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────
#  TELA: OPERAÇÕES EM ANDAMENTO
# ─────────────────────────────────────
def fmt_elapsed(ini_ts):
    s = max(int(time.time()) - int(ini_ts), 0)
    h, r = divmod(s, 3600); m, s2 = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s2:02d}", s

def tela_operacoes():
    render_logo()

    sessoes = buscar_todas_sessoes_ativas()
    n_total = len(sessoes)

    ETAPA_COR  = ["#C8566A", "#3B7DD8", "#4A7C59"]
    ETAPA_BG   = ["#FFF0F2", "#F0F5FF", "#F0F7F3"]
    ETAPA_ICON = ["📦", "🗃️", "✅"]

    # ── Header com contador + botões ─────────────────────────────────────────
    col_h1, col_h2, col_h3 = st.columns([3, 1.2, 1.2])
    with col_h1:
        st.markdown(f"""
        <div style="margin-bottom:4px;">
          <div style="font-size:10px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;
              color:#9C9490;margin-bottom:2px;">Painel de Operações</div>
          <div style="font-size:22px;font-weight:900;color:#1A1714;letter-spacing:-0.3px;">
            Em Andamento
            <span style="font-size:14px;font-weight:700;color:#C8566A;margin-left:6px;">
              {n_total} ativa{"s" if n_total != 1 else ""}
            </span>
          </div>
        </div>""", unsafe_allow_html=True)
    with col_h2:
        st.markdown('<div class="btn-iniciar btn-sm">', unsafe_allow_html=True)
        if st.button("＋ Nova Op.", use_container_width=True):
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_h3:
        st.markdown('<div class="btn-voltar btn-sm">', unsafe_allow_html=True)
        if st.button("← Lobby", use_container_width=True):
            st.session_state.tela = "home"; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Campo de busca por número de pedido ──────────────────────────────────
    st.markdown("""
    <style>
    div[data-testid="stTextInput"] label { display:none !important; }
    div[data-testid="stTextInput"] input {
        border: 2px solid #E0DBD4 !important;
        border-radius: 12px !important;
        background: #fff !important;
        font-family: 'Nunito', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 14px 18px !important;
        height: 52px !important;
        transition: border-color .2s !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #C8566A !important;
        box-shadow: 0 0 0 4px rgba(200,86,106,0.10) !important;
    }
    </style>""", unsafe_allow_html=True)

    busca = st.text_input("_busca", placeholder="🔍  Buscar por número do pedido...",
                          key="busca_pedido_painel")
    busca = busca.strip()

    # ── Sem sessões ──────────────────────────────────────────────────────────
    if not sessoes:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        components.html("""<!DOCTYPE html><html><body style="background:transparent;
        font-family:sans-serif;padding:0;margin:0;">
        <div style="background:#F0F7F3;border:1.5px solid #4A7C59;border-radius:16px;
                    padding:48px 24px;text-align:center;">
            <div style="font-size:40px;margin-bottom:12px;">✅</div>
            <div style="font-size:16px;font-weight:800;color:#2d5a3d;margin-bottom:6px;">
                Nenhuma operação em andamento</div>
            <div style="font-size:12px;color:#4A7C59;font-weight:600;">
                Use "＋ Nova Op." para iniciar um processo.</div>
        </div></body></html>""", height=170, scrolling=False)
        return

    # ── Filtragem por busca ──────────────────────────────────────────────────
    if busca:
        sessoes_visiveis = [s for s in sessoes if busca in str(s.get("pedido",""))]
    else:
        sessoes_visiveis = sessoes

    if busca and not sessoes_visiveis:
        st.markdown(f"""
        <div style="background:#FEF3C7;border:1.5px solid #F59E0B;border-radius:12px;
                    padding:16px 20px;text-align:center;margin:8px 0;">
          <div style="font-size:14px;font-weight:800;color:#92400E;">
            Nenhuma operação com pedido <code>{busca}</code> em andamento.</div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Separador de resultados ──────────────────────────────────────────────
    if busca:
        st.markdown(f"""
        <div style="font-size:11px;font-weight:800;color:#4A7C59;
            letter-spacing:1.5px;text-transform:uppercase;margin:10px 0 6px;">
            ✓ {len(sessoes_visiveis)} resultado(s) para "{busca}"
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="font-size:11px;font-weight:700;color:#9C9490;margin:10px 0 6px;">
            Todos os pedidos — role para encontrar o seu
        </div>""", unsafe_allow_html=True)

    # ── Cards das sessões ────────────────────────────────────────────────────
    for s in sessoes_visiveis:
        ped     = s.get("pedido", "")
        op      = s.get("operador", "")
        eta_idx = int(s.get("etapa_idx", 0))
        ini     = int(s.get("iniciado_em", 0))
        cor     = ETAPA_COR[eta_idx]
        bg      = ETAPA_BG[eta_idx]
        icon    = ETAPA_ICON[eta_idx]
        lbl     = ETAPAS_LBL[eta_idx]
        elapsed_str, _ = fmt_elapsed(ini)
        ini_op  = (op[0]+op[1]).upper() if len(op) >= 2 else op[0].upper()
        uid     = f"{ped}_{eta_idx}"

        # Card + timer ao vivo via JS dentro do iframe
        components.html(f"""<!DOCTYPE html><html><head>
        <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@700;800;900&family=DM+Mono:wght@500&display=swap" rel="stylesheet">
        <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{background:transparent;font-family:Nunito,sans-serif;}}
        .card{{background:#fff;border:1.5px solid #EDE9E4;border-left:5px solid {cor};
               border-radius:14px;padding:14px 16px;
               box-shadow:0 2px 14px rgba(0,0,0,0.06);
               display:flex;align-items:center;gap:14px;}}
        .av{{width:44px;height:44px;border-radius:50%;flex-shrink:0;
             background:linear-gradient(135deg,{cor},{cor}99);
             display:flex;align-items:center;justify-content:center;
             font-size:15px;font-weight:900;color:#fff;
             box-shadow:0 3px 10px rgba(0,0,0,0.16);}}
        .name{{font-size:14px;font-weight:900;color:#1A1714;margin-bottom:3px;}}
        .badge{{display:inline-flex;align-items:center;gap:4px;background:{bg};color:{cor};
                font-size:10px;font-weight:800;padding:2px 9px;border-radius:20px;margin-right:6px;}}
        .ped{{font-family:monospace;font-size:13px;color:#5C5450;font-weight:700;}}
        .timer-wrap{{text-align:right;flex-shrink:0;}}
        .timer-lbl{{font-size:9px;font-weight:800;color:#9C9490;letter-spacing:1.5px;
                    text-transform:uppercase;margin-bottom:2px;}}
        .timer-val{{font-family:'DM Mono',monospace;font-size:24px;font-weight:500;
                    color:{cor};letter-spacing:-1px;line-height:1;}}
        </style></head>
        <body>
        <div class="card">
          <div class="av">{ini_op}</div>
          <div style="flex:1;min-width:0;">
            <div class="name">{op}</div>
            <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
              <span class="badge">{icon} {lbl}</span>
              <span class="ped">#{ped}</span>
            </div>
          </div>
          <div class="timer-wrap">
            <div class="timer-lbl">em andamento</div>
            <div class="timer-val" id="tv">{elapsed_str}</div>
          </div>
        </div>
        <script>
        (function(){{
          var ini={ini}, el=document.getElementById('tv');
          function u(){{
            var e=Math.floor(Date.now()/1000)-ini;
            var h=Math.floor(e/3600),m=Math.floor((e%3600)/60),s=e%60;
            el.textContent=String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
          }}
          u(); setInterval(u,1000);
        }})();
        </script>
        </body></html>""", height=80, scrolling=False)

        # Botão FINALIZAR — ocupa 2/3 da largura, alinhado à direita
        _, col_fin = st.columns([1, 2])
        with col_fin:
            st.markdown('<div class="btn-finalizar">', unsafe_allow_html=True)
            if st.button(
                f"■  Finalizar  ·  #{ped}  ·  {op}",
                use_container_width=True,
                key=f"fin_{uid}"
            ):
                tempo = max(int(time.time()) - ini, 1)
                salvar(ped, op, ETAPAS[eta_idx], eta_idx, tempo)
                remover_sessao_ativa(ped, eta_idx)
                if eta_idx == 2:
                    marcar_concluido(ped)
                # Limpa busca e permanece no painel
                st.session_state["busca_pedido_painel"] = ""
                st.toast(f"✅  {op}  ·  Pedido #{ped}  finalizado em  {fmt(tempo)}!", icon="🎉")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────
{
    "home":        tela_home,
    "producao":    tela_producao,
    "operacoes":   tela_operacoes,
    "admin_login": tela_admin_login,
    "admin":       tela_admin,
}.get(st.session_state.tela, tela_home)()
