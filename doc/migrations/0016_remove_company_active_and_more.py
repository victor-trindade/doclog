# Generated by Django 5.1.5 on 2025-02-04 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0015_remove_driver_active_remove_historicaldriver_active_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='active',
        ),
        migrations.RemoveField(
            model_name='historicalcompany',
            name='active',
        ),
        migrations.AddField(
            model_name='company',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='ativo'),
        ),
        migrations.AddField(
            model_name='historicalcompany',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='ativo'),
        ),
    ]
