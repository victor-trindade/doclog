import io
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Performance, Financeiro, Origem
from .forms import ImportacaoForm, FILIAL_CHOICE

# Conjunto mínimo de colunas obrigatórias para cada modelo
OBRIGATORIOS_FINANCEIRO = {"data_do_lancamento_financeiro", "valor", "periodo"}
OBRIGATORIOS_PERFORMANCE = {"data_do_periodo", "periodo", "id_da_pessoa_entregadora"}

def detectar_delimitador(arquivo):
    """Detecta se o delimitador do CSV é ';' ou ','."""
    primeira_linha = arquivo.readline().decode('utf-8-sig')
    if ';' in primeira_linha:
        delimitador = ';'
    elif ',' in primeira_linha:
        delimitador = ','
    else:
        delimitador = ';'  # Default para ponto e vírgula se não encontrar nenhum delimitador específico
    arquivo.seek(0)  # Retorna ao início do arquivo
    return delimitador

def importar_csv(request):
    if request.method == 'POST':
        form = ImportacaoForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = request.FILES.get('arquivos')
            filial = form.cleaned_data['filial'].strip()  # Remover espaços extras da filial
           
            if not arquivo:
                messages.error(request, "Nenhum arquivo foi enviado.")
                return redirect('importar_csv')

            nome_arquivo = arquivo.name.strip()  # Remover espaços extras do nome do arquivo

            # Mapeia a chave da filial para o display (nome amigável)
            filial_map = dict(FILIAL_CHOICE)
            filial_display = filial_map.get(filial, filial)  # Pega o nome amigável da filial

            # Verificar se já existe uma origem com o nome do arquivo e a filial
            if Origem.objects.filter(nome=nome_arquivo,tipo=tipo_arquivo, filial=filial_display).exists():
                messages.warning(request, f'O arquivo "{nome_arquivo}" já foi importado para a filial {filial_display}.')
                return redirect('importar_csv')

            # Verificar tipo do arquivo antes de criar a origem
            delimitador = detectar_delimitador(arquivo)
            arquivo.seek(0)  # Retorna ao início do arquivo após a detecção do delimitador
            df = pd.read_csv(arquivo, delimiter=delimitador, encoding='utf-8-sig')

            # Corrigir os cabeçalhos para remover espaços extras e garantir que as colunas sejam interpretadas corretamente
            df.columns = [col.strip().lower() for col in df.columns]

            colunas = set(df.columns)
            print("Cabeçalhos detectados:", colunas)  # Depuração

            if OBRIGATORIOS_PERFORMANCE.issubset(colunas):
                modelo = Performance
                tipo_arquivo = "performance"
            elif OBRIGATORIOS_FINANCEIRO.issubset(colunas):
                modelo = Financeiro
                tipo_arquivo = "financeiro"
            else:
                messages.error(request, f"Formato do arquivo {nome_arquivo} não reconhecido.")
                return redirect('importar_csv')

            # Criando a origem com tipo já definido
            origem = Origem.objects.create(arquivo=arquivo, nome=nome_arquivo, filial=filial_display, tipo=tipo_arquivo)

            try:
                def criar_objetos(modelo, df, origem):
                    dados_importados = []
                    print(modelo)
                    for index, row in df.iterrows():
                        try:
                            if modelo == Performance:
                                dados_importados.append(Performance(
                                    origem_doc=origem,
                                    data_do_periodo=row.get('data_do_periodo', ''),
                                    periodo=row.get('periodo', ''),
                                    duracao_do_periodo=row.get('duracao_do_periodo', ''),
                                    numero_minimo_de_entregadores_regulares_na_escala=int(row.get('numero_minimo_de_entregadores_regulares_na_escala', 0) or 0),
                                    tag=row.get('tag', ''),
                                    id_da_pessoa_entregadora=row.get('id_da_pessoa_entregadora', ''),
                                    pessoa_entregadora=row.get('pessoa_entregadora', ''),
                                    praca=row.get('praca', ''),
                                    sub_praca=row.get('sub_praca', ''),
                                    origem=row.get('origem', ''),
                                    tempo_disponivel_escalado=row.get('tempo_disponivel_escalado', ''),
                                    tempo_disponivel_absoluto=row.get('tempo_disponivel_absoluto', ''),
                                    numero_de_corridas_ofertadas=int(row.get('numero_de_corridas_ofertadas', 0) or 0),
                                    numero_de_corridas_aceitas=int(row.get('numero_de_corridas_aceitas', 0) or 0),
                                    numero_de_corridas_rejeitadas=int(row.get('numero_de_corridas_rejeitadas', 0) or 0),
                                    numero_de_corridas_completadas=int(row.get('numero_de_corridas_completadas', 0) or 0),
                                    numero_de_corridas_canceladas_pela_pessoa_entregadora=int(row.get('numero_de_corridas_canceladas_pela_pessoa_entregadora', 0) or 0),
                                    numero_de_pedidos_aceitos_e_concluidos=int(row.get('numero_de_pedidos_aceitos_e_concluidos', 0) or 0),
                                    soma_das_taxas_das_corridas_aceitas=row.get('soma_das_taxas_das_corridas_aceitas', '')
                                ))
                            else:  # Financeiro
                                dados_importados.append(Financeiro(
                                    origem_doc=origem,
                                    data_do_lancamento_financeiro=row.get('data_do_lancamento_financeiro', ''),
                                    data_do_periodo_de_referencia=row.get('data_do_periodo_de_referencia', ''),
                                    data_do_repasse=row.get('data_do_repasse', ''),
                                    periodo=row.get('periodo', ''),
                                    praca=row.get('praca', ''),
                                    subpraca=row.get('subpraca', ''),
                                    origem=row.get('origem', ''),
                                    id_da_pessoa_entregadora=row.get('id_da_pessoa_entregadora', ''),
                                    recebedor=row.get('recebedor', ''),
                                    tipo=row.get('tipo', ''),
                                    valor=row.get('valor', ''),
                                    descricao=row.get('descricao', ''),
                                    atingido=row.get('atingido', ''),
                                    percentual_de_tempo_disponivel=row.get('percentual_de_tempo_disponivel', ''),
                                    percentual_de_aceitacao=row.get('percentual_de_aceitacao', ''),
                                    percentual_de_conclusao=row.get('percentual_de_conclusao', ''),
                                    criterio_tempo_disponivel=row.get('criterio_tempo_disponivel', ''),
                                    criterio_rotas_aceitas=row.get('criterio_rotas_aceitas', ''),
                                    criterio_rotas_concluidas=row.get('criterio_rotas_concluidas', ''),
                                    margem_fee_porcentagem=row.get('margem_fee_porcentagem', '')
                                ))
                        except (ValueError, KeyError) as e:
                            mensagens_erro = f"Erro na linha {index + 2} do arquivo {nome_arquivo}: {e}"
                            messages.error(request, mensagens_erro)  # Exibe erro mais específico
                    return dados_importados

                dados_importados = criar_objetos(modelo, df, origem)

                if dados_importados:
                    with transaction.atomic():
                        modelo.objects.bulk_create(dados_importados)

                    origem.linhas_importadas = len(dados_importados)
                    origem.linhas_com_erro = len(df) - len(dados_importados)  # Linhas com erro são as restantes
                    origem.save()

                    messages.success(request, f'Arquivo "{nome_arquivo}" importado com sucesso!')
                else:
                    origem.delete()

            except Exception as e:
                origem.delete()
                messages.error(request, f"Erro ao processar o arquivo {nome_arquivo}: {e}")

            return redirect('importar_csv')

    else:
        form = ImportacaoForm()

    return render(request, 'importar_csv.html', {'form': form})
