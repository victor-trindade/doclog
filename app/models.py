#app/models.py
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from localflavor.br.models import BRCPFField, BRCNPJField  # Importando o campo do django-localflavor
from django.db import models
import re

class UpperCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        """ Converte para maiúsculas antes de salvar no banco """
        if isinstance(value, str):
            return value.upper()
        return value




class Company(models.Model):
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    cnpj = BRCNPJField(unique=True, help_text='CNPJ do Entregador')
    atividade = UpperCharField(max_length=255, null=True, blank=True)
    fundado_em = models.DateField()
    porte = UpperCharField(max_length=50)
    simples = models.BooleanField(default=False)
    simei = models.BooleanField(default=False)
    razao_social = UpperCharField(max_length=255)
    logradouro = UpperCharField(max_length=255)
    numero = models.CharField(max_length=10, null=True, blank=True)
    complemento = UpperCharField(max_length=255, null=True, blank=True)
    cep = models.CharField(max_length=10)
    bairro = UpperCharField(max_length=100)
    cidade = UpperCharField(max_length=100, )
    estado = UpperCharField(max_length=2)
    status = UpperCharField(max_length=255, verbose_name='Situação cadastral')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de criação")  # Adicionando o campo timestamp
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de atualização")

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Empresa'  # Nome singular
        verbose_name_plural = 'Empresas'  # Nome plural

    def __str__(self):
        return self.cnpj

    def clean(self):
        """Remove caracteres não numéricos do CNPJ e CEP e valida duplicidade."""
        self.cnpj = re.sub(r'\D', '', self.cnpj or '')  # Garante que o CNPJ só tenha números
        self.cep = re.sub(r'\D', '', self.cep or '')  # Remove caracteres não numéricos do CEP

        # Verifica se já existe um CNPJ cadastrado, excluindo o próprio ID
        if self.pk and Company.objects.filter(cnpj=self.cnpj).exclude(pk=self.pk).exists():
            raise ValidationError({'cnpj': 'Já existe uma empresa com esse CNPJ.'})

        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()  # Garante que todas as validações sejam aplicadas
        super().save(*args, **kwargs)

    @property
    def formatted_cep(self):
        """ Retorna o CEP formatado com o hífen """
        if self.cep and len(self.cep) == 8:
            return f'{self.cep[:5]}-{self.cep[5:]}'
        return self.cep

class Modal(models.Model):
    nome = UpperCharField(max_length=100)

    class Meta:
        verbose_name = 'Modal'  # Nome singular
        verbose_name_plural = 'Modal'  # Nome plura
    def __str__(self):
        return self.nome

class DriverCompany(models.Model):
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name='empresas_vinculadas')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='motorista_atual')

    class Meta:
        # Se o objetivo é que uma empresa tenha apenas um driver,
        # podemos definir unique_together com ambos os campos ou apenas com company,
        # mas a validação customizada será responsável por permitir a atualização do mesmo vínculo.
        unique_together = ('company',)

    def clean(self):
        qs = DriverCompany.objects.filter(company=self.company)
        if self.pk:
            qs = qs.exclude(pk=self.pk)  # Exclui a instância atual da verificação
        # Se já existir um vínculo para a mesma empresa e o driver for diferente, levanta erro.
        if qs.exists() and qs.first().driver != self.driver:
            raise ValidationError("Esta empresa já possui um motorista vinculado.")
        super().clean()

    def __str__(self):
        return f"{self.driver.nome} - {self.company.cnpj}"




