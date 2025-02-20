# Generated by Django 4.2 on 2024-10-25 09:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0010_plantentitylocalization_and_more'),
        ('acceptance_control', '0003_alarmmedia'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlagTypeLocalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Localized title of the flag type.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Localized description of the falg type.', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('flag_type', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='flag_type_localization', to='acceptance_control.flagtype')),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.language')),
            ],
            options={
                'verbose_name_plural': 'Flag Type Localizations',
                'db_table': 'flag_type_localization',
            },
        ),
        migrations.AddIndex(
            model_name='flagtypelocalization',
            index=models.Index(fields=['flag_type', 'language'], name='flag_type_l_flag_ty_1a51ad_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='flagtypelocalization',
            unique_together={('flag_type', 'language')},
        ),
    ]
