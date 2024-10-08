# Generated by Django 2.2 on 2021-06-09 10:14

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisRequestSetting',
            fields=[
                ('analysis_request_setting_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('client_name', models.CharField(blank=True, max_length=100, null=True)),
                ('client_code', models.CharField(blank=True, max_length=100, null=True)),
                ('analysis_features', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(max_length=15)),
                ('created_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'analysis_request_setting',
            },
        ),
        migrations.CreateModel(
            name='AnalysisRequest',
            fields=[
                ('analysis_request_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('analysis_request', models.CharField(blank=True, max_length=100, null=True)),
                ('analysis_request_type', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('analysis_reference', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('callback_url', models.CharField(blank=True, max_length=100, null=True)),
                ('client_reference_id', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(max_length=15)),
                ('created_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('analysis_request_setting_id', models.ForeignKey(db_column='analysis_request_setting_id', on_delete=django.db.models.deletion.CASCADE, to='analysis_request.AnalysisRequestSetting')),
            ],
            options={
                'db_table': 'analysis_request',
            },
        ),
    ]
