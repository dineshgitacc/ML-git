from rest_framework import serializers
from inference.models import TextMasterDetails,ClassificationDetails
from training.models import ClassificationMasterDetails,FileDetails,ClassmasterDetails,TextMasterHistory


class InferenceaddSerializer(serializers.Serializer):
    file_name = serializers.FileField(required=False)
    text = serializers.CharField(required=False)
    training_id = serializers.IntegerField(required=True)
    user = serializers.CharField(required=True, max_length= 50)

class InferenceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileDetails
        fields = '__all__'        


class ClassificationMasterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ClassificationMasterDetails
        fields = '__all__'
        


class TextMasterSerializer(serializers.ModelSerializer):    
    class Meta:
        model = TextMasterDetails
        fields = '__all__'


class TextMasterHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TextMasterHistory
        fields = '__all__'


class ClassificationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ClassificationDetails
        fields = '__all__'    

class ClassificationListSerializer(serializers.ModelSerializer):    
    status = serializers.CharField(source='status_id.status_name', default= '')      
    class Meta:
        model = ClassificationMasterDetails
        fields = ['batch_id','type', 'client_id', 'project_id', 'status_id', 'status','created_date_time', 'created_by']
    
class ClassificationDetailsSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source='text_id.text', default= '')    
    class Meta:
        model = ClassificationDetails
        fields = ['text_id','text','class_id']