# Extrator de Dados (PDF/JPG/PNG) com Vertex AI Gemini

Script em Python que envia **documentos (PDF/JPG/PNG)** para o **Vertex AI (Gemini)** e recebe a resposta **forçada em JSON** via `response_schema`, com **streaming seguro**, parsing robusto (remove cercas ```json … ``` e lixo) e validações simples (regex, enums).

> **Destaques**
> - ❇️ **JSON garantido** (`response_mime_type="application/json"` + `response_schema`)
> - 🔁 **Streaming** com coleta resiliente de chunks
> - 🧹 **Parser robusto** para “JSON solto” (remove cercas e trechos extras)
> - 🧰 Suporte a **PDF/JPG/PNG** (auto MIME)
> - 🛡️ **SafetySettings** e mensagens de diagnóstico úteis

---

## Sumário

- [Arquitetura (visão rápida)](#arquitetura-visão-rápida)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso (quickstart)](#uso-quickstart)
- [Esquema da saída (JSON)](#esquema-da-saída-json)
- [Exemplo de saída](#exemplo-de-saída)
- [Boas práticas de README (checklist)](#boas-práticas-de-readme-checklist)
- [Segurança & Privacidade](#segurança--privacidade)
- [Troubleshooting](#troubleshooting)
- [Qualidade de código](#qualidade-de-código)
- [Testes rápidos](#testes-rápidos)
- [Roadmap & Limitações](#roadmap--limitações)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## Arquitetura (visão rápida)

1. Você fornece **`prompt`**, **`caminho do arquivo`** e **`typeDoc`** (`pdf`/`jpg`/`png`).
2. O arquivo é lido, convertido em **Base64** e enviado ao **modelo Gemini** via Vertex AI.
3. A resposta chega **via stream** e é convertida em **JSON válido** usando um **schema** definido.
4. O parser limpa cercas de código e tenta extrair o **último objeto `{...}`** se necessário.

---

## Requisitos

- **Python** 3.10+  
- **Google Cloud Project** com **Vertex AI** habilitado
- **Credenciais** de uma **Service Account** com permissão (ex.: *Vertex AI User*, *Storage Object Viewer* se usar GCS)
- **Bibliotecas Python**:
  - `google-cloud-aiplatform` (fornece `vertexai`)
  - Standard library: `json`, `re`, `os`, `base64`

> 💡 *Nota:* O módulo `vertexai.generative_models` é distribuído com `google-cloud-aiplatform`.

---

## Instalação

```bash
# Crie e ative um virtualenv (opcional, recomendado)
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Instale dependências
pip install --upgrade pip
pip install google-cloud-aiplatform
