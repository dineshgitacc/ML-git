# Generated by Django 2.2 on 2020-08-17 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DatasetDetails',
            fields=[
                ('dataset_id', models.AutoField(db_index=True, primary_key=True, serialize=False)),
                ('folder_name', models.CharField(blank=True, max_length=255, null=True)),
                ('file_id', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(default='1', max_length=25)),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.CharField(max_length=50)),
                ('updated_date_time', models.DateTimeField(blank=True, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'db_table': 'data_set',
            },
        ),
    ]
