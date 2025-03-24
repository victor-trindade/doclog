import requests
import time
import pandas as pd
from datetime import datetime

# Configuração da API
BASE_URL = "https://app.clicksign.com/api/v1"
ACCESS_TOKEN = "db7f47cc-48f6-4869-b8e3-34767d48746d"

# BH 95b7e6de-0ad8-4cce-a667-e28d5f845549


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

# Formatação do CPF e CNPJ
def format_cpf(cpf):
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf

def format_cnpj(cnpj):
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}" if len(cnpj) == 14 else cnpj

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
        
        # Inicializa campos
        template_razao_social = "N/A"
        template_cnpj = "N/A"
        template_nome = "N/A"
        template_data = "N/A"
        signer_name = "N/A"
        signer_status = "N/A"
        signed_at = "N/A"
        signer_cpf = "N/A"
        signers_count = 0  # Contador de assinantes
        signed_count = 0  # Contador de assinantes que assinaram (status "conferred")
        
        if document_key:
            details = get_document_details(document_key)
            if details:
                template = details.get('document', {}).get('template', {}).get('data', {})
                template_razao_social = template.get('RAZÃO SOCIAL', 'N/A')
                template_cnpj = template.get('CNPJ', 'N/A')
                template_nome = template.get('NOME', 'N/A')
                template_data = f"{template.get('DIA', 'N/A')}/{template.get('MÊS', 'N/A')}/{template.get('ANO', 'N/A')}"
                
                # Processar signers
                signers = details.get('document', {}).get('signers', [])
                for signer in signers:
                    signers_count += 1  # Incrementa o contador de assinantes
                    if signer.get('signature', {}).get('validation', {}).get('status') == 'conferred':
                        signed_count += 1  # Incrementa o contador de assinantes que assinaram

                    if signer.get('sign_as') == 'contractee':  # Pega dados do "contractee"
                        signer_name = signer.get('name', 'N/A')
                        signer_cpf = signer.get('documentation', 'N/A')
                        signer_status = signer.get('signature', {}).get('validation', {}).get('status', 'N/A')
                        signed_at = format_datetime(signer.get('signature', {}).get('signed_at', ''))

        # Definir status final
        if status == "closed" and signer_status == "conferred":
            status_final = "Finalizado e Assinado"
        elif status == "closed":
            status_final = "Sem Informação"
        elif status == "running" and signer_status == "conferred":
            status_final = "Em Andamento - Assinado"
        elif status == "canceled":
            status_final = "Cancelado"
        else:
            status_final = "Em Andamento"
        
        # Adicionando dados à lista, incluindo a quantidade de assinantes e assinantes concluídos
        document_data.append([
            filename, document_key, finished_at, status,
            template_razao_social, template_cnpj, template_nome, template_data,
            signer_name, signer_cpf, signer_status, signed_at, status_final,
            f"{signed_count}/{signers_count}"  # Coluna com a quantidade de assinantes concluídos/total
        ])
        
        time.sleep(0.2)  # Pausa de 200ms entre requisições

# Criando DataFrame
df = pd.DataFrame(document_data, columns=[
    "Documento", "Chave", "Finalizado em", "Status", 
    "Razão Social do Template", "CNPJ do Template", "Nome do Assinante", "Data do Template", 
    "Nome do Assinante", "CPF do Assinante", "Status da Validação", "Data da Assinatura", "Status Final",
    "Assinantes (Concluídos/Total)"
])

# Aplicando máscaras
df["CPF do Assinante"] = df["CPF do Assinante"].apply(format_cpf)
df["CNPJ do Template"] = df["CNPJ do Template"].apply(format_cnpj)

# Gerando um nome de arquivo com base na data e hora atuais
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
file_path = f"documentos_clicksign_{current_datetime}.xlsx"

# Salvando o arquivo com o nome gerado automaticamente
df.to_excel(file_path, index=False, header=True )

print(f"✅ Arquivo Excel salvo automaticamente em: {file_path}")
