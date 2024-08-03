'''Import system modules'''
import logging
import csv
import json
import requests
import psycopg2

""" Import Django libraries """
from django.conf import settings
from django.utils import timezone

'''Import Django third party libraries'''
from background_task import background

"""Import application related modules"""
from analysis_request.controller.common_controller import CommonController

from training.controller.BackgroundProcess import add_file_to_api
from training.models import TextMasterDetails, TrainingDetails
from training.serializers import ClassificationSerializer

from inference.serializers import TextMasterSerializer

from analysis_request.models import AnalysisRequest, AnalysisRequestSetting
from analysis_request.seralizers import AnalysisRequestViewSerializer, AnalysisRequestSettingViewSerializer

# Get an instance of a logging
log = logging.getLogger(__name__)


@background(schedule=timezone.now())
def classification_retrain(training_id):
    try:
        # Get and clone classification_train details to create supervised classification request
        train = TrainingDetails.objects.get(classification_training_id=training_id)
        training_serializer = ClassificationSerializer(train)
        training_data = training_serializer.data

        if training_data:
            filename = prepare_supervisied_classification_dataset(training_data['file'][0]['file_id'])
            intent_filename = prepare_bert_intent_dataset(training_data['file'][0]['file_id'])

            log.info("Classification {} is create Successfully".format(filename))
            log.info("Intent dataset {} is create Successfully".format(intent_filename))

            if filename:
                log.info("Calling classification training")
                result = call_supervisied_classification(filename)
                if result:
                    if not result['error']:
                        TrainingDetails.objects.filter(classification_training_id=training_id).update(
                            classification_model=result['result'])
            else:
                log.error("No classification training filename found")

            if intent_filename:
                log.info("Calling intent training")
                result = call_intent_training(intent_filename, training_id)
                if result:
                    if 'error' in result:
                        log.info("Intent training response {}".format(result))
            else:
                log.error("No bert intent training filename found")

    except Exception as e:
        log.error(e)
        raise e


def prepare_supervisied_classification_dataset(file_id):
    try:
        filename = ''
        text_queryset = TextMasterDetails.objects.filter(file_id=file_id)
        text_serializer = TextMasterSerializer(text_queryset, many=True)

        if text_serializer.data:
            filename = 'retraining_classification_file_' + str(file_id) + '.csv'
            file_path = settings.MEDIA_ROOT + '/training/' + filename

            with open(file_path, 'w') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
                wr.writerow(["content", "class"])
                for data in text_serializer.data:
                    classification = ','.join(data['classification'])
                    wr.writerow([data['text'], classification])
        else:
            log.error("No text file found")
        return filename
    except Exception as e:
        raise e


def prepare_bert_intent_dataset(file_id):
    try:
        filename = ''
        text_queryset = TextMasterDetails.objects.filter(file_id=file_id)
        text_serializer = TextMasterSerializer(text_queryset, many=True)

        if text_serializer.data:
            filename = 'retraining_intent_file_' + str(file_id) + '.csv'
            file_path = settings.MEDIA_ROOT + '/training/' + filename

            with open(file_path, 'w') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
                wr.writerow(["content", "intent", "entity"])
                for data in text_serializer.data:
                    intent = '|'.join(data['classification'])
                    intent = intent.replace(' ', '_')
                    tag = get_bert_tag(data['text'], data['entities'])
                    wr.writerow([data['text'], intent, tag])
        else:
            log.error("No text file found")
        return filename
    except Exception as e:
        raise e


def call_supervisied_classification(filename):
    try:
        filename = settings.MEDIA_ROOT + '/training/' + filename
        return add_file_to_api(
            filename=filename,
            algorithm_id=settings.DEFAULT_CLASSIFICATION_ID,
            algorithm_config=json.dumps(settings.DEFAULT_CLASSIFICATION_ALGORITHM_CONFIG)
        )
    except Exception as e:
        raise e


