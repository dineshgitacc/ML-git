# Generated by Django 2.2 on 2021-06-01 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0007_classificationmasterdetails_request_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classificationmasterdetails',
            name='request_type',
        ),
        migrations.AddField(
            model_name='trainingdetails',
            name='request_type',
            field=models.CharField(default='Classification', max_length=350),
        ),
    ]
