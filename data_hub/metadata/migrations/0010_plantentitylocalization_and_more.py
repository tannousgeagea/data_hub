# Generated by Django 4.2 on 2024-10-25 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_rename_plant_entitytype_tenant'),
        ('metadata', '0009_filteritem_field_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantEntityLocalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Localized title of the plant entity.', max_length=255)),
                ('description', models.TextField(blank=True, help_text='Localized description of the plant entity.', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='metadata.language')),
                ('plant_entity', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='plant_entity_localization', to='tenants.plantentity')),
            ],
            options={
                'verbose_name_plural': 'Plant Entity Localizations',
                'db_table': 'plant_entity_localization',
            },
        ),
        migrations.AddIndex(
            model_name='plantentitylocalization',
            index=models.Index(fields=['plant_entity', 'language'], name='plant_entit_plant_e_67a10b_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='plantentitylocalization',
            unique_together={('plant_entity', 'language')},
        ),
    ]
