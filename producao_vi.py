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

# =============================================================================
# CONFIGURAÇÕES GLOBAIS
# =============================================================================
ETAPAS = ["Separação do Pedido", "Mesa de Embalagem", "Conferência do Pedido"]
ETAPA_ICONS = ["📦", "📬", "✅"]
ETAPA_CORES = ["#1565C0", "#6A0DAD", "#1B5E20"]

OPERADORES = [
    "Lucivanio",
    "Enágio",
    "Daniel",
    "Ítalo",
    "Cildenir",
    "Samya",
    "Neide",
    "Eduardo",
    "Talyson",
]

SENHA_GERENCIA = "vi2026"

# =============================================================================
# PERSISTÊNCIA DE DADOS
# =============================================================================
STATE_DIR = "vi_producao_state"
os.makedirs(STATE_DIR, exist_ok=True)

FILE_PEDIDOS    = os.path.join(STATE_DIR, "pedidos.json")
FILE_CONCLUIDOS = os.path.join(STATE_DIR, "concluidos.json")
FILE_HISTORICO  = os.path.join(STATE_DIR, "historico.json")   # todas as operações registradas


def _carregar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def carregar_pedidos():
    return _carregar(FILE_PEDIDOS)


def salvar_pedidos(data):
    _salvar(FILE_PEDIDOS, data)


def carregar_concluidos():
    d = _carregar(FILE_CONCLUIDOS)
    return d if isinstance(d, list) else []


def salvar_concluidos(data):
    _salvar(FILE_CONCLUIDOS, data)


def carregar_historico():
    """Retorna lista de todas as operações já registradas (nunca apagadas)."""
    d = _carregar(FILE_HISTORICO)
    return d if isinstance(d, list) else []


def registrar_historico(pedido_num, operador, etapa_nome, data_hora, status_pedido="em_andamento"):
    """Adiciona uma linha ao histórico permanente."""
    hist = carregar_historico()
    hist.append({
        "data_hora":     data_hora,
        "data":          data_hora.split(" ")[0] if " " in data_hora else data_hora,  # dd/mm/yyyy
        "pedido":        pedido_num,
        "operador":      operador,
        "etapa":         etapa_nome,
        "status_pedido": status_pedido,
    })
    _salvar(FILE_HISTORICO, hist)


# =============================================================================
# HELPERS DE DATA/HORA
# =============================================================================
def agora_str():
    from datetime import timezone, timedelta
    br = timezone(timedelta(hours=-3))
    return datetime.now(br).strftime("%d/%m/%Y %H:%M")


# =============================================================================
# LOGO (tenta carregar logo_vi.png do diretório)
# =============================================================================
import base64 as _b64


def _get_logo_b64():
    for p in ["logo_vi.png", "../logo_vi.png"]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return _b64.b64encode(f.read()).decode()
    return ""


_logo_b64 = _get_logo_b64()
_logo_src = f"data:image/png;base64,{_logo_b64}" if _logo_b64 else ""

if _logo_b64:
    logo_tag = f'<img src="{_logo_src}" style="height:56px;object-fit:contain;display:block;margin:0 auto 8px;filter:drop-shadow(0 3px 10px rgba(139,0,0,.5));" />'
else:
    logo_tag = '<div style="font-size:1.3rem;font-weight:900;color:#fff;letter-spacing:.1em;text-align:center;margin-bottom:8px">VI LINGERIE</div>'

# =============================================================================
# CSS GLOBAL
# =============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stApp"] {{
    font-family: 'DM Sans', sans-serif !important;
    background: #0b0b14 !important;
    color: #e8e8f0 !important;
    min-height: 100vh;
}}
[data-testid="stSidebar"] {{ display:none !important; }}
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {{ display:none !important; }}
.block-container {{ padding: 2rem 1.5rem !important; max-width: 560px !important; margin: 0 auto !important; }}

/* ── CARD BASE ── */
.vi-card {{
    background: linear-gradient(158deg, #13132a 0%, #0d0d1e 100%);
    border: 1px solid rgba(139,0,0,.45);
    border-radius: 20px;
    padding: 36px 32px 32px;
    position: relative; overflow: hidden;
    box-shadow: 0 20px 50px rgba(0,0,0,.7);
    animation: vi-fadein .5s cubic-bezier(.22,1,.36,1) both;
}}
.vi-card::after {{
    content:''; position:absolute; top:0; left:0;
    width:35%; height:100%;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.03),transparent);
    animation: vi-shimmer 5s ease 1s infinite;
    pointer-events:none;
}}

