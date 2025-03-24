#urls

from django.contrib import admin
from django.urls import path
from app.views import clicksign_contracts_view
from fato.views import importar_csv
from app.views import import_em_massa
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),  # Corrected line,
    path('processar-contratos/', clicksign_contracts_view, name='processar-contratos'), # Inicia o processamento
    path('importar/', importar_csv, name='importar_csv'),
    path('importar-pessoas/', import_em_massa, name='importar_massa'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)