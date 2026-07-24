import streamlit as st
import pandas as pd
import uuid
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Qualidade - Feedbacks", page_icon="🎯", layout="centered")

# --- DESIGN PREMIUM LIMPO ---
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
    </style>
    """, unsafe_allow_html=True)

# URL DA PLANILHA GOOGLE (QUALIDADE)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/111PYxTmh3sJ_R2kY92AnZqVM9qMOV1PLggzZU2FiULw/edit?usp=drivesdk"

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="Registros", ttl=600).copy()
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

# --- LOGO SVG ---
logo_svg = """
<div style="display: flex; justify-content: center; margin-bottom: 30px;">
    <svg width="100%" viewBox="0 0 400 350" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="350" fill="transparent" rx="12"/>
        <path d="M 320 180 L 320 50 L 50 50 L 50 300 L 320 300 L 320 250" fill="none" stroke="#ffffff" stroke-width="12" />
        <text x="75" y="150" fill="#ffffff" font-family="Arial, sans-serif" font-weight="900" font-size="70" letter-spacing="2">SETOR</text>
        <text x="50" y="235" fill="#ffffff" font-family="Arial, sans-serif" font-weight="900" font-size="52" letter-spacing="1">QUALIDADE</text>
        <text x="325" y="225" fill="#ffffff" font-family="Arial, sans-serif" font-weight="bold" font-size="28">.COM</text>
        <line x1="290" y1="260" x2="380" y2="260" stroke="#ef4444" stroke-width="12" />
    </svg>
</div>
"""
st.sidebar.markdown(logo_svg, unsafe_allow_html=True)

if st.sidebar.button("🔄 Atualizar Banco de Dados", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
st.sidebar.divider()

# --- CONTROLE DE ACESSO ---
st.sidebar.title("🔐 Acesso Seguro")
senha = st.sidebar.text_input("Senha do Coordenador:", type="password")

if senha != "coord123":
    st.warning("👋 Este aplicativo é de uso exclusivo da Coordenação.")
    st.info("👈 Digite a senha no menu lateral para liberar o acesso ao painel de Qualidade.")
    st.stop()

# --- TELA PRINCIPAL ---
st.markdown("<h1 class='main-title'>🎯 Qualidade - Feedbacks</h1>", unsafe_allow_html=True)

# CARREGA OS DADOS
df_erros = carregar_dados()

# --- 4 ABAS AGORA ---
abas = st.tabs(["📝 Lançar Erros", "📊 Dashboard", "🕒 Histórico", "👑 Fechamento"])

with abas[0]:
    st.header("📝 Lançamento Expresso")
    st.write("Transcreva os erros do papel para o sistema.")
    
    col_data, col_setor = st.columns(2)
    with col_data:
        data_lancamento = st.date_input("1. Data da Folha", datetime.today())
    with col_setor:
        setor = st.selectbox("2. Setor", ["", "Torres", "Caixas"])
    
    if setor:
        separador = st.selectbox("3. Separador", [""] + equipes[setor])
        
        if separador:
            st.divider()
            st.markdown(f"### ❌ Erros de **{separador}**")
            
            with st.form("form_erros", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    err_cor = st.number_input("🎨 Cor", min_value=0, value=0)
                with col2:
                    err_conf = st.number_input("⚙️ Config.", min_value=0, value=0)
                with col3:
                    err_mod = st.number_input("📦 Modelo", min_value=0, value=0)
                
                submit = st.form_submit_button("💾 Salvar Apontamento", type="primary", use_container_width=True)
                
                if submit:
                    total = err_cor + err_conf + err_mod
                    if total == 0:
                        st.error("⚠️ Você precisa registrar pelo menos 1 erro para salvar.")
                    else:
                        with st.spinner("⏳ Salvando no Google Drive..."):
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
                        
                        st.success(f"✅ Sucesso! {total} erros de {separador} foram salvos.")
                        time.sleep(1.5) 
                        st.rerun()      

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
            
            st.subheader("📈 Evolução Diária de Erros")
            err_por_dia = df_filtro.groupby("Data")["Total_Erros"].sum()
            st.line_chart(err_por_dia, color="#ef4444")

with abas[2]:
    st.header("🕒 Histórico de Apontamentos")
    st.dataframe(df_erros.drop(columns=["ID"], errors="ignore"), use_container_width=True, hide_index=True)

# --- NOVA ABA DE EXPORTAÇÃO ---
with abas[3]:
    st.header("👑 Fechamento e Exportação")
    st.write("Baixe a planilha completa com todo o histórico de erros para abrir no Excel.")
    
    if not df_erros.empty:
        # Prepara o arquivo no formato perfeito para o Excel do Brasil (separado por ; e com acentos)
        df_export = df_erros.drop(columns=["ID"], errors="ignore")
        csv_convertido = df_export.to_csv(index=False, sep=";").encode("utf-8-sig")
        
        hoje_str = datetime.today().strftime('%d-%m-%Y')
        
        st.download_button(
            label="📥 Baixar Relatório Completo (Excel / CSV)",
            data=csv_convertido,
            file_name=f"Relatorio_Qualidade_{hoje_str}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
        st.caption("O arquivo baixado pode ser aberto diretamente no Excel. Ele já está formatado com colunas separadas e acentuação correta.")
    else:
        st.info("Ainda não há dados para exportar.")
