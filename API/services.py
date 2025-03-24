import requests
from django.utils import timezone
from app.models import Contract, Company, Signer
import time

def retry_request(func, *args, **kwargs):
    retries = 3
    delay = 1
    while retries > 0:
        try:
            response = func(*args, **kwargs)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                print("Limite de requisições atingido, aguardando...")
                time.sleep(10)
            else:
                print(f"Erro na requisição: {response.status_code}")
        except Exception as e:
            print(f"Erro: {e}")
        retries -= 1
        time.sleep(delay)
        delay *= 2
    return None

def get_single_document():
    test_document_key = "a721cfef-466f-4812-9954-f440689b741a"
    url = f"https://app.clicksign.com/api/v1/documents/{test_document_key}?access_token=95b7e6de-0ad8-4cce-a667-e28d5f845549"
    response = retry_request(requests.get, url)
    if response:
        return [response.json()['document']]
    else:
        print("Erro ao obter documento.")
        return []

def create_or_update_contract(clicksign_document):
    document_key = clicksign_document.get("key")
    print("Document Data:", clicksign_document)

    # Pegando status do documento
    status_document = clicksign_document.get("status", "in_progress")

    # Obtendo o CNPJ do template ou do signatário
    cnpj = clicksign_document.get("template", {}).get("data", {}).get("CNPJ", "")
    if not cnpj:
        for signer in clicksign_document.get("signers", []):
            if signer.get("sign_as") == "contractee":
                cnpj = signer.get("documentation", "")

    if not cnpj:
        print(f"CNPJ não encontrado para o documento {document_key}.")
        return

    # Identificando tipo de documento pelo caminho (path)
    path = clicksign_document.get("path", "")
    document_type = path.split('/')[1] if path and len(path.split('/')) > 1 else "N/A"

    # Buscando a empresa pelo CNPJ
    company = Company.objects.filter(cnpj=cnpj).first()
    if not company:
        print(f"Empresa com CNPJ {cnpj} não encontrada.")
        return

    # Pegando data de criação correta do documento
    created_at_str = clicksign_document.get("uploaded_at")
    created_at = timezone.make_aware(
        timezone.datetime.fromisoformat(created_at_str.replace("Z", ""))
    ) if created_at_str else timezone.now()

    # Criando ou atualizando o contrato
    contract, created = Contract.objects.update_or_create(
        document_key=document_key,
        company=company,
        defaults={
            "status_document": status_document,  # Corrigido: apenas este campo
            "type": document_type,
            "deadline_at": clicksign_document.get("deadline_at", None),
            "created_at": created_at,
        }
    )

    print(f"Contrato {document_key} {'criado' if created else 'atualizado'} com created_at {created_at}.")

    # Traduzindo as funções dos signatários
    function_translation = {
        'contractee': 'Contratado',
        'contractor': 'Contratante',
        'witness': 'Testemunha',
    }

    # Criando ou atualizando os signatários
    for signer in clicksign_document.get("signers", []):
        documentation = signer.get("documentation", "").strip()  # CPF ou CNPJ
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
        signed_at = timezone.make_aware(
            timezone.datetime.fromisoformat(signed_at_str.replace("Z", "")) if signed_at_str else None
        )

        # Criando ou atualizando o signatário
        signatory, _ = Signer.objects.update_or_create(
            contract=contract,
            documentation=documentation,
            defaults={
                "status": status_signer,
                "signed_at": signed_at,
                "sign_as": translated_sign_as,
                "nome": nome,
            }
        )

    print(f"Signatários associados ao contrato {document_key}.")

def process_contracts():
    print("Buscando contrato da API ClickSign...")
    documents = get_single_document()
    for doc in documents:
        create_or_update_contract(doc)
