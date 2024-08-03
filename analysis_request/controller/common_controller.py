'''Import system modules'''
import logging
import requests
from pathlib import Path
from shutil import copyfile
import csv
import os
import psycopg2
import json

""" Import Django libraries """
from django.conf import settings

'''Import application modules'''
from analysis_request.models import AnalysisRequest, AnalysisRequestSolution, AnalysisRequestSetting
from analysis_request.seralizers import AnalysisRequestViewSerializer, AnalysisRequestSolutionMappingListSerializer, \
    AnalysisRequestSolutionInsertSerializer, AnalysisRequestSettingViewSerializer

from analysis_request.controller.background.text_analysis import text_analysis_training_process
from analysis_request.controller.analysis_connection_controller import AnalysisConnectionController

from training.models import FileDetails, TrainingDetails, StatusmasterDetails, TextMasterHistory, TextMasterDetails
from training.serializers import FileDetailsSerializer, ClassificationSerializer
from training.controller.common_controller import CommonController as TrainingCommonController

from inference.serializers import TextMasterSerializer
# from training.controller.common_controller import CommonController
# Get an instance of a logging
log = logging.getLogger(__name__)
from kafka import KafkaProducer
import json
import time

#def json_serializer(data):
#    return json.dumps(data).encode("utf-8")
#producer=KafkaProducer(bootstrap_servers=['10.10.50.36:9092'],
#                   value_serializer=json_serializer)


