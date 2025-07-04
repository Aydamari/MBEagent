import streamlit as st
import google.generativeai as genai
import PyPDF2 as pdf
import os

# --- FUNÇÕES AUXILIARES ---

@st.cache_data  # Otimização: Lê o prompt do arquivo apenas uma vez
def load_prompt(file_path):
    """Lê e retorna o conteúdo de um arquivo de texto."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"ERRO: O arquivo de prompt '{file_path}' não foi encontrado. Certifique-se de que ele está no mesmo diretório que o app.py.")
        return None

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

# Carrega o prompt mestre a partir do arquivo externo
PROMPT_MESTRE = load_prompt("master_prompt.txt")

# Configura a API do Google (para deploy no Streamlit Cloud)
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except (KeyError, FileNotFoundError):
    st.error("Chave de API do Google não configurada! Adicione-a nos segredos (secrets) do seu app no Streamlit Cloud.")
    st.stop()


# --- INTERFACE DO USUÁRIO (UI) ---

st.set_page_config(page_title="Analisador de Artigos MBE/PBE", layout="wide")
st.header("🔬 Analisador de Artigos Científicos MBE/PBE")
st.caption("Desenvolvido por Igor Eckert & Aydamari Faria-Jr")

# Barra Lateral com Configurações
st.sidebar.title("Configurações")

# Dicionário que mapeia nomes amigáveis para os nomes de API corretos
model_mapping = {
    "Gemini 2.0 Flash (Padrão)": "gemini-2.0-flash",
    "Gemma 3 27B": "gemma-3-27b-it",
    "Gemini 2.5 Pro (Em breve)": "disabled"
}
model_options = list(model_mapping.keys())

# Seletor de modelo
selected_model_name = st.sidebar.selectbox(
    "Escolha o modelo de IA:",
    options=model_options,
    index=0 # Define o modelo padrão
)
st.sidebar.info("A seleção do modelo impacta a velocidade e a qualidade da análise. O Gemini 2.5 Pro será habilitado no futuro.")

# Interface Principal
prompt_usuario = st.text_area(
    "Instruções Adicionais (Opcional):",
    height=100,
    placeholder="O prompt principal já está configurado. Use este campo para focar a análise em um ponto específico. Ex: 'Foque apenas na análise de viés de seleção' ou 'Compare os resultados com o estudo de Smith et al. 2022'."
)
uploaded_file = st.file_uploader("Faça o upload do seu artigo em PDF aqui:", type=["pdf"])
submit_button = st.button("Analisar Artigo")


# --- LÓGICA PRINCIPAL ---

# Só executa se o prompt mestre foi carregado com sucesso
if PROMPT_MESTRE and submit_button:
    actual_model_id = model_mapping[selected_model_name]

    # Validações de entrada
    if actual_model_id == "disabled":
        st.warning("O modelo Gemini 2.5 Pro ainda não está disponível. Por favor, selecione outro modelo.")
    elif uploaded_file is None:
        st.warning("Por favor, faça o upload de um arquivo PDF antes de analisar.")
    else:
        # Processamento
        with st.spinner("Extraindo texto do PDF..."):
            texto_extraido = extract_text_from_pdf(uploaded_file)

        if texto_extraido:
            st.info(f"Texto extraído com sucesso! Enviando para o modelo: **{selected_model_name}**")

            prompt_final = f"""
            {PROMPT_MESTRE}
            ---
            INSTRUÇÃO ADICIONAL DO USUÁRIO (se houver, deve complementar a tarefa principal):
            {prompt_usuario if prompt_usuario else "Nenhuma instrução adicional fornecida."}
            ---
            CONTEÚDO DO ARTIGO CIENTÍFICO PARA ANÁLISE:
            {texto_extraido}
            """

            try:
                with st.spinner(f"O modelo '{selected_model_name}' está processando a análise crítica..."):
                    model = genai.GenerativeModel(actual_model_id)
                    response = model.generate_content(prompt_final)
                
                st.subheader("Resultado da Análise Crítica:")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Ocorreu um erro ao chamar a API do Gemini: {e}")
