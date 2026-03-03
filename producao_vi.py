import streamlit as st
import pandas as pd
import time
import sqlite3
from datetime import datetime
from fpdf import FPDF
import base64

# ==========================================
# 1. ARQUITETURA DE BANCO DE DATAS (EMBUTIDA)
# ==========================================
DB_NAME = "vi_producao.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operador TEXT NOT NULL,
            pedido TEXT NOT NULL,
            etapa TEXT NOT NULL,
            inicio TIMESTAMP NOT NULL,
            fim TIMESTAMP,
            duracao_segundos INTEGER
        )
    """)
    conn.commit()
    conn.close()

def db_salvar_inicio(operador, pedido, etapa):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO producao (operador, pedido, etapa, inicio) VALUES (?, ?, ?, ?)",
        (operador, pedido, etapa, inicio)
    )
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id

def db_finalizar_etapa(registro_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fim = datetime.now()
    fim_str = fim.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT inicio FROM producao WHERE id = ?", (registro_id,))
    row = cursor.fetchone()
    if row:
        inicio = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        duracao = int((fim - inicio).total_seconds())
        cursor.execute(
            "UPDATE producao SET fim = ?, duracao_segundos = ? WHERE id = ?",
            (fim_str, duracao, registro_id)
        )
    conn.commit()
    conn.close()

def db_get_stats():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM producao WHERE fim IS NOT NULL", conn)
    conn.close()
    return df

# ==========================================
# 2. DESIGN SYSTEM & UX (CUSTOM CSS)
# ==========================================
st.set_page_config(page_title="Vi Lingerie | Sistema de Produção", page_icon="👙", layout="wide")
init_db()

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Montserrat:wght@300;400;600&display=swap');
        
        /* Reset e Base */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #FDFDFD;
            color: #2D3436;
        }
        
        .main {
            background-color: #FDFDFD;
        }

        /* Container Principal Centralizado */
        div.block-container {
            padding-top: 3rem;
            padding-bottom: 2rem;
            max-width: 900px;
            margin: auto;
        }

        /* Logo e Títulos */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 40px;
        }
        .logo-img {
            width: 220px;
            filter: drop-shadow(0px 4px 10px rgba(0,0,0,0.05));
        }
        h1, h2, h3 {
            font-family: 'Montserrat', sans-serif;
            font-weight: 300;
            text-align: center;
            letter-spacing: -0.5px;
        }

        /* Cards de Operador */
        .op-card {
            background: #FFFFFF;
            border: 1px solid #F1F2F6;
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            cursor: pointer;
            margin-bottom: 15px;
        }
        .op-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.08);
            border-color: #E2E8F0;
        }
        .avatar-initial {
            width: 65px;
            height: 65px;
            background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 15px auto;
            font-size: 22px;
            font-weight: 600;
            color: #2D3436;
            border: 1px solid #DEE2E6;
        }

        /* Botões Profissionais */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            height: 3.5em;
            background-color: #FFFFFF;
            color: #2D3436;
            border: 1px solid #E2E8F0;
            font-weight: 500;
            font-size: 16px;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .stButton>button:hover {
            background-color: #2D3436;
            color: #FFFFFF !important;
            border-color: #2D3436;
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }
        
        /* Botão Primário (Ação) */
        div[data-testid="stVerticalBlock"] > div:nth-child(2) .stButton>button {
            background-color: #2D3436;
            color: #FFFFFF;
        }

        /* Inputs Clean */
        .stTextInput>div>div>input {
            border-radius: 12px;
            height: 55px;
            border: 1px solid #E2E8F0;
            background-color: #F8FAFC;
            text-align: center;
            font-size: 18px;
        }

        /* Status & Timer */
        .timer-display {
            font-family: 'Inter', sans-serif;
            font-size: 64px;
            font-weight: 200;
            color: #2D3436;
            text-align: center;
            margin: 20px 0;
            letter-spacing: -2px;
        }
        .etapa-badge {
            background: #F1F2F6;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            color: #636E72;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Footer */
        .footer-admin {
            position: fixed;
            bottom: 20px;
            right: 20px;
            opacity: 0.5;
            transition: opacity 0.3s;
        }
        .footer-admin:hover {
            opacity: 1;
        }
        
        /* Esconder Elementos Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. LÓGICA DE NAVEGAÇÃO E ESTADO
# ==========================================
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'operador' not in st.session_state: st.session_state.operador = None
if 'etapa' not in st.session_state: st.session_state.etapa = 'Separação'
if 'pedido' not in st.session_state: st.session_state.pedido = ""
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'registro_id' not in st.session_state: st.session_state.registro_id = None

def navigate(to, **kwargs):
    for key, value in kwargs.items():
        st.session_state[key] = value
    st.session_state.page = to
    st.rerun()

# ==========================================
# 4. COMPONENTES DE INTERFACE (TELAS)
# ==========================================

def show_logo():
    st.markdown('<div class="logo-container"><img src="https://raw.githubusercontent.com/HapvidaNotre/vi-producao/main/logo_vi.png" class="logo-img"></div>', unsafe_allow_html=True)

def tela_home():
    show_logo()
    st.markdown("<h3>Controle de Produção</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #636E72; margin-bottom: 40px;'>Selecione seu perfil para iniciar</p>", unsafe_allow_html=True)
    
    operadores = ["Lucivanio", "Enagio", "Daniel", "Italo", "Cildenir", "Samya", "Neide", "Eduardo", "Talyson"]
    
    cols = st.columns(3)
    for i, nome in enumerate(operadores):
        with cols[i % 3]:
            st.markdown(f"""
                <div class="op-card">
                    <div class="avatar-initial">{nome[0]}</div>
                    <div style="font-weight: 500; font-size: 15px;">{nome}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Acessar", key=f"btn_{nome}"):
                navigate('producao', operador=nome, etapa='Separação', pedido="", start_time=None)

