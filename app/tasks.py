import logging
from datetime import datetime
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR  # Importe os eventos necessários
from django.db.models import Min
from app.models import Driver
from fato.models import Entregador, Performance
from app.services import process_contracts  # Importa a função do service.py

# Configuração de logs
logger = logging.getLogger(__name__)


def atualizar_dt_franquia():
    """Atualiza o campo dt_franquia para os drivers que ainda não possuem um."""
    logger.info("Iniciando atualização do campo dt_franquia.")
    drivers = Driver.objects.filter(uuid__isnull=False, dt_franquia__isnull=True)

    # Criando um dicionário com a primeira data disponível por UUID
    datas_franquia = Performance.objects.filter(
        id_da_pessoa_entregadora__in=drivers.values_list('uuid', flat=True)
    ).values('id_da_pessoa_entregadora').annotate(primeira_data=Min('data_do_periodo'))

    # Dicionário para facilitar a atualização
    data_map = {item['id_da_pessoa_entregadora']: item['primeira_data'] for item in datas_franquia}

    # Lista de drivers a serem atualizados
    drivers_to_update = []
    for driver in drivers:
        if driver.uuid in data_map:
            driver.dt_franquia = data_map[driver.uuid]
            drivers_to_update.append(driver)

    # Atualiza em batch para melhor desempenho
    if drivers_to_update:
        Driver.objects.bulk_update(drivers_to_update, ['dt_franquia'])
        logger.info(f"Atualizados {len(drivers_to_update)} drivers com dt_franquia.")
    else:
        logger.info("Nenhum driver foi atualizado.")


def atualizar_driver_snapshot():
    """Atualiza o snapshot diário para todos os drivers."""
    logger.info("Iniciando atualização dos snapshots dos drivers.")
    drivers = Driver.objects.all()

    for driver in drivers:
        for empresa in driver.empresas.all():
            snapshot, created = Entregador.objects.update_or_create(
                driver_id=driver.id,
                empresa_id=empresa.id,
                data_snapshot=datetime.now().date(),
                defaults={
                    'uuid': driver.uuid,
                    'nome': driver.nome,
                    'cpf': driver.cpf,
                    'email': driver.email,
                    'celular': driver.celular,
                    'nacionalidade': driver.nacionalidade,
                    'rg': driver.rg,
                    'orgao_emissor': driver.orgao_emissor,
                    'ticket': driver.ticket,
                    'modal_id': driver.modal.id if driver.modal else None,
                    'modal_nome': driver.modal.nome if driver.modal else None,
                    'origem': driver.origem,
                    'motivo_contato': driver.motivo_contato,
                    'dt_franquia': driver.dt_franquia,
                    'obs_txt': driver.obs_txt,
                    'is_active': driver.is_active,
                }
            )

            if created:
                logger.info(f"Snapshot criado para {driver.nome} na empresa {empresa.razao_social}.")
            else:
                logger.info(f"Snapshot atualizado para {driver.nome} na empresa {empresa.razao_social}.")

    logger.info("Atualização dos snapshots dos drivers finalizada.")


def atualizar_contrato():
    """Executa o processamento de contratos no service.py"""
    logger.info("Iniciando atualização de contratos")
    try:
        process_contracts()  # Chama a função de processamento diretamente
        logger.info("Atualização de contratos concluída.")
    except Exception as e:
        logger.error(f"Erro ao executar service.py: {e}")


def start_scheduler():
    """Inicia o agendador APScheduler, evitando duplicações."""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Agendando job de atualização do campo dt_franquia
    if not scheduler.get_job('atualizar_dt_franquia'):
        scheduler.add_job(
            atualizar_dt_franquia,
            CronTrigger(hour=0, minute=0),  # Executa às 00:00 AM
            id="atualizar_dt_franquia",
            misfire_grace_time=21600,
            replace_existing=True,
        )
        logger.info("Job 'atualizar_dt_franquia' agendado para 00:00 AM.")

    # Agendando job de atualização dos snapshots
    if not scheduler.get_job('atualizar_driver_snapshot'):
        scheduler.add_job(
            atualizar_driver_snapshot,
            CronTrigger(hour=3, minute=0),  # Executa às 03:00 AM
            id="atualizar_driver_snapshot",
            misfire_grace_time=21600,
            replace_existing=True,
        )
        logger.info("Job 'atualizar_driver_snapshot' agendado para 03:00 AM.")

    # Agendando job de execução do service.py
    if not scheduler.get_job('atualizar_contrato'):
        scheduler.add_job(
            atualizar_contrato,
            CronTrigger(hour=1, minute=0),  # Executa às 01:00 AM
            id="atualizar_contrato",
            misfire_grace_time=21600,  # Tolerância de 6 horas (6 horas * 60 minutos * 60 segundos = 21.600 segundos)
            replace_existing=True,
        )
        logger.info("Job 'atualizar_contrato' agendado para 01:00 AM.")

    # Remover o job após execução para garantir que não haverá duplicação
    scheduler.add_listener(
        lambda event: scheduler.remove_job('atualizar_contrato') if event.job_id == 'atualizar_contrato' else None,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR  # Agora com a importação correta dos eventos
    )

    scheduler.start()
    logger.info("Scheduler iniciado.")
