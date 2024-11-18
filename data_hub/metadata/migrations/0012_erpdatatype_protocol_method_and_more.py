# Generated by Django 4.2 on 2024-11-18 12:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0005_tenant_default_language'),
        ('metadata', '0011_tableasset_tableassetitem_tenanttableasset_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ERPDataType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('data_type', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.datatype')),
            ],
            options={
                'verbose_name_plural': 'ERP Data Types',
                'db_table': 'erp_data_type',
            },
        ),
        migrations.CreateModel(
            name='Protocol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('http', 'HTTP'), ('websocket', 'WebSocket'), ('ftp', 'FTP')], max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Protocols',
                'db_table': 'protocol',
            },
        ),
        migrations.CreateModel(
            name='Method',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('get', 'GET'), ('post', 'POST')], max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('endpoint_url', models.CharField(blank=True, help_text='Endpoint URL if required for API', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('protocol', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='metadata.protocol')),
            ],
            options={
                'verbose_name_plural': 'Methods',
                'db_table': 'method',
            },
        ),
        migrations.CreateModel(
            name='TenantAttachmentRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('attachment_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metadata.erpdatatype')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='tenants.tenant')),
            ],
            options={
                'verbose_name_plural': 'Tenant Attachment Requirements',
                'db_table': 'tenant_attachment_requirement',
                'unique_together': {('tenant', 'attachment_type')},
            },
        ),
        migrations.CreateModel(
            name='AttachmentAcquisitionConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('attachment_type', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.erpdatatype')),
                ('method', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.method')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='tenants.tenant')),
            ],
            options={
                'verbose_name_plural': 'Attachment Acquisition Configurations',
                'db_table': 'attachment_acquisition_configuration',
                'unique_together': {('tenant', 'attachment_type', 'method')},
            },
        ),
    ]
