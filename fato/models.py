#fato/models.py
from symtable import Class

from django.db import models
from app.models import Driver, Subpraca
from datetime import datetime
import os

import os


def upload_to(instance, filename):
    """
    Define o caminho do arquivo de upload com base na filial e no tipo.
    Exemplo: importes/sao_paulo/performance/nome_do_arquivo.csv
    """
    # Normaliza o nome da filial para evitar problemas em caminhos
    filial_slug = instance.filial.lower().replace(" ", "_")  # Remove espaços e coloca em minúsculas

    # Obtém o tipo (por exemplo, 'performance' ou 'financeiro') a partir da instância
    tipo_slug = instance.tipo.lower().replace(" ", "_")  # Normaliza o tipo (se necessário)

    return os.path.join("importes", filial_slug, tipo_slug, filename)


class Origem(models.Model):
    tipo = models.CharField(max_length=255, blank=True, null=True)  # Novo campo tipo
    arquivo = models.FileField(upload_to=upload_to)
    nome = models.CharField(max_length=255)  # Nome do CSV
    filial = models.CharField(max_length=255)  # Nome da filial
    linhas_importadas = models.IntegerField(default=0)  # Quantidade de registros bem-sucedidos
    linhas_com_erro = models.IntegerField(default=0)  # Quantidade de registros com erro
    timestamp = models.DateTimeField(auto_now_add=True)  # Data e hora da importação

    class Meta:
        unique_together = ('nome', 'filial', 'tipo')  # Garante que 'nome' e 'filial' sejam únicos juntos
        verbose_name = "Origem"
        verbose_name_plural = "Origem"

    def save(self, *args, **kwargs):
        # Garantir que o nome do arquivo seja único, concatenando com o nome da filial
        if not self.nome:
            self.nome = f"{self.filial}_{self.tipo}_{self.arquivo.name}"

        super().save(*args, **kwargs)  # Chama o save do Django para tratar a lógica de unicidade automaticamente

    def __str__(self):
        return f"{self.filial} - {self.nome}"

class Performance(models.Model):
    origem_doc = models.ForeignKey(Origem, on_delete=models.CASCADE)
    data_do_periodo = models.DateField()
    periodo = models.CharField(max_length=255)
    duracao_do_periodo = models.CharField(max_length=255)
    numero_minimo_de_entregadores_regulares_na_escala = models.IntegerField()
    tag = models.CharField(max_length=255)
    id_da_pessoa_entregadora = models.CharField(max_length=255)
    pessoa_entregadora = models.CharField(max_length=255)
    praca = models.CharField(max_length=255)
    sub_praca = models.CharField(max_length=255)
    origem = models.CharField(max_length=255)
    tempo_disponivel_escalado = models.CharField(max_length=255)  # Campo mantido como CharField
    tempo_disponivel_absoluto = models.CharField(max_length=255)  # Campo mantido como CharField
    numero_de_corridas_ofertadas = models.IntegerField()
    numero_de_corridas_aceitas = models.IntegerField()
    numero_de_corridas_rejeitadas = models.IntegerField()
    numero_de_corridas_completadas = models.IntegerField()
    numero_de_corridas_canceladas_pela_pessoa_entregadora = models.IntegerField()
    numero_de_pedidos_aceitos_e_concluidos = models.IntegerField()
    soma_das_taxas_das_corridas_aceitas = models.CharField(max_length=255)


    def __str__(self):
        return f"Performance {self.id} - {self.sub_praca}"

    class Meta:
        verbose_name = "Performance"
        verbose_name_plural = "Performance"


class Financeiro(models.Model):
    origem_doc = models.ForeignKey(Origem, on_delete=models.CASCADE)
    data_do_lancamento_financeiro = models.CharField(max_length=255, null=True, blank=True)
    data_do_periodo_de_referencia = models.CharField(max_length=255, null=True, blank=True)
    data_do_repasse = models.CharField(max_length=255, null=True, blank=True)
    periodo = models.CharField(max_length=255)
    praca = models.CharField(max_length=255)
    subpraca = models.CharField(max_length=255)
    origem = models.CharField(max_length=255)
    id_da_pessoa_entregadora = models.CharField(max_length=255)
    recebedor = models.CharField(max_length=255)
    tipo = models.CharField(max_length=255)
    valor = models.CharField(max_length=255)
    descricao = models.TextField()
    atingido = models.CharField(max_length=255)
    percentual_de_tempo_disponivel = models.CharField(max_length=255)
    percentual_de_aceitacao = models.CharField(max_length=255)
    percentual_de_conclusao = models.CharField(max_length=255)
    criterio_tempo_disponivel = models.CharField(max_length=255)
    criterio_rotas_aceitas = models.CharField(max_length=255)
    criterio_rotas_concluidas = models.CharField(max_length=255)
    margem_fee_porcentagem = models.CharField(max_length=255)


    def __str__(self):
        return f"Financeiro {self.id} - {self.subpraca}"

    class Meta:
        verbose_name = "Financeiro"
        verbose_name_plural = "Financeiro"

#fato/Driver
class Entregador(models.Model):
    # Armazenar os dados do driver diretamente
    driver_id = models.CharField(max_length=36)  # ID do Driver
    uuid = models.CharField(max_length=36, null=True, blank=True)  # UUID do Driver
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=11)
    email = models.EmailField()
    celular = models.CharField(max_length=15)
    nacionalidade = models.CharField(max_length=100)
    rg = models.CharField(max_length=15)
    orgao_emissor = models.CharField(max_length=50)

    # Informações relacionadas ao relacionamento do driver com a empresa
    empresa_id = models.CharField(max_length=36)  # ID da empresa
    empresa_nome = models.CharField(max_length=255, null=True, blank=True)  # Nome da empresa

    ticket = models.CharField(max_length=9)
    modal_id = models.CharField(max_length=36, null=True, blank=True)  # ID do Modal
    modal_nome = models.CharField(max_length=255, null=True, blank=True)  # Nome do Modal

    origem = models.CharField(choices=Driver.ORIGEM, max_length=255)
    motivo_contato = models.CharField(choices=Driver.MOTIVO, max_length=255)
    dt_franquia = models.DateField(null=True, blank=True)
    obs_txt = models.TextField(null=True, blank=True)

    # Informações adicionais
    data_snapshot = models.DateField(default=datetime.now)  # Data do snapshot
    is_active = models.BooleanField(default=True)  # Estado de atividade do driver

    class Meta:
        unique_together = ('driver_id', 'empresa_id', 'data_snapshot')  # Garante que não haverá duplicação

    def __str__(self):
        return f"Snapshot de {self.nome} (Driver ID: {self.driver_id}) na empresa {self.empresa_nome} ({self.empresa_id}) em {self.data_snapshot}"

class Periodo(models.Model):
    turno = models.CharField(max_length=255)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    duracao = models.TimeField()
    subpraca = models.ForeignKey(Subpraca, on_delete=models.SET_NULL, related_name="periodos", null=True, blank=True)