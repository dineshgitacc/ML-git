# Generated by Django 2.2 on 2021-06-10 17:02

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0009_auto_20210609_1836'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingdetails',
            name='analysis_request_id',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='textmasterdetails',
            name='classification',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='textmasterdetails',
            name='entities',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='textmasterdetails',
            name='intent',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
