'''Import system libraries'''
import requests
import json
import xlrd
import logging

'''Import rest framework libraries'''
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from rest_framework import permissions

'''Import django libraries'''
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.auth import authenticate
from django_filters import rest_framework as filters
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

'''Import oauth libraries'''
from oauth2_provider.models import Application
from oauth2_provider.views.base import TokenView
from oauth2_provider.models import get_access_token_model, get_application_model
from oauth2_provider.signals import app_authorized

'''Import apllication modules'''
from training.models import FileDetails,TrainingDetails,DatasetDetails,ClassmasterDetails,ModelDetails, TextMasterDetails
from training.serializers import TokenSerializer,TrainingSerializer,ClassificationListSerializer,ClassmasterSerializer,ClassificationSerializer, RegistrationSerializer, UserListSerializer, ModelSerializer
from training.controller.training import TrainingController

from inference.serializers import TextMasterSerializer

from analysis_request.controller.background.retrain import classification_retrain, update_client_table

# Get an instance of a logging
log = logging.getLogger(__name__)

class UserRegistrationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        try:
            if "email" in request.data and "username" in request.data and "first_name" in request.data and "last_name" in request.data and "is_active" in request.data and 'password' in request.data:
                serializer = RegistrationSerializer(data=request.data)
                data = dict()
                if serializer.is_valid():
                    user = serializer.save()
                    data["error"] = False
                    data["message"] = "successfully registered a new user."
                else:
                    data["error"] = True
                    data["message"] = serializer.errors

                    for key, value in serializer.errors.items():
                        data["message"][key] = value[0]

                return Response(data)
            else:
                if 'email' not in request.data:
                    return Response({'error' : True, 'message' : 'email is required'})
                elif 'username' not in request.data:
                    return Response({'error' : True, 'message' : 'username is required'})
                elif 'first_name' not in request.data:
                    return Response({'error' : True, 'message' : 'first_name is required'})
                elif 'last_name' not in request.data:
                    return Response({'error' : True, 'message' : 'last_name is required'})
                elif 'is_active' not in request.data:
                    return Response({'error' : True, 'message' : 'is_active is required'})
                else:
                    return Response({'error' : True, 'message' : 'password is required'})
        except:
            return Response({'error' : True, 'message' : 'Something went wrong'})

class UserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            user_details = User.objects.all()
            serializer = UserListSerializer(user_details, many=True)
            return Response({'error': False, 'data':serializer.data})
        except:
            return Response({'error' : True, 'message' : 'Something went wrong'})

class LoginView(TokenView):
    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        url, headers, body, status = self.create_token_response(request)
        body = json.loads(body)
        if status == 200:
            access_token = body.get("access_token")
            if access_token is not None:
                token = get_access_token_model().objects.get(token=access_token)
                app_authorized.send(sender=self, request=request, token=token)
                body["status"] = True
                body['user'] = {
                    'id': token.user.id,
                    'username': token.user.username,
                    'email': token.user.email
                }
                body = json.dumps(body)
        elif status == 401:
            body["status"] = False
            body["error_description"] = "Invalid Client."
            body = json.dumps(body)
        else:
            body["status"] = False
            body = json.dumps(body)
        response = HttpResponse(content=body, status=status)
        for k, v in headers.items():
            response[k] = v
        return response

class FileUploadDraftView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            training = TrainingController()
            response = training.add_draft(request)
            print(response)
            return Response(response)
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class FileDatasetList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            classification_details = TrainingDetails.objects.filter(classification_training_id = request.data['classification_id'])
            serializer = ClassificationListSerializer(classification_details, many=True)
            # row data for first object only
            count = 0
            for file in serializer.data[0]["file"]:
                training = TrainingController()
                response = training.get_details(file)
                serializer.data[0]["file"][count]["data"] = response
                count = count + 1

            if len(serializer.data) > 0:
                return Response({'error' : False, 'data' : serializer.data, 'status' : 200})
            else:
                return Response({'error' : False, 'data' : serializer.data, 'status' : 400})
        except:
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})

class AlgorithmSelectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            training = TrainingController()
            response = training.select_algorithm(request)
            return Response(response)
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class AlgorithmDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            training = TrainingController()
            response = training.algorithm_detail(request)
            return Response(response)
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class FileUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            training = TrainingController()
            response = training.add_training(request)
            return Response(response)
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class AnalysisFileUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            training = TrainingController()
            response = training.add_training_analysis(request)
            return Response(response)

        except Exception as e:
            return Response({'error' : True, 'message' : str(e)})

class ClassificationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClassificationListSerializer
    pagination_class = LimitOffsetPagination()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('created_date_time', 'created_by', )

    def post(self, request):
        try:
            if "request_type" in request.data:
                queryset = TrainingDetails.objects.filter(request_type = request.data["request_type"]).order_by('-classification_training_id')
                created_by = request.query_params.get("created_by", None)
                created_date_time = request.query_params.get("created_date_time", None)

                if (created_by or created_date_time):
                    queryset = queryset.filter(Q(created_by=created_by) |
                                            Q(created_date_time__date=created_date_time))

                page = self.pagination_class.paginate_queryset(queryset, request)
                if page is not None:
                    serializer = self.serializer_class(page, many=True)
                    if len(serializer.data) > 0:
                        count = 0
                        for file_item in serializer.data:
                            row_count = 0
                            if(file_item['file'] != None):
                                for item in file_item["file"]:
                                    training = TrainingController()
                                    response = training.get_details(item)
                                    row_count = row_count + response["rows"]
                                serializer.data[count]["rows"] = row_count
                                count = count + 1
                                # print(serializer.data)
                        return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 200})
                    else:
                        return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 400})
                else:
                    return self.pagination_class.get_paginated_response({'error' : False, 'data' : serializer.data, 'status' : 400})
            else:
                return Response({'error' : True, 'message' : 'Something went worng'})
        except Exception as e:
            print(e)
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})

class TrainingNamesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if 'user' in request.data:
                training_master = TrainingDetails.objects.filter(status_id = 3)
                serializer = ClassificationSerializer(training_master, many=True)
                return Response({'error' : False, 'data' : serializer.data})
            else:
                return Response({'error' : True, 'message' : 'User required'})
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class TrainingNamesAvailableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if 'user' in request.data and 'training_name' in request.data:
                training_master = TrainingDetails.objects.filter(training_name = request.data["training_name"])
                if training_master:
                    return Response({'error' : False, 'message' : "training name avaiable"})
                else:
                    return Response({'error' : False, 'message' : "training name is not avaiable"})
            else:
                if 'training_name' in request.data:
                    return {'error' : True, 'message' : 'training_name is required'}
                else:
                    return Response({'error' : True, 'message' : 'User required'})
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class FileDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            data = []
            classification_details = TrainingDetails.objects.filter(classification_training_id = request.data['classification_id'])
            serializer = ClassificationListSerializer(classification_details, many=True)
            path = settings.MEDIA_ROOT+"/training/"
            output_file = path + "training_detail_" + str(request.data['classification_id']) + ".xlsx"

            loc = (output_file)
            wb = xlrd.open_workbook(loc)
            for sheet in wb.sheets():
                number_of_rows = sheet.nrows
                for row in range(0, number_of_rows):
                    data.append(sheet.row_values(row))
            if len(data) > 0:
                cols_index = 0
                for cols in data[0]:
                    if cols == 'content':
                        content_clmn = cols_index
                    cols_index = cols_index + 1
            serializer.data[0]["file_data"] = data

            if len(serializer.data) > 0:
                return Response({'error' : False, 'data' : serializer.data, 'status' : 200})
            else:
                return Response({'error' : False, 'data' : serializer.data, 'status' : 400})
        except:
            return Response({'status' : False, 'message' : 'Something went worng'})

class ModelDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if 'classification_training_id' not in request.data:
                return {'error' : True, 'message' : 'classification_training_id is required'}
            elif 'user' not in request.data:
                return {'error' : True, 'message' : 'user is required'}
            else:
                model_data = ModelDetails.objects.filter(classification_training_id = request.data['classification_training_id'])
                model_serializer = ModelSerializer(model_data, many = True)
                return Response({'error' : False, 'data' : model_serializer.data})
        except:
            return Response({'error' : True, 'message' : 'Something went worng'})

