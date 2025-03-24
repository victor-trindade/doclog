import requests
import time
from datetime import timedelta

import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import threading

# Configuração da API
BASE_URL = "https://app.clicksign.com/api/v1"
ACCESS_TOKEN = "52e81e6a-964f-4252-ae90-a23174d5c598"

api_keys = {
    "D&G_SP": "ea2a208c-c8e6-443c-a796-f236f6c2e142",
    "D&G_CAMP": "76b65771-7858-4d58-ac44-d0e29a82309b",
    "D&G_BH": "95b7e6de-0ad8-4cce-a667-e28d5f845549",
    "D&G_SA": "4bd972fb-7517-4e7b-89cc-02ba7797b355",
    "D&G_SBC": "52e81e6a-964f-4252-ae90-a23174d5c598"
}

# Sessão HTTP persistente
session = requests.Session()

# Lista para armazenar logs de erro
error_log = []

# Função para registrar logs de erro
def log_error(document_key, filename, status, reason):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if reason.startswith("Erro "):
        parts = reason.split()
        if len(parts) >= 2 and parts[1].isdigit():
            code = parts[1]
            reason = f"Erro {code}"
    error_log.append([timestamp, document_key, filename, status, reason])


# Função de tentativa com backoff exponencial
def retry_request(func, *args, rate_limiter=None, pbar_global=None, **kwargs):
    retries = 3
    delay = 1
    while retries > 0:
        try:
            response = func(*args, **kwargs)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                tqdm.write("\nLimite de requisições atingido (429), aguardando reset...", end="")
                # Tempo fixo de 10 segundos
                sleep_time = 10
                for i in range(sleep_time):
                    tqdm.write(f"Aguardando {sleep_time-i} segundos até o reset ⏳", end="\r")
                    pbar_global.update(0)  # Atualiza a barra de progresso sem mudar o valor total
                    time.sleep(1)  # Espera de 1 segundo por vez
                tqdm.write("")  # Para garantir que a linha de progresso seja concluída
            else:
                log_error(args[0], "N/A", "N/A", f"Erro {response.status_code}")
        except Exception as e:
            log_error("N/A", "N/A", "N/A", "Erro durante requisição")
        retries -= 1
        if retries > 0:
            if rate_limiter is not None:
                rate_limiter.wait_for_next()
            time.sleep(delay)
            delay *= 2
        else:
            log_error(args[0], "N/A", "N/A", "Falha após várias tentativas")
    return None




# Classe RateLimiter para controlar as requisições
class RateLimiter:
    def __init__(self):
        self.max_requests_per_interval = 50
        self.interval_seconds = 11
        self.timestamps = []
        self.lock = threading.Lock()

    def wait_for_next(self):
        with self.lock:
            current_time = time.time()
            # Limita o número de requisições dentro do intervalo
            self.timestamps = [ts for ts in self.timestamps if current_time - ts < self.interval_seconds]
            if len(self.timestamps) >= self.max_requests_per_interval:
                # Aguarda o tempo necessário até o reset
                sleep_time = self.interval_seconds - (current_time - self.timestamps[0])
                if sleep_time > 0:
                    #tqdm.write(f"\rAguardando {sleep_time:.2f} segundos 🕑", end="")
                    time.sleep(sleep_time)
                current_time = time.time()
            self.timestamps.append(current_time)

# Função para buscar detalhes do documento
def get_document_details(document_key, rate_limiter):
    url = f"{BASE_URL}/documents/{document_key}?access_token={ACCESS_TOKEN}"
    response = retry_request(session.get, url, rate_limiter=rate_limiter)
    if response:
        rate_limiter.wait_for_next()  # Espera a quantidade de requisições adequada
        return response.json()
    else:
        log_error(document_key, "N/A", "N/A", "Erro ao obter detalhes do documento 🛑")
        return None

# Função para buscar todos os documentos
def get_all_documents(rate_limiter):
    print("Buscando todos os documentos 📑...")
    page_number = 1
    all_documents = []
    while True:
        url = f"{BASE_URL}/documents?access_token={ACCESS_TOKEN}&page={page_number}"
        response = retry_request(session.get, url, rate_limiter=rate_limiter)
        if response:
            rate_limiter.wait_for_next()  # Aguarda a próxima requisição
            data = response.json()
            documents = data.get('documents', [])
            all_documents.extend(documents)
            next_page = data['page_infos'].get('next_page')
            if not next_page:
                break
            page_number = next_page
        else:
            log_error("N/A", "N/A", "N/A", f"Erro ao obter lista de documentos na página {page_number} ❌")
            break
    print(f"Total de documentos encontrados: {len(all_documents)} 📊")
    return all_documents

