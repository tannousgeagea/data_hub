# Generated by Django 4.2 on 2024-10-10 09:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_alter_tenant_table'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entitytype',
            old_name='plant',
            new_name='tenant',
        ),
    ]