# Generated by Django 2.2 on 2021-07-27 07:49

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0013_textmasterdetails_hierarchy'),
    ]

    operations = [
        migrations.AddField(
            model_name='textmasterdetails',
            name='solution_mapping_id',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
