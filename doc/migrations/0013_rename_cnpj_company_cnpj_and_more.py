# Generated by Django 5.1.5 on 2025-02-04 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('doc', '0012_company_active_historicalcompany_active'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company',
            old_name='CNPJ',
            new_name='cnpj',
        ),
        migrations.RenameField(
            model_name='historicalcompany',
            old_name='CNPJ',
            new_name='cnpj',
        ),
        migrations.RemoveField(
            model_name='driver',
            name='ano',
        ),
        migrations.RemoveField(
            model_name='driver',
            name='dia',
        ),
        migrations.RemoveField(
            model_name='driver',
            name='mes',
        ),
        migrations.RemoveField(
            model_name='historicaldriver',
            name='ano',
        ),
        migrations.RemoveField(
            model_name='historicaldriver',
            name='dia',
        ),
        migrations.RemoveField(
            model_name='historicaldriver',
            name='mes',
        ),
    ]
