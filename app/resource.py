from import_export import resources, fields
from .models import Driver


class DriverResource(resources.ModelResource):
    # Campos do Motorista
    nome = fields.Field(attribute='nome', column_name='Nome do Motorista')
    cpf = fields.Field(attribute='cpf', column_name='CPF')
    email = fields.Field(attribute='email', column_name='E-mail')
    celular = fields.Field(attribute='celular', column_name='Celular')
    nacionalidade = fields.Field(attribute='nacionalidade', column_name='Nacionalidade')
    rg = fields.Field(attribute='rg', column_name='RG')
    orgao_emissor = fields.Field(attribute='orgao_emissor', column_name='Órgão Emissor')
    data_nascimento = fields.Field(attribute='data_nascimento_prestador', column_name='Data de Nascimento')

    # Campos da Empresa
    empresa = fields.Field(column_name='Empresa Associada')
    cnpj_empresa = fields.Field(column_name='CNPJ da Empresa')
    endereco_empresa = fields.Field(column_name='Endereço da Empresa')
    bairro_empresa = fields.Field(column_name='Bairro')
    cidade_empresa = fields.Field(column_name='Cidade')
    estado_empresa = fields.Field(column_name='Estado')
    ativa_empresa = fields.Field(column_name='Empresa Ativa')

    class Meta:
        model = Driver
        fields = (
            'nome', 'cpf', 'email', 'celular', 'nacionalidade', 'rg', 'orgao_emissor', 'data_nascimento',
            'empresa', 'cnpj_empresa', 'endereco_empresa', 'bairro_empresa', 'cidade_empresa', 'estado_empresa',
            'ativa_empresa'
        )
        export_order = fields  # Define a ordem das colunas no Excel

    def dehydrate_empresa(self, driver):
        # Busca a empresa associada
        if driver.empresas.exists():
            return ', '.join([empresa.razao_social for empresa in driver.empresas.all()])
        return "Sem Empresa"

    def dehydrate_cnpj_empresa(self, driver):
        if driver.empresas.exists():
            return ', '.join([empresa.cnpj for empresa in driver.empresas.all()])
        return "N/A"

    def dehydrate_endereco_empresa(self, driver):
        if driver.empresas.exists():
            return ', '.join([
                f"{empresa.logradouro}, {empresa.numero}, {empresa.complemento}"
                for empresa in driver.empresas.all()
            ])
        return "N/A"

    def dehydrate_bairro_empresa(self, driver):
        if driver.empresas.exists():
            return ', '.join([empresa.bairro for empresa in driver.empresas.all()])
        return "N/A"

    def dehydrate_cidade_empresa(self, driver):
        if driver.empresas.exists():
            return ', '.join([empresa.cidade for empresa in driver.empresas.all()])
        return "N/A"

    def dehydrate_estado_empresa(self, driver):
        if driver.empresas.exists():
            return ', '.join([empresa.estado for empresa in driver.empresas.all()])
        return "N/A"

    def dehydrate_ativa_empresa(self, driver):
        if driver.empresas.exists():
            return ', '.join(['Sim' if empresa.is_active else 'Não' for empresa in driver.empresas.all()])
        return "N/A"

    def export_queryset(self, queryset):
        """
        Duplica os registros no export para cada empresa associada ao motorista.
        """
        new_queryset = []
        for driver in queryset:
            empresas = driver.empresas.all()
            if empresas.exists():
                for empresa in empresas:
                    # Cria uma cópia do motorista e atribui os dados da empresa
                    driver_copy = driver
                    driver_copy._current_company = empresa.razao_social
                    driver_copy._current_cnpj = empresa.cnpj
                    driver_copy._current_endereco = ', '.join([
                        f"{empresa.logradouro}, {empresa.numero}, {empresa.complemento}"
                    ])
                    driver_copy._current_bairro = empresa.bairro
                    driver_copy._current_cidade = empresa.cidade
                    driver_copy._current_estado = empresa.estado
                    driver_copy._current_ativa = empresa.is_active
                    new_queryset.append(driver_copy)
            else:
                # Se o motorista não tem empresa, adiciona um valor "N/A"
                driver_copy = driver
                driver_copy._current_company = "Sem Empresa"
                driver_copy._current_cnpj = "N/A"
                driver_copy._current_endereco = "N/A"
                driver_copy._current_bairro = "N/A"
                driver_copy._current_cidade = "N/A"
                driver_copy._current_estado = "N/A"
                driver_copy._current_ativa = "N/A"
                new_queryset.append(driver_copy)

        return new_queryset
