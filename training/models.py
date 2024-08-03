from django.db import models
from django.contrib.postgres.fields import JSONField


class ClassmasterDetails(models.Model):
    class_id = models.AutoField(primary_key = True, db_index = True)
    class_name = models.CharField(max_length = 100)
    class_code = models.CharField(max_length = 50)
    status = models.CharField(max_length=15)
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'class_master'


class StatusmasterDetails(models.Model):
    status_id = models.AutoField(primary_key = True, db_index = True)
    status_name = models.CharField(max_length = 500)
    class Meta:
        db_table ='status_master'


class ClientclassmappingDetails(models.Model):
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    class_id = models.IntegerField()
    class Meta:
        db_table = 'client_class_mapping'


class ClientclassificationmappingDetails(models.Model):
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    classification_type_id = models.IntegerField()
    class Meta:
        db_table = 'client_classification_mapping'


class ClassificationMasterDetails(models.Model):
    batch_id = models.AutoField(primary_key = True, db_index = True)
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    type = models.CharField(max_length = 10)
    reference_number = models.CharField(max_length = 250, blank = True, null = True)
    callback_url = models.CharField(max_length = 500, blank = True, null = True)
    status_id = models.ForeignKey(StatusmasterDetails, on_delete = models.CASCADE)
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'batch_master'

class FileDetails(models.Model):
    file_id = models.AutoField(primary_key = True, db_index = True)
    file_name = models.CharField(max_length = 250)
    file_type = models.CharField(max_length = 8)
    file_size = models.IntegerField()
    file_path = models.CharField(max_length = 500)
    batch_id = models.ForeignKey(ClassificationMasterDetails, on_delete = models.CASCADE, blank = True, null = True)
    class_id = models.CharField(max_length = 500, blank = True, null = True)
    status_id = models.IntegerField()
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'file_details'

class TrainingDetails(models.Model):
    classification_training_id = models.AutoField(primary_key = True, db_index = True)
    training_name = models.CharField(max_length = 250, blank = True, null = True)
    file = JSONField(blank = True, null = True) #PROTECT
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    reference_number = models.CharField(max_length = 250, blank = True, null = True)
    callback_url = models.CharField(max_length = 500, blank = True, null = True)
    result = JSONField(blank = True, null = True)
    nlp_training_id = models.IntegerField(default = 0)
    request_type = models.CharField(max_length = 350, default='Classification')
    status_id = models.ForeignKey(StatusmasterDetails, on_delete = models.CASCADE)
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    analysis_request_id = models.IntegerField(default = 0)
    classification_model= JSONField(blank = True, null = True)
    intent_model= JSONField(blank = True, null = True)
    class Meta:
        db_table = 'classification_training'


class TextMasterHistory(models.Model):
    text_history_id = models.AutoField(primary_key = True, db_index = True)
    file_id = models.ForeignKey(FileDetails, on_delete = models.CASCADE, blank = True, null = True)
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    text = models.TextField(blank = True, null = True)
    status_id = models.IntegerField()
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    text_reference_id= models.IntegerField(blank = True, null = True)
    class Meta:
        db_table = 'text_master_history'


class TextMasterDetails(models.Model):
    text_id = models.AutoField(primary_key = True, db_index = True)
    file_id = models.ForeignKey(FileDetails, on_delete = models.CASCADE, blank = True, null = True)
    client_id = models.IntegerField()
    project_id = models.IntegerField()
    text = models.TextField(blank = True, null = True)
    intent = JSONField(blank = True, null = True)
    classification = JSONField(blank = True, null = True)
    entities = JSONField(blank = True, null = True)
    sentiment = models.TextField(blank=True, null=True)
    predictive = models.TextField(blank=True, null=True)
    hierarchy = JSONField(blank = True, null = True)
    status_id = models.IntegerField()
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    text_reference_id = models.IntegerField(blank = True, null = True)
    solution_mapping_id = JSONField(blank = True, null = True)
    class Meta:
        db_table = 'text_master'

class DatasetDetails(models.Model):
    training_dataset_id = models.AutoField(primary_key = True, db_index = True)
    classification_training_id = models.ForeignKey(TrainingDetails, on_delete = models.CASCADE)
    text_id = models.ForeignKey(TextMasterDetails, on_delete = models.CASCADE)
    class_id = models.CharField(max_length =50)
    status_id = models.IntegerField()
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'training_data_set'

class ModelDetails(models.Model):
    model_id = models.AutoField(primary_key = True, db_index = True)
    classification_training_id =  models.ForeignKey(TrainingDetails, on_delete = models.CASCADE)
    nlp_model_id = models.IntegerField(default = 0)
    algorithm_id = models.IntegerField(default = 0)
    algorithm_name = models.CharField(max_length = 255, blank = True, null = True)
    algorithm_config = models.TextField(blank = True, null = True)
    accuracy = models.FloatField(default = 0)
    data = JSONField(blank = True, null = True)
    is_default = models.IntegerField(default=1)
    status = models.ForeignKey(StatusmasterDetails, on_delete = models.CASCADE)
    created_date_time = models.DateTimeField(auto_now_add = True)
    created_by = models.CharField(max_length = 50)
    updated_date_time = models.DateTimeField(blank = True, null = True)
    updated_by = models.CharField(max_length = 50, blank = True, null = True)
    class Meta:
        db_table = 'model_details'