/* ── ANIMAÇÕES ── */
@keyframes vi-fadein {{
    from {{ opacity:0; transform:translateY(18px); }}
    to   {{ opacity:1; transform:translateY(0); }}
}}
@keyframes vi-shimmer {{
    from {{ transform:translateX(-120%); }}
    to   {{ transform:translateX(300%); }}
}}
@keyframes vi-pulse {{
    0%,100% {{ opacity:1; }} 50% {{ opacity:.5; }}
}}
@keyframes vi-spin {{
    to {{ transform:rotate(360deg); }}
}}
@keyframes vi-glow {{
    0%,100% {{ box-shadow:0 0 0 0 rgba(139,0,0,0); }}
    50%      {{ box-shadow:0 0 22px 4px rgba(180,0,0,.28); }}
}}

/* ── LOADING SCREEN ── */
.vi-loading {{
    position:fixed; inset:0;
    background:#0b0b14;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    z-index:9999;
    animation: vi-fadein .3s ease;
}}
.vi-spinner {{
    width:48px; height:48px;
    border:3px solid rgba(139,0,0,.2);
    border-top-color:#dc2626;
    border-radius:50%;
    animation:vi-spin .8s linear infinite;
    margin:20px auto 14px;
}}
.vi-loading-text {{
    font-size:.82rem; font-weight:600;
    color:#9ca3af; letter-spacing:.12em;
    text-transform:uppercase;
    animation:vi-pulse 1.4s ease infinite;
}}

/* ── TÍTULO DA SEÇÃO ── */
.vi-section-title {{
    font-size:.68rem; font-weight:700;
    color:#6b7280; letter-spacing:.14em;
    text-transform:uppercase;
    margin-bottom:16px;
    display:flex; align-items:center; gap:8px;
}}
.vi-section-title::before {{
    content:''; display:inline-block;
    width:20px; height:2px;
    background:#8B0000; border-radius:2px;
}}

/* ── BADGE ETAPA ── */
.vi-etapa-badge {{
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 14px; border-radius:20px;
    font-size:.72rem; font-weight:700;
    letter-spacing:.06em; text-transform:uppercase;
    border:1px solid rgba(255,255,255,.12);
}}

