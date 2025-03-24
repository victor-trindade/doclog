#fato/forms.py

from django import forms
from django.forms.widgets import FileInput, Select

# Classe para permitir o upload de múltiplos arquivos (não será mais usada)
class MultiFileInput(FileInput):
    allow_multiple_selected = True  # Permite selecionar múltiplos arquivos, mas não será necessário agora

# Opções de filial para o campo 'filial'
FILIAL_CHOICE = [
    ('sao_paulo', 'D&G SP'),
    ('sao_bernardo', 'D&G SBC'),
    ('santo_andre', 'D&G SA'),
    ('campinas', 'D&G CA'),
    ('belo_horizonte', 'D&G BH'),
]

def validate_file_extension(value):
    if not value.name.endswith('.csv'):
        raise forms.ValidationError('Apenas arquivos CSV são permitidos.')

class ImportacaoForm(forms.Form):
    arquivos = forms.FileField(
        widget=FileInput(),
        required=True,
        validators=[validate_file_extension]
    )

    filial = forms.ChoiceField(
        choices=FILIAL_CHOICE,
        required=True,
        widget=Select(attrs={'class': 'select2 form-control'})  # Para estilizar o select com select2
    )
