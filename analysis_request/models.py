from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

class AnalysisRequestSetting(models.Model):
    analysis_request_setting_id = models.AutoField(primary_key = True, db_index = True)
    client_name = models.CharField(max_length=100, blank=True, null=True)
    client_code = models.CharField(max_length=100, blank=True, null=True)
    analysis_features = JSONField(default=dict, blank=True, null=True)
    extras = JSONField(default=dict, blank=True, null=True)
    status = models.CharField(max_length=15)
    created_date= models.DateTimeField(default=timezone.now, null=True, blank=True)
    created_by = models.CharField(max_length = 50)
    updated_date= models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)

    class Meta:
        db_table = 'analysis_request_setting'

class AnalysisRequest(models.Model):
    analysis_request_id = models.AutoField(primary_key = True, db_index = True)
    analysis_request = JSONField(default=dict, blank=False, null=False)
    analysis_request_type = JSONField(default=dict, blank=False, null=False)
    analysis_reference = JSONField(default=dict, blank=True, null=True)
    analysis_request_setting_id = models.ForeignKey(AnalysisRequestSetting, db_column='analysis_request_setting_id', on_delete=models.CASCADE, blank=False, null=False)
    callback_url = models.CharField(max_length= 100, blank=True, null=True)
    client_reference_id= models.CharField(max_length= 100,blank=True, null=True)
    status = models.CharField(max_length=15)
    created_date= models.DateTimeField(default=timezone.now, null=True, blank=True)
    created_by = models.CharField(max_length = 50)
    updated_date= models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)

    class Meta:
        db_table = 'analysis_request'


class AnalysisRequestSolution(models.Model):
    solution_master_id = models.AutoField(primary_key = True, db_index = True)
    analysis_request_id = models.IntegerField()
    solution_text = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15)
    created_date= models.DateTimeField(default=timezone.now, null=True, blank=True)
    created_by = models.CharField(max_length = 50)
    updated_date= models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)

    class Meta:
        db_table = 'analysis_request_solution'