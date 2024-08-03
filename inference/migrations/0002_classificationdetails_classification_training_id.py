# Generated by Django 2.2 on 2020-07-01 04:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0003_trainingdetails_training_name'),
        ('inference', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='classificationdetails',
            name='classification_training_id',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='training.TrainingDetails'),
        ),
    ]
