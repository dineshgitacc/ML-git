# Generated by Django 2.2 on 2021-07-27 06:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('analysis_request', '0003_auto_20210609_1842'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisRequestSolution',
            fields=[
                ('analysis_request_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('solution_master_id', models.IntegerField(unique=True)),
                ('solution_list', models.CharField(blank=True, max_length=700, null=True)),
                ('status', models.CharField(max_length=15)),
                ('created_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'analysis_request_solution',
            },
        ),
    ]
