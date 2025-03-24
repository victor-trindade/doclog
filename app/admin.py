from django.db.models import Q, Count
from django.contrib import admin
from .resource import DriverResource
from import_export.admin import ExportMixin
from simple_history.admin import SimpleHistoryAdmin
from django.contrib.admin import BooleanFieldListFilter
from .models import Driver, Company, Praca, Subpraca, Contract, Signer, Modal, DriverCompany, BankAccount, Bank
from django.db import IntegrityError, transaction
from django.contrib import messages
from django import forms


class BaseAdmin(SimpleHistoryAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name, field in form.base_fields.items():
            if field.help_text:
                field.widget.attrs["placeholder"] = field.help_text  # Coloca o help_text como placeholder
                field.help_text = ""  # Remove o help_text padrão do Django Admin
        return form


class ModalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome']  # Customize os campos conforme necessário
    search_fields = ['nome', 'id']




class BankAccountInline(admin.StackedInline):
    model = BankAccount
    fk_name = 'driver'  # Define qual campo de relacionamento será usado (no caso o OneToOne entre Driver e BankAccount)
    extra = 1  # Número de formulários em branco que serão exibidos
    fields = ('agencia', 'conta', 'digito', 'tipo', 'banco')  # Campos que você deseja mostrar


# Inline para Signatário
class SignerInline(admin.TabularInline):
    model = Signer
    extra = 0  # Número de linhas extras
    verbose_name = "Signatário"
    verbose_name_plural = "Signatários"
    fields = ('nome', 'sign_as', 'status', 'signed_at')  # Organize os campos aqui
    readonly_fields = ('nome', 'sign_as', 'status', 'signed_at')  # Torne os campos somente leitura, se necessário


class DriverInline(admin.StackedInline):
    model = Driver.empresas.through
    extra = 1
    verbose_name = "Motorista"
    verbose_name_plural = "Motoristas"

class CompanyInline(admin.TabularInline):
    model = DriverCompany  # Relacionamento Many-to-Many entre Driver e Company
    extra = 1  # Número de linhas extras para o usuário preencher
    verbose_name = "Empresa"
    verbose_name_plural = "Empresas"
    fk_name = 'driver'  # Relaciona com o modelo Driver
    fields = ('company',)

class DriverAdmin(ExportMixin, SimpleHistoryAdmin):
    resource_class = DriverResource  # Adiciona a funcionalidade de exportação
    list_display = ['uuid', 'nome', 'get_cpf_formatted', 'get_razao_social', 'get_CNPJ', 'email', 'is_active', 'get_agencia', 'get_conta', 'get_digito', 'get_tipo']
    search_fields = ['id', 'uuid', 'cpf', 'nome', 'empresas__cnpj', 'empresas__razao_social']
    inlines = [CompanyInline, BankAccountInline]  # Removemos BankAccountInline, pois é um relacionamento OneToOne

    fieldsets = (
        ('Entregador', {
            'fields': (
                'uuid', 'nome', 'nacionalidade', 'cpf', 'rg', 'orgao_emissor', 'data_nascimento_prestador',
                'email', 'celular', 'subpraca', 'is_active'
            )
        }),
        ('Salesforce', {
            'fields': ('ticket', 'modal', 'origem', 'motivo_contato', 'dt_franquia', 'obs_txt')
        }),

    )


    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('subpraca').prefetch_related('empresas_vinculadas__company')

    def get_razao_social(self, obj):
        """ Retorna a última empresa ativa vinculada ao motorista """
        empresa_ativa = (
            obj.empresas_vinculadas.filter(company__is_active=True)
            .order_by('-id')
            .first()
        )
        return empresa_ativa.company.razao_social if empresa_ativa else "Nenhuma Empresa Ativa"

    get_razao_social.short_description = 'Última Empresa Ativa'

    def get_CNPJ(self, obj):
        """ Retorna o CNPJ da última empresa ativa vinculada ao motorista """
        empresa_ativa = (
            obj.empresas_vinculadas.filter(company__is_active=True)
            .order_by('-id')
            .first()
        )
        return empresa_ativa.company.cnpj if empresa_ativa else "Nenhum CNPJ Ativo"

    get_CNPJ.short_description = 'CNPJ Última Empresa Ativa'

    def get_cpf_formatted(self, obj):
        cpf = obj.cpf
        if cpf and len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf or "CPF Não Informado"

    get_cpf_formatted.short_description = "CPF"

    # Métodos para exibir os campos bancários
    def get_agencia(self, obj):
        return obj.conta_bancaria.agencia if obj.conta_bancaria else "Não informado"
    get_agencia.short_description = "Agência"

    def get_conta(self, obj):
        return obj.conta_bancaria.conta if obj.conta_bancaria else "Não informado"
    get_conta.short_description = "Conta"

    def get_digito(self, obj):
        return obj.conta_bancaria.digito if obj.conta_bancaria else "Não informado"
    get_digito.short_description = "Dígito"

    def get_tipo(self, obj):
        return obj.conta_bancaria.get_tipo_display() if obj.conta_bancaria else "Não informado"
    get_tipo.short_description = "Tipo da Conta"

    class Media:
        js = ("js/imask.js", "js/cep.js")


class CompanyAdmin(BaseAdmin):
    list_display = ['razao_social', 'get_driver_cpf', 'get_cnpj_formatted', 'logradouro', 'bairro', 'cidade', 'estado', 'status', 'is_active']
    search_fields = ['drivers__uuid', 'drivers__cpf', 'razao_social', 'cnpj']
    ordering = ['razao_social']

    list_filter = [
        'estado',
        'cidade',
        ('is_active', BooleanFieldListFilter)
    ]

    fieldsets = (
        ('Empresa', {
            'fields': (
                'cnpj', 'razao_social', 'atividade', 'fundado_em', 'porte',
                'logradouro', 'numero', 'complemento', 'cep', 'bairro', 'cidade', 'estado',
                'simples', 'simei', 'is_active', 'status',
            )
        }),
    )

    class Media:
        js = (
            "js/imask.js",
            "js/cep.js",  # Certifique-se de que este arquivo contém as máscaras
        )

    def get_driver_uuid(self, obj):
        """ Exibe o UUID do motorista associado à empresa """
        driver_associado = DriverCompany.objects.filter(company=obj).first()  # Pega o motorista associado
        return str(driver_associado.driver.uuid) if driver_associado else 'Sem Motorista'

    get_driver_uuid.short_description = 'Driver UUID'

    def get_driver_cpf(self, obj):
        """ Exibe o CPF do motorista associado à empresa """
        driver_associado = DriverCompany.objects.filter(company=obj).first()  # Pega o motorista associado
        if driver_associado and driver_associado.driver.cpf:
            cpf = driver_associado.driver.cpf
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"  # Formata o CPF
        return "Sem Motoristas"

    get_driver_cpf.short_description = 'Driver CPF'

    def get_cnpj_formatted(self, obj):
        cnpj = obj.cnpj
        if cnpj and len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj or "CNPJ Não Informado"

    get_cnpj_formatted.short_description = "CNPJ"

    inlines = [DriverInline]

    def get_search_results(self, request, queryset, search_term):
        search_term_clean = ''.join(filter(str.isdigit, search_term))  # Remove tudo que não for número
        queryset, use_distinct = super().get_search_results(request, queryset, search_term_clean)
        return queryset, use_distinct


class SignedAtFilter(admin.SimpleListFilter):
    title = 'Data de Assinatura Confirmada'
    parameter_name = 'signed_at'

    def lookups(self, request, model_admin):
        return (
            ('signed', 'Assinado'),
            ('not_signed', 'Não Assinado'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'signed':
            return queryset.filter(signers__signed_at__isnull=False).distinct()
        if self.value() == 'not_signed':
            return queryset.filter(signers__signed_at__isnull=True).distinct()
        return queryset


class ContractAdmin(SimpleHistoryAdmin):
    list_display = [
        'document_key', 'type', 'get_driver_uuid', 'company', 'get_driver_info',
        'get_signers_count', 'created_at', 'get_signed_at','status_final'
    ]
    search_fields = ['type', 'document_key', 'company__razao_social', 'company__cnpj', 'status_document']
    list_filter = ['status_document', 'company', SignedAtFilter]
    ordering = ['company', 'status_document']

    inlines = [SignerInline]  # Inclua o inline de signatários

    fieldsets = (
        ('Documento', {
            'fields': ('document_key', 'type', 'company', 'status_document', 'created_at', 'deadline_at', 'get_signed_at')
        }),
    )

    readonly_fields = ['created_at', 'deadline_at', 'get_signed_at']  # Adicionando o campo como somente leitura

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Conta o número de signatários com status 'conferred' no banco de dados
        return queryset.annotate(signed_count=Count('signers', filter=Q(signers__status='conferred')))

    def get_driver_uuid(self, obj):
        drivers = obj.company.drivers.all()
        return ', '.join([str(driver.uuid) for driver in drivers]) if drivers.exists() else 'Sem Motorista'

    get_driver_uuid.short_description = 'Driver UUID(s)'

    def get_driver_info(self, obj):
        drivers = obj.company.drivers.all()
        return ', '.join([driver.nome for driver in drivers]) if drivers.exists() else 'Sem Motorista'

    get_driver_info.short_description = 'Motorista(s)'

    def get_signed_at(self, obj):
        # Tenta pegar o primeiro signatário com data de assinatura, sem considerar "sign_as" diretamente
        signed_contractee = obj.signers.filter(signed_at__isnull=False).order_by('-signed_at').first()

        if signed_contractee and signed_contractee.signed_at:
            return signed_contractee.signed_at.strftime('%d/%m/%Y %H:%M:%S')
        else:
            return "Não Assinado"

    get_signed_at.short_description = 'Assinado em'


    def get_signers_count(self, obj):
        return f"{obj.signed_count}/{obj.signers.count()}"

    get_signers_count.short_description = '(Assinantes/Total)'


class SignerAdmin(SimpleHistoryAdmin):
    list_display = ['get_document_key', 'get_sign_as', 'get_status', 'get_signed_at', 'documentation']
    search_fields = ['contract__document_key', 'sign_as', 'status', 'contract__company__razao_social']
    list_filter = ['contract__document_key', 'status', 'contract__company', 'signed_at']
    ordering = ['contract', ]

    # Métodos para customizar a exibição no list_display
    def get_document_key(self, obj):
        return obj.contract.document_key

    get_document_key.short_description = 'Chave do Documento'

    def get_sign_as(self, obj):
        return obj.sign_as

    get_sign_as.short_description = 'Assinado Como'

    def get_status(self, obj):
        return obj.get_status_display()

    get_status.short_description = 'Status'

    def get_signed_at(self, obj):
        return obj.signed_at

    get_signed_at.short_description = 'Data de Assinatura'

    def get_readonly_fields(self, request, obj=None):
        # Exemplo de campo somente leitura: "signed_at" após assinatura
        if obj and obj.signed_at:
            return ['signed_at']
        return super().get_readonly_fields(request, obj)


class PracaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'uf')  # Campos que serão exibidos na listagem
    search_fields = ('nome', 'uf')  # Permite a busca pelos campos nome e uf
    list_filter = ('uf',)  # Filtro por UF
    ordering = ('nome',)  # Ordena por nome na listagem

class SubpracaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'praca')  # Campos que serão exibidos na listagem
    search_fields = ('nome', 'praca')  # Permite a busca pelo nome da subpraça
    list_filter = ('praca',)  # Filtro pela praça
    ordering = ('nome',)  # Ordena por nome na listagem


class DriverCompanyAdmin(admin.ModelAdmin):
    list_display = ('driver', 'company')  # Exibe o motorista e a empresa na lista
    search_fields = (
    'driver__nome', 'company__razao_social')  # Permite pesquisa pelo nome do motorista e razão social da empresa
    list_filter = ('company',)  # Filtro por empresa
    raw_id_fields = ('driver', 'company')  # Exibe campos de ForeignKey como campos de pesquisa rápidos

from .models import BankAccount




@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("agencia", "conta", "digito", "tipo")
    list_filter = ("tipo",)
    search_fields = ("agencia", "conta")
    ordering = ("agencia", "conta")


# Registra os modelos no Django Admin
admin.site.register(Bank)
admin.site.register(DriverCompany, DriverCompanyAdmin)
admin.site.register(Praca, PracaAdmin)
admin.site.register(Subpraca, SubpracaAdmin)
admin.site.register(Modal, ModalAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(Signer, SignerAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Contract, ContractAdmin)