class AnalysisTextList(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            classification_details = TrainingDetails.objects.filter(classification_training_id = request.data['classification_id'])
            serializer = ClassificationListSerializer(classification_details, many=True)
            # row data for first object only
            count = 0
            result={}
            result['classification_id']=request.data['classification_id']
            result['classification_status']=serializer.data[0]['status']
            result['count']=0
            result['data']=[]
            file_id = []
            print(request.data['classification'])
            for file in serializer.data[0]["file"]:
                # file_id = file['file_id']
                file_id.append(file['file_id'])

            if  file_id:
                condition = Q(file_id__in=file_id)
                if 'client' in request.data and request.data['client']:
                    condition &= Q(client_id=request.data['client'])
                if 'classification' in request.data and request.data['classification']:
                    condition &= Q(classification__icontains=request.data['classification'])
                if 'intent' in request.data and request.data['intent']:
                    condition &= Q(intent__icontains=request.data['intent'])
                if 'entity' in request.data and request.data['entity']:
                    condition &= Q(entities__icontains=request.data['entity'])
                if 'searchcontent' in request.data and request.data['searchcontent']:
                    condition &= Q(text__icontains=request.data['searchcontent'])
                print(condition)
                offset=request.data['offset']
                limit=request.data['limit']
                textmaster_query=TextMasterDetails.objects.filter(condition).order_by('text_id')[int(offset):int(offset)+int(limit)]
                taxtmaster_serializer=TextMasterSerializer(textmaster_query, many=True)
                textmaster_count=TextMasterDetails.objects.filter(condition).count()
                # print(taxtmaster_serializer.data)
                result['data'].extend(taxtmaster_serializer.data)
                result['count']= result['count'] + textmaster_count
                # training = TrainingController()
                # response = training.get_details(file)
                # serializer.data[0]["file"][count]["data"] = response
                # count = count + 1

            if len(result) > 0:
                return Response({'error' : False, 'data' : result, 'status' : 200})
            else:
                return Response({'error' : False, 'data' : result, 'status' : 400})
        except:
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})

class AnalysisClassifyCallBack(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            classification_details = TrainingDetails.objects.filter(classification_training_id = request.data['classification_id'])
            serializer = ClassificationListSerializer(classification_details, many=True)
            # row data for first object only
            count = 0
            result={}
            result['classification_id']=request.data['classification_id']
            result['data']=[]


            if len(result) > 0:
                return Response({'error' : False, 'data' : result, 'status' : 200})
            else:
                return Response({'error' : False, 'data' : result, 'status' : 400})
        except:
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})

class UpdateAnalysisClassification(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if request.data['text_id']:
                data= json.loads(json.dumps(str(request.data['classification']).split(',')))
                TextMasterDetails.objects.filter(
                    text_id=request.data['text_id']
                ).update(
                    classification=data
                )
                update_client_table(text_id=request.data['text_id'], data=data, type="classification")
                return Response({'error' : False, 'message' : 'sucess', 'status' : 200})
            else:
                return Response({'error' : True, 'message' : 'An error occured', 'status' : 400})
        except:
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})

class UpateAnalysisIntent(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if request.data['text_id']:
                data = json.loads(json.dumps(str(request.data['intent']).split(',')))
                TextMasterDetails.objects.filter(
                    text_id=request.data['text_id']
                ).update(
                    intent=data
                )
                update_client_table(text_id=request.data['text_id'], data=data, type="intent")
                return Response({'error' : False, 'message' : 'sucess', 'status' : 200})
            else:
                return Response({'error' : True, 'message' : 'An error occured', 'status' : 400})
        except Exception as e:
            return Response({'error' : True, 'message' : str(e), 'status' : 417})

class UpdateAnalysisEntities(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if request.data['text_id']:
                data= json.loads(request.data['entities'])
                TextMasterDetails.objects.filter(
                    text_id=request.data['text_id']
                ).update(
                    entities=data
                )
                update_client_table(text_id=request.data['text_id'], data=data, type="entity")
                return Response({'error' : False, 'message' : 'sucess', 'status' : 200})
            else:
                return Response({'error' : True, 'message' : 'An error occured', 'status' : 400})
        except:
            return Response({'error' : True, 'message' : 'Something went worng', 'status' : 417})

class ReTraining(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            if 'training_id' in request.data:
                log.info(request.data)
                TrainingDetails.objects.filter(classification_training_id = request.data['training_id']).update(status_id=9)
                classification_retrain(request.data['training_id'])
                return Response({'error' : False, 'data' : request.data, 'status' : 200})
            else:

                return Response({'error' : True, 'message' : 'Invalid training id', 'status' : 400}, status=400)
        except Exception as e:
            return Response({'error' : True, 'message' : str(e), 'status' : 417})