def tela_producao():
    show_logo()
    
    # Header de Status
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <span class="etapa-badge">{st.session_state.etapa}</span>
            <h2 style="margin-top: 15px;">{st.session_state.operador}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 4, 1])
    
    with col_c:
        if st.session_state.start_time is None:
            # Fase de Entrada de Dados
            pedido = st.text_input("Número do Pedido", placeholder="Ex: 45092", label_visibility="collapsed")
            st.session_state.pedido = pedido
            
            st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
            if st.button("INICIAR ETAPA"):
                if st.session_state.pedido:
                    st.session_state.start_time = time.time()
                    st.session_state.registro_id = db_salvar_inicio(
                        st.session_state.operador, 
                        st.session_state.pedido, 
                        st.session_state.etapa
                    )
                    st.rerun()
                else:
                    st.error("Insira o número do pedido para continuar.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("← Voltar", key="back_home"):
                navigate('home')
        else:
            # Fase de Cronômetro Ativo
            st.markdown(f"<p style='text-align: center; color: #636E72;'>Monitorando Pedido: <b>{st.session_state.pedido}</b></p>", unsafe_allow_html=True)
            
            # Timer (Visual)
            placeholder = st.empty()
            duracao = int(time.time() - st.session_state.start_time)
            placeholder.markdown(f'<div class="timer-display">{duracao // 60:02d}:{duracao % 60:02d}</div>', unsafe_allow_html=True)
            
            if st.button("FINALIZAR AGORA"):
                db_finalizar_etapa(st.session_state.registro_id)
                navigate('conclusao')

def tela_conclusao():
    show_logo()
    st.markdown("<h2 style='color: #27AE60;'>✓ Etapa Concluída</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Pedido <b>{st.session_state.pedido}</b> finalizado na fase de <b>{st.session_state.etapa}</b>.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    etapas = ["Separação", "Conferência", "Embalagem"]
    curr_idx = etapas.index(st.session_state.etapa)
    
    if curr_idx < len(etapas) - 1:
        proxima = etapas[curr_idx + 1]
        st.markdown(f"<p style='text-align: center; font-size: 14px;'>Deseja avançar para <b>{proxima}</b>?</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("SIM, EU MESMO"):
                navigate('producao', etapa=proxima, start_time=None)
        with c2:
            if st.button("SIM, OUTRO OPERADOR"):
                navigate('home')
    
    if st.button("FINALIZAR PEDIDO / NOVO PEDIDO", key="finish_all"):
        navigate('home')

def tela_admin():
    show_logo()
    st.markdown("<h3>Painel de Gestão</h3>", unsafe_allow_html=True)
    
    if st.button("← Sair do Painel"): navigate('home')
    
    df = db_get_stats()
    
    if df.empty:
        st.info("Aguardando primeiros registros de produção...")
    else:
        # Métricas Enterprise
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total de Etapas", len(df))
        with m2:
            st.metric("Pedidos Atendidos", df['pedido'].nunique())
        with m3:
            avg_time = int(df['duracao_segundos'].mean())
            st.metric("Tempo Médio", f"{avg_time // 60}m {avg_time % 60}s")
        
        # Visualizações
        tab1, tab2 = st.tabs(["📊 Performance", "📋 Histórico Completo"])
        
        with tab1:
            st.markdown("#### Eficiência por Operador")
            perf = df.groupby('operador').agg({'duracao_segundos': ['count', 'mean']})
            perf.columns = ['Etapas Concluídas', 'Média (seg)']
            st.dataframe(perf.style.highlight_max(axis=0, color='#F1F2F6'), use_container_width=True)
            
            st.markdown("#### Gargalos por Etapa")
            etapa_perf = df.groupby('etapa')['duracao_segundos'].mean()
            st.bar_chart(etapa_perf)
            
        with tab2:
            st.dataframe(df.sort_values('fim', ascending=False), use_container_width=True)
            
            # Exportação PDF
            if st.button("Gerar Relatório Executivo (PDF)"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(190, 15, "Relatório de Produtividade - Vi Lingerie", ln=True, align="C")
                pdf.set_font("Arial", "", 10)
                pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
                pdf.ln(10)
                
                # Header Tabela
                pdf.set_fill_color(240, 240, 240)
                pdf.set_font("Arial", "B", 9)
                cols = [("Operador", 35), ("Pedido", 25), ("Etapa", 35), ("Início", 45), ("Duração", 30)]
                for col_name, width in cols:
                    pdf.cell(width, 10, col_name, 1, 0, 'C', True)
                pdf.ln()
                
                # Dados
                pdf.set_font("Arial", "", 8)
                for _, row in df.iterrows():
                    pdf.cell(35, 8, str(row['operador']), 1)
                    pdf.cell(25, 8, str(row['pedido']), 1)
                    pdf.cell(35, 8, str(row['etapa']), 1)
                    pdf.cell(45, 8, str(row['inicio']), 1)
                    pdf.cell(30, 8, f"{row['duracao_segundos']}s", 1)
                    pdf.ln()
                
                pdf_output = pdf.output(dest="S").encode("latin-1", "ignore")
                b64 = base64.b64encode(pdf_output).decode()
                href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_vi.pdf" style="text-decoration:none; color:white; background:#2D3436; padding:10px 20px; border-radius:8px;">Clique aqui para baixar o PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

# ==========================================
# 5. ROTEAMENTO PRINCIPAL
# ==========================================
inject_custom_css()

if st.session_state.page == 'home':
    tela_home()
elif st.session_state.page == 'producao':
    tela_producao()
elif st.session_state.page == 'conclusao':
    tela_conclusao()
elif st.session_state.page == 'admin':
    tela_admin()

# Botão de Gestão Discreto
st.markdown('<div class="footer-admin">', unsafe_allow_html=True)
if st.button("⚙️ Gestão", key="admin_access"):
    navigate('admin')
st.markdown('</div>', unsafe_allow_html=True)
