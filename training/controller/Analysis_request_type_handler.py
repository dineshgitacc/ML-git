
import csv
import json
import logging

import pandas as pd

'''Import django modules'''
from django.conf import settings
from django.utils import timezone

'''Import django third party modules '''
from background_task import background

'''Import application modules'''
from training.models import TrainingDetails
from training.serializers import ClassificationListSerializer
from training.controller.BackgroundProcess import training_process

from analysis_request.models import AnalysisRequest
from analysis_request.seralizers import AnalysisRequestViewSerializer
from analysis_request.controller.common_controller import CommonController as AnalysisCommonController

from training.controller.common_controller import CommonController

# Get an instance of a logging
log = logging.getLogger(__name__)


def text_analysis_process(training_id,request):
    try:
        no_class_flag = False
        intent_entity_flag = True
        # training_json_data = []
        classification_completion = False

        # Get analysis training details and update the status to inprogress using training id
        classification = TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=2)

        # Get analysis training details
        classification = TrainingDetails.objects.get(classification_training_id=training_id)
        classification_data = ClassificationListSerializer(classification)

        # Update analysis_request status
        AnalysisRequest.objects.filter(analysis_request_id=int(classification_data.data['analysis_request_id'])).update(
            status='Inprogress',
            analysis_reference={"classification": {"classification_training_id": 0, "status": "New", "model_path": ""},
                                "intent": {"intent_training_id": 0, "status": "New", "model_path": ""}})

        # Get file name and file path from classification_training object
        file_path = classification_data.data['file'][0]['file_path']
        file_name = classification_data.data['file'][0]['file_name']

        # create obj for common controller
        common = CommonController()

        # Insert the data into text_master, class_master and training_data_set by read csv file
        with open(file_path + '/' + file_name, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)

            # Iterate each row of a CSV file
            for rows in csvReader:

                # training_json_data.append({"content": rows['content'], "class": rows['class']})

                if rows['class']:
                    classification_list = (str(rows['class']).strip()).split(',')
                    classification_list = [classification.capitalize() if len(classification) > 1 else 'Others' for
                                           classification in classification_list]
                else:
                    classification_list = ''

                # Insert into solution master
                solution_ids = ''

                if rows['solution']:
                    solution_ids = []
                    solution_obj = common.add_to_solution_master(
                        text=rows['solution'],
                        analysis_request_id=classification_data.data['analysis_request_id']
                    )
                    solution_ids.append(solution_obj.solution_master_id)

                # Insert into text_master
                text_reference_id = rows['id'] if 'id' in rows else 0

                text_obj = common.add_to_text_master(
                    rows['content'],
                    1,
                    classification_data.data['file'][0]['file_id'],
                    classification=classification_list,
                    reference_id=text_reference_id,
                    solution_map_id=solution_ids
                )

                if text_obj:
                    # Get or Create in class_master
                    if rows['class']:
                        class_ids = common.get_or_create_class(rows['class'], 1)
                        common.add_to_training_data_set(training_id, text_obj.text_id, 1, class_ids)
                    else:
                        if not no_class_flag:
                            no_class_flag = True
                            log.info("Class information not found. Applying unsupervisied method")
                        common.add_to_training_data_set(training_id, text_obj.text_id, 1)

        algorithm_detail = request['ml_algorithm_detail']
        algorithm_name = algorithm_detail['ml_algorithm_name'] if 'ml_algorithm_detail' in request else ''
        algorithm_name = algorithm_name.upper()
        log.info('algorithm_name {}'.format(algorithm_name))

        # Prepare file_url
        _file_id = classification_data.data['file'][0]['file_id']
        file_url = common.get_data_in_file_by_file_id(_file_id)

        if algorithm_name in ['UNSUPERVISED LEARNING', 'UNSUPERVISED_LEARNING']:
            log.info("Calling clustering Extraction")
            common.update_analysis_request(
                analysis_request_id=classification_data.data['analysis_request_id'],
                key="hierarchy",
                json_data={
                    "training_id": 0, "status": 'Inprogress'}
            )
            if file_url != '':
                common.call_clustering_api(file_url, training_id)
            else:
                log.info("Unsupervised File url not set")

        elif algorithm_name in ['SUPERVISED LEARNING', 'SUPERVISED_LEARNING'] and algorithm_detail['model_name'] != '':
            log.info("Calling Supervised Classification Extraction")
            common.update_analysis_request(
                analysis_request_id=classification_data.data['analysis_request_id'],
                key='classification',
                json_data={"intent_training_id": 0, "status": "Inprogress", "model_path": ""}
            )
            log.info("File Url - {}".format(file_url))

            if file_url != '':
                model_name = algorithm_detail['model_name']
                _response = common.call_supervised_process_classification(file_url, training_id, model_name,request)
            else:
                log.info("File url not set")

            classification_completion = True

        elif algorithm_name in ['AUTO CLASSIFICATION', 'AUTO_CLASSIFICATION']:
            intent_entity_flag = False
            if file_url != '':
                common.call_auto_unsupervised_classification(file_url, training_id,request)
            else:
                log.info("File url not set")
        else:
            log.info("Calling Zeroshot Text Classification Extraction")
            common.update_analysis_request(
                analysis_request_id=classification_data.data['analysis_request_id'],
                key='classification',
                json_data={"intent_training_id": 0, "status": "Inprogress", "model_path": ""}
            )

            log.info("File Url - {}".format(file_url))
            if file_url != '':
                labels = request['ml_algorithm_detail']['label'] if 'label' in request['ml_algorithm_detail'] else ["others", "access issue",
                                                                                             "approval issue",
                                                                                             "booking issue",
                                                                                             "invoice issue",
                                                                                             "process issue",
                                                                                             "quote issue",
                                                                                             "payment issue"]
                _response = common.call_process_classification(file_url, labels, training_id,request)
            else:
                log.info("File url not set")

            classification_completion = True

        log.info("Calling Intent Extraction")
        if file_url != '' and intent_entity_flag:
            _response = common.call_process_intent_entity(file_url, training_id,request)

        # common.update_analysis_request(
        #     analysis_request_id=classification_data.data['analysis_request_id'],
        #     key='intent',
        #     json_data={"intent_training_id": 0, "status": "Inprogress", "model_path": ""}
        # )
        # common.call_intent_classification(training_id)

        if classification_data.data['analysis_request_id']:
            log.info("Calling callback if exist")
            analysis_common = AnalysisCommonController()
            analysis_common.check_for_callback(classification_data.data['analysis_request_id'], training_id)

        log.info("Checking for completion")
        if classification_completion:
            TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=3)



    except Exception as e:
        log.error(e)
        raise e


