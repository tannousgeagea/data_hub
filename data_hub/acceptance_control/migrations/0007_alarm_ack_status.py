# Generated by Django 4.2 on 2024-11-18 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance_control', '0006_deliveryerpattachment_acquisition_configuration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarm',
            name='ack_status',
            field=models.BooleanField(default=False),
        ),
    ]