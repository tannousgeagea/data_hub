# Generated by Django 4.2 on 2024-12-02 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0006_sensorbox'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensorbox',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
    ]