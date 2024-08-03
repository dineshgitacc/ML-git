import requests
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from dataset.models import DatasetDetails
from training.models import FileDetails
from dataset.serializers import DatasetUploadSerializer, DatasetSerializer, DatasetDetailsSerializer, DatasetUpdateSerializer
from training.serializers import TrainingSerializer
import csv
import xlrd
import json
import pandas as pd

class DatasetController:

    def __init__(self):
        pass

    def check_folder(self, request):
        if 'folder_name' in request.data and 'user' in request.data:
            path = 'media/dataset/' + request.data['folder_name']
            if os.path.isdir(path):
                return { 'error' : False, 'message' : 'Folder Name already exists'}
            else :
                return { 'error' : False, 'message' : 'Folder Name available' }    
        else:
            return { 'error': True, 'message': 'Folder name required'}
            
    def get_list(self, request):
        pass

    def upload(self, request):
        
        input_serializer = DatasetUploadSerializer(data = request.data)
        if input_serializer.is_valid():
            # check folder available or not
            path = 'media/dataset/' + input_serializer.data['folder_name']
            if os.path.isdir(path):
                return { 'error' : True, 'message' : 'Folder Name already exists'}

            media_type = ('csv', 'xls', 'xlsx', 'eml', 'pdf', 'msg', 'docx')                            

            files_list = request.FILES.getlist('file_name')
            # check file format
            for files in files_list:                                                                
                if files.name.split('.')[-1] not in media_type:
                    return {'error' : True, "message" : "Invalid file format", 'classification_id' : '', 'status' : 412, 'reference_number' : ''}                                                            
            
            file_ids = []    
            for files in files_list:
                # File upload
                file_type = files.name.split('.')[-1]
                file_size = files.size
                location = 'media/dataset/' + input_serializer.data['folder_name']
                fs = FileSystemStorage(location = location)
                filename = fs.save(files.name, files)                                                
                uploaded_file_url = fs.url(filename)

                # File row_datas
                file_data = { 'file_name' : filename, 'file_type' : file_type, 'file_size' : file_size, 'file_path' : location, 'status_id' : 1, 'created_by' : request.data['user']}
                file_serializer = TrainingSerializer(data = file_data)                                
                if file_serializer.is_valid():                    
                    file_details = file_serializer.save()                    
                    file_ids.append(str(file_details.file_id))                                                                                                            
                else:
                    return {'error' : True, "message" : file_serializer.errors, 'classification_id' : '', 'status' : 412, 'reference_number' : ''}

            dataset_data = {'folder_name' : input_serializer.data['folder_name'], 'file_id' : ','.join(file_ids), 'status' : '1', 'created_by' : input_serializer.data['user']}            
            dataset_serializer = DatasetSerializer(data = dataset_data)            
            if dataset_serializer.is_valid():
                dataset = dataset_serializer.save()
                return { 'error' : False , 'message' : 'Daset uploaded successfully.', 'dataset_id' : dataset.dataset_id}
            else:
                return { 'error' : True , 'message' : dataset_serializer.errors}
             
        else:
            return { 'error' : True , 'message' : input_serializer.errors}
    
    def details(self, request):
        
        if 'dataset' in request.data and 'user' in request.data:
            dataset_obj = DatasetDetails.objects.filter(dataset_id = request.data['dataset'])
            serializer = DatasetDetailsSerializer(dataset_obj, many = True)
            if len(serializer.data) > 0:
                dataset_details = serializer.data[0]
                file_info = []
                for files_id in dataset_details['file_id'].split(','):
                    file_details = FileDetails.objects.filter(file_id=files_id)
                    file_serializer = TrainingSerializer(file_details, many=True)
                    if len(file_serializer.data) > 0:
                        file_info.append(file_serializer.data[0])
                dataset_details['file_details'] = file_info

                return { 'error' : False , 'message' : 'successfully', 'data' : dataset_details}

            else:
                return { 'error' : True , 'message' : 'dataset not found', 'status' : 400}            
        else:
            return { 'error' : True , 'message' : 'dataset/user is required'}

    def file_details(self, request):
        if 'file_id' in request.data and 'user' in request.data:
            file_data = FileDetails.objects.filter(file_id=request.data['file_id'])
            file_serializer = TrainingSerializer(file_data , many = True)

            if len(file_serializer.data) > 0:
                file_details = file_serializer.data[0]
                data = []                
                filename = file_details["file_path"]+"/"+file_details["file_name"]
                filetype = file_details['file_type']        
                content_clmn = -1
                if filetype == 'csv':
                    with open(filename, newline='', encoding="utf8", errors='ignore') as csvfile:                        
                        reader = csv.DictReader(csvfile)
                        headers = reader.fieldnames
                        data.append(headers)                        
                        cols_index = 0
                        for cols in headers:                    
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
                file_details['data'] = data
                file_details['content_cols'] = content_clmn
                return { 'error' : False, 'data' : file_details}

            else:                
                return { 'error' : True , 'message' : 'file row_data not found', 'status' : 400}
        else:
            return { 'error' : True , 'message' : 'dataset/user is required'}

    def save_dataset(self, request):
        try:
            input_serializer = DatasetUpdateSerializer(data = request.data)
            if input_serializer.is_valid():
                data = json.loads(request.data["data"]) 
                path = settings.APP_LOC
                output_file = path+'/'+input_serializer.data["file_path"] +'/' +input_serializer.data["file_name"]                               
                df = pd.DataFrame(data)
                
                if input_serializer.data['file_type'] == "csv":
                    df.to_csv(output_file, index=False, header=False)
                else:
                    df.to_excel(output_file, index=False, header=False)
                return { 'error' : False, 'message' : 'ok'}
            else:
                return { 'error' : True , 'message' : input_serializer.errors}
            
        except Exception as e:
            print(e)
            return { 'error' : True , 'message' : 'Something went wrong', 'error_description' : e}
        