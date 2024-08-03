from rest_framework import serializers
from analysis_request.models import AnalysisRequest, AnalysisRequestSetting, AnalysisRequestSolution


class AnalysisRequestSettingViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisRequestSetting

        fields = ('analysis_request_setting_id', 'client_name', 'client_code', 'analysis_features', 'status', 'created_date', 'created_by', 'updated_date', 'updated_by', 'extras')


class AnalysisRequestViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalysisRequest

        fields = ('analysis_request', 'analysis_request_type', 'analysis_reference', 'analysis_request_setting_id', 'callback_url', 'client_reference_id', 'status', 'created_date', 'created_by', 'updated_date', 'updated_by')


class AnalysisRequestSolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRequestSolution
        fields = ('analysis_request_id','solution_text')

class AnalysisRequestSolutionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRequestSolution
        fields = '__all__'

class AnalysisRequestSolutionMappingListSerializer(serializers.ModelSerializer):
    class Meta:
            model = AnalysisRequestSolution
            fields = ('solution_master_id','analysis_request_id','solution_text')

class AnalysisRequestSolutionInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRequestSolution
        fields = '__all__'
