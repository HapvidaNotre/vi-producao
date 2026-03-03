import streamlit as st
import sqlite3
import time
import base64
import os
from datetime import datetime
from pathlib import Path
import streamlit.components.v1 as components

# ─────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────
st.set_page_config(
    page_title="Vi Lingerie - Producao",
    page_icon="👗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

OPERADORES = ["Lucivanio", "Enagio", "Daniel", "Italo", "Cildenir", "Samya", "Neide", "Eduardo", "Talyson"]
ETAPAS = ["Separacao", "Conferencia", "Embalagem"]
ETAPAS_LABEL = ["Separação", "Conferência", "Embalagem"]
ADMIN_SENHA = "vi2025"
DB_PATH = Path(__file__).parent / "producao.db"

# ─────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido TEXT NOT NULL,
            operador TEXT NOT NULL,
            etapa TEXT NOT NULL,
            etapa_idx INTEGER NOT NULL,
            tempo_segundos INTEGER NOT NULL,
            data TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

def salvar_registro(pedido, operador, etapa, etapa_idx, tempo):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO registros (pedido, operador, etapa, etapa_idx, tempo_segundos, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pedido, operador, etapa, etapa_idx, tempo, datetime.now().strftime("%d/%m/%Y %H:%M")))
    con.commit()
    con.close()

def buscar_registros():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM registros ORDER BY id DESC")
    rows = cur.fetchall()
    con.close()
    return rows

def limpar_registros():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM registros")
    con.commit()
    con.close()

init_db()

# ─────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────
def fmt_tempo(s):
    if s < 60:
        return f"{s}s"
    m, sec = divmod(s, 60)
    if m < 60:
        return f"{m}m {sec:02d}s"
    h, mi = divmod(m, 60)
    return f"{h}h {mi:02d}m"

def get_logo_b64():
    logo_path = Path(__file__).parent / "logo_vi.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def media(lst):
    return int(sum(lst) / len(lst)) if lst else 0

# ─────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────
defaults = {
    "tela": "home",          # home | producao | admin | admin_login
    "operador": None,
    "pedido": None,
    "etapa_idx": 0,
    "rodando": False,
    "inicio": None,
    "tempo_acumulado": 0,
    "modal": None,           # None | proxima | quem
    "erro_pedido": False,
    "erro_senha": False,
    "pedido_proximo": None,  # pedido passado para proximo operador
    "etapa_proximo": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────
#  CSS
# ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #F7F5F2 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
footer { display: none !important; }
#MainMenu { display: none; }
.block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 660px !important; }

/* ── LOGO ── */
.logo-box { text-align: center; margin-bottom: 2rem; }
.logo-box img { height: 58px; object-fit: contain; }

/* ── OPERADOR GRID (handled via component) ── */

/* ── SECTION LABEL ── */
.section-label {
    font-size: 11px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    color: #8C8480; margin-bottom: 1rem; text-align: center;
}