class CommonController():

    def create_analysis_request(self, request, analysis_request_setting_obj):
        """
        Create analysis function is used to create a new record in analysis_request table
        Input:
            request <object of request>
            analysis_request_setting_id <object of analysis_request_setting>
        Output:
            None
        """
        try:
            obj = AnalysisRequest.objects.create(
                analysis_request=request,
                analysis_request_type=request['request_type'],
                analysis_request_setting_id=analysis_request_setting_obj,
                callback_url=request['callback_url'],
                client_reference_id=request['reference_id'],
                status='New',
                created_by=1
            )
            obj.save()
            return obj
        except Exception as e:
            log.error(e)
            raise e

    def raise_analysis_request(self, request, analysis_request_setting_obj, analysis_request_id=0):
        """
        Create analysis function is used to create a new record in analysis_request table
        Input:
            request <object of request>
            analysis_request_setting_id <object of analysis_request_setting>
        Output:
            boolean
        """
        try:
            print("Summarization coming to raise_analysis_request")
            log.info('Summarization coming to raise_analysis_request')
            text_analysis_training_process(analysis_request_setting_obj, request, analysis_request_id)
        except Exception as e:
            log.error(e)
            raise e

    def connect_data_source(self, settings_obj, source_type, request, analysis_request_id=0):
        try:
            if source_type == 'database':
                if settings_obj['extras']:
                    for extra in settings_obj['extras']:
                        if 'database' in extra:
                            connection_obj = AnalysisConnectionController()
                            return connection_obj.connect_to_database(extra['database'], request, analysis_request_id)
        except Exception as e:
            log.error(e)
            raise e
        return False

    def handle_file_master(self, file_path, analysis_request_id, request, req_name):
        from training.controller.AnalysisBackgroundProcess import analysis_training_process
        if file_path:
            file_list = str(file_path).split('/')
            extension = list(str(file_list[-1]).split('.'))[-1]
            copyfile(file_path, 'media/training/' + str(file_list[-1]))

            file_obj = FileDetails.objects.create(
                file_name=str(file_list[-1]),
                file_type=extension,
                file_size=Path(file_path).stat().st_size,
                file_path='media/training',
                status_id=1,
                created_by=1
            )
            file_obj.save()
            file_data_obj = FileDetails.objects.filter(file_id=file_obj.file_id)
            file_serializer = FileDetailsSerializer(file_data_obj, many=True)

            training_name_list = str(file_list[-1]).split('_')
            name = list(str(training_name_list[-1]).split('.'))[-0]
            training_name_list.pop()
            training_name_list.pop(0)
            training_name = " ".join(training_name_list)
            training_name = training_name + ' ' + name + ' ' + str(analysis_request_id)

            training_obj = TrainingDetails.objects.create(
                training_name=str(training_name).title(),
                file=file_serializer.data,
                client_id=settings.CLIENT_ID,
                project_id=settings.PROJECT_ID,
                request_type='Analysis',
                status_id=StatusmasterDetails.objects.get(status_name='New'),
                created_by='System',
                analysis_request_id=analysis_request_id
            )
            training_obj.save()

            with open(file_path, encoding='utf-8') as csvf:
                csvReader = csv.DictReader(csvf)

                for rows in csvReader:
                    TextMasterHistory.objects.create(
                        file_id=file_obj,
                        client_id=settings.CLIENT_ID,
                        project_id=settings.PROJECT_ID,
                        text=rows['content'],
                        status_id=1,
                        created_by=1,
                        text_reference_id=rows['id']
                    ).save()
            log.info('analysis_training_process for {}'.format(req_name))
            analysis_training_process(training_id=training_obj.classification_training_id, json_data='', user=1,
                                      host='', request=request, req_name=req_name,file_path=file_path)
        else:
            raise "No file path"

    def hit_text_analysis(self,text_analysis_path,request,analysis_settings,analysis_request_id):
        intent_entity_flag = True
        file_url = settings.APP_URL+'/'+text_analysis_path
        algorithm_detail = request['ml_algorithm_detail']
        algorithm_name = algorithm_detail['ml_algorithm_name'] if 'ml_algorithm_detail' in request else ''
        algorithm_name = algorithm_name.upper()
        log.info('algorithm_name {}'.format(algorithm_name))
        common = TrainingCommonController()
        if algorithm_name in ['UNSUPERVISED LEARNING', 'UNSUPERVISED_LEARNING']:
            log.info("Calling clustering Extraction")
            # if file_url != '':
                # common.call_clustering_api(file_url,analysis_request_id)
            # else:
            #     log.info("Unsupervised File url not set")
            classification_payload = {
                "topic_id":"unsupervised_classification",
                "training_file": file_url.replace('/media/','/static/'),
                "callback": settings.HIERARCHICAL_CLUSTERING_CALLBACK_URL,
                "reference_id": analysis_request_id,
                "num_iclusters": 10,
                "nlp_request": request,
                "db_info":analysis_settings                
            }
        elif algorithm_name in ['SUPERVISED LEARNING', 'SUPERVISED_LEARNING'] and algorithm_detail['model_name'] != '':
            log.info("Calling Supervised Classification Extraction")
            model_name = algorithm_detail['model_name']
            # if file_url != '':
            #     _response = common.call_supervised_process_classification(file_url, analysis_request_id, model_name,request,analysis_settings)
            # else:
            #     log.info("File url not set")

            classification_payload = {
                "topic_id": "supervised_classification",
                "file_url": file_url.replace('/media/','/static/'),
                "callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
                "reference_id": analysis_request_id,
                "model_name": model_name,
                "nlp_request": request,
                "db_info":analysis_settings
            }

        elif algorithm_name in ['AUTO CLASSIFICATION', 'AUTO_CLASSIFICATION']:
            intent_entity_flag = False
            # if file_url != '':
            #     common.call_auto_unsupervised_classification(file_url, analysis_request_id,request)
            # else:
            #     log.info("File url not set")
            classification_payload = {
                "topic_id": "auto_classification",
                "file_url": file_url.replace('/media/','/static/'),
                "classification_callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
                "intent_entity_callback_url": "{}{}".format(settings.APP_URL,
                                                            "/analysis/cluster/intent_entity/callback/"),
                "reference_id": analysis_request_id,
                "nlp_request": request,
                "db_info":analysis_settings
            }

            final_payload = {
               'classification_payload':classification_payload,
               'intent_payload':{}
           }

        elif algorithm_name in ['ZEROSHOT PYTORCH', 'ZEROSHOT_PYTORCH']:
            log.info("Calling Pytorch Zeroshot Text Classification Extraction")
            labels = request['ml_algorithm_detail']['label'] if 'label' in request['ml_algorithm_detail'] else [
                "others", "access issue",
                "approval issue",
                "booking issue",
                "invoice issue",
                "process issue",
                "quote issue",
                "payment issue"]

            classification_payload = {
                "topic_id": "pytorch_zeroshot_classification",
                "file_url": file_url.replace('/media/','/static/'),
                "callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
                "reference_id": analysis_request_id,
                "labels": labels,
                "nlp_request":request,
                "db_info":analysis_settings
            }            

        else:
            log.info("Calling Zeroshot Text Classification Extraction")
            # if file_url != '':
            #     labels = request['ml_algorithm_detail']['label'] if 'label' in request['ml_algorithm_detail'] else ["others", "access issue",
            #                                                                                  "approval issue",
            #                                                                                  "booking issue",
            #                                                                                  "invoice issue",
            #                                                                                  "process issue",
            #                                                                                  "quote issue",
            #                                                                                  "payment issue"]
            #     _response = common.call_process_classification(file_url, labels, analysis_request_id,request,analysis_settings)
            # else:
            #     log.info("File url not set")
            labels = request['ml_algorithm_detail']['label'] if 'label' in request['ml_algorithm_detail'] else ["others", "access issue",
                                                                                         "approval issue",
                                                                                         "booking issue",
                                                                                         "invoice issue",
                                                                                         "process issue",
                                                                                         "quote issue",
                                                                                         "payment issue"]
            classification_payload = {
                "topic_id": "zeroshot_classification",
                "file_url": file_url.replace('/media/','/static/'),
                "callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
                "reference_id": analysis_request_id,
                "labels": labels,
                "nlp_request":request,
                "db_info":analysis_settings
            }
        # if file_url != '' and intent_entity_flag:
        #     log.info("Calling Intent Extraction")
            # _response = common.call_process_intent_entity(file_url, analysis_request_id,request,analysis_settings)
        # if intent_entity_flag:

        #model_name = algorithm_detail['model_name']

        #classification_payload = {
        #    "topic_id": "supervised_classification",
        #    "file_url": file_url.replace('/media/','/static/'),
        #    "callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
        #    "reference_id": analysis_request_id,
        #    "model_name": "lexmark_model",
        #    "nlp_request": request,
        #    "db_info": analysis_settings
        #}

        if intent_entity_flag:

            intent_entity_payload = {
                "file_url": file_url.replace('/media/','/static/'),
                "callback_url": "{}{}".format(settings.APP_URL, "/analysis/cluster/intent_entity/callback/"),
                "reference_id": analysis_request_id,
                "entity_model": "general_model",#"MORGAN_STANLEE_MODEL",
                "nlp_request":request,
               "db_info":analysis_settings
            }

            final_payload = {
               'classification_payload':classification_payload,
               'intent_payload':intent_entity_payload
           }
        log.info('final_payload - {}'.format(final_payload))
        #response = requests.post('http://10.10.50.36:8005/topic')
        pro = settings.PRODUCER
        pro.send("testtopic5", {"request_data": final_payload})
        #time.sleep(1)
        #pro.close()
        pro.flush()
        log.info('producer sent data successfully')
        # log.info("intent_entity_process - status code {}".format(response.status_code))
        # if response.status_code == 200:
        #     log.info("intent_entity_process request passed")
        #     return response.json()

    def hit_sentiment_analysis(self,sentiment_path,request,analysis_settings,analysis_request_id):
        file_url = settings.APP_URL + '/' + sentiment_path

        sentiment_analysis_payload = {
            "file_url": file_url.replace('/media/', '/static/'),
            "callback_url": settings.HIERARCHICAL_CLUSTERING_CALLBACK_URL,
            "reference_id": analysis_request_id,
            "column_name": "content",
            "nlp_request": request,
           "db_info": analysis_settings
        }
        log.info('sentiment_analysis_payload {}'.format(sentiment_analysis_payload))
        response = requests.post(
            settings.SENTIMENT_ANALYSIS_URL,
            json=sentiment_analysis_payload)
        log.info('sentiment response {}'.format(response))

    def hit_summarization(self,summarization_path,request,analysis_settings,analysis_request_id):
        file_url = settings.APP_URL + '/' + summarization_path
        log.info(file_url)
        log.info(request)
        log.info(analysis_settings)
        log.info(analysis_request_id)
        print(file_url)
        print(request)
        print(analysis_settings)
        print(analysis_request_id)
        pass

        # sentiment_analysis_payload = {
        #     "file_url": file_url.replace('/media/', '/static/'),
        #     "callback_url": settings.HIERARCHICAL_CLUSTERING_CALLBACK_URL,
        #     "reference_id": analysis_request_id,
        #     "column_name": "content",
        #     "nlp_request": request,
        #    "db_info": analysis_settings
        # }
        # log.info('sentiment_analysis_payload {}'.format(sentiment_analysis_payload))
        # response = requests.post(
        #     settings.SENTIMENT_ANALYSIS_URL,
        #     json=sentiment_analysis_payload)
        # log.info('sentiment response {}'.format(response))

    def send_file_to_analysis(self, data_path, analysis_request_id, request,analysis_settings):
        print("summarization coming to send_file_to_analysis")
        try:
            text_analysis_path = data_path['text_analysis_path']
            sentiment_path = data_path['sentiment_analysis_path']
            predictive_path = data_path['predictive_analysis_path']
            summarization_path = data_path['summarization_path']
            if text_analysis_path:
                log.info('text analysis analysis started')
                self.hit_text_analysis(text_analysis_path,request,analysis_settings,analysis_request_id)
                # self.handle_file_master(file_path,analysis_request_id, request,'text_analysis',analysis_settings)
            if sentiment_path:
                log.info('sentiment analysis started')
                self.hit_sentiment_analysis(sentiment_path,request,analysis_settings,analysis_request_id)
                # hit_sentiment_analysis()
                # self.handle_file_master(sentiment_path,analysis_request_id, request,'sentiment_analysis')
            if summarization_path:
                print("summarization analysis started")
                log.info('sentiment analysis started')
                self.hit_summarization(summarization_path,request,analysis_settings,analysis_request_id)
                #########

            if predictive_path:
                log.info('predictive analysis started')
                # hit_predictive_analysis()
                # self.handle_file_master(predictive_path,analysis_request_id, request,'predictive_analysis')

        except Exception as e:
            log.error(e)
            raise e


    def check_for_callback(self, analysis_request_id, training_id=0):
        try:
            if analysis_request_id:
                # Get analysis request data
                anaysis_data = AnalysisRequest.objects.get(analysis_request_id=analysis_request_id)
                analysis_seralizer = AnalysisRequestViewSerializer(anaysis_data)
                analysis = analysis_seralizer.data

                if analysis:
                    analysis_count = 0
                    completed_count = 0
                    for data in analysis['analysis_reference']:
                        analysis_count += 1
                        if str(analysis['analysis_reference'][data]['status']).lower() == 'completed':
                            completed_count += 1

                    if analysis_count == completed_count and completed_count != 0:
                        if analysis['analysis_request']['callback_url']:
                            self.init_call_back(training_id, analysis)

                        # Updating analysis request status to complete
                        log.info("Updating analysis request status to complete for {}".format(analysis_request_id))
                        AnalysisRequest.objects.filter(analysis_request_id=analysis_request_id).update(
                            status='Completed')

                        # Updating classification training status to complete
                        log.info("Updating classification training status to complete for {}".format(training_id))
                        TrainingDetails.objects.filter(classification_training_id=training_id).update(status_id=3)

                        log.info("Analysis request id {} is completed".format(str(analysis_request_id)))
                    else:
                        log.info("Analysis request id {} is incomplete".format(str(analysis_request_id)))

        except Exception as e:
            log.error(e)
            raise e

    def init_call_back(self, training_id, analysis):
        try:
            log.info("Calling callback {}".format(analysis['analysis_request']['callback_url']))

            callback_response = analysis['analysis_request']
            callback_response['training_id'] = training_id

            log.info(callback_response)

            response = requests.post(
                url=analysis['analysis_request']['callback_url'],
                json={"error": False, "message": "sucess", "status": 200, "data": callback_response},
                verify=False
            )

            log.info(response.content)
        except Exception as e:
            log.error(e)


    def process_intent_entity_callback(self, training_id, file_url):
        try:
            # Get training details by its training_id
            training_query_set = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(training_query_set)
            if training_serializer.data:
                # Calling function to download a file
                file_path = self.download_file_from_url(file_url)
                log.info(file_path)
                # Read file, if exists
                if os.path.exists(file_path):
                    with open(file_path, encoding='utf-8') as csvf:
                        csvReader = csv.DictReader(csvf)

                        # Iterate each row of a CSV file
                        for rows in csvReader:

                            if rows['intent'] and rows['entity']:
                                text_query_set = TextMasterDetails.objects.filter(text_id=rows['id'])
                                text_serializer = TextMasterSerializer(text_query_set, many=True)
                                # Update text_master
                                #log.info("Predicted class {} for text id {}".format(rows['classes'], rows['id']))
                                # text_query_set.update(intent=rows['intent'], entities=rows['entity'])
                                text_query_set.update(intent=eval(rows['intent']), entities=eval(rows['entity']))

                else:
                    raise "File not found " + str(file_path)

                if training_serializer.data['analysis_request_id']:
                    # Updating classification result to reference table
                    training_common = TrainingCommonController()
                    training_common.update_reference_data(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        file_id=training_serializer.data['file'][0]['file_id'],
                        type='intent'
                    )

                    # Update reference table classification status
                    training_common.update_analysis_request(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        key='intent',
                        json_data={"status": "Completed"}
                    )

                    log.info("Calling callback and status check modules")
                    self.check_for_callback(training_serializer.data['analysis_request_id'], training_id)

        except Exception as e:
            raise e

    def process_sentiment_analysis_callback(self, training_id, file_url):
        try:
            # Get training details by its training_id
            training_query_set = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(training_query_set)
            if training_serializer.data:
                # Calling function to download a file
                file_path = self.download_file_from_url(file_url)
                log.info(file_path)
                # Read file, if exists
                if os.path.exists(file_path):
                    with open(file_path, encoding='utf-8') as csvf:
                        csvReader = csv.DictReader(csvf)

                        # Iterate each row of a CSV file
                        for rows in csvReader:

                            if rows['Label']:
                                text_query_set = TextMasterDetails.objects.filter(text_id=rows['id'])
                                text_serializer = TextMasterSerializer(text_query_set, many=True)
                                # Update text_master
                                # log.info("Predicted class {} for text id {}".format(rows['classes'], rows['id']))
                                # text_query_set.update(intent=rows['intent'], entities=rows['entity'])
                                text_query_set.update(sentiment=rows['Label'])
                            else:
                                log.info('label not present in the excel so cant able to update sentiment analysis')

                else:
                    raise "File not found " + str(file_path)
                if training_serializer.data['analysis_request_id']:
                    # Updating classification result to reference table
                    training_common = TrainingCommonController()
                    training_common.update_reference_data(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        file_id=training_serializer.data['file'][0]['file_id'],
                        type='sentiment'
                    )

                    # Update reference table classification status
                    training_common.update_analysis_request(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        key='intent',
                        json_data={"status": "Completed"}
                    )

                    log.info("Calling callback and status check modules")
                    self.check_for_callback(training_serializer.data['analysis_request_id'], training_id)

        except Exception as e:
            raise e

    def process_predictive_analysis_callback(self, training_id, file_url):
        try:
            # Get training details by its training_id
            training_query_set = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(training_query_set)
            if training_serializer.data:
                # Calling function to download a file
                file_path = self.download_file_from_url(file_url)
                log.info(file_path)
                # Read file, if exists
                if os.path.exists(file_path):
                    with open(file_path, encoding='utf-8') as csvf:
                        csvReader = csv.DictReader(csvf)

                        # Iterate each row of a CSV file
                        for rows in csvReader:

                            if rows['label']:
                                text_query_set = TextMasterDetails.objects.filter(text_id=rows['id'])
                                text_serializer = TextMasterSerializer(text_query_set, many=True)
                                # Update text_master
                                # log.info("Predicted class {} for text id {}".format(rows['classes'], rows['id']))
                                # text_query_set.update(intent=rows['intent'], entities=rows['entity'])
                                text_query_set.update(predictive=rows['label'])
                            else:
                                log.info('label not present in the excel so cant able to update sentiment analysis')

                else:
                    raise "File not found " + str(file_path)
                if training_serializer.data['analysis_request_id']:
                    # Updating classification result to reference table
                    training_common = TrainingCommonController()
                    training_common.update_reference_data(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        file_id=training_serializer.data['file'][0]['file_id'],
                        type='predictive'
                    )

                    # Update reference table classification status
                    training_common.update_analysis_request(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        key='intent',
                        json_data={"status": "Completed"}
                    )

                    log.info("Calling callback and status check modules")
                    self.check_for_callback(training_serializer.data['analysis_request_id'], training_id)

        except Exception as e:
            raise e

    def process_clustr_classification_callback(self, training_id, file_url):
        try:
            # Get training details by its training_id
            training_query_set = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(training_query_set)
            if training_serializer.data:
                # Calling function to download a file
                file_path = self.download_file_from_url(file_url)
                log.info(file_path)
                # Read file, if exists
                if os.path.exists(file_path):
                    with open(file_path, encoding='utf-8') as csvf:
                        csvReader = csv.DictReader(csvf)

                        # Iterate each row of a CSV file
                        for rows in csvReader:

                            if rows['classes']:
                                text_query_set = TextMasterDetails.objects.filter(text_id=rows['id'])
                                text_serializer = TextMasterSerializer(text_query_set, many=True)

                                # Update text_master
                                log.info("Predicted class {} for text id {}".format(rows['classes'], rows['id']))
                                text_query_set.update(classification=list(rows['classes'].split(',')))

                                self.update_analysis_solution_details(rows['id'],
                                                                      training_serializer.data['analysis_request_id'])
                else:
                    raise "File not found " + str(file_path)

                if training_serializer.data['analysis_request_id']:
                    # Updating classification result to reference table
                    training_common = TrainingCommonController()
                    training_common.update_reference_data(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        file_id=training_serializer.data['file'][0]['file_id'],
                        type='classification'
                    )

                    # Update reference table classification status
                    training_common.update_analysis_request(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        key='classification',
                        json_data={"classification_training_id": 0, "status": "Completed", "model_path": ""}
                    )

                    log.info("Calling callback and status check modules")
                    self.check_for_callback(training_serializer.data['analysis_request_id'], training_id)

        except Exception as e:
            raise e

    def download_file_from_url(self, file_url):
        try:
            # Download response file by file url
            response = requests.get(file_url, verify=False)

            if response:
                log.info(response)
                # Creat dir if not exists
                file_dir = settings.MEDIA_ROOT + '/output_file'

                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)

                # Create filename from the url
                filename = list(str(file_url).split('/'))[-1]

                # Create file path to save file
                filepath = settings.MEDIA_ROOT + '/output_file/' + filename

                # Write response content into file_path
                with open(filepath, "wb") as file:
                    file.write(response.content)
                    file.close()
                return filepath
            return False
        except Exception as e:
            log.info('csv download failed')
            raise e

    def process_hierarchical_clustering_callback(self, training_id, file_url):
        try:
            # Get training details by its training_id
            training_query_set = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(training_query_set)
            if training_serializer.data:
                # Calling function to download a file
                file_path = self.download_file_from_url(file_url)
                log.info(file_path)
                # Read file, if exists
                if os.path.exists(file_path):
                    with open(file_path, encoding='utf-8') as csvf:
                        csvReader = csv.DictReader(csvf)

                        # Iterate each row of a CSV file
                        for rows in csvReader:

                            if rows['classes']:
                                text_query_set = TextMasterDetails.objects.filter(text_id=rows['id'])
                                text_serializer = TextMasterSerializer(text_query_set, many=True)

                                # Update text_master
                                log.info("Predicted class {} for text id {}".format(str(int(float(rows['classes']))), rows['id']))
                                text_query_set.update(hierarchy=str(int(float(rows['classes']))))

                                self.update_analysis_solution_details(rows['id'],
                                                                      training_serializer.data['analysis_request_id'])
                else:
                    raise "File not found " + str(file_path)

                if training_serializer.data['analysis_request_id']:
                    # Updating classification result to reference table
                    training_common = TrainingCommonController()
                    training_common.update_reference_data(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        file_id=training_serializer.data['file'][0]['file_id'],
                        type='hierarchy'
                    )

                    # Update reference table classification status
                    training_common.update_analysis_request(
                        analysis_request_id=training_serializer.data['analysis_request_id'],
                        key='hierarchy',
                        json_data={"training_id": 0, "status": "Completed", "model_path": ""}
                    )

                    log.info("Calling callback and status check modules")
                    self.check_for_callback(training_serializer.data['analysis_request_id'], training_id)

        except Exception as e:
            raise e

    def updateSolutionMapping(self, text_id, mapping_id, analysis_request_id):
        try:
            if text_id:
                idList = [mapping_id]
                # Get mapping Ids in Text maaster.
                textMasterResponse = TextMasterDetails.objects.values_list('solution_mapping_id').filter(
                    text_id=int(text_id))
                if (textMasterResponse[0] != None):
                    print(textMasterResponse[0][0])
                    if (type(textMasterResponse[0][0]) == list):
                        # Extend Mapping ID.
                        idList.extend(textMasterResponse[0][0])
                textMasterResponse.update(solution_mapping_id=idList)
                self.update_analysis_solution_details(text_id, analysis_request_id, 'app')
                print("Update COMPLTED")
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def deleteSolutionMapping(self, text_id, mapping_id, analysis_request_id):
        try:
            if text_id and mapping_id:
                textMasterResponse = TextMasterDetails.objects.values_list('solution_mapping_id').filter(
                    text_id=int(text_id))
                if (textMasterResponse[0] != None):
                    if (type(textMasterResponse[0][0]) == list):
                        # Remove Mapping ID.
                        finalList = textMasterResponse[0][0]
                        finalList.remove(int(mapping_id))
                textMasterResponse.update(solution_mapping_id=finalList)
                self.update_analysis_solution_details(text_id, analysis_request_id)
                print("Remove COMPLTED")
                return True
            return False
        except Exception as e:
            print(e)
            return False

    def getSolutionMappingList(self, text_id):
        try:
            if text_id:
                textMasterResponse = TextMasterDetails.objects.values_list('solution_mapping_id').filter(
                    text_id=int(text_id))
                print(textMasterResponse)
                if (textMasterResponse[0] != None):
                    return list(textMasterResponse[0][0])
            return False
        except Exception as e:
            print(e)
            return False

    def update_analysis_solution_details(self, text_id, analysis_request_id=0, type='bg'):
        print(text_id, analysis_request_id)
        con = None
        solution_data = ''
        try:
            if analysis_request_id:
                query_set = TextMasterDetails.objects.get(text_id=text_id)
                text_serializer = TextMasterSerializer(query_set)

                if text_serializer.data:
                    train = TrainingDetails.objects.get(file__0__file_id=text_serializer.data['file_id'],
                                                        nlp_training_id=0)
                    training_serializer = ClassificationSerializer(train)
                    training_data = training_serializer.data
                    log.info(training_data)

                    solution_query_set = AnalysisRequestSolution.objects.filter(
                        solution_master_id__in=text_serializer.data['solution_mapping_id'])
                    solution_serializer = AnalysisRequestSolutionInsertSerializer(solution_query_set, many=True)

                    if solution_serializer.data:
                        solution_data = []
                        for s_data in solution_serializer.data:
                            solution_data.append(str(s_data['solution_text']).replace("'", ""))

                        log.info(solution_data)
                        anaysis_data = AnalysisRequest.objects.get(analysis_request_id=analysis_request_id)
                        analysis_seralizer = AnalysisRequestViewSerializer(anaysis_data)
                        analysis = analysis_seralizer.data

                        analysis_setting = AnalysisRequestSetting.objects.get(
                            analysis_request_setting_id=analysis['analysis_request_setting_id'])
                        analysis_setting_serializer = AnalysisRequestSettingViewSerializer(analysis_setting)
                        analysis_setting = analysis_setting_serializer.data

                        if analysis_setting['extras']:
                            con = psycopg2.connect(
                                database=analysis_setting['extras'][0]['database']['database'],
                                user=analysis_setting['extras'][0]['database']['username'],
                                password=analysis_setting['extras'][0]['database']['password'],
                                port=analysis_setting['extras'][0]['database']['port'],
                                host=analysis_setting['extras'][0]['database']['hostname']
                            )
                            cur = con.cursor()
                            log.info("Updating solution value")
                            sql = "Update {}.{} set ml_solutions='{}' WHERE analysis_unique_id={}".format(
                                analysis_setting['extras'][0]['database']['schema'],
                                analysis['analysis_request']['table_name'],
                                json.dumps(solution_data),
                                text_serializer.data['text_reference_id']
                            )

                            log.info(sql)
                            cur.execute(sql)
                            con.commit()

                            if type == 'app':
                                self.init_call_back(training_data['classification_training_id'], analysis)

        except psycopg2.DatabaseError as e:
            log.error(e)
            raise e
        except Exception as e:
            log.error(e)
            raise e
        finally:
            if con:
                con.close()
