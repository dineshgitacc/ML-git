import requests
import json
import xlrd
import re
import logging
import pandas as pd
from django.conf import settings
from django.utils import timezone
from background_task import background
from training.models import TrainingDetails, FileDetails, ModelDetails, ClassmasterDetails
from training.serializers import TrainingSerializer, DatasetSerializer, ClassmasterSerializer
from inference.serializers import TextMasterSerializer

# Get an instance of a logging
log = logging.getLogger(__name__)


@background(schedule=timezone.now())
def training_process(training_id, json_data, user):
    try:
        project_id = settings.PROJECT_ID
        client_id = settings.CLIENT_ID
        classification = TrainingDetails.objects.filter(classification_training_id=training_id)
        classification.update(status_id=2)

        model_details = ModelDetails.objects.filter(classification_training_id=classification[0], is_default=1)
        model_details.update(status=2)
        algorithm_id = model_details[0].algorithm_id
        algorithm_config = model_details[0].algorithm_config

        path = settings.MEDIA_ROOT + "/training/"
        data = json.loads(json_data)
        df = pd.DataFrame(data)
        output_file = path + "training_detail_" + str(training_id) + ".xlsx"
        df = df[['content', 'class']]
        df.to_excel(output_file, index=False)

        loc = (output_file)
        wb = xlrd.open_workbook(loc)
        for sheet in wb.sheets():
            number_of_rows = sheet.nrows
            for row in range(0, number_of_rows):
                text_master = {'text': sheet.row_values(row)[0], 'client_id': client_id, 'project_id': project_id,
                               'status_id': 1, 'created_by': user}
                text_serializer = TextMasterSerializer(data=text_master)
                if text_serializer.is_valid():
                    text_details = text_serializer.save()
                    class_ids = classmaster(sheet.row_values(row), user)
                    dataset_serializer = DatasetSerializer(
                        data={'classification_training_id': classification[0].classification_training_id,
                              'class_id': ','.join(class_ids), 'text_id': text_details.text_id, 'status_id': 1,
                              'created_by': user})
                    if dataset_serializer.is_valid():
                        dataset_serializer.save()
                    else:
                        return {'error': True, 'message': dataset_serializer.errors}
                else:
                    return {'error': True, 'message': text_serializer.errors}

        api_response = add_file_to_api(output_file, algorithm_id, algorithm_config)
        print(api_response)
        print(api_response["result"]["training_master_id"], "api response")
        # Updated nlp_training_id in TrainingDetails
        classification.update(nlp_training_id=api_response["result"]["training_master_id"])

    except Exception as e:
        print(e)
        raise e


def add_file_to_api(filename, algorithm_id, algorithm_config):
    files = {"training_file": open(filename, 'rb')}
    post_data = {"client_id": settings.CLIENT_ID, "project_id": settings.PROJECT_ID,
                 "algorithm_id": algorithm_id,
                 "algorithm_config": algorithm_config}
    log.info(post_data)
    classification_server = settings.CLASSIFICATION_SERVER + 'training_data'
    r = requests.post(classification_server, files=files, data=post_data)
    if r.status_code == 200:
        log.info(r.json())
        return r.json()
    else:
        log.error(r.text)
        return False


def classmaster(row, username):
    class_codes = list((re.sub('[\W_]', '', v).lower() for v in row[1].split(',')))
    class_names = row[1].split(',')
    class_ids = []
    for i in range(len(class_codes)):
        classMaster = ClassmasterDetails.objects.filter(class_code=class_codes[i])
        serializer = ClassmasterSerializer(classMaster, many=True)

        if classMaster.count() == 0:
            master_detail = ClassmasterDetails(class_code=class_codes[i], class_name=class_names[i], status=1,
                                               created_by=username)
            master_detail.save()
            class_ids.append(str(master_detail.class_id))
        else:
            class_ids.append(str(serializer.data[0].get('class_id')))

    return class_ids
