# MBEagent
MBE Analyzer — análise crítica estruturada de artigos científicos MBE/PBE (Igor Eckert & Aydamari Faria-Jr).

Integrado ao ecossistema [iaemedicina.com.br](https://iaemedicina.com.br/ferramentas/mbeagent/).

## Modelos (setembro/2026)
- **Gemini 3.8 Flash** (`gemini-3.8-flash`) — padrão, mais recente
- Gemini 3.7 Flash (`gemini-3.7-flash`)
- Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) — opção econômica
- Gemini 2.5 Pro (`gemini-2.5-pro`) — Pro estável (o 3.1 Pro ainda é preview)

Referência de descontinuações: ai.google.dev/gemini-api/docs/deprecations

## Configuração
Segredos do Streamlit (obrigatório):
- `GOOGLE_API_KEY`: chave da API Gemini

Prompt mestre de análise crítica (uma das duas opções):
1. **Recomendado — arquivo versionado:** crie `prompt_mestre.md` na raiz do repositório. Assim o roteiro
   ganha histórico no git e permite revisão técnica/MBE com controle de versão.
2. Segredo `MASTER_PROMPT` (compatibilidade com a configuração atual). O arquivo tem precedência quando existe.

## Stack
- Streamlit · google-genai (SDK atual do Gemini) · PyPDF2
- V6: proteção contra PDF escaneado (sem texto), truncamento com aviso em artigos muito longos,
  validação de resposta vazia e fonte do prompt visível na barra lateral.
