import requests
import csv
import xlrd
import docxpy
from pdfreader import SimplePDFViewer
from django.conf import settings
from django.utils import timezone
from background_task import background
from training.models import ClassificationMasterDetails, FileDetails, ClassmasterDetails, TrainingDetails
from training.serializers import TrainingSerializer, ClassmasterSerializer
from inference.serializers import TextMasterSerializer, ClassificationSerializer
from inference.controller.eml_parser import EmailParser
from inference.controller.msg_parser import MsgParser


@background(schedule=timezone.now())
def inference_process(inference_id, training_id):

    try:
        file_class_list = []
        project_id = settings.PROJECT_ID
        client_id = settings.CLIENT_ID
        classification = ClassificationMasterDetails.objects.filter(batch_id = inference_id)
        file_details = FileDetails.objects.filter(batch_id = inference_id)
        file_serializer = TrainingSerializer(file_details, many = True)

        training_master_id = TrainingDetails.objects.filter(classification_training_id=training_id)
        for file_data in file_serializer.data:
            file_data = file_serializer.data[0]
            filename = settings.MEDIA_ROOT+"/inference/"+file_data['file_name']
            file_id = file_data['file_id']
            file_type = file_data['file_type']
            if file_type == 'csv':
                with open(filename, newline='', encoding="utf8", errors='ignore') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        text_master = {'text' : row[0], 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'status_id' : 1, 'created_by' : 'Admin'}
                        file_class_list = add_to_textmaster(inference_id, text_master, file_class_list, training_id)

            elif file_type == 'eml' or file_type == "msg":
                if file_type == "eml":
                    parser_obj = EmailParser(filename)
                else:
                    parser_obj = MsgParser(filename)
                parsed_text = parser_obj.get_parsed_text()

                for text in parsed_text:
                    # Text Master Details
                    join_delimiter = '@#@!' # 1.from 2.to 3.date 4.subject 5.body text
                    text_master = {'text' : join_delimiter.join(text), 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'status_id' : 1, 'created_by' : 'Admin'}
                    text_serializer = TextMasterSerializer(data = text_master)
                    if text_serializer.is_valid():
                        text_details = text_serializer.save()
                        post_data ={ 'client_id' : settings.CLIENT_ID, 'training_master_id' : training_master_id[0].nlp_training_id, 'text' : text[4]}
                        classification_server = settings.CLASSIFICATION_SERVER+'inference'
                        r = requests.post(classification_server, data=post_data)
                        result_json = r.json()
                        result_classes = result_json.get('result', '')
                        class_id = get_classId(result_classes)
                        file_class_list.append(class_id)

                        # Classification Master Details
                        class_master_detail = {'batch_id' : inference_id, 'text_id' : text_details.text_id, 'result' : result_json.get('result', ''), 'classification_training_id' : training_id, 'class_id' : ','.join(class_id), 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'process_type' : 7, 'status_id' : 1, 'created_by' : 'Admin'}
                        class_master_serializer = ClassificationSerializer(data = class_master_detail)
                        if class_master_serializer.is_valid():
                            class_master_serializer.save()
                        else:
                            print(class_master_serializer.errors)
                    else:
                        print('error', text_serializer.errors)
                        continue
            elif file_type == 'pdf':
                fd = open(filename, "rb")
                viewer = SimplePDFViewer(fd)
                viewer.render()

                text_master = {'text' : "".join(viewer.canvas.strings), 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'status_id' : 1, 'created_by' : 'Admin'}
                file_class_list = add_to_textmaster(inference_id, text_master, file_class_list, training_id)

            elif file_type == "docx":
                text = docxpy.process(filename)
                text_master = {'text': text, 'client_id': settings.CLIENT_ID, 'project_id': settings.PROJECT_ID,
                                   'status_id': 1, 'created_by': 'Admin'}
                file_class_list = add_to_textmaster(inference_id, text_master, file_class_list, training_id)

            else:  # for xls,xlsx format inference process
                loc = (filename)
                wb = xlrd.open_workbook(loc)
                for sheet in wb.sheets():
                    number_of_rows = sheet.nrows
                    for row in range(0, number_of_rows):
                        text_master = {'text' : sheet.row_values(row)[0], 'client_id' : settings.CLIENT_ID, 'project_id' : settings.PROJECT_ID, 'status_id' : 1, 'created_by' : 'Admin'}
                        file_class_list = add_to_textmaster(inference_id, text_master, file_class_list, training_id)

        # Update file class name
        class_count = 0
        class_name = ''

        for file_class in file_class_list:
            if class_count < file_class_list.count(file_class):
                class_count = file_class_list.count(file_class)
                class_name = file_class

        if class_count > 0:
            file_details.update(class_id = class_name)

        # Updated as completed
        classification.update(status_id=3)

    except Exception as e:
        print("error in inference process")
        print(e)


def add_to_textmaster(job_id, text_data, file_class_list, training_id):
    training_master_id = TrainingDetails.objects.filter(classification_training_id=training_id)
    text_master = {'text' : text_data.get('text', ''), 'client_id' : text_data.get('client_id', ''), 'project_id' : text_data.get('project_id', ''), 'status_id' : text_data.get('status_id', ''), 'created_by' : text_data.get('created_by', '')}
    text_serializer = TextMasterSerializer(data = text_master)
    if text_serializer.is_valid():
        text_details = text_serializer.save()
        post_data ={ 'client_id' : text_data.get('client_id', ''), 'training_master_id' : training_master_id[0].nlp_training_id, 'text' : text_data.get('text', '')}
        classification_server = settings.CLASSIFICATION_SERVER+'inference'
        r = requests.post(classification_server, data=post_data)
        result_json = r.json()
        result_classes = result_json.get('result', '')
        class_id = get_classId(result_classes)
        file_class_list.append(class_id)
        # Classification Master Details
        # class_master_detail = {'batch_id' : job_id, 'text_id' : text_details.text_id, 'result' : result_json.get('result', ''), 'class_id' : ','.join(class_id), 'client_id' : text_data.get('client_id', ''), 'project_id' : text_data.get('project_id', ''), 'process_type' : 7, 'status_id' : '1', 'created_by' : text_data.get('created_by', '')}
        class_master_detail = {'batch_id' : job_id, 'text_id' : text_details.text_id, 'result' : result_json.get('result', ''), 'classification_training_id' : training_id, 'class_id' : class_id, 'client_id' : text_data.get('client_id', ''), 'project_id' : text_data.get('project_id', ''), 'process_type' : 7, 'status_id' : '1', 'created_by' : text_data.get('created_by', '')}
        class_master_serializer = ClassificationSerializer(data = class_master_detail)
        if class_master_serializer.is_valid():
            class_master_serializer.save()
        else:
            print(class_master_serializer.errors)
    else:
        print('error', text_serializer.errors)
    return file_class_list


def get_classId(result):

    class_list = ''
    for i in result:
        classMaster = ClassmasterDetails.objects.filter(class_name=i)
        serializer = ClassmasterSerializer(classMaster, many=True)
        if len(serializer.data) > 0:
            class_list= str(serializer.data[0]['class_id'])
        else:
            class_code = i
            if i.find('__label__') != -1 :
                class_code = i[9:]
            class_data = {'class_name' : i, 'class_code' : class_code, 'status' : '1'}
            class_serializer = ClassmasterSerializer(data = class_data)
            if class_serializer.is_valid():
                class_result = class_serializer.save()
                class_list = str(class_result.class_id)
            else:
                print(class_serializer.errors)
    return class_list