/* ── STEPPER ── */
.stepper { display: flex; align-items: flex-start; gap: 0; margin-bottom: 1.5rem; }
.step { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 5px; }
.step-dot {
    width: 28px; height: 28px; border-radius: 50%;
    border: 2px solid #E8E3DC; background: #F0EDE8;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; color: #8C8480; z-index: 1;
}
.step-dot.active { background: #C8566A; border-color: #C8566A; color: #fff; box-shadow: 0 0 0 4px rgba(200,86,106,0.15); }
.step-dot.done { background: #4A7C59; border-color: #4A7C59; color: #fff; }
.step-lbl { font-size: 10px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; color: #8C8480; text-align: center; }
.step-lbl.active { color: #C8566A; }
.step-lbl.done { color: #4A7C59; }
.step-line { flex: 1; height: 2px; background: #E8E3DC; margin-top: 13px; }
.step-line.done { background: #4A7C59; }

/* ── CARD ── */
.vi-card {
    background: #FFFFFF; border: 1.5px solid #E8E3DC;
    border-radius: 14px; padding: 24px;
    box-shadow: 0 2px 14px rgba(0,0,0,0.05); margin-bottom: 1rem;
}

/* ── BADGE ── */
.badge-op {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 100px;
    background: #F5E8EB; color: #C8566A;
    font-size: 12px; font-weight: 600; margin-bottom: 1rem;
}
.badge-green { background: #E8F2EC; color: #4A7C59; }

/* ── TIMER ── */
.timer-wrap { text-align: center; padding: 12px 0; }
.timer-num {
    font-family: 'DM Mono', monospace;
    font-size: 56px; font-weight: 500;
    color: #C8566A; letter-spacing: -2px; line-height: 1;
}
.timer-stopped { color: #1A1714; }
.pedido-lbl { font-size: 12px; font-weight: 600; color: #8C8480; text-align: center; margin-bottom: 2px; }
.pedido-num {
    font-family: 'DM Mono', monospace; font-size: 22px; font-weight: 500;
    color: #1A1714; text-align: center; margin-bottom: 16px;
}
.etapa-lbl { font-size: 13px; color: #8C8480; text-align: center; margin-bottom: 20px; }

/* ── BUTTONS ── */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important; letter-spacing: 0.5px !important;
    border-radius: 10px !important; transition: all .2s !important;
    height: 52px !important; font-size: 15px !important;
}
.btn-primary > button {
    background: #C8566A !important; color: #fff !important; border: none !important;
    box-shadow: 0 4px 14px rgba(200,86,106,0.25) !important; width: 100% !important;
}
.btn-primary > button:hover { background: #b04560 !important; transform: translateY(-1px) !important; }
.btn-dark > button {
    background: #1A1714 !important; color: #fff !important; border: none !important;
    width: 100% !important;
}
.btn-dark > button:hover { background: #333 !important; }
.btn-outline > button {
    background: transparent !important; color: #1A1714 !important;
    border: 1.5px solid #E8E3DC !important;
}
.btn-outline > button:hover { border-color: #C8566A !important; color: #C8566A !important; }
.btn-green > button {
    background: #4A7C59 !important; color: #fff !important; border: none !important;
    width: 100% !important;
}
.btn-sm > button { height: 38px !important; font-size: 12px !important; padding: 0 16px !important; }

/* ── MODAL ── */
.modal-overlay {
    position: fixed; inset: 0; background: rgba(26,23,20,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 999; backdrop-filter: blur(4px);
}
.modal-box {
    background: #fff; border-radius: 16px; padding: 32px;
    max-width: 380px; width: 90%; text-align: center;
    box-shadow: 0 8px 40px rgba(0,0,0,0.15);
}
.modal-icon { font-size: 40px; margin-bottom: 12px; }
.modal-title { font-size: 18px; font-weight: 700; margin-bottom: 8px; color: #1A1714; }
.modal-msg { font-size: 14px; color: #8C8480; margin-bottom: 24px; line-height: 1.6; }

/* ── ADMIN ── */
.stat-box {
    background: #fff; border: 1.5px solid #E8E3DC; border-radius: 12px;
    padding: 16px; text-align: center;
}
.stat-num { font-family: 'DM Mono', monospace; font-size: 30px; font-weight: 500; color: #C8566A; }
.stat-lbl { font-size: 11px; font-weight: 600; color: #8C8480; letter-spacing: 0.5px; margin-top: 4px; }

/* table */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 9px 10px; font-size: 10px; font-weight: 700;
     letter-spacing: 1px; text-transform: uppercase; color: #8C8480; border-bottom: 1.5px solid #E8E3DC; }
td { padding: 11px 10px; border-bottom: 1px solid #F0EDE8; color: #1A1714; }

/* tags */
.tag { display: inline-block; padding: 2px 8px; border-radius: 100px; font-size: 10px; font-weight: 700; }
.tag-sep { background: #EBF0FB; color: #3B5EC6; }
.tag-conf { background: #FBF2E6; color: #C47B2A; }
.tag-emb { background: #E8F2EC; color: #4A7C59; }

/* input */
.stTextInput > div > div > input {
    border: 1.5px solid #E8E3DC !important; border-radius: 10px !important;
    background: #F7F5F2 !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important; padding: 14px 16px !important; color: #1A1714 !important;
}
.stTextInput > div > div > input:focus { border-color: #C8566A !important; box-shadow: none !important; }
label { font-size: 12px !important; font-weight: 600 !important; color: #8C8480 !important; letter-spacing: 0.5px !important; }

/* admin footer btn */
.admin-footer { position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%); z-index: 100; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
#  LOGO COMPONENT
# ─────────────────────────────────────
def render_logo():
    b64 = get_logo_b64()
    if b64:
        st.markdown(f'<div class="logo-box"><img src="data:image/png;base64,{b64}" alt="Vi Lingerie"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="logo-box" style="font-size:24px;font-weight:700;color:#C8566A;">Vi Lingerie</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  STEPPER COMPONENT
# ─────────────────────────────────────
def render_stepper(etapa_idx):
    steps_html = ""
    for i, label in enumerate(ETAPAS_LABEL):
        if i < etapa_idx:
            dot_cls = "done"; lbl_cls = "done"
        elif i == etapa_idx:
            dot_cls = "active"; lbl_cls = "active"
        else:
            dot_cls = ""; lbl_cls = ""
        steps_html += f'<div class="step"><div class="step-dot {dot_cls}">{i+1}</div><div class="step-lbl {lbl_cls}">{label}</div></div>'
        if i < 2:
            line_cls = "done" if i < etapa_idx else ""
            steps_html += f'<div class="step-line {line_cls}"></div>'
    st.markdown(f'<div class="stepper">{steps_html}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TIMER LOGIC
# ─────────────────────────────────────
def get_elapsed():
    if st.session_state.rodando and st.session_state.inicio:
        return st.session_state.tempo_acumulado + int(time.time() - st.session_state.inicio)
    return st.session_state.tempo_acumulado

# ─────────────────────────────────────
#  TELA: HOME
# ─────────────────────────────────────
def tela_home():
    render_logo()
    st.markdown('<div class="section-label">Selecione o Operador</div>', unsafe_allow_html=True)

    # Restore pending state (outro operador)
    if st.session_state.pedido_proximo:
        pedido_restore = st.session_state.pedido_proximo
        etapa_restore = st.session_state.etapa_proximo
        st.info(f"📦 Pedido **{pedido_restore}** aguardando: **{ETAPAS_LABEL[etapa_restore]}**")

    # Build operators JSON for the component
    ops_json = str(OPERADORES).replace("'", '"')

    # Render interactive 3D avatar grid via HTML component
    clicked = components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700&display=swap" rel="stylesheet">
    <style>
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{
        font-family: 'DM Sans', sans-serif;
        background: transparent;
        display: flex; flex-direction: column; align-items: center;
        padding: 4px 0 12px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
        width: 100%;
        max-width: 520px;
      }}
      .op-wrap {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 9px;
        cursor: pointer;
        perspective: 600px;
      }}
      .avatar {{
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: linear-gradient(145deg, #D9617A, #9E3F52);
        box-shadow:
          0 6px 0 #7a2d3e,
          0 8px 16px rgba(158,63,82,0.45),
          inset 0 2px 4px rgba(255,255,255,0.25),
          inset 0 -2px 4px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        font-weight: 700;
        color: #fff;
        text-shadow: 0 1px 3px rgba(0,0,0,0.25);
        transition:
          transform 0.18s cubic-bezier(.34,1.56,.64,1),
          box-shadow 0.18s ease,
          background 0.15s ease;
        transform-style: preserve-3d;
        user-select: none;
        position: relative;
        overflow: hidden;
      }}
      /* shine overlay */
      .avatar::before {{
        content: '';
        position: absolute;
        top: -30%;
        left: -20%;
        width: 60%;
        height: 60%;
        background: radial-gradient(ellipse, rgba(255,255,255,0.35) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        transition: opacity 0.2s;
      }}
      .op-wrap:hover .avatar {{
        transform: translateY(-6px) rotateX(12deg) scale(1.08);
        box-shadow:
          0 12px 0 #7a2d3e,
          0 18px 32px rgba(158,63,82,0.55),
          inset 0 2px 6px rgba(255,255,255,0.35),
          inset 0 -2px 4px rgba(0,0,0,0.15);
        background: linear-gradient(145deg, #E06B82, #B04A5E);
      }}
      .op-wrap:active .avatar {{
        transform: translateY(2px) rotateX(4deg) scale(0.96);
        box-shadow:
          0 2px 0 #7a2d3e,
          0 4px 10px rgba(158,63,82,0.4),
          inset 0 2px 6px rgba(0,0,0,0.2);
        background: linear-gradient(145deg, #B04A5E, #8B3347);
        transition: transform 0.08s ease, box-shadow 0.08s ease;
      }}
      /* ripple */
      .ripple {{
        position: absolute;
        border-radius: 50%;
        background: rgba(255,255,255,0.4);
        transform: scale(0);
        animation: ripple-anim 0.5s linear;
        pointer-events: none;
      }}
      @keyframes ripple-anim {{
        to {{ transform: scale(3.5); opacity: 0; }}
      }}
      .op-name {{
        font-size: 12px;
        font-weight: 600;
        color: #1A1714;
        text-align: center;
        letter-spacing: 0.2px;
        line-height: 1.2;
      }}
    </style>
    </head>
    <body>
    <div class="grid" id="grid"></div>
    <script>
      const OPERADORES = {ops_json};
      const grid = document.getElementById('grid');

      OPERADORES.forEach(op => {{
        const wrap = document.createElement('div');
        wrap.className = 'op-wrap';

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = op[0].toUpperCase();

        const name = document.createElement('div');
        name.className = 'op-name';
        name.textContent = op;

        // Ripple effect on click
        avatar.addEventListener('click', function(e) {{
          // ripple
          const ripple = document.createElement('span');
          ripple.className = 'ripple';
          const rect = avatar.getBoundingClientRect();
          const size = Math.max(rect.width, rect.height);
          ripple.style.width = ripple.style.height = size + 'px';
          ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
          ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
          avatar.appendChild(ripple);
          setTimeout(() => ripple.remove(), 600);

          // Send to Streamlit after short delay for animation
          setTimeout(() => {{
            window.parent.postMessage({{
              type: 'streamlit:setComponentValue',
              value: op
            }}, '*');
          }}, 120);
        }});

        wrap.appendChild(avatar);
        wrap.appendChild(name);
        grid.appendChild(wrap);
      }});
    </script>
    </body>
    </html>
    """, height=320)

    # Handle click from component
    if clicked and isinstance(clicked, str) and clicked in OPERADORES:
        op = clicked
        st.session_state.operador = op
        if st.session_state.pedido_proximo:
            st.session_state.pedido = st.session_state.pedido_proximo
            st.session_state.etapa_idx = st.session_state.etapa_proximo
            st.session_state.pedido_proximo = None
            st.session_state.etapa_proximo = None
        else:
            st.session_state.pedido = None
            st.session_state.etapa_idx = 0
        st.session_state.rodando = False
        st.session_state.inicio = None
        st.session_state.tempo_acumulado = 0
        st.session_state.tela = "producao"
        st.rerun()

# ─────────────────────────────────────
#  TELA: PRODUCAO
# ─────────────────────────────────────
def tela_producao():
    render_logo()
    render_stepper(st.session_state.etapa_idx)

    op = st.session_state.operador
    etapa_idx = st.session_state.etapa_idx
    etapa_label = ETAPAS_LABEL[etapa_idx]

    # Badge operador
    st.markdown(f'<div class="badge-op">● {op}</div>', unsafe_allow_html=True)

    # ── FASE: Entrada do pedido ──
    if not st.session_state.rodando and st.session_state.tempo_acumulado == 0 and not st.session_state.modal:
        with st.container():
            st.markdown(f'<div style="font-size:13px;color:#8C8480;margin-bottom:6px;">Etapa: <strong>{etapa_label}</strong></div>', unsafe_allow_html=True)

            pedido_default = st.session_state.pedido or ""
            pedido_input = st.text_input("NÚMERO DO PEDIDO", value=pedido_default, placeholder="Ex: #00123")

            if st.session_state.erro_pedido:
                st.markdown('<span style="color:#C8566A;font-size:12px;">⚠ Digite o número do pedido.</span>', unsafe_allow_html=True)

            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("▶  INICIAR", use_container_width=True):
                if not pedido_input.strip():
                    st.session_state.erro_pedido = True
                    st.rerun()
                else:
                    st.session_state.erro_pedido = False
                    st.session_state.pedido = pedido_input.strip()
                    st.session_state.rodando = True
                    st.session_state.inicio = time.time()
                    st.session_state.tempo_acumulado = 0
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
        if st.button("← Voltar", use_container_width=False):
            st.session_state.tela = "home"
            st.session_state.pedido_proximo = None
            st.session_state.etapa_proximo = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── FASE: Rodando ──
    elif st.session_state.rodando:
        elapsed = get_elapsed()
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        timer_str = f"{h:02d}:{m:02d}:{s:02d}"

        st.markdown(f'<div class="pedido-lbl">PEDIDO</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pedido-num">{st.session_state.pedido}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="timer-wrap"><div class="timer-num">{timer_str}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="etapa-lbl">Etapa: <strong>{etapa_label}</strong></div>', unsafe_allow_html=True)

        st.markdown('<div class="btn-dark">', unsafe_allow_html=True)
        if st.button("■  FINALIZAR", use_container_width=True):
            # Save elapsed
            st.session_state.tempo_acumulado = get_elapsed()
            st.session_state.rodando = False
            st.session_state.inicio = None
            # Save to DB
            salvar_registro(
                st.session_state.pedido,
                st.session_state.operador,
                ETAPAS[etapa_idx],
                etapa_idx,
                st.session_state.tempo_acumulado
            )
            if etapa_idx < 2:
                st.session_state.modal = "proxima"
            else:
                st.session_state.modal = "concluido"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Auto-refresh every second
        time.sleep(1)
        st.rerun()

    # ── MODAL: Próxima etapa? ──
    elif st.session_state.modal == "proxima":
        elapsed = st.session_state.tempo_acumulado
        next_label = ETAPAS_LABEL[etapa_idx + 1]

        st.markdown(f"""
        <div style="background:#fff;border:1.5px solid #E8E3DC;border-radius:14px;padding:28px;text-align:center;box-shadow:0 2px 14px rgba(0,0,0,0.05);margin-bottom:1rem;">
          <div style="font-size:36px;margin-bottom:12px;">✅</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;">Etapa Concluída!</div>
          <div style="font-size:14px;color:#8C8480;margin-bottom:20px;line-height:1.6;">
            <strong>{etapa_label}</strong> finalizada em <strong>{fmt_tempo(elapsed)}</strong>.<br>
            Deseja ir para <strong>{next_label}</strong>?
          </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button(f"Sim, ir para {next_label}", use_container_width=True):
                st.session_state.modal = "quem"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("Encerrar pedido", use_container_width=True):
                st.session_state.modal = None
                st.session_state.pedido = None
                st.session_state.etapa_idx = 0
                st.session_state.tempo_acumulado = 0
                st.session_state.tela = "home"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── MODAL: Quem faz? ──
    elif st.session_state.modal == "quem":
        next_label = ETAPAS_LABEL[etapa_idx + 1]
        st.markdown(f"""
        <div style="background:#fff;border:1.5px solid #E8E3DC;border-radius:14px;padding:28px;text-align:center;box-shadow:0 2px 14px rgba(0,0,0,0.05);margin-bottom:1rem;">
          <div style="font-size:36px;margin-bottom:12px;">👤</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;">Quem faz a próxima etapa?</div>
          <div style="font-size:14px;color:#8C8480;margin-bottom:20px;">
            {etapa_label} &rarr; <strong>{next_label}</strong>
          </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Eu mesmo", use_container_width=True):
                st.session_state.etapa_idx += 1
                st.session_state.tempo_acumulado = 0
                st.session_state.modal = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("Outro operador", use_container_width=True):
                # Save pedido info for next operator
                st.session_state.pedido_proximo = st.session_state.pedido
                st.session_state.etapa_proximo = etapa_idx + 1
                st.session_state.pedido = None
                st.session_state.etapa_idx = 0
                st.session_state.tempo_acumulado = 0
                st.session_state.modal = None
                st.session_state.tela = "home"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ── MODAL: Pedido concluído ──
    elif st.session_state.modal == "concluido":
        elapsed = st.session_state.tempo_acumulado
        st.markdown(f"""
        <div style="background:#fff;border:1.5px solid #E8E3DC;border-radius:14px;padding:28px;text-align:center;box-shadow:0 2px 14px rgba(0,0,0,0.05);margin-bottom:1rem;">
          <div style="font-size:40px;margin-bottom:12px;">🎉</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px;">Pedido Concluído!</div>
          <div style="font-size:14px;color:#8C8480;margin-bottom:20px;line-height:1.6;">
            Pedido <strong>{st.session_state.pedido}</strong> finalizado com sucesso!<br>
            Embalagem: <strong>{fmt_tempo(elapsed)}</strong>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        if st.button("Voltar ao início", use_container_width=True):
            st.session_state.modal = None
            st.session_state.pedido = None
            st.session_state.etapa_idx = 0
            st.session_state.tempo_acumulado = 0
            st.session_state.tela = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: ADMIN LOGIN
# ─────────────────────────────────────
def tela_admin_login():
    render_logo()
    st.markdown('<div class="section-label">Área Administrativa</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="vi-card">', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:32px;margin-bottom:8px;">🔐</div>', unsafe_allow_html=True)
        senha = st.text_input("SENHA", type="password", placeholder="Digite a senha")
        if st.session_state.erro_senha:
            st.markdown('<span style="color:#C8566A;font-size:12px;">⚠ Senha incorreta.</span>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
            if st.button("← Voltar", use_container_width=True):
                st.session_state.erro_senha = False
                st.session_state.tela = "home"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            if st.button("Entrar", use_container_width=True):
                if senha == ADMIN_SENHA:
                    st.session_state.erro_senha = False
                    st.session_state.tela = "admin"
                    st.rerun()
                else:
                    st.session_state.erro_senha = True
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
#  TELA: ADMIN PANEL
# ─────────────────────────────────────
def tela_admin():
    render_logo()

    col_title, col_back = st.columns([3, 1])
    with col_title:
        st.markdown('<div class="section-label" style="text-align:left;margin-bottom:2px;">Painel Administrativo</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:20px;font-weight:700;margin-bottom:1rem;">Visão Geral</div>', unsafe_allow_html=True)
    with col_back:
        st.markdown('<div class="btn-outline btn-sm">', unsafe_allow_html=True)
        if st.button("← Voltar"):
            st.session_state.tela = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    regs = buscar_registros()

    # Stats
    pedidos_completos = list({r[1] for r in regs if r[4] == 2})
    ops_ativos = list({r[2] for r in regs})
    total_tempo = sum(r[5] for r in regs)
    avg = media([r[5] for r in regs]) // 60 if regs else 0

    c1, c2, c3 = st.columns(3)
    for col, num, lbl in zip([c1, c2, c3],
                              [len(pedidos_completos), len(ops_ativos), f"{avg}m"],
                              ["Pedidos Concluídos", "Operadores Ativos", "Tempo Médio"]):
        with col:
            st.markdown(f"""
            <div class="stat-box">
              <div class="stat-num">{num}</div>
              <div class="stat-lbl">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Por operador
    st.markdown('<div style="font-size:13px;font-weight:700;margin-bottom:10px;">Desempenho por Operador</div>', unsafe_allow_html=True)
    op_map = {}
    for r in regs:
        op = r[2]
        if op not in op_map:
            op_map[op] = {"pedidos": set(), "sep": [], "conf": [], "emb": []}
        op_map[op]["pedidos"].add(r[1])
        if r[4] == 0: op_map[op]["sep"].append(r[5])
        if r[4] == 1: op_map[op]["conf"].append(r[5])
        if r[4] == 2: op_map[op]["emb"].append(r[5])

    if op_map:
        rows_html = ""
        for op, d in op_map.items():
            rows_html += f"""
            <tr>
              <td><span style="font-weight:600">{op}</span></td>
              <td>{len(d['pedidos'])}</td>
              <td>{fmt_tempo(media(d['sep'])) if d['sep'] else '—'}</td>
              <td>{fmt_tempo(media(d['conf'])) if d['conf'] else '—'}</td>
              <td>{fmt_tempo(media(d['emb'])) if d['emb'] else '—'}</td>
            </tr>"""
        st.markdown(f"""
        <div class="vi-card">
        <table><thead><tr>
          <th>Operador</th><th>Pedidos</th><th>Separação</th><th>Conferência</th><th>Embalagem</th>
        </tr></thead><tbody>{rows_html}</tbody></table>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="vi-card" style="text-align:center;color:#8C8480;padding:24px;">Nenhum registro ainda.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Histórico
    col_h, col_clr = st.columns([3, 1])
    with col_h:
        st.markdown('<div style="font-size:13px;font-weight:700;margin-bottom:10px;">Histórico de Pedidos</div>', unsafe_allow_html=True)
    with col_clr:
        if st.button("🗑 Limpar dados"):
            limpar_registros()
            st.rerun()

    tag_cls = ["tag-sep", "tag-conf", "tag-emb"]
    if regs:
        hist_html = ""
        for r in regs[:60]:
            hist_html += f"""
            <tr>
              <td><span style="font-family:'DM Mono',monospace;font-size:12px">{r[1]}</span></td>
              <td>{r[2]}</td>
              <td><span class="tag {tag_cls[r[4]]}">{r[3]}</span></td>
              <td style="font-family:'DM Mono',monospace;font-size:12px">{fmt_tempo(r[5])}</td>
              <td style="color:#8C8480;font-size:12px">{r[6]}</td>
            </tr>"""
        st.markdown(f"""
        <div class="vi-card">
        <table><thead><tr>
          <th>Pedido</th><th>Operador</th><th>Etapa</th><th>Tempo</th><th>Data</th>
        </tr></thead><tbody>{hist_html}</tbody></table>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="vi-card" style="text-align:center;color:#8C8480;padding:24px;">Nenhum registro ainda.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Exportar CSV
    if regs:
        import csv, io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["ID", "Pedido", "Operador", "Etapa", "Etapa_Idx", "Tempo_Segundos", "Data"])
        for r in regs:
            writer.writerow(r)
        st.download_button(
            label="⬇  Exportar Relatório CSV",
            data=buf.getvalue().encode("utf-8"),
            file_name=f"vi_producao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ─────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────
tela = st.session_state.tela
if tela == "home":
    tela_home()
elif tela == "producao":
    tela_producao()
elif tela == "admin_login":
    tela_admin_login()
elif tela == "admin":
    tela_admin()

# ── Admin footer button (only on home) ──
if st.session_state.tela == "home":
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([2, 1, 2])
    with col_c:
        st.markdown('<div class="btn-outline btn-sm">', unsafe_allow_html=True)
        if st.button("⚙ Admin", use_container_width=True):
            st.session_state.tela = "admin_login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
