import os
import csv
from django.db import transaction
from .models import Performance, Financeiro


def importar_csv_performance(caminho_arquivo, filial, batch_size=1000):
    with open(caminho_arquivo, mode='r', encoding='utf-8') as file:
        leitor_csv = csv.DictReader(file, delimiter=';')
        performances = []
        for linha in leitor_csv:
            performance = Performance(
                data_do_periodo=linha['data_do_periodo'],
                periodo=linha['periodo'],
                duracao_do_periodo=linha['duracao_do_periodo'],
                numero_minimo_de_entregadores_regulares_na_escala=linha[
                    'numero_minimo_de_entregadores_regulares_na_escala'],
                tag=linha['tag'],
                id_da_pessoa_entregadora=linha['id_da_pessoa_entregadora'],
                pessoa_entregadora=linha['pessoa_entregadora'],
                praca=linha['praca'],
                sub_praca=linha['sub_praca'],
                origem=linha['origem'],
                tempo_online_escalado=linha['tempo_online_escalado'],
                tempo_online_absoluto=linha['tempo_online_absoluto'],
                numero_de_corridas_ofertadas=linha['numero_de_corridas_ofertadas'],
                numero_de_corridas_aceitas=linha['numero_de_corridas_aceitas'],
                numero_de_corridas_rejeitadas=linha['numero_de_corridas_rejeitadas'],
                numero_de_corridas_completadas=linha['numero_de_corridas_completadas'],
                numero_de_corridas_canceladas_pela_pessoa_entregadora=linha[
                    'numero_de_corridas_canceladas_pela_pessoa_entregadora'],
                numero_de_pedidos_aceitos_e_concluidos=linha['numero_de_pedidos_aceitos_e_concluidos'],
                soma_das_taxas_das_corridas_aceitas=linha['soma_das_taxas_das_corridas_aceitas'],
                filial=filial  # Aqui associamos a filial com base na subpasta
            )
            performances.append(performance)

            if len(performances) >= batch_size:
                # Salvar em batch e limpar a lista
                with transaction.atomic():
                    Performance.objects.bulk_create(performances)
                performances = []  # Limpar para o próximo lote

        # Salvar o que restou após o loop
        if performances:
            with transaction.atomic():
                Performance.objects.bulk_create(performances)


def importar_csv_financeiro(caminho_arquivo, filial, batch_size=1000):
    with open(caminho_arquivo, mode='r', encoding='utf-8') as file:
        leitor_csv = csv.DictReader(file, delimiter=';')
        financeiros = []
        for linha in leitor_csv:
            financeiro = Financeiro(
                data_do_lancamento_financeiro=linha['data_do_lancamento_financeiro'],
                data_do_periodo_de_referencia=linha['data_do_periodo_de_referencia'],
                data_do_repasse=linha['data_do_repasse'],
                periodo=linha['periodo'],
                praca=linha['praca'],
                subpraca=linha['subpraca'],
                origem=linha['origem'],
                id_da_pessoa_entregadora=linha['id_da_pessoa_entregadora'],
                recebedor=linha['recebedor'],
                tipo=linha['tipo'],
                valor=linha['valor'],
                descricao=linha['descricao'],
                atingido=linha['atingido'],
                percentual_de_tempo_online=linha['percentual_de_tempo_online'],
                percentual_de_aceitacao=linha['percentual_de_aceitacao'],
                percentual_de_conclusao=linha['percentual_de_conclusao'],
                criterio_tempo_online=linha['criterio_tempo_online'],
                criterio_rotas_aceitas=linha['criterio_rotas_aceitas'],
                criterio_rotas_concluidas=linha['criterio_rotas_concluidas'],
                margem_fee_porcentagem=linha['margem_fee_porcentagem'],
                filial=filial  # Aqui associamos a filial com base na subpasta
            )
            financeiros.append(financeiro)

            if len(financeiros) >= batch_size:
                # Salvar em batch e limpar a lista
                with transaction.atomic():
                    Financeiro.objects.bulk_create(financeiros)
                financeiros = []  # Limpar para o próximo lote

        # Salvar o que restou após o loop
        if financeiros:
            with transaction.atomic():
                Financeiro.objects.bulk_create(financeiros)


def importar_pasta(csv_dir, batch_size=1000):
    for root, dirs, files in os.walk(csv_dir):
        for dir_name in dirs:
            # Aqui você obtém o nome da filial da subpasta
            filial = dir_name
            for file in os.listdir(os.path.join(root, dir_name)):
                if file.endswith(".csv"):
                    caminho_arquivo = os.path.join(root, dir_name, file)
                    if "performance" in file.lower():
                        importar_csv_performance(caminho_arquivo, filial, batch_size)
                    elif "financeiro" in file.lower():
                        importar_csv_financeiro(caminho_arquivo, filial, batch_size)
