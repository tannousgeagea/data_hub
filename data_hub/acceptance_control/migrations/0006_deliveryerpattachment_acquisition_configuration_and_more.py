# Generated by Django 4.2 on 2024-11-18 12:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0012_erpdatatype_protocol_method_and_more'),
        ('acceptance_control', '0005_deliveryerpattachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryerpattachment',
            name='acquisition_configuration',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='metadata.attachmentacquisitionconfiguration'),
        ),
        migrations.AddField(
            model_name='deliveryerpattachment',
            name='attachment_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metadata.erpdatatype'),
        ),
        migrations.AddField(
            model_name='deliveryerpattachment',
            name='delivery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='acceptance_control.delivery'),
        ),
        migrations.AlterUniqueTogether(
            name='deliveryerpattachment',
            unique_together={('delivery', 'attachment_type')},
        ),
    ]