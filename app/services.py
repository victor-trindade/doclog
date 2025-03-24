import logging
from django.utils import timezone
import time
import requests
import re
from .models import Contract, Company, Signer

# Configuração básica do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Função de tentativa de requisição
def retry_request(func, *args, **kwargs):
    retries = 3
    delay = 1
    while retries > 0:
        try:
            response = func(*args, **kwargs)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                logger.warning("Limite de requisições atingido, aguardando...")
                time.sleep(10)
            else:
                logger.error(f"Erro na requisição: {response.status_code}")
        except Exception as e:
            logger.error(f"Erro: {e}")
        retries -= 1
        time.sleep(delay)
        delay *= 2
    return None

# Função para buscar todos os documentos com paginação
def get_all_documents(access_token):
    logger.info("Iniciando busca de documentos...")
    page_number = 1
    all_documents = []
    while True:
        url = f"https://app.clicksign.com/api/v1/documents?access_token={access_token}&page={page_number}"
        response = retry_request(requests.get, url)
        if response:
            data = response.json()
            documents = data.get('documents', [])
            all_documents.extend(documents)
            next_page = data['page_infos'].get('next_page')
            if not next_page:
                logger.info(f"Fim da busca de documentos (página {page_number}).")
                break
            page_number = next_page
        else:
            logger.error("Erro ao obter documentos.")
            break
    logger.info(f"Total de documentos encontrados: {len(all_documents)}.")
    return all_documents

# Função para buscar detalhes de um documento específico
def get_document_details(document_key, access_token):
    logger.info(f"Buscando detalhes do documento {document_key}...")
    url = f"https://app.clicksign.com/api/v1/documents/{document_key}?access_token={access_token}"
    response = retry_request(requests.get, url)
    if response:
        logger.info(f"Detalhes do documento {document_key} obtidos com sucesso.")
        return response.json()['document']
    else:
        logger.error(f"Erro ao obter detalhes do documento {document_key}.")
        return None

def create_or_update_contract(clicksign_document, access_token, contracts_to_create_or_update, signers_to_create_or_update):
    document_key = clicksign_document.get("key")
    logger.info(f"Iniciando criação/atualização do contrato {document_key}...")

    # Pegando status do documento
    status_document = clicksign_document.get("status", "in_progress")

    # Obtendo o CNPJ do template ou do signatário
    cnpj = clicksign_document.get("template", {}).get("data", {}).get("CNPJ", "")
    if not cnpj:
        for signer in clicksign_document.get("signers", []):
            if signer.get("sign_as") == "contractee":
                cnpj = signer.get("documentation", "")

    if not cnpj:
        logger.error(f"CNPJ não encontrado para o documento {document_key}.")
        return

    # Normaliza o CNPJ para remover pontuações
    cnpj = re.sub(r'\D', '', cnpj)

    # Identificando tipo de documento pelo caminho (path)
    path = clicksign_document.get("path", "")
    document_type = path.split('/')[1] if path and len(path.split('/')) > 1 else "N/A"

    # Buscando a empresa pelo CNPJ
    company = Company.objects.filter(cnpj=cnpj).first()
    if not company:
        logger.error(f"Empresa com CNPJ {cnpj} não encontrada.")
        return

    # Pegando data de criação correta do documento
    created_at_str = clicksign_document.get("uploaded_at")
    created_at = None
    if created_at_str:
        try:
            created_at = timezone.make_aware(timezone.datetime.fromisoformat(created_at_str.replace("Z", "")))
        except ValueError:
            created_at = timezone.now()

    # Criando ou atualizando o contrato
    contract, created = Contract.objects.update_or_create(
        document_key=document_key,
        company=company,
        defaults={
            "status_document": status_document,
            "type": document_type,
            "deadline_at": clicksign_document.get("deadline_at", None),
            "created_at": created_at or timezone.now(),
        }
    )

    contracts_to_create_or_update.append(contract)
    logger.info(f"Contrato {document_key} {'criado' if created else 'atualizado'} com created_at {created_at}.")

    # Traduzindo as funções dos signatários
    function_translation = {
        'contractee': 'Contratado',
        'contractor': 'Contratante',
        'witness': 'Testemunha',
    }

    # Criando ou atualizando os signatários
    for signer in clicksign_document.get("signers", []):
        documentation = re.sub(r'\D', '', signer.get("documentation", ""))  # Normaliza CPF/CNPJ
        sign_as = signer.get("sign_as", "")
        nome = signer.get("name", "")

        # Traduzindo a função do signatário
        translated_sign_as = function_translation.get(sign_as, sign_as)

        # Pegando status correto do signatário
        signature_data = signer.get("signature", {})
        validation_data = signature_data.get("validation", {})
        status_signer = validation_data.get("status", "N/A")

        # Pegando data correta de assinatura
        signed_at_str = signature_data.get("signed_at", None)
        signed_at = None
        if signed_at_str:
            try:
                signed_at = timezone.make_aware(timezone.datetime.fromisoformat(signed_at_str.replace("Z", "")))
            except ValueError:
                signed_at = None

        # Verificando se o signatário já existe no contrato (evitando duplicação)
        existing_signer = Signer.objects.filter(contract=contract, documentation=documentation).first()

        if existing_signer:
            # Atualizando os campos do signatário se ele já existir
            existing_signer.status = status_signer
            existing_signer.signed_at = signed_at
            existing_signer.sign_as = translated_sign_as
            existing_signer.nome = nome
            signers_to_create_or_update.append(existing_signer)  # Marcar como atualização
            logger.info(f"Signatário {nome} atualizado.")
        else:
            # Criar um novo signatário se não encontrar um existente
            signatory = Signer(
                contract=contract,
                documentation=documentation,
                status=status_signer,
                signed_at=signed_at,
                sign_as=translated_sign_as,
                nome=nome,
            )
            signers_to_create_or_update.append(signatory)  # Marcar como criação
            logger.info(f"Signatário {nome} criado.")

    logger.info(f"Signatários associados ao contrato {document_key}.")

def process_contracts():
    logger.info("Iniciando o processamento de contratos...")
    api_keys = {
        "D&G_BH": "95b7e6de-0ad8-4cce-a667-e28d5f845549",
    }

    contracts_to_create_or_update = []
    signers_to_create_or_update = []

    for company_name, access_token in api_keys.items():
        logger.info(f"Buscando contratos para a empresa {company_name}...")
        documents = get_all_documents(access_token)
        for doc in documents:
            document_details = get_document_details(doc["key"], access_token)
            if document_details:
                create_or_update_contract(document_details, access_token, contracts_to_create_or_update, signers_to_create_or_update)

    # Criar os contratos em massa
    Contract.objects.bulk_create(contracts_to_create_or_update, ignore_conflicts=True)

    # Criar os signatários em massa
    Signer.objects.bulk_create(signers_to_create_or_update, ignore_conflicts=True)

    # Agora, atualize o status final para cada contrato
    contracts_to_update = []
    for contract in contracts_to_create_or_update:
        contract.status_final = contract.calculate_status_final()  # Chama o método para calcular o status
        contracts_to_update.append(contract)

    # Atualize os contratos com o novo status final
    if contracts_to_update:
        Contract.objects.bulk_update(contracts_to_update, ['status_final'])

    logger.info("Processamento concluído.")
