import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import BytesIO

st.set_page_config(
    page_title="Vi Lingerie — Produção",
    layout="centered",
    page_icon="🏭",
    initial_sidebar_state="collapsed"
)

# ── constantes ──────────────────────────────────────────────
ETAPAS       = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_LABELS = ["SEPARAÇÃO", "EMBALAGEM", "CONFERÊNCIA"]

OPERADORES = [
    "Lucivanio", "Enágio", "Daniel", "Ítalo", "Cildenir",
    "Samya", "Neide", "Eduardo", "Talyson",
]

SENHA_GERENCIA = "vi2026"
ETAPA_COLORS   = ["#1D4ED8", "#7C3AED", "#16a34a"]

STATE_DIR = "vi_producao_state"
os.makedirs(STATE_DIR, exist_ok=True)
FILE_PEDIDOS    = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS = os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO  = os.path.join(STATE_DIR, "historico.json")

# ── I/O ─────────────────────────────────────────────────────
def _load(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def carregar_pedidos():    return _load(FILE_PEDIDOS)
def salvar_pedidos(d):     _save(FILE_PEDIDOS, d)
def carregar_concluidos():
    d = _load(FILE_CONCLUIDOS); return d if isinstance(d, list) else []
def salvar_concluidos(d):  _save(FILE_CONCLUIDOS, d)
def carregar_historico():
    d = _load(FILE_HISTORICO); return d if isinstance(d, list) else []

def registrar_historico(pedido, operador, etapa, dh, status="em_andamento"):
    h = carregar_historico()
    h.append({"data_hora": dh, "data": dh.split(" ")[0] if " " in dh else dh,
               "pedido": pedido, "operador": operador, "etapa": etapa, "status_pedido": status})
    _save(FILE_HISTORICO, h)

def agora_str():
    from datetime import timezone, timedelta
    return datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

def fmt_tempo(s):
    if not s or s < 0: return "00:00:00"
    return f"{int(s//3600):02d}:{int((s%3600)//60):02d}:{int(s%60):02d}"

import base64 as _b64
def _get_logo_b64():
    for p in ["logo_vi.png", "../logo_vi.png"]:
        if os.path.exists(p):
            with open(p,"rb") as f: return _b64.b64encode(f.read()).decode()
    return ""
_logo_b64 = _get_logo_b64()
_logo_src = f"data:image/png;base64,{_logo_b64}" if _logo_b64 else ""
logo_html = (f'<img src="{_logo_src}" style="height:34px;object-fit:contain;" />'
             if _logo_b64
             else '<span style="font-family:\'Playfair Display\',serif;font-size:1.6rem;font-weight:900;color:#8B0000;letter-spacing:.06em">VI LINGERIE</span>')

# ── avatar ───────────────────────────────────────────────────
_PALETTE = ["#7C3AED","#1D4ED8","#B91C1C","#047857","#C2410C","#6D28D9","#0369A1","#374151","#BE185D"]
def av_cor(nome): return _PALETTE[sum(ord(c) for c in nome) % len(_PALETTE)]
def av_ini(nome):
    p = nome.strip().split()
    return (p[0][0] + (p[-1][0] if len(p)>1 else "")).upper()
def avatar_tag(nome, size=44):
    ini = av_ini(nome); cor = av_cor(nome); fs = int(size*.34)
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{cor};'
            f'display:inline-flex;align-items:center;justify-content:center;'
            f'font-size:{fs}px;font-weight:700;color:#fff;flex-shrink:0;'
            f'font-family:\'DM Sans\',sans-serif;">{ini}</div>')

