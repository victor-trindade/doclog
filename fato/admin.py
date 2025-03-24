#fato/admin.py

from django.contrib import admin
from .models import Financeiro, Performance, Origem, Entregador, Periodo


@admin.register(Origem)
class OrigemAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome','tipo', 'filial', 'linhas_importadas', 'linhas_com_erro', 'timestamp')
    search_fields = ('nome', 'filial')
    list_filter = ('filial', 'timestamp')
    ordering = ('-timestamp',)
    readonly_fields = [field.name for field in Origem._meta.fields]  # Todos os campos readonly


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    def get_filial(self, obj):
        return obj.origem_doc.filial if obj.origem_doc else "Sem Origem"

    get_filial.short_description = "Filial"

    list_display = ('data_do_periodo', 'id_da_pessoa_entregadora', 'pessoa_entregadora',
                    'sub_praca', 'numero_de_corridas_ofertadas',
                    'numero_de_corridas_completadas', 'tempo_disponivel_absoluto', 'get_filial')
    search_fields = ('origem_doc__nome', 'sub_praca', 'id_da_pessoa_entregadora')
    list_filter = ('sub_praca', 'periodo')
    ordering = ('-data_do_periodo',)

    readonly_fields = [field.name for field in Performance._meta.fields]  # Todos os campos readonly


@admin.register(Financeiro)
class FinanceiroAdmin(admin.ModelAdmin):
    def get_filial(self, obj):
        return obj.origem_doc.filial if obj.origem_doc else "Sem Origem"

    get_filial.short_description = "Filial"

    list_display = ('origem_doc','id_da_pessoa_entregadora','recebedor', 'get_filial', 'data_do_lancamento_financeiro',
                    'subpraca', 'valor', 'descricao')
    search_fields = ('origem_doc__nome', 'subpraca', 'id_da_pessoa_entregadora', 'descricao')
    list_filter = ('subpraca', 'tipo', 'periodo')
    ordering = ('-data_do_lancamento_financeiro',)

    readonly_fields = [field.name for field in Financeiro._meta.fields]  # Todos os campos readonly

@admin.register(Entregador)
class EntregadorAdmin(admin.ModelAdmin):
    # Defina os campos que deseja exibir no admin
    list_display = ('cpf', 'email', 'empresa_id', 'driver_id', 'data_snapshot', 'is_active')

    # Se você estiver utilizando `select_related`, remova isso
    # list_select_related = ('empresa', 'driver') # Isso geraria o erro, já que não são ForeignKeys

@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('turno', 'hora_inicio', 'hora_fim', 'duracao', 'subpraca')
    list_filter = ('subpraca',)
    search_fields = ('turno', 'subpraca__nome')  # Caso tenha um campo de nome na model Subpraca
    ordering = ('turno',)
