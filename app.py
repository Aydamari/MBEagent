# --- START OF FILE app.py ---

import streamlit as st
from google import genai
import PyPDF2 as pdf
from pathlib import Path

# --- CONFIGURAÇÃO DE MODELOS (conforme docs.google.dev/gemini-api/docs/deprecations, set/2026) ---
# gemini-3.8-flash: Flash mais recente (set/2026) · gemini-3.7-flash: Flash anterior da linha 3.x
# gemini-3.5-flash-lite: opção econômica · gemini-2.5-pro: Pro estável (o 3.1 Pro ainda é preview)
MODELOS = {
    "Gemini 3.8 Flash (mais recente)": "gemini-3.8-flash",
    "Gemini 3.7 Flash": "gemini-3.7-flash",
    "Gemini 3.5 Flash-Lite (econômico)": "gemini-3.5-flash-lite",
    "Gemini 2.5 Pro (estável)": "gemini-2.5-pro",
}
MODELO_PADRAO = "Gemini 3.8 Flash (mais recente)"

# Temperatura baixa: prioriza fidelidade ao artigo e consistência da leitura crítica
# (premissa de Reliability do roteiro MBE) em vez de criatividade.
TEMPERATURA = 0.2

# Protege a janela de contexto e o custo: artigos acima disso são truncados com aviso.
LIMITE_CARACTERES = 400_000
MINIMO_CARACTERES = 200  # abaixo disso, provável PDF escaneado (sem camada de texto)


# --- FUNÇÕES AUXILIARES ---

def extract_text_from_pdf(uploaded_file):
    """Extrai texto de um arquivo PDF enviado, separando páginas."""
    try:
        pdf_reader = pdf.PdfReader(uploaded_file)
        paginas = [(page.extract_text() or "") for page in pdf_reader.pages]
        return "\n\n".join(paginas).strip()
    except Exception as e:
        st.error(f"Erro ao ler o PDF: {e}")
        return None


def carregar_config():
    """Carrega chave de API e prompt mestre.

    O prompt mestre pode viver no arquivo versionado `prompt_mestre.md` (recomendado:
    permite revisão técnica MBE com histórico no git) ou no segredo MASTER_PROMPT
    (compatibilidade com a configuração atual do Streamlit Cloud).
    Retorna (client, prompt, fonte_do_prompt) ou interrompe o app com mensagem clara.
    """
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except (KeyError, FileNotFoundError):
        st.error("ERRO: segredo 'GOOGLE_API_KEY' não configurado nos segredos do app.")
        st.stop()

    arquivo_prompt = Path(__file__).parent / "prompt_mestre.md"
    if arquivo_prompt.exists():
        prompt = arquivo_prompt.read_text(encoding="utf-8").strip()
        if prompt:
            return genai.Client(api_key=api_key), prompt, "arquivo prompt_mestre.md (versionado)"
        st.warning("O arquivo prompt_mestre.md está vazio — usando o segredo MASTER_PROMPT.")
    try:
        return genai.Client(api_key=api_key), st.secrets["MASTER_PROMPT"], "segredo MASTER_PROMPT"
    except (KeyError, FileNotFoundError):
        st.error("ERRO: nenhum prompt mestre encontrado. Crie o arquivo 'prompt_mestre.md' ou configure o segredo 'MASTER_PROMPT'.")
        st.stop()


# --- CONFIGURAÇÃO INICIAL ---
client, PROMPT_MESTRE, FONTE_PROMPT = carregar_config()


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


st.header("🔬 Analisador de Artigos Científicos MBE/PBE_V6")
st.caption("Desenvolvido por Igor Eckert & Aydamari Faria-Jr · Integrado ao ecossistema iaemedicina.com.br")

# Barra Lateral com Configurações
st.sidebar.title("Configurações")

selected_model_name = st.sidebar.selectbox(
    "Escolha o modelo de IA:", options=list(MODELOS.keys()), index=list(MODELOS).index(MODELO_PADRAO)
)
st.sidebar.info("A seleção do modelo impacta a velocidade e a qualidade da análise.")
st.sidebar.caption(f"Roteiro de análise carregado de: {FONTE_PROMPT}")

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
    actual_model_id = MODELOS[selected_model_name]

    if uploaded_file is None:
        st.warning("Por favor, faça o upload de um arquivo PDF antes de analisar.")
    else:
        with st.spinner("Extraindo texto do PDF..."):
            texto_extraido = extract_text_from_pdf(uploaded_file)

        if texto_extraido:
            if len(texto_extraido) < MINIMO_CARACTERES:
                st.error("O PDF não contém texto extraível (provável documento escaneado/imagem). "
                         "Envie o PDF com camada de texto ou use uma ferramenta de OCR antes.")
                st.stop()

            if len(texto_extraido) > LIMITE_CARACTERES:
                st.warning(f"Artigo muito longo ({len(texto_extraido):,} caracteres). "
                           f"A análise usará os primeiros {LIMITE_CARACTERES:,} — verifique se a seção relevante ficou de fora.")
                texto_extraido = texto_extraido[:LIMITE_CARACTERES]

            st.info(f"Texto extraído com sucesso! Enviando para o modelo: **{selected_model_name}**")

            prompt_final = f"{PROMPT_MESTRE}\n---\nINSTRUÇÃO ADICIONAL DO USUÁRIO:\n{prompt_usuario if prompt_usuario else 'Nenhuma.'}\n---\nCONTEÚDO DO ARTIGO:\n{texto_extraido}"

            try:
                with st.spinner(f"O modelo '{selected_model_name}' está processando a análise crítica..."):
                    response = client.models.generate_content(
                        model=actual_model_id,
                        contents=prompt_final,
                        config=genai.types.GenerateContentConfig(temperature=TEMPERATURA),
                    )

                resultado = (response.text or "").strip() if response is not None else ""
                if not resultado:
                    st.error("O modelo não retornou texto (possível bloqueio por políticas de conteúdo). "
                             "Tente outro modelo ou verifique o artigo.")
                    st.stop()

                st.subheader("Resultado da Análise Crítica")

                # Usa o container nativo do Streamlit para um visual limpo.
                with st.container(border=True):
                    st.markdown(resultado)

            except Exception as e:
                st.error(f"Ocorreu um erro ao chamar a API do Gemini: {e}")