def sentiment_analysis_process(training_id,request):
    try:
        no_class_flag = False
        # training_json_data = []
        classification_completion = False

        # Get analysis training details and update the status to inprogress using training id
        classification = TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=2)

        # Get analysis training details
        classification = TrainingDetails.objects.get(classification_training_id=training_id)
        classification_data = ClassificationListSerializer(classification)

        # Update analysis_request status
        AnalysisRequest.objects.filter(analysis_request_id=int(classification_data.data['analysis_request_id'])).update(
            status='Inprogress',
            analysis_reference={"classification": {"classification_training_id": 0, "status": "New", "model_path": ""},
                                "intent": {"intent_training_id": 0, "status": "New", "model_path": ""}})

        # Get file name and file path from classification_training object
        file_path = classification_data.data['file'][0]['file_path']
        file_name = classification_data.data['file'][0]['file_name']

        # create obj for common controller
        common = CommonController()

        # Insert the data into text_master, class_master and training_data_set by read csv file
        with open(file_path + '/' + file_name, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)

            # Iterate each row of a CSV file
            for rows in csvReader:

                # training_json_data.append({"content": rows['content'], "class": rows['class']})

                if rows['class']:
                    classification_list = (str(rows['class']).strip()).split(',')
                    classification_list = [classification.capitalize() if len(classification) > 1 else 'Others' for
                                           classification in classification_list]
                else:
                    classification_list = ''

                # Insert into solution master
                solution_ids = ''

                if rows['solution']:
                    solution_ids = []
                    solution_obj = common.add_to_solution_master(
                        text=rows['solution'],
                        analysis_request_id=classification_data.data['analysis_request_id']
                    )
                    solution_ids.append(solution_obj.solution_master_id)

                # Insert into text_master
                text_reference_id = rows['id'] if 'id' in rows else 0

                text_obj = common.add_to_text_master(
                    rows['content'],
                    1,
                    classification_data.data['file'][0]['file_id'],
                    classification=classification_list,
                    reference_id=text_reference_id,
                    solution_map_id=solution_ids
                )

                if text_obj:
                    # Get or Create in class_master
                    if rows['class']:
                        class_ids = common.get_or_create_class(rows['class'], 1)
                        common.add_to_training_data_set(training_id, text_obj.text_id, 1, class_ids)
                    else:
                        if not no_class_flag:
                            no_class_flag = True
                            log.info("Class information not found. Applying unsupervisied method")
                        common.add_to_training_data_set(training_id, text_obj.text_id, 1)

        # Prepare file_url
        _file_id = classification_data.data['file'][0]['file_id']
        file_url = common.get_data_in_file_by_file_id(_file_id)
        if file_url != '':
            _response = common.call_process_sentiment_analysis(file_url, training_id)


        if classification_data.data['analysis_request_id']:
            log.info("Calling callback if exist")
            analysis_common = AnalysisCommonController()
            analysis_common.check_for_callback(classification_data.data['analysis_request_id'], training_id)

        log.info("Checking for completion")
        if classification_completion:
            TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=3)



    except Exception as e:
        log.error(e)
        raise e



