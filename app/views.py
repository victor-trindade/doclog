# app/views.py
from django.http import JsonResponse
from threading import Thread
from app.services import process_contracts
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .forms import CSVUploadForm
from .models import Driver, Company, DriverCompany, Modal
from django.db import IntegrityError
from django.core.exceptions import ValidationError

def import_em_massa(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        # Ler o arquivo CSV
        csv_file = request.FILES['csv_file']
        data = pd.read_csv(csv_file)

        # Percorrer cada linha do CSV
        for index, row in data.iterrows():
            try:
                # Criar ou obter o motorista
                driver, created = Driver.objects.get_or_create(
                    cpf=row['cpf'],
                    defaults={
                        'nome': row['nome_motorista'],
                        'nacionalidade': row['nacionalidade'],
                        'rg': row['rg'],
                        'email': row['email_motorista'],
                        'celular': row['celular_motorista'],
                        'data_nascimento_prestador': row['data_nascimento_prestador'],
                        'ticket': row['ticket'],
                        'origem': row['origem'],
                        'motivo_contato': row['motivo_contato'],
                        'dt_franquia': row['dt_franquia'],
                    }
                )

                # Criar ou obter a empresa
                company, created = Company.objects.get_or_create(
                    cnpj=row['empresa_cnpj'],
                    defaults={
                        'razao_social': row['razao_social_empresa'],
                    }
                )

                # Associar o motorista à empresa
                DriverCompany.objects.get_or_create(driver=driver, company=company)

                # Adicionar o modal ao motorista (caso tenha)
                if 'modal' in row and pd.notnull(row['modal']):
                    modal, created = Modal.objects.get_or_create(nome=row['modal'])
                    driver.modal = modal
                    driver.save()

            except IntegrityError as e:
                print(f"Erro de integridade: {e}")
            except ValidationError as e:
                print(f"Erro de validação: {e}")

        return HttpResponse("Importação concluída com sucesso!")

    return render(request, 'import_csv.html', {'form': CSVUploadForm()})





# Função para iniciar o processamento de contratos
def clicksign_contracts_view(request):

    def async_process():
        process_contracts()  # Chama o processamento dos contratos

    Thread(target=async_process).start()  # Processamento assíncrono para não bloquear a requisição

    return JsonResponse({"message": "Processamento iniciado. Acompanhe o status em tempo real!"})
