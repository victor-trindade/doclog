from django.core.management.base import BaseCommand
from app.models import Driver
from fato.models import Performance
from django.db.models import Min

# Função que será executada
def atualizar_dt_franquia():
    drivers = Driver.objects.filter(uuid__isnull=False, dt_franquia__isnull=True)
    for driver in drivers:
        # Usando o campo 'id_da_pessoa_entregadora' para relacionar com o 'uuid' do Driver
        primeira_data = Performance.objects.filter(id_da_pessoa_entregadora=driver.uuid).aggregate(Min('data_do_periodo'))['data_do_periodo__min']
        if primeira_data:
            driver.dt_franquia = primeira_data
            driver.save()

class Command(BaseCommand):
    help = 'Força a execução e atualiza a dt_franquia dos drivers'

    def handle(self, *args, **kwargs):
        # Força a execução do job manualmente
        atualizar_dt_franquia()  # Executa diretamente a função associada ao job

        self.stdout.write(self.style.SUCCESS('Função executada manualmente com sucesso!'))
