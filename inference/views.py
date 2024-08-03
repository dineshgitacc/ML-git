from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.pagination import LimitOffsetPagination
from inference.serializers import InferenceaddSerializer,InferenceFileSerializer,ClassificationMasterSerializer,TextMasterSerializer,ClassificationSerializer,ClassificationListSerializer,ClassificationDetailsSerializer
from inference.models import TextMasterDetails,ClassificationDetails
from training.models import ClassificationMasterDetails,FileDetails
from inference.controller.inference import InferenceController
import csv
import xlrd
import re

class InferenceListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ClassificationMasterDetails.objects.all().order_by('-batch_id')
    serializer_class = ClassificationListSerializer
    pagination_class = LimitOffsetPagination()

    def post(self, request):
        try:
            page = self.pagination_class.paginate_queryset(self.queryset, request)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                if len(serializer.data) > 0:
                    for item in serializer.data:
                        classification_details = ClassificationDetails.objects.filter(batch_id = item['batch_id'])
                        details_serilaizer = ClassificationDetailsSerializer(classification_details, many = True)
                        item['rows'] = len(details_serilaizer.data)
                    return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 200})
                else:
                    return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 400})
        except Exception as e:
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})


class InferenceUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        try:
            inference_obj = InferenceController()
            if 'file_name' in request.FILES:
                response = inference_obj.inferenceFile(request)
                return Response(response)
            else:
                return Response({'error' : False, 'message' : 'Something went worng'})            
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})


class InferenceTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            inference_serializer = InferenceaddSerializer(data=request.data)
            if inference_serializer.is_valid():
                inference_obj = InferenceController()
                response = inference_obj.add_inference(request)
                return Response(response)
            else:                
                return Response({'error' : False, 'message' : inference_serializer.errors, 'classification_id' : '', 'status' : 412, 'reference_number' : ''})               
        except Exception as e:
            print(e)
            return Response({'error' : False, 'message' : 'Something went worng', 'classification_id' : '', 'status' : 417, 'reference_number' : ''})

class InferenceDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            inference_obj = InferenceController() 
            response = inference_obj.inference_details(request)
            return Response(response)  
        except Exception as e:
            print(e)
            return Response({'error' : False, 'message' : 'Something went worng'})