def predictive_analysis_process(training_id,request,file_path_predictive):
    try:
        no_class_flag = False
        # training_json_data = []
        classification_completion = False

        # Get analysis training details and update the status to inprogress using training id
        classification = TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=2)

        # Get analysis training details
        classification = TrainingDetails.objects.get(classification_training_id=training_id)
        classification_data = ClassificationListSerializer(classification)

        # Update analysis_request status
        AnalysisRequest.objects.filter(analysis_request_id=int(classification_data.data['analysis_request_id'])).update(
            status='Inprogress',
            analysis_reference={"classification": {"classification_training_id": 0, "status": "New", "model_path": ""},
                                "intent": {"intent_training_id": 0, "status": "New", "model_path": ""}})

        # Get file name and file path from classification_training object
        file_path = classification_data.data['file'][0]['file_path']
        file_name = classification_data.data['file'][0]['file_name']

        # create obj for common controller
        common = CommonController()

        # Insert the data into text_master, class_master and training_data_set by read csv file
        with open(file_path + '/' + file_name, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)

            # Iterate each row of a CSV file
            for rows in csvReader:

                # training_json_data.append({"content": rows['content'], "class": rows['class']})

                if rows['class']:
                    classification_list = (str(rows['class']).strip()).split(',')
                    classification_list = [classification.capitalize() if len(classification) > 1 else 'Others' for
                                           classification in classification_list]
                else:
                    classification_list = ''

                # Insert into solution master
                solution_ids = ''

                if rows['solution']:
                    solution_ids = []
                    solution_obj = common.add_to_solution_master(
                        text=rows['solution'],
                        analysis_request_id=classification_data.data['analysis_request_id']
                    )
                    solution_ids.append(solution_obj.solution_master_id)

                # Insert into text_master
                text_reference_id = rows['id'] if 'id' in rows else 0

                text_obj = common.add_to_text_master(
                    rows['content'],
                    1,
                    classification_data.data['file'][0]['file_id'],
                    classification=classification_list,
                    reference_id=text_reference_id,
                    solution_map_id=solution_ids
                )

                if text_obj:
                    # Get or Create in class_master
                    if rows['class']:
                        class_ids = common.get_or_create_class(rows['class'], 1)
                        common.add_to_training_data_set(training_id, text_obj.text_id, 1, class_ids)
                    else:
                        if not no_class_flag:
                            no_class_flag = True
                            log.info("Class information not found. Applying unsupervisied method")
                        common.add_to_training_data_set(training_id, text_obj.text_id, 1)

        # Prepare file_url
        _file_id = classification_data.data['file'][0]['file_id']
        proper_id_file_url = common.get_data_in_file_by_file_id(_file_id)
        log.info('predictive analysis proper_id_file_url - {}'.format(proper_id_file_url))
        df_ = pd.read_csv(proper_id_file_url)
        nonproper_id_filer_url = settings.APP_URL + '/' + file_path_predictive
        log.info('predictive analysis nonproper_id_filer_url - {}'.format(nonproper_id_filer_url))
        #df2_ = pd.read_csv(nonproper_id_filer_url)
        df2_ = pd.read_csv(file_path_predictive)
        df2_['id'] = df_['id']
        df2_.drop([ 'content','class','solution'], axis=1, inplace=True)
        file_location = file_path_predictive.replace('upload_file','training')
        df2_.to_csv(file_location,index=False)
        file_url = settings.APP_URL+'/' + file_location.replace('media/','static/')
        if file_url != '':
            _response = common.call_process_predictive_analysis(file_url, training_id,request)

        if classification_data.data['analysis_request_id']:
            log.info("Calling callback if exist")
            analysis_common = AnalysisCommonController()
            analysis_common.check_for_callback(classification_data.data['analysis_request_id'], training_id)

        log.info("Checking for completion")
        if classification_completion:
            TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=3)



    except Exception as e:
        log.error(e)
        raise e
