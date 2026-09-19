# MBEagent
MBE Analyzer — análise crítica estruturada de artigos científicos MBE/PBE (Igor Eckert & Aydamari Faria-Jr).

Integrado ao ecossistema [iaemedicina.com.br](https://iaemedicina.com.br/ferramentas/mbeagent/).

## Segredos necessários (Streamlit secrets)
- `GOOGLE_API_KEY`: chave da API Gemini
- `MASTER_PROMPT`: roteiro mestre de análise crítica

## Stack
- Streamlit · google-genai (SDK novo do Gemini) · PyPDF2
- Modelos: Gemini 2.5 Flash (padrão), 2.5 Flash-Lite e 2.5 Pro
