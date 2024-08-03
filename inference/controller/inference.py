import requests
import csv
import xlrd
import re
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .eml_parser import EmailParser
from inference.serializers import InferenceFileSerializer, ClassificationMasterSerializer, TextMasterSerializer, ClassificationSerializer, ClassificationListSerializer, ClassificationDetailsSerializer
from inference.models import TextMasterDetails, ClassificationDetails
from inference.controller.BackgroundProcess import inference_process,get_classId
from training.models import ClassificationMasterDetails, ClassmasterDetails, TrainingDetails
from training.serializers import ClassmasterSerializer


class InferenceController:

    def add_inference(self, request):
        try:
            if 'text' in request.data:
                return self.inferenceText(request)
            else:
                return self.inferenceFile(request)
        except Exception as e:
            return {'error' : True, 'message' : 'something went wrong', 'status' : 417, 'classification_id' : '', 'reference_number' : ''}

    def inferenceText(self, request):
        try:
            # Batch Master
            batch_data = { 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'type' : 'Text', 'status_id' : 1, 'created_by' : request.data['user']}
            classification_serializer = ClassificationMasterSerializer(data = batch_data)
            inferenced_text=0
            if classification_serializer.is_valid():
                classification = classification_serializer.save()
                for text in request.data["text"].split("\n"):
                    if text:
                        text_master = {'text' : text, 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'status_id' : 1, 'created_by' : request.data['user']}
                        text_serializer = TextMasterSerializer(data = text_master)
                        if text_serializer.is_valid():
                            text_details = text_serializer.save()
                            training_master_id = TrainingDetails.objects.filter(classification_training_id=request.data['training_id'])
                            post_data ={ 'client_id' : text_master.get('client_id', ''), 'training_master_id' : training_master_id[0].nlp_training_id, 'text' : text_master.get('text', '')}
                            classification_server = settings.CLASSIFICATION_SERVER+'inference'
                            r = requests.post(classification_server, data=post_data)
                            result_json = r.json()
                            result_classes = result_json.get('result', '')
                            class_id = get_classId(result_classes)
                            # Classification Master Details
                            # class_master_detail = {'batch_id' : classification.batch_id, 'text_id' : text_details.text_id, 'result' : result_json.get('result', ''), 'class_id' : ','.join(class_id), 'client_id' : text_master.get('client_id', ''), 'project_id' : text_master.get('project_id', ''), 'process_type' : 7, 'status_id' : '1', 'created_by' : text_master.get('created_by', '')}
                            class_master_detail = {'batch_id' : classification.batch_id, 'text_id' : text_details.text_id, 'result' : result_json.get('result', ''), 'class_id' : class_id, 'classification_training_id' : request.data['training_id'],'client_id' : text_master.get('client_id', ''), 'project_id' : text_master.get('project_id', ''), 'process_type' : 7, 'status_id' : '1', 'created_by' : text_master.get('created_by', '')}
                            class_master_serializer = ClassificationSerializer(data = class_master_detail)
                            if class_master_serializer.is_valid():
                                class_master_serializer.save()
                                classification_update = ClassificationMasterDetails.objects.filter(batch_id = classification.batch_id)
                                classification_update.update(status_id=3)
                                inferenced_text+=1
                            else:
                                print(class_master_serializer.errors)
                        else:
                            return {'error' : True, 'classification_id' : '', "message" : text_serializer.errors, 'status' : 412, 'reference_number' : ''}

                
                if inferenced_text==0:
                    return {'error' : True, 'classification_id' : '', "message" : 'No data available for inference', 'status' : 412, 'reference_number' : ''}
                else:
                    return {'error' : False, 'classification_id' : classification.batch_id, 'message' : 'Added Successfully', 'status' : 200, 'reference_number' : ''}
            else:
                return {'error' : True, 'classification_id' : '', "message" : classification_serializer.errors, 'status' : 412, 'reference_number' : ''}
        except Exception as e:
            print(e)
            return {'error' : True, 'message' : e, 'status' : 417, 'classification_id' : '', 'reference_number' : ''}


    def inferenceFile(self, request):
        try:
            if 'file_name' in request.FILES:
                media_type = ('csv', 'xls', 'xlsx', 'eml', 'pdf', 'msg', 'docx')

                files_list = request.FILES.getlist('file_name')

                for files in files_list:
                    if files.name.split('.')[-1] not in media_type:
                        return {'error' : True, "message" : "Invalid file format", 'classification_id' : '', 'status' : 412, 'reference_number' : ''}
                # Batch Master
                batch_data = { 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'type' : 'File', 'status_id' : 2, 'created_by' : request.data['user']}
                classification_serializer = ClassificationMasterSerializer(data = batch_data)
                if classification_serializer.is_valid():
                    classification = classification_serializer.save()
                    for files in files_list:

                        # File upload
                        file_type = files.name.split('.')[-1]
                        file_size = files.size
                        fs = FileSystemStorage(location='media/inference')
                        filename = fs.save(files.name, files)
                        uploaded_file_url = fs.url(filename)

                        # File Details
                        file_data = { 'file_name' : filename, 'file_type' : file_type, 'file_size' : file_size, 'file_path' : 'media/inference', 'batch_id' : classification.batch_id, 'status_id' : 1, 'created_by' : request.data['user']}
                        file_serializer = InferenceFileSerializer(data = file_data)
                        if file_serializer.is_valid():
                            files = file_serializer.save()
                        else:
                            return {'error' : True, "message" : file_serializer.errors, 'classification_id' : '', 'status' : 412, 'reference_number' : ''}

                    inference_process(classification.batch_id, request.data['training_id'])

                    return {'error' : False, 'classification_id' : classification.batch_id, 'message' : 'Uploaded Successfully', 'status' : 200, 'reference_number' : ''}
                else:
                    return {'error' : True, "message" : classification_serializer.errors, 'classification_id' : '', 'status' : 412, 'reference_number' : ''}

            else:
                return {'error' : True, "message" : "file_name(file) required", 'classification_id' : '', 'status' : 412, 'reference_number' : ''}
        except Exception as e:
            print(e)
            return {'error' : True, 'message' : 'something went wrong', 'status' : 417, 'classification_id' : '', 'reference_number' : ''}

    def inference_details(self, request):
        try:
            classification = ClassificationMasterDetails.objects.filter(batch_id = request.data['class_master'])
            serializer = ClassificationListSerializer(classification, many = True)
            if len(serializer.data) > 0:
                batch_details = serializer.data[0]
                classification_details = ClassificationDetails.objects.filter(batch_id = request.data['class_master'])
                details_serilaizer = ClassificationDetailsSerializer(classification_details, many = True)
                batch_details['rows'] = len(details_serilaizer.data)

                for class_names in details_serilaizer.data:
                    if class_names['class_id']:
                        class_details = ClassmasterDetails.objects.get(class_id = int(class_names['class_id']))
                        class_master = ClassmasterSerializer(class_details)

                        class_names['class_code'] = ''
                        if len(class_master.data) > 0:
                            class_names['class_code'] = class_master.data['class_name']
                batch_details['text_data'] = details_serilaizer.data
                # row = len(details_serilaizer.data)
                # class_ids = []
                # for class_id in details_serilaizer.data:
                #     if class_id['class_id'] != None:
                #         text_class = class_id['class_id']
                #         for v in text_class.split(','):
                #             class_ids.append(v)
                # get class details
                # class_ids = list(dict.fromkeys(class_ids))
                # class_details = ClassmasterDetails.objects.filter(class_id__in = class_ids)
                # class_master = ClassmasterSerializer(class_details, many = True)
                # return {'error' : False, 'row' : row, 'type' : '', 'class' : class_master.data, 'data' : details_serilaizer.data}
                return {'error' : False, 'data' : batch_details, 'rows' : len(details_serilaizer.data)}
            else:
                return {'error' : True, 'message' : 'Data not found', 'status' : 400}
        except Exception as e:
            print('Line no 122', e)
            return {'error' : True, 'message' : 'Something went wrong', 'status' : 417}
