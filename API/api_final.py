import requests
import time
import pandas as pd
from datetime import datetime

# Configuração da API
BASE_URL = "https://app.clicksign.com/api/v1"
ACCESS_TOKEN = "95b7e6de-0ad8-4cce-a667-e28d5f845549"

# Função para buscar detalhes do documento
def get_document_details(document_key):
    url = f"{BASE_URL}/documents/{document_key}?access_token={ACCESS_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter detalhes do documento {document_key}. Status: {response.status_code}")
        return None

# Função para buscar todos os documentos
def get_all_documents():
    page_number = 1
    all_documents = []
    while True:
        url = f"{BASE_URL}/documents?access_token={ACCESS_TOKEN}&page={page_number}"
        response = requests.get(url)
        if response.status_code != 200:
            break
        data = response.json()
        documents = data.get('documents', [])
        all_documents.extend(documents)
        next_page = data['page_infos'].get('next_page')
        if not next_page:
            break
        page_number = next_page
    return all_documents

# Funções auxiliares de formatação
def format_cpf(cpf):
    if cpf:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf
    return ""

def format_cnpj(cnpj):
    if cnpj:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}" if len(cnpj) == 14 else cnpj
    return ""

def format_datetime(date_str):
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", ""))
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            return date_str
    return ""

# Lista para armazenar os dados
document_data = []

# Buscando documentos
documents = get_all_documents()

# Processando os documentos
for doc in documents:
    status = doc.get('status')
    if status != 'canceled':
        filename = doc.get('filename')
        document_key = doc.get('key')
        finished_at = format_datetime(doc.get('finished_at', ''))
        document_path = "N/A"

        # Inicializa campos do template e assinante
        template_razao_social, template_cnpj, template_nome, template_data = "N/A", "N/A", "N/A", "N/A"
        signer_name, signer_cpf, signer_status, signed_at = "N/A", "N/A", "N/A", "N/A"
        signers_count, signed_count = 0, 0

        if document_key:
            details = get_document_details(document_key)

            if details and 'document' in details:
                document_info = details.get('document', {})

                # Extraindo o path e a pasta
                path = document_info.get('path', '')
                if path:
                    document_path = path.split('/')[1] if '/' in path else path

                # Processando o template
                template = document_info.get('template', None)
                if isinstance(template, dict):
                    template_razao_social = template.get('data', {}).get('RAZÃO SOCIAL', 'N/A')
                    template_cnpj = template.get('data', {}).get('CNPJ', 'N/A')
                    template_nome = template.get('data', {}).get('NOME', 'N/A')
                    template_data = f"{template.get('data', {}).get('DIA', 'N/A')}/{template.get('data', {}).get('MÊS', 'N/A')}/{template.get('data', {}).get('ANO', 'N/A')}"
                else:
                    template_razao_social = "N/A"
                    template_cnpj = "N/A"
                    template_nome = "N/A"
                    template_data = "N/A"

                # Processando assinantes
                signers = document_info.get('signers', [])
                for signer in signers:
                    signers_count += 1
                    if signer.get('signature', {}).get('validation', {}).get('status') == 'conferred':
                        signed_count += 1
                    if signer.get('sign_as') == 'contractee':
                        signer_name = signer.get('name', 'N/A')
                        signer_cpf = signer.get('documentation', 'N/A')
                        signer_status = signer.get('signature', {}).get('validation', {}).get('status', 'N/A')
                        signed_at = format_datetime(signer.get('signature', {}).get('signed_at', ''))
            else:
                print(f"⚠️ Aviso: Detalhes do documento {document_key} não encontrados.")
                continue

        # Definir status final
        if status == "closed" and signer_status == "conferred":
            status_final = "Finalizado e Assinado"
        elif status == "closed":
            status_final = "Finalizado sem Assinatura"
        elif status == "running" and signer_status == "conferred":
            status_final = "Em Andamento - Assinado"
        else:
            status_final = "Em Andamento"

        # Adicionando dados à lista
        document_data.append([
            filename, document_key, finished_at, status,
            template_razao_social, template_cnpj, template_nome, template_data,
            signer_name, signer_cpf, signer_status, signed_at, status_final,
            f"{signed_count}/{signers_count}", document_path
        ])

        time.sleep(0.2)

# Criando DataFrame
df = pd.DataFrame(document_data, columns=[
    "Documento", "Chave", "Finalizado em", "Status",
    "Razão Social do Template", "CNPJ do Template", "Nome do Assinante", "Data do Template",
    "Nome do Assinante", "CPF do Assinante", "Status da Validação", "Data da Assinatura", "Status Final",
    "Assinantes (Concluídos/Total)", "Pasta"
])

# Aplicando máscaras
df["CPF do Assinante"] = df["CPF do Assinante"].apply(format_cpf)
df["CNPJ do Template"] = df["CNPJ do Template"].apply(format_cnpj)

# Gerando nome do arquivo
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = f"documentos_clicksign_{current_datetime}.xlsx"

# Salvando o arquivo
df.to_excel(file_path, index=False, header=True)

print(f"✅ Arquivo Excel salvo automaticamente em: {file_path}")