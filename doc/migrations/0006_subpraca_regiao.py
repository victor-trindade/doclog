# Generated by Django 5.1.5 on 2025-01-29 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0005_praca_subpraca'),
    ]

    operations = [
        migrations.AddField(
            model_name='subpraca',
            name='regiao',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]
