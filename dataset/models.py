from django.db import models
from django.contrib.postgres.fields import JSONField

# Create your models here.
class DatasetDetails(models.Model):
    dataset_id = models.AutoField(primary_key = True, db_index = True)
    folder_name = models.CharField(max_length = 255, blank = True, null = True)
    file_id = models.CharField(max_length = 255, blank = True, null = True)
    status = models.CharField(max_length = 25, default= '1')
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'data_set'