import csv
from requests.api import request
import xlrd
import re
import requests
import json
import pandas as pd
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from training.serializers import TrainingSerializer, ClassificationSerializer, ClassmasterSerializer
from training.models import FileDetails, TrainingDetails, ClassmasterDetails, ModelDetails, StatusmasterDetails
from training.controller.BackgroundProcess import training_process
from training.controller.AnalysisBackgroundProcess import analysis_training_process
from inference.serializers import TextMasterHistorySerializer, TextMasterSerializer


class TrainingController:

    def __init__(self):
        pass

    def add_draft(self, request):
        if 'file_name' in request.data and 'training_name' in request.data and 'request_type' in request.data and 'user' in request.data:
            media_type = ('csv', 'xls', 'xlsx', 'eml')

            files = request.data.getlist('file_name')
            files_list = list()
            for file in files:
                if file.name.split('.')[-1] not in media_type:
                    return {'error' : True, "message" : "Invalid file format",
                            'classification_id' : '',
                            'status' : 412, 'reference_number' : ''}

                file_type = file.name.split('.')[-1]
                file_size = file.size

                if file_type in media_type:
                    # File upload
                    fs = FileSystemStorage(location='media/training')
                    filename = fs.save(file.name, file)
                    uploaded_file_url = fs.url(filename)

                    # File Details
                    file_serializer = TrainingSerializer(data = { 'file_name' : filename, 'file_type' : file_type, 'file_path' : 'media/training', 'file_size' : file_size, 'status_id' : 1, 'created_by' : request.data['user']})
                    if file_serializer.is_valid():
                        file_details = file_serializer.save()
                        files_list.append(file_serializer.data)
                        filename = settings.MEDIA_ROOT+"/training/"+filename

                        if file_type == 'csv':
                            with open(filename, newline='', encoding="utf8", errors='ignore') as csvfile:
                                reader = csv.reader(csvfile)
                                for row in reader:
                                    text_master = {'file_id' : file_details.file_id, 'text' : row[0], 'client_id' : 1, 'project_id' : 1,'status_id' : 1, 'created_by' : request.data['user']}
                                    text_serializer = TextMasterHistorySerializer(data = text_master)
                                    # text_serializer = TextMasterSerializer(data = text_master)
                                    if text_serializer.is_valid():
                                        text_details = text_serializer.save()
                                    else:
                                        return {'error' : True, 'message' : text_serializer.errors}
                        else:
                            loc = (filename)
                            wb = xlrd.open_workbook(loc)
                            for sheet in wb.sheets():
                                number_of_rows = sheet.nrows
                                for row in range(0, number_of_rows):
                                    text_master = {'file_id' : file_details.file_id, 'text' : sheet.row_values(row)[0], 'client_id' : 1, 'project_id' : 1,'status_id' : 1, 'created_by' : request.data['user']}
                                    text_serializer = TextMasterHistorySerializer(data = text_master)
                                    # text_serializer = TextMasterSerializer(data = text_master)
                                    if text_serializer.is_valid():
                                        text_details = text_serializer.save()
                                    else:
                                        return {'error' : True, 'message' : text_serializer.errors}
                                break
                    else:
                        return {'error' : True, 'message' : file_serializer.errors}
                else:
                        return {'error' : True, 'message' : 'Invalid file format'}

            # Classification Details
            classification_serializer = ClassificationSerializer(data = {'training_name' : request.data['training_name'],'file' : files_list, 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'status_id' : 8, 'reference_number' : '', 'callback_url' : '', 'created_by' : request.data['user']})
            if classification_serializer.is_valid():
                classification_details = classification_serializer.save(request_type = request.data["request_type"])

                return {'error' : False, 'path' : uploaded_file_url, "classification_training_id": classification_details.classification_training_id}

            else:
                return {'error' : True, 'message' : classification_serializer.errors}
        else:
            if 'file_name' not in request.FILES:
                return {'error' : True, 'message' : 'file_name is required'}
            elif 'user' not in request.data:
                return {'error' : True, 'message' : 'user is required'}
            else:
                return {'error' : True, 'message' : 'training_name is required'}

    def select_algorithm(self, request):
        if 'classification_training_id' in request.data and 'data' in request.data and 'user' in request.data:
            classification_detail = TrainingDetails.objects.filter(classification_training_id=request.data["classification_training_id"])
            path = settings.MEDIA_ROOT+"/training/"

            data = json.loads(request.data["data"])
            df = pd.DataFrame(data)
            output_file = path + "training_detail_" + request.data["classification_training_id"] + ".xlsx"
            df.to_excel(output_file, index=False)

            files={"training_file": open(output_file, 'rb')}

            classification_server = settings.CLASSIFICATION_SERVER+'sampling'
            r = requests.post(classification_server, files=files)
            result_json = r.json()

            return {'error' : False, 'classification_training_id':request.data["classification_training_id"], 'algorithm_select' : result_json}

        else:
            if 'classification_training_id' not in request.data:
                return {'error' : True, 'message' : 'classification_training_id is required'}
            elif 'data' not in request.data:
                return {'error' : True, 'message' : 'data is required'}
            else:
                return {'error' : True, 'message' : 'user is required'}

    def algorithm_detail(self, request):
        if "algorithm_id" in request.data and 'user' in request.data:
            post_data = { "algorithm_id": int(request.data["algorithm_id"])}

            classification_server = settings.CLASSIFICATION_SERVER+'algorithm_details'

            r = requests.post(classification_server, data=post_data)
            result_json = r.json()

            return {'error' : False, 'algorithm_detail' : result_json}
        else:
            if 'algorithm_id' not in request.data:
                return {'error' : True, 'message' : 'algorithm_id is required'}
            else:
                return {'error' : True, 'message' : 'user is required'}

    def add_training(self, request):

        if "classification_training_id" in request.data and "algorithm_id" in request.data and "data" in request.data and "algorithm_name" in request.data and "algorithm_config" in request.data and 'user' in request.data:
            classification_detail = TrainingDetails.objects.filter(classification_training_id=request.data["classification_training_id"])
            classification_detail.update(status_id=1,request_type = 'Classification')
            status_master = StatusmasterDetails.objects.get(status_id=1)
            model_details = ModelDetails.objects.filter(classification_training_id=classification_detail[0])
            model_details.update(is_default = 0)
            model_details = ModelDetails.objects.create(classification_training_id=classification_detail[0], status=status_master, created_by=request.data["user"], algorithm_id = request.data["algorithm_id"], algorithm_name = request.data["algorithm_name"], algorithm_config = request.data["algorithm_config"])
            # if created:
            # model_details.algorithm_id = request.data["algorithm_id"]
            # model_details.algorithm_name = request.data["algorithm_name"]
            # model_details.algorithm_config = request.data["algorithm_config"]
            # model_details.save()

            training_process(classification_detail[0].classification_training_id, request.data["data"], request.data["user"])

            return {'error' : False, 'message' : "file uploaded successfully"}
        else:
            if 'classification_training_id' not in request.data:
                return {'error' : True, 'message' : 'classification_training_id is required'}
            elif 'algorithm_id' not in request.data:
                return {'error' : True, 'message' : 'algorithm_id is required'}
            elif 'algorithm_config' not in request.data:
                return {'error' : True, 'message' : 'algorithm_config is required'}
            elif 'algorithm_name' not in request.data:
                return {'error' : True, 'message' : 'algorithm_name is required'}
            elif 'data' not in request.data:
                return {'error' : True, 'message' : 'data is required'}
            else:
                return {'error' : True, 'message' : 'user is required'}


    def add_training_analysis(self, request):

        if "classification_training_id" in request.data and "data" in request.data and 'user' in request.data:
            host=  request.get_host() 
            classification_detail = TrainingDetails.objects.filter(classification_training_id=request.data["classification_training_id"])
            classification_detail.update(status_id=1,request_type = 'Analysis')
            status_master = StatusmasterDetails.objects.get(status_id=1)
            analysis_training_process(classification_detail[0].classification_training_id, request.data["data"], request.data["user"], host)
            return {'error' : False, 'message' : "file uploaded successfully"}
        else:
            if 'classification_training_id' not in request.data:
                return {'error' : True, 'message' : 'classification_training_id is required'}
            elif 'data' not in request.data:
                return {'error' : True, 'message' : 'data is required'}
            else:
                return {'error' : True, 'message' : 'user is required'}

    def classmaster(request, username):
        class_codes = list((re.sub('[\W_]', '', v).lower() for v in request[0].split(',')))
        class_names = request[0].split(',')
        class_ids = []
        for i in range(len(class_codes)):
            classMaster = ClassmasterDetails.objects.filter(class_code=class_codes[i])
            serializer = ClassmasterSerializer(classMaster, many=True)

            if classMaster.count() == 0:
                master_detail = ClassmasterDetails(class_code = class_codes[i], class_name = class_names[i], status = 1, created_by = username)
                master_detail.save()
                class_ids.append(str(master_detail.class_id))
            else:
                class_ids.append(str(serializer.data[0].get('class_id')))

        return class_ids


    def get_details(self, row_data):
        data = []
        filetype = ''

        filename = settings.MEDIA_ROOT+"/training/"+row_data["file_name"]
        filetype = row_data['file_type']
        content_clmn = -1
        if filetype == 'csv':
            with open(filename, newline='', encoding="utf8", errors='ignore') as csvfile:
                reader = csv.reader(csvfile)
                i = next(reader)
                data.append(i)
                reader = csv.DictReader(csvfile)
                cols_index = 0
                for cols in data[0]:
                    if cols == 'content':
                        content_clmn = cols_index
                    cols_index = cols_index + 1

                for row in reader:
                    row_data = []
                    for cols in row:
                        row_data.append(row[cols])
                    data.append(row_data)
                csvfile.close()
        elif filetype == 'eml':
            raw_email = ''
            with open(filename, 'r', newline="\r\n", errors='ignore') as emlfile:
                raw_email = emlfile.read()
            emlfile.close()
            data = raw_email.split("\r\n")
        else:
            loc = (filename)
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

        return {'error' : False, 'file_type' : filetype, 'rows' : len(data), 'data' : data, 'content_column' : content_clmn}
