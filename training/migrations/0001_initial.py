# Generated by Django 2.2 on 2020-03-27 08:07

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClassificationMasterDetails',
            fields=[
                ('batch_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('client_id', models.IntegerField()),
                ('project_id', models.IntegerField()),
                ('type', models.CharField(max_length=10)),
                ('reference_number', models.CharField(blank=True, max_length=250, null=True)),
                ('callback_url', models.CharField(blank=True, max_length=500, null=True)),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'batch_master',
            },
        ),
        migrations.CreateModel(
            name='ClassmasterDetails',
            fields=[
                ('class_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('class_name', models.CharField(max_length=100)),
                ('class_code', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=15)),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'class_master',
            },
        ),
        migrations.CreateModel(
            name='ClientclassificationmappingDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.IntegerField()),
                ('project_id', models.IntegerField()),
                ('classification_type_id', models.IntegerField()),
            ],
            options={
                'db_table': 'client_classification_mapping',
            },
        ),
        migrations.CreateModel(
            name='ClientclassmappingDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.IntegerField()),
                ('project_id', models.IntegerField()),
                ('class_id', models.IntegerField()),
            ],
            options={
                'db_table': 'client_class_mapping',
            },
        ),
        migrations.CreateModel(
            name='FileDetails',
            fields=[
                ('file_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('file_name', models.CharField(max_length=250)),
                ('file_type', models.CharField(max_length=8)),
                ('file_size', models.IntegerField()),
                ('file_path', models.CharField(max_length=500)),
                ('class_id', models.CharField(blank=True, max_length=500, null=True)),
                ('status_id', models.IntegerField()),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('batch_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='training.ClassificationMasterDetails')),
            ],
            options={
                'db_table': 'file_details',
            },
        ),
        migrations.CreateModel(
            name='StatusmasterDetails',
            fields=[
                ('status_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('status_name', models.CharField(max_length=500)),
            ],
            options={
                'db_table': 'status_master',
            },
        ),
        migrations.CreateModel(
            name='TrainingDetails',
            fields=[
                ('classification_training_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('client_id', models.IntegerField()),
                ('project_id', models.IntegerField()),
                ('reference_number', models.CharField(blank=True, max_length=250, null=True)),
                ('callback_url', models.CharField(blank=True, max_length=500, null=True)),
                ('result', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('status_id', models.IntegerField()),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('file_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.FileDetails')),
            ],
            options={
                'db_table': 'classification_training',
            },
        ),
        migrations.CreateModel(
            name='TextMasterDetails',
            fields=[
                ('text_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('client_id', models.IntegerField()),
                ('project_id', models.IntegerField()),
                ('text', models.TextField(blank=True, null=True)),
                ('status_id', models.IntegerField()),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('file_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='training.FileDetails')),
            ],
            options={
                'db_table': 'text_master',
            },
        ),
        migrations.CreateModel(
            name='DatasetDetails',
            fields=[
                ('training_dataset_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('class_id', models.CharField(max_length=50)),
                ('status_id', models.IntegerField()),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('classification_training_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.TrainingDetails')),
                ('text_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.TextMasterDetails')),
            ],
            options={
                'db_table': 'training_data_set',
            },
        ),
        migrations.AddField(
            model_name='classificationmasterdetails',
            name='status_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='training.StatusmasterDetails'),
        ),
    ]
