from django import forms
from .models import Driver

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['nome', 'cpf', 'email', 'celular', 'nome_completo_prestador', 
                  'cpf_prestador', 'data_nascimento_prestador', 'dia', 'mes', 'ano', 'empresas']
