from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from simple_history.utils import update_change_reason
from .models import Driver, Company, Praca, Subpraca, Contract

class DriverInline(admin.StackedInline):
    model = Driver.empresas.through  # Relacionamento ManyToMany entre Driver e Company
    extra = 1  # Número de linhas em branco para adicionar novos registros
    verbose_name = "Motorista"
    verbose_name_plural = "Motoristas"

class CompanyInline(admin.TabularInline):  # Pode ser StackedInline também
    model = Driver.empresas.through  # Relacionamento ManyToMany entre Driver e Company
    extra = 1  # Número de linhas em branco para adicionar novos registros
    verbose_name = "Empresa"
    verbose_name_plural = "Empresas"


class DriverAdmin(SimpleHistoryAdmin):
    list_display = ['uuid','nome', 'cpf', 'get_razao_social', 'get_CNPJ','email', 'is_active']
    search_fields = ['id','uuid', 'cpf', 'nome', 'empresas__cnpj', 'empresas__razao_social']
    inlines = [CompanyInline]

    def get_razao_social(self, obj):
        return obj.empresas.first().razao_social if obj.empresas.exists() else 'Não Associada'

    get_razao_social.short_description = 'Razão Social'

    def get_CNPJ(self, obj):
        return obj.empresas.last().cnpj if obj.empresas.exists() else 'Não Associada'

    get_CNPJ.short_description = 'cnpj'


class CompanyAdmin(SimpleHistoryAdmin):
    list_display = ['razao_social', 'get_driver_uuid','get_driver_cpf', 'cnpj', 'endereco', 'bairro', 'cidade', 'estado']
    search_fields = ['drivers__uuid', 'drivers__cpf', 'razao_social', 'cnpj']  # Usando a relação correta com 'drivers'
    list_filter = ['estado', 'cidade']
    ordering = ['razao_social']

    def get_driver_uuid(self, obj):
        # Retorna uma lista de UUIDs dos motoristas relacionados
        return ', '.join([str(driver.uuid) for driver in obj.drivers.all()]) if obj.drivers.exists() else 'Sem Motoristas'

    get_driver_uuid.short_description = 'Driver UUID'

    def get_driver_cpf(self, obj):
        # Retorna uma lista de UUIDs dos motoristas relacionados
        return ', '.join([str(driver.cpf) for driver in obj.drivers.all()]) if obj.drivers.exists() else 'Sem cnpj'
    get_driver_cpf.short_description = 'CPF'


    # Adicionando o TabularInline ao CompanyAdmin
   # inlines = [DriverInline]

admin.site.register(Driver, DriverAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Praca)
admin.site.register(Subpraca)
admin.site.register(Contract)

