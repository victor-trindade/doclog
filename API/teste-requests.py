import requests
import time

# Configuração base da API
BASE_URL = "https://app.clicksign.com/api/v1"
ACCESS_TOKEN = "95b7e6de-0ad8-4cce-a667-e28d5f845549"  # 🔥 Exposta para testes

# Função para fazer requisições com controle de taxa usando os cabeçalhos da API
def rate_limited_request(url, params=None):
    """Faz requisição respeitando os limites de taxa da API."""
    while True:
        try:
            response = requests.get(url, params=params)
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                return response
            # Extrair cabeçalhos de controle de taxa
            rate_limit_remaining = int(response.headers.get('X-Rate-Limit-Remaining', 0))
            rate_limit_reset = int(response.headers.get('X-Rate-Limit-Reset', time.time()))

            if rate_limit_remaining == 0:
                # Se não restam requisições, aguarda até o reset
                wait_time = rate_limit_reset - time.time()

                # Garante que o tempo de espera não seja negativo
                if wait_time > 0:
                    print(f"Limite de requisições atingido. Aguardando {wait_time:.2f} segundos até o reset.")
                    time.sleep(wait_time)
                else:
                    print("O tempo de espera já passou, tentando novamente imediatamente.")
                    time.sleep(0.1)  # Pequeno intervalo antes de tentar novamente
            else:
                # Caso ainda haja requisições disponíveis, continue
                return response
        except requests.exceptions.RequestException as e:
            print(f"Erro ao tentar fazer requisição: {e}")
            break

def get_all_closed_documents():
    """Busca todos os documentos com status 'closed' e exibe seus detalhes com paginação."""
    url = f"{BASE_URL}/documents"
    params = {"access_token": ACCESS_TOKEN}
    
    all_closed_documents = []  # Lista para armazenar documentos fechados
    page = 1  # Inicia na primeira página

    while True:
        params["page[number]"] = page
        params["page[size]"] = 20  # Ajuste o tamanho da página conforme necessário

        try:
            # Faz a requisição para obter os documentos com rate-limiting
            response = rate_limited_request(url, params=params)
            response.raise_for_status()
            response_data = response.json()

            # Percorre os documentos e encontra todos com status 'closed'
            for doc in response_data.get("documents", []):
                if doc.get("status") == "closed":
                    all_closed_documents.append(doc)  # Adiciona o documento à lista

            # Informações sobre as páginas
            page_info = response_data.get("page_infos", {})
            total_pages = page_info.get("total_pages", 1)
            next_page = page_info.get("next_page", None)

            # Verifica se há mais páginas
            if next_page and page < total_pages:
                page = next_page  # Avança para a próxima página
            else:
                break  # Se não houver mais páginas, encerra o loop

        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar documentos: {e}")
            break

    if not all_closed_documents:
        print("Nenhum documento fechado encontrado.")
        return []

    return all_closed_documents  # Retorna a lista de documentos fechados

# 🔹 Testando a função
closed_documents = get_all_closed_documents()

# Exibir todos os documentos fechados
if closed_documents:
    for doc in closed_documents:
        print(f"📄 Documento encontrado: {doc.get('filename')}")
        print(f"🔑 Chave: {doc.get('key')}")
        print(f"📅 Finalizado em: {doc.get('finished_at')}")
        print("-" * 40)
else:
    print("Nenhum documento fechado encontrado.")
