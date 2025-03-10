# Generated by Django 4.2 on 2024-12-20 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('acceptance_control', '0010_alarm_meta_info_alarm_value_alarmattr'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliveryflag',
            name='event_uid',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='deliveryflag',
            name='exclude_from_dashboard',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deliveryflag',
            name='feedback_provided',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='deliveryflag',
            name='is_actual_alarm',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
