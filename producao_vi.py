import streamlit as st
import pandas as pd
import time
from datetime import datetime
import sqlite3
from fpdf import FPDF
import base64

# Importar funções do banco de dados
import database

# Configuração da página
st.set_page_config(page_title="Vi Lingerie - Produção", page_icon="👙", layout="wide")

# Inicializar banco de dados
database.init_db()

# --- ESTILIZAÇÃO CSS (Clean & Minimalist) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FAFAFA;
        color: #333;
    }
    
    .main {
        background-color: #FAFAFA;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #FFFFFF;
        color: #333;
        border: 1px solid #DDD;
        transition: all 0.3s;
        font-weight: 600;
    }
    
    .stButton>button:hover {
        border-color: #000;
        background-color: #F0F0F0;
    }
    
    .btn-proximo {
        background-color: #000 !important;
        color: #FFF !important;
    }
    
    .avatar-circle {
        width: 80px;
        height: 80px;
        background-color: #EEE;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
        font-size: 24px;
        font-weight: 600;
        color: #555;
        border: 2px solid #DDD;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .avatar-circle:hover {
        transform: scale(1.05);
        border-color: #999;
    }
    
    .centered-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    
    .logo-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 250px;
        margin-bottom: 30px;
    }
    
    /* Remover barras de rolagem e focar no centro */
    section.main {
        overflow: hidden;
    }
    
    div.block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        max-width: 800px;
    }
    
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        padding: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DA SESSÃO ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'operador' not in st.session_state:
    st.session_state.operador = None
if 'etapa' not in st.session_state:
    st.session_state.etapa = 'Separação'
if 'pedido' not in st.session_state:
    st.session_state.pedido = ""
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'registro_id' not in st.session_state:
    st.session_state.registro_id = None

# --- FUNÇÕES DE NAVEGAÇÃO ---
def ir_para_home():
    st.session_state.page = 'home'
    st.session_state.operador = None
    st.session_state.etapa = 'Separação'
    st.session_state.pedido = ""
    st.session_state.start_time = None
    st.rerun()

def ir_para_producao(operador):
    st.session_state.operador = operador
    st.session_state.page = 'producao'
    st.rerun()

def ir_para_admin():
    st.session_state.page = 'admin'
    st.rerun()

# --- COMPONENTES DA INTERFACE ---

def header():
    st.markdown(f'<img src="https://raw.githubusercontent.com/HapvidaNotre/vi-producao/main/logo_vi.png" class="logo-img">', unsafe_allow_html=True)

