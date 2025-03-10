# Generated by Django 4.2 on 2025-02-25 13:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0017_tenanttableassetitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantTableFilterItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Indicates if the filter item is currently active for this tenant.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('filter_item', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='tenant_items', to='metadata.filteritem')),
                ('tenant_table_filter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_filter_items', to='metadata.tenanttablefilter')),
            ],
            options={
                'verbose_name_plural': 'Tenant Table Filter Items',
                'db_table': 'tenant_table_filter_item',
                'unique_together': {('tenant_table_filter', 'filter_item')},
            },
        ),
    ]
