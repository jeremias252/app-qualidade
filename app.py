import streamlit as st
import pandas as pd
import uuid
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Qualidade - Feedbacks", page_icon="🎯", layout="centered")

# --- DESIGN PREMIUM E MODO ESCURO ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    
    .main-title {
        text-align: center;
        font-weight: 800;
        padding-bottom: 1rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #333333;
    }
    .destaque-erro {
        background-color: #2b1111;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #4a1f1f;
        text-align: center;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# URL DA PLANILHA GOOGLE (QUALIDADE)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/111PYxTmh3sJ_R2kY92AnZqVM9qMOV1PLggzZU2FiULw/edit?usp=drivesdk"

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="Registros", ttl=600).copy()
        # Se a planilha for recém-criada e estiver vazia, ele cria as colunas
        if df.empty or "ID" not in df.columns:
            df = pd.DataFrame(columns=["ID", "Data", "Setor", "Separador", "Erro_Cor", "Erro_Configuracao", "Erro_Modelo", "Total_Erros"])
            conn.update(spreadsheet=URL_PLANILHA, worksheet="Registros", data=df)
        else:
            df = df.dropna(subset=["ID"])
            for col in ["Erro_Cor", "Erro_Configuracao", "Erro_Modelo", "Total_Erros"]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    except Exception as e:
        st.error("⚠️ Falha de comunicação com o Google Drive. A internet pode ter oscilado. Tente atualizar a página.")
        st.stop()
    return df

def salvar_dados(df):
    conn.update(spreadsheet=URL_PLANILHA, worksheet="Registros", data=df)

# EQUIPES
equipes = {
    "Torres": ["Fran", "Henrique", "Leonardo", "Patrick"],
    "Caixas": ["Marcello", "Fabiano", "Sérgio", "Renan", "Gustavo"]
}

# --- TELA PRINCIPAL ---
st.markdown("<h1 class='main-title'>🎯 Qualidade - Feedbacks</h1>", unsafe_allow_html=True)

# --- CONTROLE DE ACESSO (SÓ COORDENADOR) ---
st.sidebar.title("🔐 Acesso Restrito")
senha = st.sidebar.text_input("Senha do Coordenador:", type="password")

if senha != "coord123":
    st.warning("👋 Este aplicativo é de uso exclusivo da Coordenação para feedbacks.")
    st.info("👈 Digite a senha no menu lateral para liberar o acesso.")
    st.stop()

if st.sidebar.button("🔄 Atualizar Banco de Dados", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# CARREGA OS DADOS
df_erros = carregar_dados()

abas = st.tabs(["📝 Lançar Erros", "📊 Dashboard de Qualidade", "🕒 Histórico"])

with abas[0]:
    st.header("📝 Lançamento Diário")
    st.write("Transcreva as marcações do papel para o sistema de forma rápida.")
    
    col_data, col_setor = st.columns(2)
    with col_data:
        data_lancamento = st.date_input("1. Data da Folha", datetime.today())
    with col_setor:
        setor = st.selectbox("2. Setor", ["", "Torres", "Caixas"])
    
    if setor:
        separador = st.selectbox("3. Separador", [""] + equipes[setor])
        
        if separador:
            st.markdown(f"### ❌ Erros de **{separador}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                err_cor = st.number_input("🎨 Cor", min_value=0, value=0)
            with col2:
                err_conf = st.number_input("⚙️ Config.", min_value=0, value=0)
            with col3:
                err_mod = st.number_input("📦 Modelo", min_value=0, value=0)
            
            total = err_cor + err_conf + err_mod
            
            st.markdown(f"<div class='destaque-erro'><b>Total de erros apontados hoje:</b> <span style='color:#ef4444; font-size:20px; font-weight:bold;'>{total}</span></div>", unsafe_allow_html=True)
            
            if st.button("💾 Salvar Apontamento", type="primary", use_container_width=True):
                if total == 0:
                    st.warning("⚠️ Você precisa registrar pelo menos 1 erro, ou não há nada para salvar.")
                else:
                    novo = pd.DataFrame([{
                        "ID": str(uuid.uuid4()), 
                        "Data": data_lancamento.strftime("%Y-%m-%d"), 
                        "Setor": setor, 
                        "Separador": separador, 
                        "Erro_Cor": err_cor, 
                        "Erro_Configuracao": err_conf, 
                        "Erro_Modelo": err_mod, 
                        "Total_Erros": total
                    }])
                    df_erros = pd.concat([novo, df_erros], ignore_index=True)
                    salvar_dados(df_erros)
                    st.cache_data.clear()
                    st.success(f"✅ Erros de {separador} salvos com sucesso!")
                    time.sleep(1.5) # Aguarda 1.5 segundos para você ler a mensagem
                    st.rerun()      # Limpa a tela para o próximo lançamento

with abas[1]:
    st.header("📊 Raio-X da Equipe")
    
    if df_erros.empty:
        st.info("Nenhum erro registrado no sistema ainda.")
    else:
        col_d1, col_d2 = st.columns(2)
        d_inicio = col_d1.date_input("Data Inicial", datetime.today().replace(day=1), key="d_in")
        d_fim = col_d2.date_input("Data Final", datetime.today(), key="d_fim")
        
        df_filtro = df_erros.copy()
        df_filtro['Data_Filtro'] = pd.to_datetime(df_filtro['Data']).dt.date
        df_filtro = df_filtro[(df_filtro['Data_Filtro'] >= d_inicio) & (df_filtro['Data_Filtro'] <= d_fim)]
        
        if df_filtro.empty:
            st.warning("Nenhum erro encontrado neste período.")
        else:
            setor_filtro = st.radio("Analisar Setor:", ["Todos", "Torres", "Caixas"], horizontal=True)
            if setor_filtro != "Todos":
                df_filtro = df_filtro[df_filtro["Setor"] == setor_filtro]
            
            tot_cor = df_filtro["Erro_Cor"].sum()
            tot_conf = df_filtro["Erro_Configuracao"].sum()
            tot_mod = df_filtro["Erro_Modelo"].sum()
            
            st.markdown("### 🏆 Pódio de Erros (O que mais erramos?)")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("🎨 Cor", int(tot_cor))
            col_m2.metric("⚙️ Configuração", int(tot_conf))
            col_m3.metric("📦 Modelo", int(tot_mod))
            
            st.divider()
            st.subheader("⚠️ Ranking: Quem mais errou no período?")
            err_por_sep = df_filtro.groupby("Separador")["Total_Erros"].sum().sort_values(ascending=False)
            st.bar_chart(err_por_sep, color="#ef4444")
            
            st.subheader("📈 Evolução Diária de Erros (Setor)")
            err_por_dia = df_filtro.groupby("Data")["Total_Erros"].sum()
            st.line_chart(err_por_dia, color="#F38020")

with abas[2]:
    st.header("🕒 Histórico de Apontamentos")
    st.dataframe(df_erros.drop(columns=["ID"], errors="ignore"), use_container_width=True, hide_index=True)