def tela_selecao_operador():
    header()
    st.markdown("<h3 style='text-align: center; font-weight: 300; margin-bottom: 30px;'>Selecione seu Perfil</h3>", unsafe_allow_html=True)
    
    operadores = ["Lucivanio", "Enagio", "Daniel", "Italo", "Cildenir", "Samya", "Neide", "Eduardo", "Talyson"]
    
    cols = st.columns(3)
    for i, nome in enumerate(operadores):
        with cols[i % 3]:
            st.markdown(f"""
                <div class="centered-content">
                    <div class="avatar-circle">{nome[0]}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(nome, key=f"btn_{nome}"):
                ir_para_producao(nome)

def tela_producao():
    header()
    
    st.markdown(f"<h4 style='text-align: center;'>Operador: <b>{st.session_state.operador}</b></h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #888;'>Etapa Atual: {st.session_state.etapa}</p>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.session_state.start_time is None:
                # Fase de Início
                pedido_input = st.text_input("Número do Pedido", value=st.session_state.pedido, placeholder="Digite o número...", key="pedido_input")
                st.session_state.pedido = pedido_input
                
                if st.button("INICIAR", key="btn_iniciar"):
                    if st.session_state.pedido:
                        st.session_state.start_time = time.time()
                        # Salvar no banco
                        st.session_state.registro_id = database.salvar_inicio(
                            st.session_state.operador, 
                            st.session_state.pedido, 
                            st.session_state.etapa
                        )
                        st.rerun()
                    else:
                        st.error("Por favor, insira o número do pedido.")
            else:
                # Fase em andamento
                st.markdown(f"<h2 style='text-align: center; color: #555;'>Pedido: {st.session_state.pedido}</h2>", unsafe_allow_html=True)
                
                # Timer dinâmico (visual apenas)
                placeholder = st.empty()
                duracao_atual = int(time.time() - st.session_state.start_time)
                minutos = duracao_atual // 60
                segundos = duracao_atual % 60
                placeholder.markdown(f"<h1 style='text-align: center; font-weight: 300;'>{minutos:02d}:{segundos:02d}</h1>", unsafe_allow_html=True)
                
                if st.button("FINALIZAR", key="btn_finalizar"):
                    database.finalizar_etapa(st.session_state.registro_id)
                    st.session_state.page = 'pos_producao'
                    st.rerun()

def tela_pos_producao():
    header()
    st.markdown("<h3 style='text-align: center;'>Etapa concluída com sucesso!</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Deseja ir para a próxima etapa?</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("SIM"):
            st.session_state.page = 'decisao_proxima'
            st.rerun()
            
    with col2:
        if st.button("NÃO / NOVO PEDIDO"):
            ir_para_home()

def tela_decisao_proxima():
    header()
    
    # Lógica de transição de etapas
    etapas = ["Separação", "Conferência", "Embalagem"]
    current_idx = etapas.index(st.session_state.etapa)
    
    if current_idx < len(etapas) - 1:
        proxima_etapa = etapas[current_idx + 1]
    else:
        st.warning("Todas as etapas deste pedido foram concluídas.")
        if st.button("Voltar ao Início"):
            ir_para_home()
        return

    st.markdown(f"<h4 style='text-align: center;'>Próxima Etapa: <b>{proxima_etapa}</b></h4>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Quem executará a próxima fase?</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("VOCÊ MESMO"):
            st.session_state.etapa = proxima_etapa
            st.session_state.start_time = None
            st.session_state.page = 'producao'
            st.rerun()
            
    with col2:
        if st.button("OUTRO OPERADOR"):
            ir_para_home()

def gerar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatório de Produtividade - Vi Lingerie", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 10, "Operador", 1)
    pdf.cell(30, 10, "Pedido", 1)
    pdf.cell(40, 10, "Etapa", 1)
    pdf.cell(50, 10, "Início", 1)
    pdf.cell(40, 10, "Duração (s)", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(30, 10, str(row['operador']), 1)
        pdf.cell(30, 10, str(row['pedido']), 1)
        pdf.cell(40, 10, str(row['etapa']), 1)
        pdf.cell(50, 10, str(row['inicio']), 1)
        pdf.cell(40, 10, str(row['duracao_segundos']), 1)
        pdf.ln()
    
    # Removendo caracteres especiais para evitar erro de codificação no latin-1 básico
    return pdf.output(dest="S").encode("latin-1", "ignore")

def tela_admin():
    header()
    st.markdown("<h3 style='text-align: center;'>Painel Administrativo</h3>", unsafe_allow_html=True)
    
    if st.button("← Voltar"):
        ir_para_home()
        
    df = database.get_stats()
    
    if df.empty:
        st.info("Nenhum dado registrado ainda.")
    else:
        # Métricas Rápidas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Etapas", len(df))
        m2.metric("Pedidos Únicos", df['pedido'].nunique())
        m3.metric("Tempo Médio (s)", int(df['duracao_segundos'].mean()))
        
        # Tabelas
        st.markdown("#### Desempenho por Operador")
        stats_op = df.groupby('operador').agg({
            'pedido': 'count',
            'duracao_segundos': 'mean'
        }).rename(columns={'pedido': 'Qtd Etapas', 'duracao_segundos': 'Tempo Médio (s)'})
        st.table(stats_op)
        
        st.markdown("#### Lista de Concluídos")
        st.dataframe(df[['operador', 'pedido', 'etapa', 'inicio', 'duracao_segundos']], use_container_width=True)
        
        # PDF
        pdf_bytes = gerar_pdf(df)
        st.download_button(
            label="Gerar Relatório em PDF",
            data=pdf_bytes,
            file_name=f"relatorio_vi_lingerie_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

# --- ROTEAMENTO ---
if st.session_state.page == 'home':
    tela_selecao_operador()
elif st.session_state.page == 'producao':
    tela_producao()
elif st.session_state.page == 'pos_producao':
    tela_pos_producao()
elif st.session_state.page == 'decisao_proxima':
    tela_decisao_proxima()
elif st.session_state.page == 'admin':
    tela_admin()

# Rodapé Discreto
st.markdown("""
    <div class="footer">
        <hr style="margin: 20px 0 10px 0; opacity: 0.1;">
    </div>
    """, unsafe_allow_html=True)

if st.button("Painel Administrativo", key="admin_btn", help="Acesso restrito"):
    ir_para_admin()
