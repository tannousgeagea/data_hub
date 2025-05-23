# Generated by Django 4.2 on 2024-11-27 15:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0005_tenant_default_language'),
        ('metadata', '0012_erpdatatype_protocol_method_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the feedback form', max_length=255)),
                ('is_active', models.BooleanField(default=True, help_text='Indicates if the filter item is currently active.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Feedback Form',
                'verbose_name_plural': 'Feedback Forms',
                'db_table': 'feedback_form',
            },
        ),
        migrations.CreateModel(
            name='FormField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.datatype')),
            ],
            options={
                'verbose_name_plural': 'Form Fields',
                'db_table': 'form_field',
            },
        ),
        migrations.CreateModel(
            name='TenantFeedbackForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Indicates if the filter item is currently active.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('feedback_form', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.feedbackform')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='tenants.tenant')),
            ],
            options={
                'verbose_name_plural': 'Tenant Feedback Form',
                'db_table': 'tenant_feedback_form',
            },
        ),
        migrations.CreateModel(
            name='FeedbackFormFieldItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_key', models.CharField(help_text='Value for the option', max_length=255)),
                ('is_active', models.BooleanField(default=True, help_text='Indicates if the filter item is currently active.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.formfield')),
                ('field_order', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.fieldorder')),
            ],
            options={
                'verbose_name': 'Feedback Form Field Item',
                'verbose_name_plural': 'Feedback Form Field Items',
                'db_table': 'feedback_form_field_item',
            },
        ),
        migrations.CreateModel(
            name='FormFieldLocalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Localized title of the filter.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Localized description of the filter.', null=True)),
                ('placeholder', models.CharField(default='Select', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.formfield')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.language')),
            ],
            options={
                'verbose_name': 'Form Field Localization',
                'verbose_name_plural': 'Form Field Localizations',
                'db_table': 'form_field_localization',
                'unique_together': {('field', 'language')},
            },
        ),
        migrations.CreateModel(
            name='FeedbackFormFieldItemLocalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Localized title of the filter.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Localized description of the filter.', null=True)),
                ('placeholder', models.CharField(default='Select', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('field_item', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.feedbackformfielditem')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.language')),
            ],
            options={
                'verbose_name': 'Feedback Form Field Item Localization',
                'verbose_name_plural': 'Feedback Form Field Items Localizations',
                'db_table': 'feedback_form_field_item_localization',
                'unique_together': {('field_item', 'language')},
            },
        ),
        migrations.CreateModel(
            name='FeedbackFormField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_hidden', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, null=True)),
                ('dependency', models.JSONField(blank=True, help_text='Conditions for showing this field', null=True)),
                ('field_order', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.fieldorder')),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.feedbackform')),
                ('form_field', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.formfield')),
            ],
            options={
                'verbose_name': 'Feedback Form Field',
                'verbose_name_plural': 'Feedback Form Fields',
                'db_table': 'feedback_form_field',
                'unique_together': {('form', 'form_field')},
            },
        ),
    ]
