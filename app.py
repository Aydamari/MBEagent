# --- START OF FILE app.py ---

import streamlit as st
from google import genai
import PyPDF2 as pdf

# --- FUNÇÃO AUXILIAR ---

def extract_text_from_pdf(uploaded_file):
    """Extrai texto de um arquivo PDF enviado."""
    if uploaded_file is not None:
        try:
            pdf_reader = pdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            st.error(f"Erro ao ler o PDF: {e}")
            return None
    return None

# --- CONFIGURAÇÃO INICIAL E CARREGAMENTO DE DADOS ---
# Lê o prompt e a chave de API diretamente do sistema de segredos do Streamlit.
# Isso funciona tanto localmente (com .streamlit/secrets.toml) quanto na nuvem.
try:
    PROMPT_MESTRE = st.secrets["MASTER_PROMPT"]
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except (KeyError, FileNotFoundError):
    st.error("ERRO: Segredos não configurados! Certifique-se de que 'GOOGLE_API_KEY' e 'MASTER_PROMPT' estão configurados nos segredos do seu app.")
    st.stop()


# --- INTERFACE DO USUÁRIO (UI) ---

st.set_page_config(page_title="Analisador de Artigos MBE/PBE", layout="wide")

# CSS mínimo e eficaz para corrigir a cor dos cabeçalhos e da tabela.
st.markdown("""
<style>
    /* Força a cor preta nos cabeçalhos gerados pelo Markdown */
    h2, h3 {
        color: black !important;
        font-weight: bold !important;
    }
    /* Força a cor preta e negrito nos cabeçalhos das tabelas Markdown */
    th {
        color: black !important;
        font-weight: bold !important;
        background-color: #fafafa !important;
    }
</style>
""", unsafe_allow_html=True)


st.header("🔬 Analisador de Artigos Científicos MBE/PBE_V5")
st.caption("Desenvolvido por Igor Eckert & Aydamari Faria-Jr · Integrado ao ecossistema iaemedicina.com.br")

# Barra Lateral com Configurações
st.sidebar.title("Configurações")

model_mapping = {
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Flash-Lite": "gemini-2.5-flash-lite",
    "Gemini 2.5 Pro": "gemini-2.5-pro"
}
model_options = list(model_mapping.keys())

selected_model_name = st.sidebar.selectbox(
    "Escolha o modelo de IA:", options=model_options, index=0
)
st.sidebar.info("A seleção do modelo impacta a velocidade e a qualidade da análise.")

# Interface Principal
prompt_usuario = st.text_area(
    "Instruções Adicionais (Opcional):",
    height=100,
    placeholder="Ex: 'Analise o artigo em anexo."
)
uploaded_file = st.file_uploader("Faça o upload do seu artigo em PDF aqui:", type=["pdf"])
submit_button = st.button("Analisar Artigo")


# --- LÓGICA PRINCIPAL ---

if PROMPT_MESTRE and submit_button:
    actual_model_id = model_mapping[selected_model_name]

    if uploaded_file is None:
        st.warning("Por favor, faça o upload de um arquivo PDF antes de analisar.")
    else:
        with st.spinner("Extraindo texto do PDF..."):
            texto_extraido = extract_text_from_pdf(uploaded_file)

        if texto_extraido:
            st.info(f"Texto extraído com sucesso! Enviando para o modelo: **{selected_model_name}**")

            prompt_final = f"{PROMPT_MESTRE}\n---\nINSTRUÇÃO ADICIONAL DO USUÁRIO:\n{prompt_usuario if prompt_usuario else 'Nenhuma.'}\n---\nCONTEÚDO DO ARTIGO:\n{texto_extraido}"

            try:
                with st.spinner(f"O modelo '{selected_model_name}' está processando a análise crítica..."):
                    response = client.models.generate_content(
                        model=actual_model_id,
                        contents=prompt_final
                    )

                st.subheader("Resultado da Análise Crítica")

                # Usa o container nativo do Streamlit para um visual limpo.
                with st.container(border=True):
                    st.markdown(response.text)

            except Exception as e:
                st.error(f"Ocorreu um erro ao chamar a API do Gemini: {e}")