class   Driver(models.Model):
    MOTIVO = [
        ('nuvem_para_franquia', 'Nuvem para Franquia'),
        ('franquia_para_franquia', 'Franquia para Franquia'),
        ('novo_cadastro', 'Novo Cadastro'),
    ]

    ORIGEM = [
        ('indicacao_entregador', 'Indicação Entregador'),
        ('anuncio', 'Anúncios'),
        ('leads', 'Leads Entrego'),
        ('acao_campo', 'Ação de Campo'),
        ('reentrada', 'Reentrada D&G'),
    ]

    is_active = models.BooleanField(default=True, verbose_name='ativo')
    uuid = models.CharField(max_length=36,default=None, null=True, blank=True, unique=True)
    nome = UpperCharField(max_length=255)
    nacionalidade = UpperCharField(max_length=100)
    cpf = BRCPFField(unique=True)
    rg = models.CharField(max_length=15)
    orgao_emissor = models.CharField(max_length=50)
    # Dados de contato
    email = models.EmailField(unique=True)
    celular = models.CharField(unique=True, max_length=15, validators=[RegexValidator(regex=r'^\+?\d{1,4}?\d{9,15}$', message='Celular inválido')])
    data_nascimento_prestador = models.DateField()
    empresas = models.ManyToManyField(Company, through=DriverCompany, related_name='motorista')# Relacionamento com a empresa
    subpraca = models.ForeignKey('Subpraca', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')
    history = HistoricalRecords()
    # Salesforce
    ticket = models.CharField(max_length=9)
    modal = models.ForeignKey(Modal, on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')
    origem = models.CharField(choices=ORIGEM, max_length=255)
    motivo_contato = models.CharField(choices=MOTIVO, max_length=255)
    dt_franquia = models.DateField(null=True, blank=True, verbose_name='ingresso na Franquia')
    obs_txt = models.TextField(verbose_name='Observação', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    # Dados Bancarios

    def __str__(self):
        return self.nome

    def clean(self):
        """Remove caracteres não numéricos do CPF e RG antes de validar."""
        self.cpf = re.sub(r'\D', '', self.cpf)  # Remove tudo que não for número
        self.rg = re.sub(r'\D', '', self.rg)
        super().clean()


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class Bank(models.Model):
    nome = UpperCharField(max_length=255)
    codigo = models.CharField(max_length=3)
    tipo = models.CharField(max_length=20)

    def __str__(self):
       return f"{self.codigo} - {self.nome}"

    class Meta:
        verbose_name = 'Banco'  # Nome singular
        verbose_name_plural = 'Bancos'  # Nome plural

class BankAccount(models.Model):
    TIPO = [
        ('sem_conta', 'Sem Conta'),
        ('corrente', 'Corrente'),
        ('poupanca', 'Poupança'),
    ]
    banco = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='contas',null=True, blank=True)
    agencia = UpperCharField(max_length=4, blank=True)
    conta = models.CharField(max_length=12, blank=True)
    digito = models.CharField(max_length=1, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO)
    driver = models.OneToOneField(Driver, on_delete=models.CASCADE, related_name='conta_bancaria')
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.banco.nome} - {self.agencia}/{self.conta}-{self.digito}"

   # @classmethod
    #def get_tipo_choices(cls):
     #   """Carrega os tipos de banco registrados no banco de dados."""
       # return [(bank.code, bank.name) for bank in Bank.objects.all()]

    def __str__(self):
        return self.conta

    class Meta:
        verbose_name = 'Conta Bancaria'  # Nome singular
        verbose_name_plural = 'Contas Bancarias'  # Nome plural



class Contract(models.Model):
    # Status do documento
    DOCUMENT_STATUS_CHOICES = [
        ('running', 'Em Andamento'),
        ('closed', 'Finalizado'),
        ('canceled', 'Cancelado'),
    ]

    # Campos do contrato
    type = models.CharField(max_length=255, verbose_name='Raiz')  # Tipo de contrato
    document_key = models.CharField(max_length=255, unique=True, verbose_name='Chave do documento')  # Chave do documento na Clicksign
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contracts', verbose_name='Empresa')  # Empresa relacionada
    status_document = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='running',verbose_name='Status do documento')  # Status do documento
    created_at = models.DateTimeField(auto_now_add=False, verbose_name='Criado em')  # Data de criação do contrato
    deadline_at = models.DateTimeField(null=True, blank=True, verbose_name='Data limite')  # Data limite para assinatura
    status_final = models.CharField(max_length=255, blank=True, null=True)  # Novo campo regular para salvar status_final

    class Meta:
        verbose_name = 'Contrato'  # Nome singular
        verbose_name_plural = 'Contratos'  # Nome plural


    def __str__(self):
        return f"Contrato com {self.company}"


    def signers_count(self):
        return self.signers.count()  # Contagem total de signatários

    def signed_count(self):
        return self.signers.filter(status='conferred').count()  # Contagem de assinantes que assinaram

    def calculate_status_final(self):
        if not self.pk:  # Verifique se o contrato ainda não foi salvo
            return "Em Andamento"  # Pode ser outro status default para contratos novos

        signers_qs = self.signers.all()  # Agora podemos acessar os signatários depois de ter o pk
        if not signers_qs.exists():
            return "Sem Signatários"

        if self.status_document == 'closed':
            if self.signed_count() == self.signers_count():
                return "Finalizado e Assinado"
            else:
                return "Finalizado sem Assinatura"
        elif self.status_document == 'running':
            return "Em Andamento"

        return "Desconhecido"

    def save(self, *args, **kwargs):
        # Verifica se o contrato já foi salvo antes de calcular o status final
        if not self.pk:  # Se não tiver pk, o contrato é novo
            self.status_final = self.calculate_status_final()

        super().save(*args, **kwargs)  # Salva o contrato normalmente

        # Agora que o contrato tem um pk, podemos recalcular o status final
        if self.pk:
            self.status_final = self.calculate_status_final()  # Atualiza o status_final com base nos signatários
            super().save(update_fields=['status_final'])  # Atualiza apenas o campo status_final


class Signer(models.Model):
    # Status do signatário
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('conferred', 'Assinado'),
        ('declined', 'Recusado'),
        ('not_applicable', 'Não Aplicável'),
    ]

    # Relacionamentos
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='signers', verbose_name='Contrato')  # Contrato associado
    sign_as = UpperCharField(max_length=255, verbose_name='Assinado por')  # Função do signatário (ex: contractee)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Status do signatário
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Assinatura em')  # Data de assinatura, se houver
    documentation = models.CharField(max_length=255, null=True, blank=True, verbose_name='Documento')  # Documentação do signatário (se necessário)
    nome = UpperCharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = 'Signatario'  # Nome singular
        verbose_name_plural = 'Signatários'  # Nome plural

    def __str__(self):
        return f"Signatário {self.sign_as} do contrato {self.contract.document_key}"



class Praca(models.Model):
    nome = UpperCharField(max_length=255, unique=True)
    uf = UpperCharField(max_length=2)

    class Meta:
        verbose_name = 'Praça'  # Nome singular
        verbose_name_plural = 'Praças'  # Nome plural


    def __str__(self):
        return self.nome


class Subpraca(models.Model):
    nome = UpperCharField(max_length=255)
    praca = models.ForeignKey(Praca, on_delete=models.CASCADE, related_name='subpracas')

    class Meta:
        verbose_name = 'Sub-Praça'  # Nome singular
        verbose_name_plural = 'Sub-Praças'  # Nome plural


    def __str__(self):
        return f"{self.nome}"


