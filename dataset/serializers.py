from rest_framework import serializers
from dataset.models import DatasetDetails

class DatasetUploadSerializer(serializers.Serializer):
    file_name = serializers.FileField(required=True)
    folder_name = serializers.CharField(required=True)    
    user = serializers.CharField(required=True, max_length= 50)

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetDetails
        fields = ['folder_name', 'file_id', 'status', 'created_by']

class DatasetDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetDetails
        fields = '__all__'

class DatasetUpdateSerializer(serializers.Serializer):
    file_name = serializers.CharField(required=True)
    file_path = serializers.CharField(required=True)    
    file_type = serializers.CharField(required=True)    
    data = serializers.CharField(required=True)    
    user = serializers.CharField(required=True, max_length= 50)