# ════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,[data-testid="stApp"]{
    font-family:'DM Sans',sans-serif!important;
    background:#EDEBE8!important;
    color:#111827!important;
    min-height:100vh;
}
[data-testid="stSidebar"],header[data-testid="stHeader"],
[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
.block-container{padding:1.8rem 1rem 3rem!important;max-width:540px!important;margin:0 auto!important;}

/* WORDMARK */
.vi-wordmark{text-align:center;margin-bottom:18px;padding-top:4px;}

/* CARD */
.vi-card{background:#fff;border-radius:20px;box-shadow:0 2px 24px rgba(0,0,0,.09),0 1px 4px rgba(0,0,0,.04);overflow:hidden;animation:vi-up .32s cubic-bezier(.22,1,.36,1) both;}
@keyframes vi-up{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}

/* HEADER */
.vi-header{padding:14px 18px;display:flex;align-items:center;gap:12px;border-bottom:2.5px solid transparent;position:relative;}
.vi-header-bar{position:absolute;bottom:-2.5px;left:0;right:0;height:2.5px;}
.vi-header-label{font-size:.58rem;font-weight:700;color:#9ca3af;text-transform:uppercase;letter-spacing:.14em;margin-bottom:1px;}
.vi-header-name{font-size:.9rem;font-weight:700;color:#111827;}
.vi-header-badge{margin-left:auto;display:inline-flex;align-items:center;gap:5px;padding:5px 13px;border-radius:999px;font-size:.62rem;font-weight:700;letter-spacing:.1em;border:1.5px solid currentColor;white-space:nowrap;}
.vi-logout-btn{padding:5px;cursor:pointer;opacity:.4;transition:opacity .15s;}
.vi-logout-btn:hover{opacity:.8;}

/* BODY */
.vi-body{padding:24px 20px 24px;}

/* STEPPER */
.vi-stepper{display:flex;align-items:flex-start;margin-bottom:24px;}
.vi-step-col{display:flex;flex-direction:column;align-items:center;gap:5px;flex:0 0 auto;}
.vi-step-circle{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:all .3s;}
.vi-step-lbl{font-size:.54rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;text-align:center;white-space:nowrap;}
.vi-step-line{flex:1;height:1.5px;background:#e5e7eb;margin-top:19px;}
.vi-step-line-done{background:#1D4ED8;}

/* SCAN AREA */
.vi-scan-area{text-align:center;padding:16px 0 12px;}
.vi-scan-title{font-size:1rem;font-weight:700;color:#111827;margin-bottom:3px;}
.vi-scan-sub{font-size:.73rem;color:#9ca3af;margin-bottom:16px;}

/* PEDIDO BIG */
.vi-num{font-family:'Playfair Display',serif;font-size:3.8rem;font-weight:900;color:#111827;line-height:1;text-align:center;margin:8px 0;}
.vi-num span{color:#9ca3af;font-size:2rem;vertical-align:.25em;}

/* TIMER */
.vi-timer{display:flex;align-items:center;justify-content:center;gap:6px;font-family:'DM Mono',monospace;font-size:1.45rem;font-weight:500;color:#374151;letter-spacing:.06em;margin-bottom:18px;}

/* BOTÕES */
.vi-btn-blue>button{background:#1D4ED8!important;border:none!important;border-radius:14px!important;color:#fff!important;font-weight:700!important;font-size:.9rem!important;letter-spacing:.06em!important;padding:17px 24px!important;font-family:'DM Sans',sans-serif!important;width:100%;box-shadow:0 4px 16px rgba(29,78,216,.32)!important;transition:all .2s!important;}
.vi-btn-blue>button:hover{background:#1e40af!important;transform:translateY(-1px)!important;box-shadow:0 6px 22px rgba(29,78,216,.42)!important;}
.vi-btn-red>button{background:#DC2626!important;border:none!important;border-radius:14px!important;color:#fff!important;font-weight:700!important;font-size:.9rem!important;letter-spacing:.06em!important;padding:17px 24px!important;font-family:'DM Sans',sans-serif!important;width:100%;box-shadow:0 4px 16px rgba(220,38,38,.32)!important;transition:all .2s!important;animation:pulse-red 2s ease infinite;}
@keyframes pulse-red{0%,100%{box-shadow:0 4px 16px rgba(220,38,38,.32);}50%{box-shadow:0 4px 28px rgba(220,38,38,.58);}}
.vi-btn-red>button:hover{background:#b91c1c!important;transform:translateY(-1px)!important;}
.vi-btn-green>button{background:#16a34a!important;border:none!important;border-radius:14px!important;color:#fff!important;font-weight:700!important;font-size:.9rem!important;letter-spacing:.06em!important;padding:17px 24px!important;font-family:'DM Sans',sans-serif!important;width:100%;box-shadow:0 4px 16px rgba(22,163,74,.3)!important;transition:all .2s!important;}
.stButton>button{background:transparent!important;border:1.5px solid #e5e7eb!important;border-radius:12px!important;color:#6b7280!important;font-weight:600!important;font-size:.78rem!important;letter-spacing:.04em!important;padding:10px 16px!important;font-family:'DM Sans',sans-serif!important;width:100%;transition:all .18s!important;}
.stButton>button:hover{background:#f9fafb!important;color:#374151!important;border-color:#d1d5db!important;}

/* INPUTS */
[data-testid="stTextInput"] label,[data-testid="stSelectbox"] label,[data-testid="stPasswordInput"] label{display:none!important;}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#F4F4F4!important;border:1.5px solid transparent!important;border-radius:12px!important;color:#111827!important;font-family:'DM Mono',monospace!important;font-size:1rem!important;padding:14px 18px!important;}
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus{border-color:#1D4ED8!important;box-shadow:0 0 0 3px rgba(29,78,216,.1)!important;}
[data-testid="stTextInput"] input::placeholder{color:#aaa!important;}
[data-testid="stSelectbox"]>div>div{background:#F4F4F4!important;border:1.5px solid transparent!important;border-radius:12px!important;color:#111827!important;}
[data-testid="stPasswordInput"] input{background:#F4F4F4!important;border:1.5px solid transparent!important;border-radius:12px!important;}

/* HR */
.vi-hr{height:1px;background:#f3f4f6;margin:16px 0;border:none;}

/* ALERTS */
.vi-alert{padding:11px 15px;border-radius:12px;font-size:.78rem;font-weight:500;margin:8px 0;display:flex;align-items:center;gap:8px;}
.vi-ok  {background:#f0fdf4;border:1.5px solid #bbf7d0;color:#16a34a;}
.vi-err {background:#fef2f2;border:1.5px solid #fecaca;color:#dc2626;}
.vi-inf {background:#eff6ff;border:1.5px solid #bfdbfe;color:#1d4ed8;}
.vi-warn{background:#fffbeb;border:1.5px solid #fde68a;color:#d97706;}

/* OP GRID */
.vi-op-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0;}
.vi-op-cell{background:#f9fafb;border:2px solid #f3f4f6;border-radius:14px;padding:14px 8px 12px;display:flex;flex-direction:column;align-items:center;gap:8px;font-size:.73rem;font-weight:600;color:#374151;text-align:center;transition:all .18s;}

/* DONE */
@keyframes vi-pop{from{opacity:0;transform:scale(.88);}to{opacity:1;transform:scale(1);}}
.vi-done-card{background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #bbf7d0;border-radius:18px;padding:28px 20px;text-align:center;animation:vi-pop .4s cubic-bezier(.34,1.56,.64,1) both;}

/* ASK CARD */
.vi-ask-card{background:#f9fafb;border-radius:14px;padding:16px;margin-top:12px;}
.vi-ask-title{font-size:.68rem;font-weight:700;color:#6b7280;text-transform:uppercase;letter-spacing:.12em;margin-bottom:12px;}

/* FOOTER */
.vi-footer{text-align:center;margin-top:16px;font-size:.7rem;color:#9ca3af;cursor:pointer;}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# COMPONENTS
# ════════════════════════════════════════════════════════════
def render_header(operador, etapa_idx, show_logout=True):
    cor   = ETAPA_COLORS[etapa_idx]
    label = ETAPA_LABELS[etapa_idx]
    av    = avatar_tag(operador, 44)
    logout_icon = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>"""
    st.markdown(f"""
    <div class="vi-header">
        {av}
        <div>
            <div class="vi-header-label">ESTAÇÃO CENTRAL</div>
            <div class="vi-header-name">{operador}</div>
        </div>
        <div class="vi-header-badge" style="color:{cor};">{label}</div>
        {'<div class="vi-logout-btn" id="_logout_icon">'+logout_icon+'</div>' if show_logout else ''}
        <div class="vi-header-bar" style="background:{cor};"></div>
    </div>
    """, unsafe_allow_html=True)


def render_stepper(etapa_idx):
    ICONS = [
        # box
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
        # mail
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
        # check clipboard
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/></svg>',
    ]
    CHECK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'

    html = '<div class="vi-stepper">'
    for i, label in enumerate(ETAPA_LABELS):
        done   = i < etapa_idx
        active = i == etapa_idx
        cor    = ETAPA_COLORS[i]
        if done:
            circ = f'background:{cor};color:#fff;'
            lbl  = f'color:{cor};font-weight:700;'
            icon = CHECK
        elif active:
            circ = f'background:{cor};color:#fff;box-shadow:0 0 0 5px {cor}20;'
            lbl  = f'color:{cor};font-weight:800;'
            icon = ICONS[i]
        else:
            circ = 'background:#f3f4f6;color:#d1d5db;'
            lbl  = 'color:#d1d5db;'
            icon = ICONS[i]
        html += f'<div class="vi-step-col"><div class="vi-step-circle" style="{circ}">{icon}</div><div class="vi-step-lbl" style="{lbl}">{label}</div></div>'
        if i < 2:
            line = 'vi-step-line-done' if done else ''
            html += f'<div class="vi-step-line {line}"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TELA INICIAL — SELEÇÃO DE OPERADOR
# ════════════════════════════════════════════════════════════
def tela_inicial():
    st.markdown(f'<div class="vi-wordmark">{logo_html}</div>', unsafe_allow_html=True)
    st.markdown('<div class="vi-card"><div class="vi-body">', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:20px">
        <div style="font-size:1rem;font-weight:700;color:#111827">Apontamento de Produção</div>
        <div style="font-size:.72rem;color:#9ca3af;margin-top:3px">Selecione seu nome para começar</div>
    </div>
    <hr class="vi-hr" style="margin-top:0">
    <div style="font-size:.6rem;font-weight:700;color:#9ca3af;letter-spacing:.14em;text-transform:uppercase;margin-bottom:14px">QUEM É VOCÊ?</div>
    """, unsafe_allow_html=True)

    sel = st.session_state.get("_sel_op")

    # Grade 3×N de operadores
    rows = [OPERADORES[i:i+3] for i in range(0, len(OPERADORES), 3)]
    for row in rows:
        cols = st.columns(len(row))
        for col, nome in zip(cols, row):
            with col:
                cor  = av_cor(nome)
                ini  = av_ini(nome)
                is_s = sel == nome
                bd   = "#1D4ED8" if is_s else "#f3f4f6"
                bg   = "#eff6ff" if is_s else "#f9fafb"
                tc   = "#1D4ED8" if is_s else "#374151"
                st.markdown(f"""
                <div style="background:{bg};border:2px solid {bd};border-radius:14px;
                    padding:14px 8px 12px;display:flex;flex-direction:column;
                    align-items:center;gap:8px;cursor:pointer;">
                    <div style="width:38px;height:38px;border-radius:50%;background:{cor};
                        display:flex;align-items:center;justify-content:center;
                        font-size:13px;font-weight:700;color:#fff;">{ini}</div>
                    <div style="font-size:.72rem;font-weight:600;color:{tc};line-height:1.2;text-align:center">{nome}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(nome, key=f"selop_{nome}", use_container_width=True):
                    st.session_state["_sel_op"] = nome
                    st.rerun()

    # Esconde texto dos botões, deixa área clicável
    st.markdown("""
    <style>
    div[data-testid="stButton"] button span{font-size:0!important;}
    div[data-testid="stButton"] button{
        position:relative!important;
        margin-top:-76px!important;
        height:76px!important;
        opacity:0!important;
        border:none!important;
        cursor:pointer!important;
        background:transparent!important;
        box-shadow:none!important;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('<hr class="vi-hr">', unsafe_allow_html=True)

    if sel:
        st.markdown(f'<div class="vi-alert vi-inf" style="margin-bottom:10px">👤 Selecionado: <b>{sel}</b></div>', unsafe_allow_html=True)

    st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
    if st.button("→  Entrar no sistema", use_container_width=True, key="btn_entrar"):
        if not sel:
            st.markdown('<div class="vi-alert vi-err">⚠️ Selecione seu nome primeiro.</div>', unsafe_allow_html=True)
        else:
            st.session_state.update({
                "_operador":    sel,
                "_turno_inicio": time.time(),
                "_etapa_idx":   0,
                "_flow":        "input",
                "_pedido":      None,
                "_ts_inicio":   None,
                "_ts_fim":      None,
                "_ask_mode":    None,
            })
            st.session_state.pop("_sel_op", None)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)  # body + card

    # Link gerência
    st.markdown('<div class="vi-footer">🔒 Acesso Gerência</div>', unsafe_allow_html=True)
    if st.button("Acesso Gerência", use_container_width=False, key="btn_ger_link"):
        st.session_state["_modo"] = "gerencia"
        st.rerun()
    st.markdown("""
    <style>
    div[data-testid="stButton"]:last-child button{
        opacity:0!important;margin-top:-28px!important;height:28px!important;
        border:none!important;background:transparent!important;cursor:pointer!important;
    }
    </style>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TELA DO OPERADOR
# ════════════════════════════════════════════════════════════
def tela_operador():
    operador  = st.session_state.get("_operador","")
    etapa_idx = st.session_state.get("_etapa_idx", 0)
    flow      = st.session_state.get("_flow","input")
    pedido    = st.session_state.get("_pedido")
    ts_inicio = st.session_state.get("_ts_inicio")
    elapsed   = fmt_tempo(time.time() - ts_inicio) if ts_inicio and flow == "running" else None

    st.markdown(f'<div class="vi-wordmark">{logo_html}</div>', unsafe_allow_html=True)
    st.markdown('<div class="vi-card">', unsafe_allow_html=True)
    render_header(operador, etapa_idx)
    st.markdown('<div class="vi-body">', unsafe_allow_html=True)

    # ── Botão de logout invisível sobreposto ao ícone ──
    # (usamos um botão Streamlit separado abaixo do card)

    # ══ INPUT ══════════════════════════════════════════
    if flow == "input":

        if etapa_idx == 0:
            # Scan / digitar
            SCAN_SVG = """<svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#c0bab4" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/>
              <line x1="7" y1="12" x2="17" y2="12"/>
              <line x1="12" y1="7" x2="12" y2="17"/>
            </svg>"""
            st.markdown(f"""
            <div class="vi-scan-area">
                {SCAN_SVG}
                <div class="vi-scan-title">Bipar ou digitar pedido</div>
                <div class="vi-scan-sub">Insira o número do pedido para iniciar</div>
            </div>
            """, unsafe_allow_html=True)

            c_i, c_b = st.columns([4, 1])
            with c_i:
                num_input = st.text_input("pedido", placeholder="Ex: 12345",
                                          key="inp_num", label_visibility="collapsed")
            with c_b:
                st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
                go = st.button("→", use_container_width=True, key="btn_go")
                st.markdown('</div>', unsafe_allow_html=True)

            if go:
                num = st.session_state.get("inp_num","").strip()
                db  = carregar_pedidos()
                if not num:
                    st.markdown('<div class="vi-alert vi-err">⚠️ Informe o número do pedido.</div>', unsafe_allow_html=True)
                elif num in db:
                    st.markdown(f'<div class="vi-alert vi-err">⚠️ Pedido #{num} já está em andamento.</div>', unsafe_allow_html=True)
                else:
                    st.session_state.update({"_pedido": num, "_flow": "confirm"})
                    st.rerun()
        else:
            # Embalagem / Conferência
            render_stepper(etapa_idx)
            db         = carregar_pedidos()
            chave_op   = "op_emb" if etapa_idx == 1 else "op_conf"
            etapa_need = 1 if etapa_idx == 1 else 2
            disponiveis= sorted([p for p, d in db.items()
                                  if d.get("etapa") == etapa_need and chave_op not in d])

            if not disponiveis:
                st.markdown(f'<div class="vi-alert vi-warn">⏳ Nenhum pedido disponível para {ETAPA_LABELS[etapa_idx]} ainda. Aguarde a etapa anterior.</div>', unsafe_allow_html=True)
                if st.button("🔄 Verificar novamente", use_container_width=True, key="btn_recheck"):
                    st.rerun()
            else:
                pedido_sel = st.selectbox("Selecione o pedido",
                                          ["— Selecione —"] + disponiveis,
                                          key=f"sel_ped_{etapa_idx}",
                                          label_visibility="visible")
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
                if st.button(f"▶  INICIAR {ETAPA_LABELS[etapa_idx]}", use_container_width=True, key=f"btn_ini_{etapa_idx}"):
                    if pedido_sel == "— Selecione —":
                        st.markdown('<div class="vi-alert vi-err">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state.update({"_pedido": pedido_sel, "_flow": "confirm"})
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # ══ CONFIRM ════════════════════════════════════════
    elif flow == "confirm":
        render_stepper(etapa_idx)
        st.markdown(f'<div class="vi-num"><span>#</span>{pedido}</div>', unsafe_allow_html=True)
        st.markdown('<div class="vi-btn-blue" style="margin-top:8px">', unsafe_allow_html=True)
        if st.button(f"▶  INICIAR {ETAPA_LABELS[etapa_idx]}", use_container_width=True, key="btn_start_confirm"):
            st.session_state.update({"_flow": "running", "_ts_inicio": time.time()})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("← Alterar pedido", use_container_width=True, key="btn_back_confirm"):
            st.session_state.update({"_flow": "input", "_pedido": None})
            st.rerun()

    # ══ RUNNING ════════════════════════════════════════
    elif flow == "running":
        render_stepper(etapa_idx)
        st.markdown(f"""
        <div class="vi-num"><span>#</span>{pedido}</div>
        <div class="vi-timer">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            {elapsed}
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-btn-red">', unsafe_allow_html=True)
        if st.button(f"■  CONCLUIR {ETAPA_LABELS[etapa_idx]}", use_container_width=True, key="btn_concluir"):
            now    = agora_str()
            ts_fim = time.time()
            db     = carregar_pedidos()

            if etapa_idx == 0:
                db[pedido] = {"pedido": pedido, "etapa": 1, "op_sep": operador, "dt_sep": now}
                registrar_historico(pedido, operador, ETAPAS[0], now, "em_andamento")
            elif etapa_idx == 1:
                if pedido in db:
                    db[pedido].update({"etapa": 2, "op_emb": operador, "dt_emb": now})
                    registrar_historico(pedido, operador, ETAPAS[1], now, "em_andamento")
            elif etapa_idx == 2:
                if pedido in db:
                    db[pedido].update({"etapa": 3, "op_conf": operador, "dt_conf": now})
                    conc = carregar_concluidos()
                    conc.append(db[pedido])
                    salvar_concluidos(conc)
                    del db[pedido]
                    registrar_historico(pedido, operador, ETAPAS[2], now, "concluido")

            salvar_pedidos(db)
            next_flow = "ask_next" if etapa_idx < 2 else "done"
            st.session_state.update({"_ts_fim": ts_fim, "_flow": next_flow})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("✕ Cancelar operação", use_container_width=True, key="btn_cancel_run"):
            st.session_state.update({"_flow": "input", "_pedido": None, "_ts_inicio": None})
            st.rerun()

    # ══ ASK_NEXT ═══════════════════════════════════════
    elif flow == "ask_next":
        prox_idx  = etapa_idx + 1
        prox_cor  = ETAPA_COLORS[prox_idx]
        prox_nome = ETAPA_LABELS[prox_idx]
        ts_fim    = st.session_state.get("_ts_fim", time.time())
        dur       = fmt_tempo(ts_fim - ts_inicio) if ts_inicio else "--"

        render_stepper(etapa_idx)  # mostra etapa atual como active (já rodou, mas mosramos onde estamos)

        st.markdown(f"""
        <div style="text-align:center;margin-bottom:10px">
            <div style="background:#f0fdf4;border:1.5px solid #bbf7d0;border-radius:10px;
                padding:9px 16px;display:inline-block;margin-bottom:8px;">
                <span style="font-size:.6rem;font-weight:700;color:#16a34a;letter-spacing:.1em;text-transform:uppercase;">
                    ✓ {ETAPA_LABELS[etapa_idx]} CONCLUÍDA &nbsp;·&nbsp; {dur}
                </span>
            </div>
            <div class="vi-num"><span>#</span>{pedido}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="vi-ask-card">
            <div class="vi-ask-title" style="color:{prox_cor};">
                Próxima etapa: {prox_nome} — Quem vai realizar?
            </div>
        """, unsafe_allow_html=True)

        ask_mode = st.session_state.get("_ask_mode")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
            if st.button(f"✓ Sou eu  ({operador.split()[0]})", use_container_width=True, key="btn_mesmo"):
                _avancar(etapa_idx, pedido, operador)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            if st.button("👤 Outro operador", use_container_width=True, key="btn_outro"):
                st.session_state["_ask_mode"] = "select"
                st.rerun()

        if ask_mode == "select":
            outros = [op for op in OPERADORES if op != operador]
            outro  = st.selectbox("Operador", ["— Selecione —"] + outros,
                                  key="sel_prox_op", label_visibility="collapsed")
            st.markdown('<div class="vi-btn-blue" style="margin-top:8px">', unsafe_allow_html=True)
            if st.button("▶ Confirmar e Iniciar", use_container_width=True, key="btn_conf_outro"):
                if outro == "— Selecione —":
                    st.markdown('<div class="vi-alert vi-err">⚠️ Selecione.</div>', unsafe_allow_html=True)
                else:
                    _avancar(etapa_idx, pedido, outro)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # ask-card

    # ══ DONE ═══════════════════════════════════════════
    elif flow == "done":
        ts_fim = st.session_state.get("_ts_fim", time.time())
        dur    = fmt_tempo(ts_fim - ts_inicio) if ts_inicio else "--"
        st.markdown(f"""
        <div class="vi-done-card">
            <div style="font-size:2.8rem;margin-bottom:6px">🎉</div>
            <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:900;color:#16a34a;margin-bottom:4px">Pedido Concluído!</div>
            <div style="font-family:'DM Mono',monospace;font-size:2.2rem;font-weight:700;color:#111827;margin:8px 0">#{pedido}</div>
            <div style="font-size:.7rem;color:#6b7280">Todas as etapas finalizadas · {dur}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
        if st.button("▶  Iniciar Novo Pedido", use_container_width=True, key="btn_novo"):
            st.session_state.update({
                "_flow": "input", "_etapa_idx": 0,
                "_pedido": None, "_ts_inicio": None, "_ts_fim": None, "_ask_mode": None,
            })
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # fecha card
    st.markdown('</div></div>', unsafe_allow_html=True)

    # botão de trocar operador fora do card
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    if st.button("⏏  Trocar Operador / Sair", use_container_width=True, key="btn_sair"):
        for k in list(st.session_state.keys()):
            st.session_state.pop(k, None)
        st.rerun()


def _avancar(etapa_atual, pedido, proximo_op):
    prox = etapa_atual + 1
    st.session_state.update({
        "_operador":  proximo_op,
        "_etapa_idx": prox,
        "_flow":      "confirm",
        "_pedido":    pedido,
        "_ts_inicio": None,
        "_ts_fim":    None,
        "_ask_mode":  None,
    })
    st.rerun()


# ════════════════════════════════════════════════════════════
# TELA LOGIN GERÊNCIA
# ════════════════════════════════════════════════════════════
def tela_login_gerencia():
    st.markdown(f'<div class="vi-wordmark">{logo_html}</div>', unsafe_allow_html=True)
    st.markdown('<div class="vi-card"><div class="vi-body">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:18px">
        <div style="font-size:1rem;font-weight:700;color:#111827">Área da Gerência</div>
        <div style="font-size:.72rem;color:#9ca3af;margin-top:3px">Informe a senha de acesso</div>
    </div>""", unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password", placeholder="••••••••", label_visibility="collapsed")
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="vi-btn-blue">', unsafe_allow_html=True)
    if st.button("🔓 Acessar", use_container_width=True, key="btn_ger_login"):
        if senha == SENHA_GERENCIA:
            st.session_state["_gerencia_ok"] = True
            st.rerun()
        else:
            st.markdown('<div class="vi-alert vi-err">❌ Senha incorreta.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    if st.button("← Voltar", use_container_width=True, key="btn_volta_ger"):
        st.session_state.pop("_modo", None)
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TELA EXTRATO
# ════════════════════════════════════════════════════════════
def tela_extrato():
    conc = carregar_concluidos()
    pend = carregar_pedidos()
    hist = carregar_historico()

    st.markdown(f'<div class="vi-wordmark">{logo_html}</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;margin-bottom:14px"><div style="font-size:.95rem;font-weight:700;color:#111827">Extrato de Produção</div><div style="font-size:.68rem;color:#9ca3af">Consulta, filtros e relatórios</div></div>', unsafe_allow_html=True)

    ts = len([h for h in hist if h.get("etapa")==ETAPAS[0]])
    te = len([h for h in hist if h.get("etapa")==ETAPAS[1]])
    tc = len([h for h in hist if h.get("etapa")==ETAPAS[2]])
    tk = len(conc)
    c1,c2,c3,c4 = st.columns(4)
    for col,lab,val,cor in [(c1,"📦 Sep.",ts,"#1D4ED8"),(c2,"📬 Emb.",te,"#7C3AED"),(c3,"✅ Conf.",tc,"#16a34a"),(c4,"🎯 Conc.",tk,"#DC2626")]:
        with col:
            st.markdown(f'<div class="vi-card" style="padding:12px;text-align:center;border-radius:14px"><div style="font-size:.55rem;color:#9ca3af;text-transform:uppercase;letter-spacing:.1em;font-weight:700">{lab}</div><div style="font-size:1.7rem;font-weight:700;color:{cor};font-family:\'DM Mono\',monospace">{val}</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    a1,a2,a3 = st.tabs(["📅 Histórico","📋 Concluídos","⏳ Em Andamento"])

    with a1:
        if not hist:
            st.markdown('<div class="vi-alert vi-inf">ℹ️ Nenhuma operação registrada.</div>', unsafe_allow_html=True)
        else:
            df = pd.DataFrame(hist)
            def pd_dt(s):
                try: return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
                except: return pd.NaT
            df["_dt"] = df["data"].apply(pd_dt)
            from datetime import date, timedelta as td
            hoje = date.today()
            cf1,cf2,cf3,cf4 = st.columns(4)
            with cf1: di = st.date_input("Início",value=hoje-td(days=7),key="di",format="DD/MM/YYYY")
            with cf2: df2 = st.date_input("Fim",value=hoje,key="df2",format="DD/MM/YYYY")
            with cf3:
                ops=["Todos"]+sorted(df["operador"].dropna().unique().tolist())
                opf=st.selectbox("Func.",ops,key="hist_op")
            with cf4:
                ets=["Todas"]+ETAPAS
                etf=st.selectbox("Etapa",ets,key="hist_et")
            mask=(df["_dt"]>=pd.Timestamp(di))&(df["_dt"]<=pd.Timestamp(df2))
            dff=df[mask].copy()
            if opf!="Todos": dff=dff[dff["operador"]==opf]
            if etf!="Todas": dff=dff[dff["etapa"]==etf]
            dff=dff.sort_values("data_hora",ascending=False)
            st.markdown(f'<div class="vi-alert vi-inf">🔍 <b>{len(dff)}</b> resultado(s)</div>',unsafe_allow_html=True)
            if len(dff):
                if opf=="Todos":
                    r=dff.groupby(["operador","etapa"]).size().reset_index(name="Qtd.")
                    r.columns=["Funcionário","Etapa","Qtd."]; st.dataframe(r,use_container_width=True,hide_index=True)
                    st.markdown('<hr class="vi-hr">',unsafe_allow_html=True)
                de=dff[["data_hora","pedido","operador","etapa","status_pedido"]].rename(columns={"data_hora":"Data/Hora","pedido":"Pedido","operador":"Funcionário","etapa":"Etapa","status_pedido":"Status"})
                de["Status"]=de["Status"].map({"em_andamento":"⏳","concluido":"✅"}).fillna(de["Status"])
                st.dataframe(de,use_container_width=True,hide_index=True)
                na=f"extrato_{opf.replace(' ','_')}_{di.strftime('%d%m%Y')}"
                d1,d2=st.columns(2)
                with d1: st.download_button("⬇️ CSV",data=de.to_csv(index=False).encode("utf-8"),file_name=f"{na}.csv",mime="text/csv",use_container_width=True,key="dl_csv")
                with d2:
                    xb=BytesIO()
                    with pd.ExcelWriter(xb,engine="openpyxl") as w: de.to_excel(w,index=False,sheet_name="Histórico")
                    xb.seek(0)
                    st.download_button("⬇️ Excel",data=xb.getvalue(),file_name=f"{na}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="dl_xlsx")

    with a2:
        if conc:
            dc=pd.DataFrame(conc).rename(columns={"pedido":"Pedido","op_sep":"Op. Sep.","dt_sep":"Data Sep.","op_emb":"Op. Emb.","dt_emb":"Data Emb.","op_conf":"Op. Conf.","dt_conf":"Data Conf."}).drop(columns=["etapa"],errors="ignore")
            st.dataframe(dc,use_container_width=True,hide_index=True)
            xb2=BytesIO()
            with pd.ExcelWriter(xb2,engine="openpyxl") as w: dc.to_excel(w,index=False,sheet_name="Concluídos")
            xb2.seek(0)
            e1,e2=st.columns(2)
            with e1: st.download_button("⬇️ CSV",data=dc.to_csv(index=False).encode("utf-8"),file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.csv",mime="text/csv",use_container_width=True,key="dl_conc_csv")
            with e2: st.download_button("⬇️ Excel",data=xb2.getvalue(),file_name=f"concluidos_{datetime.now().strftime('%d%m%Y')}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="dl_conc_xlsx")
        else:
            st.markdown('<div class="vi-alert vi-inf">ℹ️ Nenhum pedido finalizado.</div>',unsafe_allow_html=True)

    with a3:
        if pend:
            el={1:"📬 Aguard. Embalagem",2:"✅ Aguard. Conferência"}
            rows=[{"Pedido":f"#{d['pedido']}","Etapa":el.get(d.get("etapa",0),"—"),"Op. Sep.":d.get("op_sep","—"),"Op. Emb.":d.get("op_emb","—")} for p,d in pend.items()]
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        else:
            st.markdown('<div class="vi-alert vi-ok">✅ Nenhum pedido em andamento.</div>',unsafe_allow_html=True)

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    if st.button("← Sair da Gerência", use_container_width=True, key="btn_sair_ger"):
        st.session_state.pop("_modo",None); st.session_state.pop("_gerencia_ok",None); st.rerun()


# ════════════════════════════════════════════════════════════
# ROTEADOR
# ════════════════════════════════════════════════════════════
modo = st.session_state.get("_modo")

if not modo:
    if "_operador" in st.session_state:
        tela_operador()
    else:
        tela_inicial()
elif modo == "gerencia":
    if not st.session_state.get("_gerencia_ok"):
        tela_login_gerencia()
    else:
        tela_extrato()
