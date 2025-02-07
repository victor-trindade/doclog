from django.db import models
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords

# Modelo para armazenar dados comuns
class BaseModel(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True, validators=[RegexValidator(regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', message='CPF inválido')])

    class Meta:
        abstract = True

class Company(models.Model):
    cnpj = models.CharField(max_length=18, unique=True, validators=[RegexValidator(regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', message='Formato Obrigatório: XX.XXX.XXX/0001-XX')])
    endereco = models.CharField(max_length=255)
    bairro = models.CharField(max_length=100)
    cep = models.CharField(max_length=10, validators=[RegexValidator(regex=r'^\d{5}-\d{3}$', message='Formato Obrigatório: XXX.XXXX.XXXX-XX')])
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    razao_social = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, verbose_name='ativo')
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Empresa'  # Nome singular
        verbose_name_plural = 'Empresas'  # Nome plural

    def __str__(self):
        return self.cnpj

    def cnpj_formatado(self):
        return self.cnpj


class Driver(BaseModel):
    uuid = models.UUIDField(default=None, null=True, blank=True, unique=True)
    nacionalidade = models.CharField(max_length=100)
    rg = models.CharField(max_length=15)
    orgao_emissor = models.CharField(max_length=50)

    # Dados de contato
    email = models.EmailField(unique=True)
    celular = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\+?\d{1,4}?\d{9,15}$', message='Celular inválido')])

    data_nascimento_prestador = models.DateField()


    # Relacionamento com a empresa (Pessoa Jurídica)
    empresas = models.ManyToManyField(Company, related_name='drivers')

    # Relacionamento com Subpraça
    subpraca = models.ForeignKey('Subpraca', on_delete=models.SET_NULL, null=True, blank=True, related_name='drivers')

    is_active = models.BooleanField(default=True, verbose_name='ativo')

    history = HistoricalRecords()

    def __str__(self):
        return self.nome


class Contract(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('signed', 'Assinado'),
        ('canceled', 'Cancelado'),
    ]

    type = models.CharField(max_length=255)
    document_key = models.CharField(max_length=255, unique=True)  # Chave do documento na Clicksign
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contracts')  # Empresa relacionada
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Status do contrato
    signed_at = models.DateTimeField(null=True, blank=True)  # Data de assinatura, se houver

    def __str__(self):
        return f"Contrato de {self.driver} com {self.company}"

class Praca(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    uf = models.CharField(max_length=2)

    def __str__(self):
        return self.nome


class Subpraca(models.Model):
    nome = models.CharField(max_length=255)
    praca = models.ForeignKey(Praca, on_delete=models.CASCADE, related_name='subpracas')
    def __str__(self):
        return f"{self.nome}"