def call_intent_training(filename, training_id):
    try:
        filename = settings.APP_URL + settings.DOWNLOAD_URL + 'training/' + filename
        json_data = json.loads(settings.DEFAULT_BERT_INTENT_CONFIG)
        json_data["training_file"] = filename
        json_data["callback"] = settings.BERT_INTENT_CALLBACK_URL
        json_data["reference_id"] = training_id

        log.info(json_data)
        r = requests.post(settings.INTENT_CLASSIFICATION_SERVER + 'train/', json=json_data)
        if r.status_code == 200:
            result_json = r.json()
            if 'error' in result_json:
                if (result_json["error"] == False):
                    return result_json
        else:
            log.error(r.text)
            return False
    except Exception as e:
        raise e


def check_retrain_completion(training_id):
    try:
        train = TrainingDetails.objects.get(classification_training_id=training_id)
        training_serializer = ClassificationSerializer(train)
        training_data = training_serializer.data
        if training_data:
            if training_data['classification_model'] and training_data['intent_model']:
                train.update(status_id=3)
    except Exception as e:
        raise e


def get_bert_tag(text, entity):
    try:
        data = {}
        data['text'] = text
        data['entity'] = entity
        response = requests.post(settings.INTENT_CLASSIFICATION_SERVER + 'iob_formatter/', json=data)
        log.info("Bert IOB tag response {}".format(response))
        if response:
            if 'error' in response:
                if response['error'] == False:
                    return response['result']['iob']
            else:
                log.error(response.text)
                return ''
        return ''
    except Exception as e:
        raise e


@background(schedule=timezone.now())
def update_client_table(text_id, data, type):
    con = None
    from analysis_request.controller.common_controller import CommonController
    try:
        # Get file_id and text details from text_master
        text_queryset = TextMasterDetails.objects.get(text_id=text_id)
        text_serializer = TextMasterSerializer(text_queryset)
        text_data = text_serializer.data
        log.info(text_data)
        if text_data:
            train = TrainingDetails.objects.get(file__0__file_id=text_data['file_id'], nlp_training_id=0)
            training_serializer = ClassificationSerializer(train)
            training_data = training_serializer.data
            log.info(training_data)
            if training_data:

                # Get analysis request data
                anaysis_data = AnalysisRequest.objects.get(analysis_request_id=training_data['analysis_request_id'])
                analysis_seralizer = AnalysisRequestViewSerializer(anaysis_data)
                analysis = analysis_seralizer.data
                log.info(analysis)
                analysis_setting = AnalysisRequestSetting.objects.get(
                    analysis_request_setting_id=analysis['analysis_request_setting_id'])
                analysis_setting_serializer = AnalysisRequestSettingViewSerializer(analysis_setting)
                analysis_setting = analysis_setting_serializer.data
                log.info(analysis_setting)
                con = psycopg2.connect(
                    database=analysis_setting['extras'][0]['database']['database'],
                    user=analysis_setting['extras'][0]['database']['username'],
                    password=analysis_setting['extras'][0]['database']['password'],
                    port=analysis_setting['extras'][0]['database']['port'],
                    host=analysis_setting['extras'][0]['database']['hostname']
                )
                cur = con.cursor()
                sql = ''

                if type == 'intent':
                    data = json.dumps(data)
                    sql = "Update {}.{} set ml_intent='{}' WHERE analysis_unique_id={}".format(
                        analysis_setting['extras'][0]['database']['schema'],
                        analysis['analysis_request']['table_name'],
                        data,
                        text_data['text_reference_id']
                    )
                elif type == 'classification':
                    data = json.dumps(data)
                    sql = "Update {}.{} set ml_classification='{}' WHERE analysis_unique_id={}".format(
                        analysis_setting['extras'][0]['database']['schema'],
                        analysis['analysis_request']['table_name'],
                        data,
                        text_data['text_reference_id']
                    )
                else:
                    data = json.dumps(data)
                    sql = "Update {}.{} set ml_entity='{}' WHERE analysis_unique_id={}".format(
                        analysis_setting['extras'][0]['database']['schema'],
                        analysis['analysis_request']['table_name'],
                        data,
                        text_data['text_reference_id']
                    )
                log.info(sql)
                if sql:
                    cur.execute(sql)
                    con.commit()
                    common = CommonController()
                    common.init_call_back(training_data['classification_training_id'], analysis)

    except psycopg2.DatabaseError as e:
        log.error(e)
        raise e
    except Exception as e:
        log.error(e)
        raise e
    finally:
        if con:
            con.close()
