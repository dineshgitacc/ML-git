import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.pagination import LimitOffsetPagination
from django_filters import rest_framework as filters
from dataset.controller.dataset import DatasetController
from dataset.models import DatasetDetails
from dataset.serializers import DatasetDetailsSerializer

class DatasetFolderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            dataset = DatasetController()
            response = dataset.check_folder(request)
            return Response(response)
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})  

class DatasetUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            dataset = DatasetController()
            response = dataset.upload(request)
            return Response(response)
        except Exception as e:
            print(e)
            return Response({'error' : True, 'message' : 'Something went worng'})

class DatasetListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DatasetDetails.objects.all().order_by('-dataset_id')
    serializer_class = DatasetDetailsSerializer
    pagination_class = LimitOffsetPagination()
    
    def post(self, request):
        try:
            queryset = self.queryset
            created_by = request.query_params.get("created_by", None)
            created_date_time = request.query_params.get("created_date_time", None)

            if (created_by or created_date_time):
                queryset = queryset.filter(Q(created_by=created_by) |
                                           Q(created_date_time__date=created_date_time))

            page = self.pagination_class.paginate_queryset(queryset, request)
            if page is not None:
                serializer = self.serializer_class(page, many=True)
                if len(serializer.data) > 0:
                    return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 200})
                else:
                    return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 400})
            else:
                return Response({'error' : True, 'message' : 'Something went worng'})
        except Exception as e:
            print(e)
            return Response({'error' : True, 'message' : 'Something went worng'})

class DatasetDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            dataset = DatasetController()
            response = dataset.details(request)
            return Response(response)
        except Exception as e:
            print(e)
            return Response({'error' : True, 'message' : 'Something went worng'})

class DataFileDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            dataset = DatasetController()
            response = dataset.file_details(request)
            return Response(response)
        except Exception as e:
            print(e)
            return Response({'error' : True, 'message' : 'Something went worng'})

class DatasetSaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            dataset = DatasetController()
            response = dataset.save_dataset(request)
            return Response(response)
        except Exception as e:
            print(e)
            return Response({'error' : True, 'message' : 'Something went worng'})            