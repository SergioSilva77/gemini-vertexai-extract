import json, re, os
from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmBlockThreshold, HarmCategory


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'${path_file_pem}'


def obter_texto_documento(prompt, file, typeDoc):

    def extract_json_loose(s: str):
        """Extrai o último objeto JSON da string, removendo cercas ``` e lixo ao redor."""
        if not s:
            raise ValueError("Resposta vazia do modelo.")
        s = s.strip()
        # remove cercas tipo ```json ... ```
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.IGNORECASE|re.DOTALL).strip()
        # tenta parse direto
        try:
            return json.loads(s)
        except:
            # tenta pegar o último bloco {...}
            m = re.search(r"\{[\s\S]*\}\s*$", s)
            if not m:
                raise ValueError(f"Não foi possível localizar JSON na resposta: {s[:2000]}")
            return json.loads(m.group(0))

    def generate():
        import vertexai
        vertexai.init(project="transcricao-de-guias", location="us-central1")

        model = GenerativeModel("gemini-2.5-pro")

        gen_cfg = GenerationConfig(
            max_output_tokens=10000,  # suficiente p/ classificar e listar evidências
            temperature=0,
            top_p=0.95,
            response_mime_type="application/json",
            response_schema=schema
        )

        safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
            )
        ]

        stream = model.generate_content(
            [prompt, document1],
            generation_config=gen_cfg,
            safety_settings=safety_settings,
            stream=True,
        )

        text_parts = []
        finish_reason = None
        safety_ratings = None

        # >>> Coleta robusta dos pedaços de stream
        for chunk in stream:
            try:
                if getattr(chunk, "candidates", None):
                    c = chunk.candidates[0]
                    finish_reason = getattr(c, "finish_reason", finish_reason)
                    safety_ratings = getattr(c, "safety_ratings", safety_ratings)
                    if getattr(c, "content", None) and getattr(c.content, "parts", None):
                        for p in c.content.parts:
                            if getattr(p, "text", None):
                                text_parts.append(p.text)
            except Exception as ex:
                print("Erro ao processar chunk:", ex)

        raw = "".join(text_parts).strip()

        # >>> Diagnóstico: se veio bloqueado ou vazio, exponha o motivo
        if not raw:
            print("Resposta vazia. finish_reason:", finish_reason, "| safety_ratings:", safety_ratings)
            raise RuntimeError(f"Resposta vazia do modelo. finish_reason={finish_reason} safety={safety_ratings}")

        try:
            resultado = extract_json_loose(raw)
        except Exception as ex:
            # devolve o raw p/ você inspecionar no log
            print("Falha ao parsear JSON. RAW (até 2k chars):", raw[:2000])
            raise

        return json.dumps(resultado, ensure_ascii=False, indent=2)

    # ---------- prepara o documento ----------
    import base64
    def convert_pdf_to_base64(pdf_path):
        with open(pdf_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')


    

    # Schema Python (dict) para usar em GenerationConfig.response_schema
# Saída: ARRAY de pessoas; "grau_dependencia" é STRING obrigatória (sem enum)

    # Schema Python (dict) para usar em GenerationConfig.response_schema
# Saída: ARRAY de pessoas; itens com campos gerais + campos de RG (prefixo document_rg_*)
# Observação: "grau_dependencia" é STRING obrigatória (sem enum)

    # Schema Python (dict) para usar em GenerationConfig.response_schema
# Saída: ARRAY de pessoas; inclui has_rg / has_cnh (booleans) e campos de RG (document_rg_*)

    # Schema Python (dict) para usar em GenerationConfig.response_schema
# Saída: ARRAY de pessoas; inclui has_rg / has_cnh (booleans) e campos de RG (document_rg_*)

    schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "additionalProperties": False,
        "properties": {
            # Identificador do papel no grupo (sem enum)
            "grau_dependencia": {"type": "STRING"},

            # Booleans de presença de documentos
            "has_rg": {"type": "BOOLEAN"},
            "has_cnh": {"type": "BOOLEAN"},

            # Campos pessoais (gerais)
            "document_cpf": {"type": "STRING", "pattern": r"^\d{11}$", "nullable": True},
            "document_name": {"type": "STRING", "maxLength": 150},
            "document_mother_name": {"type": "STRING", "maxLength": 150, "nullable": True},
            "document_father_name": {"type": "STRING", "maxLength": 150, "nullable": True},
            "document_birth_date": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$"},
            "document_issuing_state": {"type": "STRING", "pattern": r"^[A-Z]{2}$", "nullable": True},
            "document_gender": {
                "type": "STRING",
                "enum": ["FEMININO", "MASCULINO", "OUTRO", "NAO_INFORMADO"]
            },
            "document_email": {"type": "STRING", "format": "email", "maxLength": 120, "nullable": True},

            # Escolaridade (enum exigido; use null se desconhecido)
            "document_schooling": {
                "type": "STRING",
                "enum": [
                    "Analfabeto, inclusive o que, embora tenha recebido instrução, não se alfabetizou",
                    "Até o 5º ano incompleto do Ensino Fundamental (Antiga 4ª série) ou que se tenha alfabetizado sem ter frequentado escola regular",
                    "5º ano completo do Ensino Fundamental",
                    "Do 6º ao 9º ano do Ensino Fundamental incompleto (antiga 5ª a 8ª série)",
                    "Ensino Fundamental Completo",
                    "Ensino Médio incompleto",
                    "Ensino Médio completo",
                    "Educação Superior incompleta",
                    "Educação Superior completa",
                    "Pós-Graduação completa",
                    "Mestrado completo",
                    "Doutorado completo"
                ],
                "nullable": True
            },

            # Raça (enum exigido; se desconhecido usar "NÃO INFORMADO")
            "document_race": {
                "type": "STRING",
                "enum": ["BRANCA", "PRETA", "PARDA", "INDÍGENA", "AMARELA", "NÃO INFORMADO"]
            },

            "document_marital_status": {
                "type": "STRING",
                "enum": ["SOLTEIRO", "CASADO", "CASADO(A)", "DIVORCIADO", "VIUVO", "UNIAO_ESTAVEL", "SEPARADO"],
                "nullable": True
            },
            "document_city": {"type": "STRING", "maxLength": 100, "nullable": True},
            "document_nationality": {"type": "STRING", "maxLength": 60, "nullable": True},
            "document_national_health_card": {"type": "STRING", "pattern": r"^\d{10,15}$", "nullable": True},

            # CNH
            "document_cnh": {"type": "STRING", "pattern": r"^\d{11}$", "nullable": True},
            "document_issuing_body_cnh": {"type": "STRING", "maxLength": 20, "nullable": True},
            "document_cnh_uf_emitter": {"type": "STRING", "pattern": r"^[A-Z]{2}$", "nullable": True},
            "document_cnh_date_exped": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$", "nullable": True},
            "document_cnh_date_expiration": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$", "nullable": True},
            "document_cnh_date_first_license": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$", "nullable": True},
            "document_cnh_category": {"type": "STRING", "pattern": r"^[A-E]{1,2}$", "nullable": True},

            # Endereço e contato
            "document_zip_code": {"type": "STRING", "pattern": r"^\d{8}$", "nullable": True},
            "document_address": {"type": "STRING", "maxLength": 200, "nullable": True},
            "document_complement": {"type": "STRING", "maxLength": 100, "nullable": True},
            "document_address_number": {"type": "STRING", "maxLength": 20, "nullable": True},
            "document_neighborhood": {"type": "STRING", "maxLength": 100, "nullable": True},
            "document_ddd_phone": {"type": "STRING", "pattern": r"^\d{2}$", "nullable": True},
            "document_phone_number": {"type": "STRING", "pattern": r"^\d{8,9}$", "nullable": True},
            "document_ddd_cell": {"type": "STRING", "pattern": r"^\d{2}$", "nullable": True},
            "document_cell_number": {"type": "STRING", "pattern": r"^\d{8,9}$", "nullable": True},

            # Outros
            "document_seller_code": {"type": "STRING", "pattern": r"^[A-Za-z0-9]{1,10}$", "nullable": True},
            "document_reg": {"type": "STRING", "maxLength": 40, "nullable": True},
            "document_effective_date": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$", "nullable": True},
            "document_number_health": {"type": "NUMBER", "minimum": 0, "nullable": True},

            # Só para titular (opcional no schema; controle na lógica de geração)
            "document_ans_record": {"type": "STRING", "maxLength": 60, "nullable": True},

            # =========================
            # CAMPOS DE RG (prefixo document_rg_*)
            # =========================
            "document_rg_naturalidade": {"type": "STRING", "maxLength": 100, "nullable": True},         # cidade (sem UF)
            "document_rg_name": {"type": "STRING", "maxLength": 150, "nullable": True},
            "document_rg_cpf": {"type": "STRING", "pattern": r"^\d{11}$", "nullable": True},
            "document_rg_birth_date": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$", "nullable": True},
            "document_rg_father_name": {"type": "STRING", "maxLength": 150, "nullable": True},
            "document_rg_mother_name": {"type": "STRING", "maxLength": 150, "nullable": True},
            "document_rg_nationality": {"type": "STRING", "maxLength": 60, "nullable": True},
            "document_rg_issue_date": {"type": "STRING", "pattern": r"^\d{2}/\d{2}/\d{4}$", "nullable": True},
            "document_rg_number": {
                "type": "STRING",
                "pattern": r"^[0-9A-Za-z.\-\/]{1,20}$",
                "nullable": True
            },
            "document_rg_issuing_body": {"type": "STRING", "maxLength": 30, "nullable": True},           # ex.: SSP, IFP, DETRAN
            "document_rg_issuing_state": {"type": "STRING", "pattern": r"^[A-Z]{2}$", "nullable": True},
            "document_rg_naturalidade_state": {"type": "STRING", "pattern": r"^[A-Z]{2}$", "nullable": True}
        },
        "required": [
            "grau_dependencia",
            "has_rg",
            "has_cnh",
            "document_name",
            "document_birth_date",
            "document_gender",
            "document_race"
        ]
    }
}

    pdf_b64 = convert_pdf_to_base64(file)

    if typeDoc == 'jpg':
        mime_type = 'image/jpeg'
    elif typeDoc == 'png':
        mime_type = 'image/png'
    else:
        mime_type = 'application/pdf'

    from vertexai.generative_models import Part
    document1 = Part.from_data(
        mime_type=mime_type,
        data=base64.b64decode(pdf_b64)
    )

    return generate()



prompt = st['classifier_prompt'][0]
document_path = r'${attachment_path}'
type = 'pdf'

resultado_vertexai = obter_texto_documento(prompt, document_path, type)
