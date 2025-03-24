from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Driver, Company, DriverCompany
from django.db.models.signals import m2m_changed



from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import DriverCompany

@receiver(m2m_changed, sender=Driver.empresas.through)
def update_driver_company(sender, instance, action, **kwargs):
    """
    Atualiza o vínculo entre Driver e Company quando as empresas associadas ao Driver são alteradas.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Remove todos os vínculos existentes para o Driver
        DriverCompany.objects.filter(driver=instance).delete()

        # Cria novos vínculos para as empresas atuais
        for company in instance.empresas.all():
            DriverCompany.objects.get_or_create(
                driver=instance,
                company=company,
                defaults={'is_active': True}  # Define is_active como True ao criar o vínculo
            )