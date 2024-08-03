from rest_framework import serializers
from .models import FileDetails,TrainingDetails,ClassmasterDetails,DatasetDetails,ModelDetails
from django.contrib.auth.models import User


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'

    def save(self):

        user = User(
                email=self.validated_data["email"],
                username=self.validated_data["username"],
                first_name=self.validated_data["first_name"],
                last_name=self.validated_data["last_name"],
                is_active=self.validated_data["is_active"],
            )
        password = self.validated_data["password"]
        user.set_password(password)
        user.save()
        return user

class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'

class TokenSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    grant_type = serializers.CharField(required=True)
    client_id = serializers.CharField(required=True)
    client_secret = serializers.CharField(required=True)

class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileDetails
        fields = '__all__'


class ClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingDetails
        fields = '__all__'

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetDetails
        fields = '__all__'

class ClassmasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassmasterDetails
        fields = ['class_id', 'class_name', 'class_code']

class ClassmasterInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassmasterDetails
        fields = '__all__'

class ClassificationListSerializer(serializers.ModelSerializer):

    # file_name = serializers.CharField(source='file_id.file_name')
    # file_type = serializers.CharField(source='file_id.file_type')
    # file_status = serializers.CharField(source='file_id.status_id')
    status = serializers.CharField(source='status_id.status_name', default= '')
    class Meta:
        model = TrainingDetails
        fields = ['classification_training_id', 'training_name', 'client_id', 'file', 'status_id', 'status','created_date_time', 'created_by', 'analysis_request_id', 'classification_model', 'intent_model']
        # fields = ['classification_training_id', 'training_name', 'client_id', 'file_name', 'file_type', 'file_status', 'status_id', 'status','created_date_time', 'created_by']

class ModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelDetails
        fields = '__all__'

class FileDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileDetails
        fields = '__all__'