# Função para processar cada documento
def process_document(doc, document_data, rate_limiter, pbar_global):
    try:
        status = doc.get('status')
        filename = doc.get('filename', 'N/A')
        document_key = doc.get('key', 'N/A')
        pasta = "N/A"  # Valor padrão para a pasta

        if status != 'canceled' and document_key:
            # Espera antes de pegar os detalhes do documento
            rate_limiter.wait_for_next()

            details = get_document_details(document_key, rate_limiter)
            if details and 'document' in details:
                document_info = details.get('document', {})

                # Extrai o campo "path" e obtém a primeira parte (a pasta)
                raw_path = document_info.get('path', '')
                if raw_path:
                    parts = raw_path.split('/')
                    if parts[0] == '' and len(parts) > 1:
                        pasta = parts[1]
                    else:
                        pasta = parts[0]

                # Processa os dados dos signatários
                signer_name = "N/A"
                signer_cpf = "N/A"
                signer_status = "N/A"
                signed_at = "N/A"
                signers_count = len(document_info.get('signers', []))
                signed_count = sum(1 for s in document_info.get('signers', [])
                                   if s.get('signature', {}).get('validation', {}).get('status') == 'conferred')

                for signer in document_info.get('signers', []):
                    if signer.get('sign_as') == 'contractee':
                        signer_name = signer.get('name', 'N/A')
                        signer_cpf = signer.get('documentation', 'N/A')
                        signer_status = signer.get('signature', {}).get('validation', {}).get('status', 'N/A')
                        signed_at = signer.get('signature', {}).get('signed_at', 'N/A')

                status_final = "Em Andamento"
                if status == "closed":
                    status_final = "Finalizado e Assinado" if signer_status == "conferred" else "Finalizado sem Assinatura"
                elif status == "running" and signer_status == "conferred":
                    status_final = "Em Andamento - Assinado"

                document_data.append([filename, document_key, status, signer_name, signer_cpf, signer_status,
                                      signed_at, status_final, f"{signed_count}/{signers_count}", pasta])
            else:
                log_error(document_key, filename, status, "Erro ao processar detalhes do documento ⚠️")
    except Exception as e:
        log_error(document_key, filename, status, f"Erro inesperado: {str(e)} 😞")
    finally:
        pbar_global.update(1)

# Função principal
# Função principal
def process_documents_excel():
    # Registra o tempo de início
    start_time = time.time()

    print("Iniciando o processo de coleta de documentos 🔍...")
    rate_limiter = RateLimiter()
    documents = get_all_documents(rate_limiter)
    total_documents = len(documents)
    document_data = []

    # Barra de progresso global
    pbar_global = tqdm(total=total_documents, desc="Processando documentos", unit=" app")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_document, doc, document_data, rate_limiter, pbar_global)
                   for doc in documents]
        for future in as_completed(futures):
            future.result()

    pbar_global.close()

    # Criação dos DataFrames
    df_documents = pd.DataFrame(document_data, columns=[
        "Documento", "Chave", "Status", "Nome do Signatário", "CPF do Signatário",
        "Status do Signatário", "Assinado em", "Status Final", "Contagem de Assinaturas", "Pasta"
    ])
    df_errors = pd.DataFrame(error_log, columns=[
        "Data/Hora", "Chave do Documento", "Nome do Documento", "Status", "Motivo da Falha"
    ])

    # Criação do arquivo Excel com múltiplas abas
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"documentos_{timestamp}.xlsx"
    with pd.ExcelWriter(output_filename, engine='xlsxwriter') as writer:
        df_documents.to_excel(writer, sheet_name="Documentos", index=False)
        df_errors.to_excel(writer, sheet_name="Erros", index=False)

    # Registra o tempo de fim
    end_time = time.time()

    # Calcula o tempo total de execução
    total_time_seconds = end_time - start_time
    # Calculando as horas, minutos e segundos
    hours = total_time_seconds // 3600
    minutes = (total_time_seconds % 3600) // 60
    seconds = total_time_seconds % 60

    # Formata a duração para horas, minutos e segundos
    total_time_formatted = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    print(f"Tempo de execução: {total_time_formatted} 🕒")
    print(f"Arquivo Excel gerado: {output_filename} 📄✅")



# Inicia o processo
process_documents_excel()
