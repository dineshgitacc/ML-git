from django.apps import apps
from django.contrib.postgres.fields import JSONField
from django.db import models
from training.models import ClassificationMasterDetails,StatusmasterDetails,TextMasterDetails,TrainingDetails


class ClassificationDetails(models.Model):
    inference_id = models.AutoField(primary_key = True, db_index = True)
    batch_id = models.ForeignKey(ClassificationMasterDetails, on_delete = models.CASCADE)
    classification_training_id = models.ForeignKey(TrainingDetails, on_delete = models.CASCADE)    
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    text_id = models.ForeignKey(TextMasterDetails, on_delete = models.CASCADE)
    result = JSONField(blank = True, null = True)
    class_id = models.CharField(max_length = 250, blank = True, null = True)    
    process_type = models.ForeignKey(StatusmasterDetails, on_delete = models.CASCADE, default = '')
    status_id = models.IntegerField()
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'inference'        