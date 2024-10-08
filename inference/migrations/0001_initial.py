# Generated by Django 2.2 on 2020-03-27 08:07

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('training', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassificationDetails',
            fields=[
                ('inference_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('client_id', models.IntegerField()),
                ('project_id', models.IntegerField()),
                ('result', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('class_id', models.CharField(blank=True, max_length=250, null=True)),
                ('status_id', models.IntegerField()),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('batch_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.ClassificationMasterDetails')),
                ('process_type', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='training.StatusmasterDetails')),
                ('text_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.TextMasterDetails')),
            ],
            options={
                'db_table': 'inference',
            },
        ),
    ]