/* ── PROGRESS STEPS ── */
.vi-steps {{
    display:flex; align-items:center; gap:0;
    margin:20px 0 28px;
}}
.vi-step {{
    flex:1; display:flex; flex-direction:column;
    align-items:center; gap:6px; position:relative;
}}
.vi-step-dot {{
    width:32px; height:32px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:.8rem; font-weight:700;
    border:2px solid rgba(255,255,255,.1);
    background:#1a1a2e; color:#6b7280;
    position:relative; z-index:1;
    transition:all .3s;
}}
.vi-step-dot.active {{
    background:#8B0000; border-color:#dc2626;
    color:#fff; box-shadow:0 0 14px rgba(220,38,38,.4);
}}
.vi-step-dot.done {{
    background:#1B5E20; border-color:#4caf50;
    color:#fff;
}}
.vi-step-label {{
    font-size:.6rem; font-weight:600;
    color:#6b7280; letter-spacing:.06em;
    text-align:center; line-height:1.3;
    text-transform:uppercase;
}}
.vi-step-label.active {{ color:#f87171; }}
.vi-step-label.done  {{ color:#66bb6a; }}
.vi-step-line {{
    flex:1; height:2px; margin-top:-22px;
    background:rgba(255,255,255,.08);
    position:relative; z-index:0;
}}
.vi-step-line.done {{ background:#4caf50; }}

/* ── PEDIDO CARD ── */
.vi-pedido-item {{
    background:rgba(255,255,255,.03);
    border:1px solid rgba(255,255,255,.08);
    border-radius:12px;
    padding:12px 16px;
    display:flex; align-items:center; gap:12px;
    margin-bottom:8px;
    cursor:pointer;
    transition:all .2s;
}}
.vi-pedido-item:hover {{
    border-color:rgba(139,0,0,.5);
    background:rgba(139,0,0,.08);
}}
.vi-pedido-num {{
    font-family:'DM Mono', monospace;
    font-size:1rem; font-weight:500;
    color:#fff;
}}
.vi-pedido-meta {{
    font-size:.7rem; color:#9ca3af;
}}

/* ── INPUTS ── */
[data-testid="stTextInput"] label p,
[data-testid="stSelectbox"] label p,
[data-testid="stNumberInput"] label p {{
    color:#9ca3af !important; font-size:.7rem !important;
    font-weight:700 !important; letter-spacing:.08em !important;
    text-transform:uppercase !important; font-family:'DM Sans',sans-serif !important;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {{
    background:rgba(255,255,255,.05) !important;
    border:1px solid rgba(139,0,0,.35) !important;
    border-radius:10px !important; color:#fff !important;
    font-family:'DM Mono',monospace !important; font-size:1rem !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background:rgba(255,255,255,.05) !important;
    border:1px solid rgba(139,0,0,.35) !important;
    border-radius:10px !important; color:#fff !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stNumberInput"] input:focus {{
    border-color:#dc2626 !important;
    box-shadow:0 0 0 3px rgba(139,0,0,.18) !important;
}}

/* ── BOTÕES ── */
.stButton > button {{
    background:linear-gradient(135deg,#7f1d1d 0%,#dc2626 100%) !important;
    border:none !important; border-radius:10px !important;
    color:#fff !important; font-weight:700 !important;
    font-size:.88rem !important; letter-spacing:.04em !important;
    padding:11px 20px !important;
    font-family:'DM Sans',sans-serif !important;
    width:100%;
    transition:opacity .2s, transform .15s !important;
}}
.stButton > button:hover {{
    opacity:.85 !important; transform:translateY(-1px) !important;
}}
.stButton > button[kind="secondary"] {{
    background:rgba(255,255,255,.06) !important;
    border:1px solid rgba(255,255,255,.12) !important;
    color:#9ca3af !important;
}}
.stButton > button[kind="secondary"]:hover {{
    background:rgba(255,255,255,.1) !important;
    opacity:1 !important;
}}

/* ── DIVIDER ── */
.vi-div {{
    height:1px;
    background:linear-gradient(90deg,transparent,rgba(139,0,0,.5),transparent);
    margin:20px 0;
}}

/* ── ALERTA ── */
.vi-alert {{
    padding:12px 16px; border-radius:10px;
    font-size:.82rem; font-weight:500;
    margin:12px 0;
}}
.vi-alert-ok  {{ background:rgba(27,94,32,.25); border:1px solid rgba(76,175,80,.3); color:#a5d6a7; }}
.vi-alert-err {{ background:rgba(139,0,0,.2);   border:1px solid rgba(220,38,38,.35); color:#f87171; }}
.vi-alert-inf {{ background:rgba(21,101,192,.2); border:1px solid rgba(66,165,245,.3); color:#90caf9; }}

/* ── OPERADOR TAG ── */
.vi-op-tag {{
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(139,0,0,.15);
    border:1px solid rgba(139,0,0,.35);
    color:#f87171; padding:4px 12px;
    border-radius:20px; font-size:.72rem;
    font-weight:700; letter-spacing:.06em;
}}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# TELA DE LOADING
# =============================================================================
def tela_loading(mensagem="Carregando...", duracao=2.2):
    if _logo_src:
        img = f'<img src="{_logo_src}" style="height:52px;object-fit:contain;filter:drop-shadow(0 3px 10px rgba(139,0,0,.5));" />'
    else:
        img = '<div style="font-size:1.2rem;font-weight:900;color:#fff;letter-spacing:.1em">VI LINGERIE</div>'

    placeholder = st.empty()
    placeholder.markdown(f"""
    <div class="vi-loading">
        {img}
        <div class="vi-spinner"></div>
        <div class="vi-loading-text">{mensagem}</div>
    </div>
    """, unsafe_allow_html=True)
    time.sleep(duracao)
    placeholder.empty()


# =============================================================================
# SPLASH INICIAL (uma vez por sessão)
# =============================================================================
if "_splash_done" not in st.session_state:
    tela_loading("Iniciando sistema de produção", duracao=2.5)
    st.session_state["_splash_done"] = True


# =============================================================================
# TELA DE LOGIN DA GERÊNCIA
# =============================================================================
def tela_login_gerencia():
    st.markdown(f"""
    <div class="vi-card" style="max-width:400px;margin:60px auto 0;">
        <div style="text-align:center;margin-bottom:4px">{logo_tag}</div>
        <div style="text-align:center;margin-bottom:6px">
            <span style="font-size:.65rem;font-weight:700;color:#f87171;
                letter-spacing:.14em;text-transform:uppercase;
                background:rgba(139,0,0,.15);border:1px solid rgba(139,0,0,.4);
                padding:3px 12px;border-radius:20px;">
                🔒 Área da Gerência
            </span>
        </div>
        <div class="vi-div"></div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 5, 1])
    with col_c:
        senha = st.text_input("Senha de gerência", type="password", placeholder="••••••••")
        if st.button("🔓 Acessar", use_container_width=True):
            if senha == SENHA_GERENCIA:
                st.session_state["_gerencia_ok"] = True
                st.rerun()
            else:
                st.markdown('<div class="vi-alert vi-alert-err">❌ Senha incorreta.</div>', unsafe_allow_html=True)
        st.markdown("")
        if st.button("← Voltar", use_container_width=True, type="secondary"):
            st.session_state.pop("_modo", None)
            st.rerun()


# =============================================================================
# TELA DE EXTRATO GERENCIAL
# =============================================================================
def tela_extrato():
    concluidos        = carregar_concluidos()
    pedidos_andamento = carregar_pedidos()
    historico         = carregar_historico()

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:20px">
        {logo_tag}
        <div style="font-size:1.1rem;font-weight:700;color:#fff;margin-top:4px">Extrato de Produção</div>
        <div style="font-size:.75rem;color:#9ca3af;margin-top:2px">Consulta, filtros e download por data e funcionário</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Cards de resumo ──────────────────────────────────────────────────────
    total_op_sep  = len([h for h in historico if h.get("etapa") == "Separação do Pedido"])
    total_op_emb  = len([h for h in historico if h.get("etapa") == "Mesa de Embalagem"])
    total_op_conf = len([h for h in historico if h.get("etapa") == "Conferência do Pedido"])
    total_conc    = len(concluidos)

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, cor, bg, border in [
        (c1, "📦 Separações",   total_op_sep,  "#64b5f6", "rgba(21,101,192,.2)",  "rgba(66,165,245,.25)"),
        (c2, "📬 Embalagens",   total_op_emb,  "#ce93d8", "rgba(106,13,173,.2)",  "rgba(171,71,188,.25)"),
        (c3, "✅ Conferências", total_op_conf, "#a5d6a7", "rgba(27,94,32,.2)",    "rgba(76,175,80,.25)"),
        (c4, "🎯 Concluídos",   total_conc,    "#f87171", "rgba(127,29,29,.2)",   "rgba(239,68,68,.25)"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {border};border-radius:12px;
                padding:12px 8px;text-align:center;">
                <div style="font-size:.58rem;color:#9ca3af;text-transform:uppercase;
                    letter-spacing:.07em;font-weight:700;margin-bottom:3px">{label}</div>
                <div style="font-size:1.7rem;font-weight:700;color:{cor}">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

    # ── Abas ─────────────────────────────────────────────────────────────────
    aba1, aba2, aba3 = st.tabs(["📅 Histórico Completo", "📋 Pedidos Concluídos", "⏳ Em Andamento"])

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 1 — HISTÓRICO COMPLETO (por data + operador)
    # ══════════════════════════════════════════════════════════════════════════
    with aba1:
        st.markdown('<div class="vi-section-title" style="margin-top:16px">🔍 Filtros de Consulta</div>', unsafe_allow_html=True)

        if not historico:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação registrada ainda.</div>', unsafe_allow_html=True)
        else:
            df_hist = pd.DataFrame(historico)

            # Converte datas para comparação
            def parse_data(s):
                try:
                    return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
                except Exception:
                    return pd.NaT

            df_hist["_data_dt"] = df_hist["data"].apply(parse_data)

            # ── Filtros ──
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                from datetime import date, timedelta as td
                hoje = date.today()
                data_ini = st.date_input("📅 Data inicial", value=hoje - td(days=7), key="dt_ini", format="DD/MM/YYYY")
            with col_f2:
                data_fim = st.date_input("📅 Data final", value=hoje, key="dt_fim", format="DD/MM/YYYY")

            col_f3, col_f4 = st.columns(2)
            with col_f3:
                ops_lista = ["Todos"] + sorted(df_hist["operador"].dropna().unique().tolist())
                op_filtro = st.selectbox("👤 Funcionário", options=ops_lista, key="hist_op")
            with col_f4:
                etapas_lista = ["Todas"] + ETAPAS
                etapa_filtro = st.selectbox("⚙️ Etapa", options=etapas_lista, key="hist_etapa")

            # ── Aplica filtros ──
            mask = (
                (df_hist["_data_dt"] >= pd.Timestamp(data_ini)) &
                (df_hist["_data_dt"] <= pd.Timestamp(data_fim))
            )
            df_filtrado = df_hist[mask].copy()

            if op_filtro != "Todos":
                df_filtrado = df_filtrado[df_filtrado["operador"] == op_filtro]
            if etapa_filtro != "Todas":
                df_filtrado = df_filtrado[df_filtrado["etapa"] == etapa_filtro]

            df_filtrado = df_filtrado.sort_values("data_hora", ascending=False)

            st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

            # ── Resumo do filtro ──
            n_res = len(df_filtrado)
            periodo_txt = f"{data_ini.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
            op_txt = op_filtro if op_filtro != "Todos" else "todos os funcionários"
            etapa_txt = etapa_filtro if etapa_filtro != "Todas" else "todas as etapas"

            st.markdown(f"""
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
                border-radius:12px;padding:14px 18px;margin-bottom:16px;">
                <div style="font-size:.7rem;color:#9ca3af;margin-bottom:6px;text-transform:uppercase;letter-spacing:.08em;font-weight:700">Resultado da consulta</div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center;">
                    <div style="font-size:.82rem;color:#fff">📅 <b>{periodo_txt}</b></div>
                    <div style="font-size:.82rem;color:#f87171">👤 <b>{op_txt}</b></div>
                    <div style="font-size:.82rem;color:#90caf9">⚙️ <b>{etapa_txt}</b></div>
                    <div style="font-size:.82rem;color:#a5d6a7;margin-left:auto;font-weight:700">{n_res} operação(ões)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if n_res == 0:
                st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhuma operação encontrada para os filtros selecionados.</div>', unsafe_allow_html=True)
            else:
                # Resumo por operador no período
                if op_filtro == "Todos":
                    resumo = df_filtrado.groupby(["operador", "etapa"]).size().reset_index(name="qtd")
                    resumo.columns = ["Funcionário", "Etapa", "Qtd. Operações"]
                    st.markdown('<div class="vi-section-title">📊 Resumo por Funcionário no Período</div>', unsafe_allow_html=True)
                    st.dataframe(resumo, use_container_width=True, hide_index=True)
                    st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

                # Tabela detalhada
                st.markdown('<div class="vi-section-title">📋 Detalhamento das Operações</div>', unsafe_allow_html=True)
                df_exib = df_filtrado[["data_hora","pedido","operador","etapa","status_pedido"]].rename(columns={
                    "data_hora":     "Data / Hora",
                    "pedido":        "Pedido",
                    "operador":      "Funcionário",
                    "etapa":         "Etapa",
                    "status_pedido": "Status",
                })
                df_exib["Status"] = df_exib["Status"].map(
                    {"em_andamento": "⏳ Em andamento", "concluido": "✅ Concluído"}
                ).fillna(df_exib["Status"])
                st.dataframe(df_exib, use_container_width=True, hide_index=True)

                # ── Downloads ──
                st.markdown("")
                st.markdown('<div class="vi-section-title">⬇️ Baixar Extrato</div>', unsafe_allow_html=True)

                nome_arquivo = f"extrato_{op_filtro.replace(' ','_')}_{data_ini.strftime('%d%m%Y')}_{data_fim.strftime('%d%m%Y')}"

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        "⬇️ Baixar CSV",
                        data=df_exib.to_csv(index=False).encode("utf-8"),
                        file_name=f"{nome_arquivo}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="dl_hist_csv"
                    )
                with col_dl2:
                    # Excel com duas abas: detalhado + resumo por operador
                    xlsx_buf = BytesIO()
                    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                        df_exib.to_excel(writer, index=False, sheet_name="Detalhado")
                        if op_filtro == "Todos":
                            resumo.to_excel(writer, index=False, sheet_name="Resumo por Funcionário")
                    xlsx_buf.seek(0)
                    st.download_button(
                        "⬇️ Baixar Excel",
                        data=xlsx_buf.getvalue(),
                        file_name=f"{nome_arquivo}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="dl_hist_xlsx"
                    )

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 2 — PEDIDOS CONCLUÍDOS
    # ══════════════════════════════════════════════════════════════════════════
    with aba2:
        st.markdown('<div class="vi-section-title" style="margin-top:16px">Pedidos Finalizados nas 3 Etapas</div>', unsafe_allow_html=True)
        if concluidos:
            df_conc = pd.DataFrame(concluidos)
            df_show = df_conc.rename(columns={
                "pedido":  "Pedido",
                "op_sep":  "Op. Separação",   "dt_sep":  "Data Separação",
                "op_emb":  "Op. Embalagem",   "dt_emb":  "Data Embalagem",
                "op_conf": "Op. Conferência", "dt_conf": "Data Conferência",
            }).drop(columns=["etapa"], errors="ignore")

            st.dataframe(df_show, use_container_width=True, hide_index=True)

            st.markdown("")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.download_button(
                    "⬇️ Baixar CSV",
                    data=df_show.to_csv(index=False).encode("utf-8"),
                    file_name=f"pedidos_concluidos_{datetime.now().strftime('%d%m%Y_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_conc_csv"
                )
            with col_c2:
                xlsx_buf2 = BytesIO()
                with pd.ExcelWriter(xlsx_buf2, engine="openpyxl") as writer:
                    df_show.to_excel(writer, index=False, sheet_name="Concluídos")
                xlsx_buf2.seek(0)
                st.download_button(
                    "⬇️ Baixar Excel",
                    data=xlsx_buf2.getvalue(),
                    file_name=f"pedidos_concluidos_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_conc_xlsx"
                )
        else:
            st.markdown('<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido finalizado ainda.</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ABA 3 — EM ANDAMENTO
    # ══════════════════════════════════════════════════════════════════════════
    with aba3:
        st.markdown('<div class="vi-section-title" style="margin-top:16px">Pedidos em Andamento</div>', unsafe_allow_html=True)
        if pedidos_andamento:
            etapa_labels = {1: "⏳ Aguardando Embalagem", 2: "⏳ Aguardando Conferência"}
            rows = []
            for p in pedidos_andamento.values():
                rows.append({
                    "Pedido":          f"#{p['pedido']}",
                    "Etapa Atual":     etapa_labels.get(p.get("etapa", 0), "—"),
                    "Op. Separação":   p.get("op_sep", "—"),
                    "Data Separação":  p.get("dt_sep", "—"),
                    "Op. Embalagem":   p.get("op_emb", "—"),
                    "Data Embalagem":  p.get("dt_emb", "—"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.markdown('<div class="vi-alert vi-alert-ok">✅ Nenhum pedido em andamento no momento.</div>', unsafe_allow_html=True)

    st.markdown("")
    if st.button("← Sair da Gerência", use_container_width=True, type="secondary"):
        st.session_state.pop("_modo", None)
        st.session_state.pop("_gerencia_ok", None)
        st.rerun()


# =============================================================================
# STEPS VISUAL
# =============================================================================
def render_steps(etapa_atual_idx):
    """Renderiza os 3 passos do processo."""
    steps_html = '<div class="vi-steps">'
    for i, (nome, icon) in enumerate(zip(ETAPAS, ETAPA_ICONS)):
        if i < etapa_atual_idx:
            dot_cls = "done"; label_cls = "done"; dot_inner = "✓"
        elif i == etapa_atual_idx:
            dot_cls = "active"; label_cls = "active"; dot_inner = icon
        else:
            dot_cls = ""; label_cls = ""; dot_inner = str(i + 1)

        short = nome.split(" ")[0]  # "Separação", "Mesa", "Conferência"
        steps_html += f'<div class="vi-step"><div class="vi-step-dot {dot_cls}">{dot_inner}</div><div class="vi-step-label {label_cls}">{short}</div></div>'
        if i < 2:
            line_cls = "done" if i < etapa_atual_idx else ""
            steps_html += f'<div class="vi-step-line {line_cls}"></div>'
    steps_html += '</div>'
    st.markdown(steps_html, unsafe_allow_html=True)


# =============================================================================
# FLUXO PRINCIPAL DO OPERADOR
# =============================================================================
def tela_operador():
    pedidos = carregar_pedidos()
    concluidos = carregar_concluidos()

    # ── STEP 1: Identificação do operador ──────────────────────────────────
    if "_operador" not in st.session_state:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:24px">
            {logo_tag}
            <div style="font-size:1rem;font-weight:700;color:#fff;margin-top:4px">Sistema de Produção</div>
            <div style="font-size:.75rem;color:#9ca3af;margin-top:2px">Identifique-se para continuar</div>
        </div>
        <div class="vi-div"></div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-section-title">👤 Identificação do Operador</div>', unsafe_allow_html=True)
        operador = st.selectbox(
            "Selecione seu nome",
            options=["— Selecione —"] + OPERADORES,
            key="sel_operador"
        )
        st.markdown("")
        if st.button("Continuar →", use_container_width=True):
            if operador == "— Selecione —":
                st.markdown('<div class="vi-alert vi-alert-err">⚠️ Por favor, selecione seu nome.</div>', unsafe_allow_html=True)
            else:
                st.session_state["_operador"] = operador
                st.rerun()
        return

    operador = st.session_state["_operador"]

    # ── STEP 2: Selecionar etapa ────────────────────────────────────────────
    if "_etapa_idx" not in st.session_state:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:8px">
            {logo_tag}
        </div>
        <div style="text-align:center;margin-bottom:18px">
            <span class="vi-op-tag">👤 {operador}</span>
        </div>
        <div class="vi-div"></div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="vi-section-title">⚙️ Selecione a Operação</div>', unsafe_allow_html=True)

        for idx, (etapa, icon, cor) in enumerate(zip(ETAPAS, ETAPA_ICONS, ETAPA_CORES)):
            # Conta pedidos disponíveis nessa etapa
            if idx == 0:
                n_disp = "—"
            elif idx == 1:
                # disponíveis = passaram pela etapa 0 e não concluíram etapa 1
                n_disp = sum(
                    1 for p, d in pedidos.items()
                    if d.get("etapa") == 1 and "op_emb" not in d
                )
            else:
                n_disp = sum(
                    1 for p, d in pedidos.items()
                    if d.get("etapa") == 2 and "op_conf" not in d
                )

            badge_disp = f'<span style="font-size:.65rem;background:rgba(255,255,255,.08);padding:2px 8px;border-radius:10px;color:#9ca3af;margin-left:8px">{n_disp} disponível(is)</span>' if isinstance(n_disp, int) else ""

            st.markdown(f"""
            <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
                border-radius:14px;padding:14px 18px;margin-bottom:10px;
                display:flex;align-items:center;gap:12px;">
                <div style="font-size:1.4rem">{icon}</div>
                <div style="flex:1">
                    <div style="font-size:.88rem;font-weight:700;color:#fff">{etapa}</div>
                    <div style="font-size:.68rem;color:#9ca3af;margin-top:2px">Etapa {idx+1} de 3 {badge_disp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Selecionar — {etapa}", key=f"btn_etapa_{idx}", use_container_width=True):
                st.session_state["_etapa_idx"] = idx
                st.rerun()

        st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)
        if st.button("← Trocar operador", use_container_width=True, type="secondary"):
            st.session_state.pop("_operador", None)
            st.rerun()
        return

    etapa_idx = st.session_state["_etapa_idx"]
    etapa_nome = ETAPAS[etapa_idx]
    etapa_icon = ETAPA_ICONS[etapa_idx]

    # ── STEP 3: Alocar pedido ───────────────────────────────────────────────
    if "_pedido_atual" not in st.session_state:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:8px">{logo_tag}</div>
        <div style="text-align:center;margin-bottom:6px">
            <span class="vi-op-tag">👤 {operador}</span>
        </div>
        <div style="text-align:center;margin-bottom:20px">
            <span class="vi-etapa-badge" style="background:rgba(139,0,0,.15);color:#f87171;border-color:rgba(139,0,0,.35);">
                {etapa_icon} {etapa_nome}
            </span>
        </div>
        """, unsafe_allow_html=True)

        render_steps(etapa_idx)
        st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

        # Etapa 0: digitar número de pedido
        if etapa_idx == 0:
            st.markdown('<div class="vi-section-title">📋 Número do Pedido</div>', unsafe_allow_html=True)
            num_pedido = st.text_input("Digite o número do pedido", placeholder="Ex: 10045", key="inp_pedido_0")
            st.markdown("")
            if st.button("Registrar Pedido →", use_container_width=True):
                num_pedido = num_pedido.strip()
                if not num_pedido:
                    st.markdown('<div class="vi-alert vi-alert-err">⚠️ Informe o número do pedido.</div>', unsafe_allow_html=True)
                elif num_pedido in pedidos:
                    st.markdown(f'<div class="vi-alert vi-alert-err">⚠️ Pedido <b>{num_pedido}</b> já foi registrado na Separação.</div>', unsafe_allow_html=True)
                else:
                    st.session_state["_pedido_atual"] = num_pedido
                    st.rerun()

        # Etapas 1 e 2: selecionar de lista de disponíveis
        else:
            if etapa_idx == 1:
                disponiveis = [p for p, d in pedidos.items() if d.get("etapa") == 1 and "op_emb" not in d]
                chave_op = "op_emb"
            else:
                disponiveis = [p for p, d in pedidos.items() if d.get("etapa") == 2 and "op_conf" not in d]
                chave_op = "op_conf"

            if not disponiveis:
                prev = ETAPAS[etapa_idx - 1]
                st.markdown(f'<div class="vi-alert vi-alert-inf">ℹ️ Nenhum pedido disponível. Aguarde a conclusão da etapa anterior: <b>{prev}</b>.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="vi-section-title">📋 Pedidos Disponíveis ({len(disponiveis)})</div>', unsafe_allow_html=True)

                opcoes = ["— Selecione um pedido —"] + sorted(disponiveis)
                pedido_sel = st.selectbox("Selecione o pedido", options=opcoes, key=f"sel_pedido_{etapa_idx}")
                st.markdown("")
                if st.button("Iniciar Operação →", use_container_width=True):
                    if pedido_sel == "— Selecione um pedido —":
                        st.markdown('<div class="vi-alert vi-alert-err">⚠️ Selecione um pedido.</div>', unsafe_allow_html=True)
                    else:
                        st.session_state["_pedido_atual"] = pedido_sel
                        st.rerun()

        st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)
        if st.button("← Trocar operação", use_container_width=True, type="secondary"):
            st.session_state.pop("_etapa_idx", None)
            st.rerun()
        return

    pedido_atual = st.session_state["_pedido_atual"]

    # ── STEP 4: Loading "Cadastrando pedido" ────────────────────────────────
    if "_loading_cadastro" not in st.session_state:
        st.session_state["_loading_cadastro"] = True
        tela_loading("Cadastrando pedido...", duracao=1.8)
        st.rerun()

    # ── STEP 5: Pergunta "Pedido finalizado?" ───────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:8px">{logo_tag}</div>
    <div style="text-align:center;margin-bottom:6px">
        <span class="vi-op-tag">👤 {operador}</span>
    </div>
    <div style="text-align:center;margin-bottom:20px">
        <span class="vi-etapa-badge" style="background:rgba(139,0,0,.15);color:#f87171;border-color:rgba(139,0,0,.35);">
            {etapa_icon} {etapa_nome}
        </span>
    </div>
    """, unsafe_allow_html=True)

    render_steps(etapa_idx)
    st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);
        border-radius:14px;padding:20px 20px 16px;margin-bottom:20px;text-align:center;">
        <div style="font-size:.65rem;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Pedido em Operação</div>
        <div style="font-family:'DM Mono',monospace;font-size:1.8rem;font-weight:500;color:#fff">#{pedido_atual}</div>
        <div style="font-size:.72rem;color:#f87171;margin-top:4px">{etapa_nome}</div>
    </div>
    """, unsafe_allow_html=True)

    # Pergunta específica por etapa
    if etapa_idx == 0:
        pergunta = "A separação do pedido foi concluída?"
    elif etapa_idx == 1:
        pergunta = "Esse pedido já saiu da mesa de embalagem?"
    else:
        pergunta = "A conferência do pedido foi concluída?"

    st.markdown(f'<div style="font-size:.9rem;font-weight:600;color:#e8e8f0;text-align:center;margin-bottom:18px">{pergunta}</div>', unsafe_allow_html=True)

    col_sim, col_nao = st.columns(2)
    with col_sim:
        if st.button("✅  Sim, concluído", use_container_width=True):
            pedidos = carregar_pedidos()
            now = agora_str()

            if etapa_idx == 0:
                pedidos[pedido_atual] = {
                    "pedido": pedido_atual,
                    "etapa": 1,
                    "op_sep": operador,
                    "dt_sep": now,
                }
                registrar_historico(pedido_atual, operador, "Separação do Pedido", now, "em_andamento")

            elif etapa_idx == 1:
                if pedido_atual in pedidos:
                    pedidos[pedido_atual]["etapa"] = 2
                    pedidos[pedido_atual]["op_emb"] = operador
                    pedidos[pedido_atual]["dt_emb"] = now
                    registrar_historico(pedido_atual, operador, "Mesa de Embalagem", now, "em_andamento")

            else:
                # Etapa 3 — finalizado!
                if pedido_atual in pedidos:
                    pedidos[pedido_atual]["etapa"] = 3
                    pedidos[pedido_atual]["op_conf"] = operador
                    pedidos[pedido_atual]["dt_conf"] = now
                    # Move para concluídos
                    conc = carregar_concluidos()
                    conc.append(pedidos[pedido_atual])
                    salvar_concluidos(conc)
                    del pedidos[pedido_atual]
                    registrar_historico(pedido_atual, operador, "Conferência do Pedido", now, "concluido")

            salvar_pedidos(pedidos)

            # Limpa estado para novo ciclo
            for k in ["_pedido_atual", "_loading_cadastro", "_etapa_idx"]:
                st.session_state.pop(k, None)

            st.session_state["_concluido_msg"] = (pedido_atual, etapa_idx)
            st.rerun()

    with col_nao:
        if st.button("↩  Ainda não", use_container_width=True, type="secondary"):
            for k in ["_pedido_atual", "_loading_cadastro"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ── Mensagem de sucesso após conclusão ──────────────────────────────────
    if "_concluido_msg" in st.session_state:
        ped_ok, etapa_ok = st.session_state.pop("_concluido_msg")
        if etapa_ok == 2:
            msg = f"🎉 Pedido <b>#{ped_ok}</b> finalizado com sucesso! Todas as etapas concluídas."
            cls = "vi-alert-ok"
        else:
            prox = ETAPAS[etapa_ok + 1]
            msg = f"✅ Pedido <b>#{ped_ok}</b> concluído em <b>{ETAPAS[etapa_ok]}</b>. Disponível para <b>{prox}</b>."
            cls = "vi-alert-ok"
        st.markdown(f'<div class="vi-alert {cls}">{msg}</div>', unsafe_allow_html=True)


# =============================================================================
# ROTEAMENTO PRINCIPAL
# =============================================================================

# Tela inicial — escolher modo
if "_modo" not in st.session_state:
    st.markdown(f"""
    <div style="text-align:center;padding:40px 0 28px">
        {logo_tag}
        <div style="font-size:1.05rem;font-weight:700;color:#fff;margin-top:6px">Sistema de Produção</div>
        <div style="font-size:.75rem;color:#6b7280;margin-top:3px">Vi Lingerie — Linha de Montagem</div>
    </div>
    <div class="vi-div"></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="vi-section-title">🚀 Como deseja acessar?</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
            border-radius:14px;padding:20px;text-align:center;margin-bottom:12px">
            <div style="font-size:2rem">🏭</div>
            <div style="font-size:.88rem;font-weight:700;color:#fff;margin-top:8px">Operador</div>
            <div style="font-size:.68rem;color:#9ca3af;margin-top:4px">Registrar etapas de produção</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Entrar como Operador", use_container_width=True, key="btn_op"):
            st.session_state["_modo"] = "operador"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
            border-radius:14px;padding:20px;text-align:center;margin-bottom:12px">
            <div style="font-size:2rem">📊</div>
            <div style="font-size:.88rem;font-weight:700;color:#fff;margin-top:8px">Gerência</div>
            <div style="font-size:.68rem;color:#9ca3af;margin-top:4px">Extrato e relatórios</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Entrar como Gerência", use_container_width=True, key="btn_ger", type="secondary"):
            st.session_state["_modo"] = "gerencia"
            st.rerun()

elif st.session_state["_modo"] == "operador":
    tela_operador()
    # Botão flutuante de sair
    st.markdown('<div class="vi-div"></div>', unsafe_allow_html=True)
    if st.button("⏏  Sair do sistema", use_container_width=True, type="secondary", key="btn_sair_op"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

elif st.session_state["_modo"] == "gerencia":
    if not st.session_state.get("_gerencia_ok"):
        tela_login_gerencia()
    else:
        tela_extrato()
