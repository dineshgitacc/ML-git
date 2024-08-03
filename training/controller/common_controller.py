'''Import System modules'''
import re
import logging
import json
import requests
import psycopg2
import threading
import time
import pandas
from django.http import HttpResponse

'''Import django modules'''
from django.conf import settings

'''Import application modules'''
from training.models import ClassmasterDetails, FileDetails, TextMasterHistory, ModelDetails, TrainingDetails, \
    StatusmasterDetails, TextMasterDetails
from inference.serializers import TextMasterSerializer
from training.serializers import ClassmasterSerializer, DatasetSerializer, ClassificationSerializer, \
    ClassmasterInsertSerializer
from analysis_request.models import AnalysisRequest, AnalysisRequestSetting
from analysis_request.seralizers import AnalysisRequestViewSerializer, AnalysisRequestSettingViewSerializer, \
    AnalysisRequestSolutionInsertSerializer

'''Import background process'''
from training.controller.BackgroundProcess import training_process

# from kafka import KafkaProducer
import json

# Get an instance of a logging
log = logging.getLogger(__name__)

def json_serializer(data):
    return json.dumps(data).encode("utf-8")
# producer=KafkaProducer(bootstrap_servers=['localhost:9092'],
#                    value_serializer=json_serializer)


class CommonController():

    def get_or_create_class(self, classes, user, delimeter=','):
        try:
            # Make class code by removing all special characters
            class_codes = list((re.sub('[\W_]', '', v).lower() for v in classes.split(',')))
            class_names = classes.split(delimeter)
            class_ids = []

            # Get or Create class id based on class code
            for i in range(len(class_codes)):
                if not class_codes[i]:
                    class_codes[i] = 'others'
                    class_names[i] = 'Others'

                classMaster = ClassmasterDetails.objects.filter(class_code=class_codes[i])
                serializer = ClassmasterSerializer(classMaster, many=True)

                if classMaster.count() == 0:
                    # Create new class
                    classmaster_serializer = ClassmasterInsertSerializer(data={
                        "class_name": class_codes[i],
                        "class_code": class_names[i],
                        "status": 1,
                        "created_by": user
                    })
                    if classmaster_serializer.is_valid():
                        master_detail = classmaster_serializer.save()
                        class_ids.append(str(master_detail.class_id))

                else:
                    class_ids.append(str(serializer.data[0].get('class_id')))

            return list(set(class_ids))
        except Exception as e:
            log.error(e)
            raise e

    def add_to_text_master(self, content, user, file_id, classification=None, reference_id=0, solution_map_id=''):
        try:
            text_serializer = TextMasterSerializer(data={
                'text': content,
                'client_id': settings.CLIENT_ID,
                'project_id': settings.PROJECT_ID,
                'status_id': 1,
                'created_by': 1,
                'file_id': file_id,
                'classification': classification,
                'text_reference_id': reference_id,
                'solution_mapping_id': solution_map_id
            })

            if text_serializer.is_valid():
                text_details = text_serializer.save()
            else:
                log.error(text_serializer.errors)
                raise text_serializer.errors
            return text_details
        except Exception as e:
            log.error(e)
            raise e

    def add_to_solution_master(self, text, analysis_request_id):
        try:
            solution_serializer = AnalysisRequestSolutionInsertSerializer(data={
                'solution_text': text,
                'status': 'Active',
                'created_by': 1,
                'analysis_request_id': analysis_request_id
            })

            if solution_serializer.is_valid():
                solution_details = solution_serializer.save()
            else:
                log.error(solution_serializer.errors)
                raise solution_serializer.errors
            return solution_details

        except Exception as e:
            print(e)
            log.error(e)
            # raise e

    def add_to_training_data_set(self, training_id, text_id, user, class_ids=''):
        try:
            dataset_serializer = DatasetSerializer(
                data={
                    'classification_training_id': training_id,
                    'class_id': ','.join(class_ids),
                    'text_id': text_id,
                    'status_id': 1,
                    'created_by': user
                }
            )
            if dataset_serializer.is_valid():
                dataset_serializer.save()
        except Exception as e:
            log.error(e)
            raise e

    def add_to_text_history(self, json_data, user, file_id):
        try:
            file_obj = FileDetails.objects.get(file_id=file_id)
            json_data = json.loads(json_data)
            for row in json_data:
                TextMasterHistory.objects.create(
                    file_id=file_obj,
                    client_id=settings.CLIENT_ID,
                    project_id=settings.PROJECT_ID,
                    text=row['content'],
                    status_id=1,
                    created_by=user
                ).save()
        except Exception as e:
            log.error(e)
            raise e

    def add_to_model_details(self, training_obj, algorithm_id, algorithm_name, algorithm_config, user):
        try:
            ModelDetails.objects.create(
                algorithm_id=algorithm_id,
                classification_training_id=training_obj,
                algorithm_name=algorithm_name,
                algorithm_config=json.dumps(algorithm_config),
                is_default=1,
                status=StatusmasterDetails.objects.get(status_name='New'),
                created_by=user
            ).save()
        except Exception as e:
            log.error(e)
            raise e

    @staticmethod
    def call_process_sentiment_analysis(file_url, reference_id):
        call_back_host = 'http://127.0.0.1:8001' if settings.APP_URL is None else settings.APP_URL
        request_data = {
            "file_url": file_url,
            "callback_url": "{}{}".format(call_back_host, "/analysis/cluster/sentiment_analysis/callback/"),
            "reference_id": reference_id,
            "column_name": "content"
        }
        # "entity_model": "MORGAN_STANLEE_MODEL"
        log.info('sentiment analysis payload {}'.format(request_data))
        sentiment_analysis_url = "{}".format(settings.SENTIMENT_ANALYSIS_URL)
        print('sentiment_analysis url', sentiment_analysis_url)
        # if settings.FAST_API is None:
        #     intent_entity_url = 'http://10.10.50.20:4106/intentner/inference'
        #     log.info("intent_entity_url : {}".format(intent_entity_url))

        response = requests.post(
            sentiment_analysis_url,
            json=request_data)
        log.info("sentiment_analysis - status code {}".format(response.status_code))
        if response.status_code == 200:
            log.info("sentiment_analysis request passed")
            return response.json()

    @staticmethod
    def call_process_predictive_analysis(file_url, reference_id,request):
        predictive_analysis_type = request['predictive_type']
        predictive_analysis_sub_type = request['predictive_analysis_auto_ml_type']
        call_back_host = 'http://127.0.0.1:8001' if settings.APP_URL is None else settings.APP_URL
        if 'manual' in predictive_analysis_type:
            predictive_analysis_url = "{}".format(settings.PREDICTIVE_ANALYSIS_MANUAL_URL)
            request_data = {
                "file_url": file_url,
                "callback_url": "{}{}".format(call_back_host, "/analysis/cluster/predictive_analysis/callback/"),
                "reference_id": reference_id,
                "column_name": request["predictive_content"].split(','),
                "target_name":request['predictive_destination_coloumn']
            }
        else:   #auto
            predictive_analysis_url = 'payload not matched'
            request_data = {}
            if predictive_analysis_sub_type.lower() == 'classification':
                predictive_analysis_url = "{}".format(settings.PREDICTIVE_ANALYSIS_CLASSIFICATION_AUTO_URL)
                request_data = {
                    "file_url": file_url,
                    "callback_url": "{}{}".format(call_back_host, "/analysis/cluster/predictive_analysis/callback/"),
                    "reference_id": reference_id,
                    "target_column": request['predictive_destination_coloumn']
                }

            elif predictive_analysis_sub_type.lower() == 'regression':
                predictive_analysis_url = "{}".format(settings.PREDICTIVE_ANALYSIS_REGRESSION_AUTO_URL)
                request_data = {
                    "file_url": file_url,
                    "callback_url": "{}{}".format(call_back_host, "/analysis/cluster/predictive_analysis/callback/"),
                    "reference_id": reference_id,
                    "target_column": request['predictive_destination_coloumn']
                }

            elif predictive_analysis_sub_type.lower() == 'forecast':
                predictive_analysis_url = "{}".format(settings.PREDICTIVE_ANALYSIS_FORECAST_AUTO_URL)
                request_data = {
                    "file_url": file_url,
                    "callback_url": "{}{}".format(call_back_host, "/analysis/cluster/predictive_analysis/callback/"),
                    "reference_id": reference_id,
                    "target_column": request['predictive_destination_coloumn'],
                    "timeseries_column": request['forecast_date_field']
                }

        # "entity_model": "MORGAN_STANLEE_MODEL"
        log.info('{} predictive analysis payload {}'.format(predictive_analysis_type,request_data))
        log.info('predictive_analysis_url {}'.format(predictive_analysis_url))

        # print('predictive_analysis url', predictive_analysis_url)
        # if settings.FAST_API is None:
        #     intent_entity_url = 'http://10.10.50.20:4106/intentner/inference'
        #     log.info("intent_entity_url : {}".format(intent_entity_url))

        response = requests.post(
            predictive_analysis_url,
            json=request_data)
        log.info("predictive_analysis - status code {}".format(response.status_code))
        if response.status_code == 200:
            log.info("predictive_analysis request passed")
            return response.json()

    @staticmethod
    def call_clustering_api(file_path, reference_id):
        try:
            log.info("Sending file to hierarchical clustering API")
            request_data = {
                "training_file": file_path,
                "callback": settings.HIERARCHICAL_CLUSTERING_CALLBACK_URL,
                "reference_id": reference_id,
                "num_clusters": 10
            }
            log.info(request_data)
            log.info(settings.HIERARCHICAL_CLUSTERING_URL)
            response = requests.post(
                settings.HIERARCHICAL_CLUSTERING_URL,
                json=request_data)

            if response.status_code == 200:
                log.info("Hierarchical clustering request sucess")
                log.info(response.json())
                return response.json()
            else:
                log.info("Hierarchical clustering request failed")
                log.error(response.text)
                return False
        except Exception as e:
            raise e

    @staticmethod
    def call_supervised_process_classification(file_url, reference_id, model_name,request,analysis_settings):
        request_data = {
            "file_url": file_url,
            "callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
            "reference_id": reference_id,
            "model_name": model_name,
            "nlp_request": request,
            "db_info":analysis_settings
        }
        log.info(request_data)

        # supervised_classification_url = "{}{}".format(settings.FAST_API_MODEL_TRAINING, 'pycaret/inference')
        # if settings.FAST_API is None:
        #     supervised_classification_url = 'http://10.10.50.20:4102/pycaret/inference'
        #     # log.info("zero_short_url : {}".format(zero_short_url))
        #
        # response = requests.post(
        #     supervised_classification_url,
        #     json=request_data)
        # log.info("call_process_supervised_classification - status code {}".format(response.status_code))
        # if response.status_code == 200:
        #     log.info("Supervised classification request passed")
        #     return response.json()

    @staticmethod
    def call_process_classification(file_url, labels, reference_id,request,analysis_settings):
        request_data = {
            "file_url": file_url,
            "callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
            "reference_id": reference_id,
            "labels": labels,
            "nlp_request":request,
            "db_info":analysis_settings
        }
        log.info(request_data)
        # producer.send("testtopic5", {"csv_url": file_url})
        # time.sleep(1)
        # zero_short_url = "{}{}".format(settings.FAST_API, 'classification/inference/file')
        # if settings.FAST_API is None:
        #     zero_short_url = 'http://10.10.50.20:4106/classification/inference/file'
        #     # log.info("zero_short_url : {}".format(zero_short_url))
        #
        # response = requests.post(
        #     zero_short_url,
        #     json=request_data)
        # log.info("call_process_classification - status code {}".format(response.status_code))
        # if response.status_code == 200:
        #     log.info("Supervised classification request passed")
        #     return response.json()

    @staticmethod
    def call_auto_unsupervised_classification(file_url, reference_id,request):
        call_back_host = 'http://10.10.50.20:4101' if settings.APP_URL is None else settings.APP_URL
        request_data = {
            "file_url": file_url,
            "classification_callback_url": settings.BERT_UNSUPERVISED_CALLBACK_URL,
            "intent_entity_callback_url": "{}{}".format(call_back_host, "/analysis/cluster/intent_entity/callback/"),
            "reference_id": reference_id,
            "nlp_request":request
        }
        log.info("Auto classification request - {}".format(request_data))
        auto_classification_url = settings.AUTO_UNSUPERVISED_URL
        response = requests.post(
            auto_classification_url,
            json=request_data)
        log.info("call_process_auto_classification - status code {}".format(response.status_code))
        if response.status_code == 200:
            log.info("Auto Unsupervised classification request passed")
            return response.json()

    @staticmethod
    def call_process_intent_entity(file_url, reference_id,request,analysis_settings):
        call_back_host = 'http://10.10.50.20:4101' if settings.APP_URL is None else settings.APP_URL
        request_data = {
            "file_url": file_url,
            "callback_url": "{}{}".format(call_back_host, "/analysis/cluster/intent_entity/callback/"),
            "reference_id": reference_id,
            "entity_model": "general_model",
            "nlp_request":request,
            "db_info":analysis_settings
        }
        # "entity_model": "MORGAN_STANLEE_MODEL"
        log.info(request_data)
        # producer.send("testtopic5", {"request_data": request_data})
        # time.sleep(1)
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        # return HttpResponse(200)
        # print('doneeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        intent_entity_url = "{}{}".format(settings.FAST_API, 'intentner/inference')
        # if settings.FAST_API is None:
        #     intent_entity_url = 'http://10.10.50.20:4106/intentner/inference'
        #     log.info("intent_entity_url : {}".format(intent_entity_url))
        #
        # response = requests.post(
        #     intent_entity_url,
        #     json=request_data)
        # log.info("intent_entity_process - status code {}".format(response.status_code))
        # if response.status_code == 200:
        #     log.info("intent_entity_process request passed")
        #     return response.json()

    @staticmethod
    def get_data_in_file_by_file_id(file_id):
        con = None
        try:
            log.info("Preparing dataset for bert model")
            # Establish database connection
            con = psycopg2.connect(database=settings.DATABASES['default']['NAME'],
                                   user=settings.DATABASES['default']['USER'],
                                   password=settings.DATABASES['default']['PASSWORD'],
                                   port=settings.DATABASES['default']['PORT'],
                                   host=settings.DATABASES['default']['HOST'])
            cur = con.cursor()

            # Query to extract data from table
            query = "SELECT text_id as id,text as content FROM text_master WHERE file_id_id=" + str(file_id)

            # Copy queryset data into CSV
            output_query = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)

            # Write content into CSV and save
            _file_name_str = str(time.time()).replace('.', '')
            filename = "training/" + str(_file_name_str) + ".csv"
            with open(settings.MEDIA_ROOT + '/' + filename, 'w') as f:
                cur.copy_expert(output_query, f)

            output_file = settings.APP_URL + settings.DOWNLOAD_URL + filename
        except Exception as e:
            log.info("Exception : {} ".format(str(e)))
            output_file = ''
        finally:
            if con:
                con.close()

        return output_file

    def call_unsupervised_classification(self, file_id, training_id, analysis_request_id=0):
        con = None
        try:
            log.info("Preparing dataset for bert model")
            # Establish database connection
            con = psycopg2.connect(database=settings.DATABASES['default']['NAME'],
                                   user=settings.DATABASES['default']['USER'],
                                   password=settings.DATABASES['default']['PASSWORD'],
                                   port=settings.DATABASES['default']['PORT'],
                                   host=settings.DATABASES['default']['HOST'])
            cur = con.cursor()

            # Query to extract data from table
            query = "SELECT text_id as id,text as content FROM text_master WHERE file_id_id=" + str(file_id)

            # Copy queryset data into CSV
            outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)

            # Write content into CSV and save
            filename = "training/training_data_set_bert_" + str(training_id) + ".csv"
            with open(settings.MEDIA_ROOT + '/' + filename, 'w') as f:
                cur.copy_expert(outputquery, f)

            log.info("Dataset file created Successfully. File name is " + str(filename))
            self.call_bert_unsupervisied_inference_api(settings.APP_URL + settings.DOWNLOAD_URL + filename, training_id)

            # Update classification id in analysis_request, if so
            if analysis_request_id:
                self.update_analysis_request(
                    analysis_request_id=analysis_request_id,
                    key="classification",
                    json_data={
                        "classification_training_id": 0,
                        "status": 'Inprogress'
                    }
                )

        except psycopg2.DatabaseError as e:
            log.error(e)
            raise e
        except Exception as e:
            log.error(e)
            raise e
        finally:
            if con:
                con.close()
        return False

    def add_supervised_classification(self, training_id, json_data, user, file_id):
        try:
            # Add json data into text_master_history
            self.add_to_text_history(json_data, user, file_id)

            # Get and clone classification_train details to create supervised classification request
            train = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(train)

            # Override neccessary data to make new request
            data = training_serializer.data
            data['classification_training_id'] = None
            data['status_id'] = StatusmasterDetails.objects.get(status_name='New')
            data['request_type'] = "Classification"

            # Create new classification training request
            new_train_obj = TrainingDetails(**data)
            new_train_obj.save()

            # Add algorithm and its config to model_master
            self.add_to_model_details(training_obj=new_train_obj, algorithm_id=settings.DEFAULT_CLASSIFICATION_ID,
                                      algorithm_name=settings.DEFAULT_CLASSIFICATION_ALGORITHM,
                                      algorithm_config=settings.DEFAULT_CLASSIFICATION_ALGORITHM_CONFIG, user=user)

            # Update classification id in analysis_request, if so
            if data['analysis_request_id']:
                self.update_reference_data(data['analysis_request_id'], file_id, 'classification')

                self.update_analysis_request(
                    analysis_request_id=data['analysis_request_id'],
                    key="classification",
                    json_data={
                        "classification_training_id": new_train_obj.classification_training_id,
                        "status": 'Completed'
                    }
                )

            # Call classification training background process
            training_process(new_train_obj.classification_training_id, json_data, user)
        except Exception as e:
            log.error(e)
            raise e

    def thread_call_text_classification_inference_api(self, job_no, text_serializer_data, labels):

        for data in text_serializer_data:
            text_id = data['text_id']
            if job_no != text_id % 5:
                continue
            log.info("processing.....")

            # for idx, text_serializer_data in enumerate(list_of_dfs):
            #     if job_no != idx % 2:
            #         continue

            if True:
                # text_serializer_data.insert(3, "content", text_serializer_data['text'], True)
                # text_serializer_data = text_serializer_data[['text_id', 'content']]

                # allText = text_serializer_data.to_dict(orient='records')
                # data['text'], text_id = data['text_id']
                result = self.call_text_classification_fast_inference_api(text=data['text'], labels=labels)
                if result:
                    if not result['error']:
                        classificationCount = 0
                        for classificationData in result["data"]:
                            classification = ''
                            if classificationData['predicted_class']:
                                classification = [classificationData['predicted_class']]
                            else:
                                classification = ["un-mapped"]
                            TextMasterDetails.objects.filter(text_id=data['text_id']).update(
                                classification=classification)
                            classificationCount += 1
                    else:
                        log.error(result)
            else:
                log.error("serializer data not found")

    """
    Make Intent inference API through thread call - Maximum no.of thread is 5
    """

    def thread_call_intent_api(self, text_serializer_data, job_no):
        for data in text_serializer_data:
            text_id = data['text_id']
            if job_no != text_id % 5:
                continue

            if data['text']:
                result = self.call_intent_inference_api(text=data['text'], text_id=data['text_id'])
                if result:
                    if not result['error']:
                        intent = ''
                        entity = ''
                        if result['result']['intent']:
                            intent = result['result']['intent']
                        else:
                            intent = ["un-mapped"]

                        if result['result']['entity']:
                            entity = result['result']['entity']

                        if intent and entity:
                            TextMasterDetails.objects.filter(text_id=data['text_id']).update(
                                intent=intent,
                                entities=entity
                            )
                        elif intent:
                            TextMasterDetails.objects.filter(text_id=data['text_id']).update(
                                intent=intent
                            )
                        elif entity:
                            TextMasterDetails.objects.filter(text_id=data['text_id']).update(
                                entities=entity
                            )
                    else:
                        log.error(result)

    def call_text_classification(self, training_id, request):
        try:
            # Get and clone classification_train details to create supervised classification request
            train = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(train)

            # Get file_id
            file_id = training_serializer.data['file'][0]['file_id']

            # Get Text data from text_master_history
            query = TextMasterDetails.objects.filter(file_id=file_id)
            text_serializer = TextMasterSerializer(query, many=True)
            # Initialize threading
            split_count = 5
            # df = pandas.DataFrame(text_serializer.data)
            # list_of_dfs = [df.loc[i:i + split_count - 1, :] for i in range(0, len(df), split_count)]

            t1 = threading.Thread(target=self.thread_call_text_classification_inference_api,
                                  args=(0, text_serializer.data, request['labels']))

            t2 = threading.Thread(target=self.thread_call_text_classification_inference_api,
                                  args=(1, text_serializer.data, request['labels']))

            t3 = threading.Thread(target=self.thread_call_text_classification_inference_api,
                                  args=(2, text_serializer.data, request['labels']))

            t4 = threading.Thread(target=self.thread_call_text_classification_inference_api,
                                  args=(3, text_serializer.data, request['labels']))

            t5 = threading.Thread(target=self.thread_call_text_classification_inference_api,
                                  args=(4, text_serializer.data, request['labels']))

            t1.start()
            t2.start()
            t3.start()
            t4.start()
            t5.start()

            t1.join()
            t2.join()
            t3.join()
            t4.join()
            t5.join()

            # Update classification id in analysis_request, if so
            if training_serializer.data['analysis_request_id']:
                log.info("Updating intent data into client table")
                self.update_reference_data(training_serializer.data['analysis_request_id'], file_id, 'classification')
                self.update_analysis_request(
                    analysis_request_id=training_serializer.data['analysis_request_id'],
                    key="classification",
                    json_data={
                        "status": 'Completed'
                    }
                )
        except Exception as e:
            log.error(e)
            raise e

    def call_intent_classification(self, training_id):
        try:
            # Get and clone classification_train details to create supervised classification request
            train = TrainingDetails.objects.get(classification_training_id=training_id)
            training_serializer = ClassificationSerializer(train)

            # Get file_id
            file_id = training_serializer.data['file'][0]['file_id']

            # Get Text data from text_master_history
            query = TextMasterDetails.objects.filter(file_id=file_id)
            text_serializer = TextMasterSerializer(query, many=True)
            # Initialize threading
            t1 = threading.Thread(target=self.thread_call_intent_api, args=(text_serializer.data, 0))
            t2 = threading.Thread(target=self.thread_call_intent_api, args=(text_serializer.data, 1))
            t3 = threading.Thread(target=self.thread_call_intent_api, args=(text_serializer.data, 2))
            t4 = threading.Thread(target=self.thread_call_intent_api, args=(text_serializer.data, 3))
            t5 = threading.Thread(target=self.thread_call_intent_api, args=(text_serializer.data, 4))
            # Start Threading
            t1.start()
            t2.start()
            t3.start()
            t4.start()
            t5.start()
            # Collecting thread response
            t1.join()
            t2.join()
            t3.join()
            t4.join()
            t5.join()

            # Update classification id in analysis_request, if so
            if training_serializer.data['analysis_request_id']:
                log.info("Updating intent data into client table")
                self.update_reference_data(training_serializer.data['analysis_request_id'], file_id, 'intent')

                self.update_analysis_request(
                    analysis_request_id=training_serializer.data['analysis_request_id'],
                    key="intent",
                    json_data={
                        "intent_training_id": 0,
                        "status": 'Completed'
                    }
                )

        except Exception as e:
            log.error(e)
            raise e

    """
    New FAST_API_CLASSIFICATION_INFERENCE called here
    """

    def call_text_classification_fast_inference_api(self, text, labels):
        try:
            if labels:
                labels_data = labels
            else:
                labels_data = [
                    "Others",
                    "access issue",
                    "approval issue",
                    "booking issue",
                    "invoice issue",
                    "process issue",
                    "quote issue",
                    "payment issue"
                ]
            request_data = {
                "summary": {
                    "text_id": "",
                    "content": text
                },
                "labels": labels_data
            }
            url = settings.FAST_API + settings.FAST_API_CLASSIFICATION_INFERENCE
            log.info(url)
            log.info(request_data)
            response = requests.post(
                url,
                json=request_data)
            log.info("calling call_text_classification_inference_api {}".format(url))
            if response.status_code == 200:
                log.info("call_text_classification_inference_api success")
                return response.json()
            else:
                log.info("call_text_classification_inference_api failed")
                log.error(response.text)
                return False
        except Exception as e:
            log.error(e)
            return False

    def call_text_classification_inference_api(self, text):
        try:
            request_data = {
                "ticket_description": [text]
            }
            url = settings.CLASSIFICATION_SERVER + 'intent/inference/lexmark'
            response = requests.post(
                url,
                json=request_data)
            log.info("calling call_text_classification_inference_api {}".format(url))
            if response.status_code == 200:
                log.info("call_text_classification_inference_api success")
                return response.json()
            else:
                log.info("call_text_classification_inference_api failed")
                log.error(response.text)
                return False
        except Exception as e:
            log.error(e)
            return False

    def call_intent_inference_api(self, text, text_id=''):
        try:
            log.info("Calling intent api")
            request_data = {
                "text": text,
                "model_path": settings.DEFAULT_UNSUPERVISED_MODEL
            }

            url = settings.INTENT_CLASSIFICATION_SERVER + 'inference/'
            log.info("Intent url {} : id - {} and its request data {}".format(url, str(text_id), request_data))

            response = requests.post(
                settings.INTENT_CLASSIFICATION_SERVER + 'inference/',
                json=request_data)

            if response.status_code == 200:
                log.info("BERT Intent request sucess")
                return response.json()
            else:
                log.info("BERT Intent request failed")
                log.error(response.text)
                return False
        except Exception as e:
            log.error(e)
            return False

    def call_bert_unsupervisied_inference_api(self, file_path, reference_id=''):
        try:
            log.info("Sending file to bert API")
            request_data = {
                "training_file": file_path,
                "callback": settings.BERT_UNSUPERVISED_CALLBACK_URL,
                "reference_id": reference_id
            }
            log.info(request_data)
            log.info(settings.UNSUPERVISED_CLASSIFICATION_URL)
            response = requests.post(
                settings.UNSUPERVISED_CLASSIFICATION_URL,
                json=request_data)

            if response.status_code == 200:
                log.info("BERT Unsupervised classification request sucess")
                return response.json()
            else:
                log.info("BERT Unsupervised classification request failed")
                log.error(response.text)
                return False
        except Exception as e:
            raise e

    def update_analysis_request(self, analysis_request_id, key, json_data):
        try:
            if analysis_request_id:
                anaysis_data = AnalysisRequest.objects.get(analysis_request_id=analysis_request_id)
                analysis_seralizer = AnalysisRequestViewSerializer(anaysis_data)
                analysis = analysis_seralizer.data

                key = str(key).lower()
                if not analysis['analysis_reference']:
                    analysis['analysis_reference'] = {}
                    analysis['analysis_reference'][key] = json_data
                else:
                    analysis['analysis_reference'][key] = json_data

                AnalysisRequest.objects.filter(
                    analysis_request_id=analysis_request_id
                ).update(
                    analysis_reference=analysis['analysis_reference']
                )
        except Exception as e:
            raise e

    def update_reference_data(self, analysis_request_id, file_id, type):
        con = None
        try:
            if file_id and analysis_request_id:
                # Get text master data
                query_set = TextMasterDetails.objects.filter(file_id=file_id)
                text_serializer = TextMasterSerializer(query_set, many=True)
                if text_serializer.data:
                    # Get analysis request data
                    anaysis_data = AnalysisRequest.objects.get(analysis_request_id=analysis_request_id)
                    analysis_seralizer = AnalysisRequestViewSerializer(anaysis_data)
                    analysis = analysis_seralizer.data

                    analysis_setting = AnalysisRequestSetting.objects.get(
                        analysis_request_setting_id=analysis['analysis_request_setting_id'])
                    analysis_setting_serializer = AnalysisRequestSettingViewSerializer(analysis_setting)
                    analysis_setting = analysis_setting_serializer.data

                    con = psycopg2.connect(
                        database=analysis_setting['extras'][0]['database']['database'],
                        user=analysis_setting['extras'][0]['database']['username'],
                        password=analysis_setting['extras'][0]['database']['password'],
                        port=analysis_setting['extras'][0]['database']['port'],
                        host=analysis_setting['extras'][0]['database']['hostname']
                    )
                    cur = con.cursor()
                    if type == 'intent':
                        for data in text_serializer.data:
                            if data['intent'] or data['entities']:

                                intent = json.dumps(data['intent']) if data['intent'] else {}
                                entity = json.dumps(data['entities']) if data['entities'] else {}

                                if intent and entity:
                                    sql = "Update {}.{} set ml_intent='{}', ml_entity='{}' WHERE analysis_unique_id={}".format(
                                        analysis_setting['extras'][0]['database']['schema'],
                                        analysis['analysis_request']['table_name'],
                                        intent,
                                        entity,
                                        data['text_reference_id']
                                    )
                                elif intent:
                                    sql = "Update {}.{} set ml_intent='{}' WHERE analysis_unique_id={}".format(
                                        analysis_setting['extras'][0]['database']['schema'],
                                        analysis['analysis_request']['table_name'],
                                        intent,
                                        data['text_reference_id']
                                    )
                                elif entity:
                                    sql = "Update {}.{} set ml_entity='{}' WHERE analysis_unique_id={}".format(
                                        analysis_setting['extras'][0]['database']['schema'],
                                        analysis['analysis_request']['table_name'],
                                        entity,
                                        data['text_reference_id']
                                    )
                                log.info(sql)
                                cur.execute(sql)
                                con.commit()
                    elif type == 'classification':
                        for data in text_serializer.data:
                            if data['classification']:
                                sql = "Update {}.{} set ml_classification='{}' WHERE analysis_unique_id={}".format(
                                    analysis_setting['extras'][0]['database']['schema'],
                                    analysis['analysis_request']['table_name'],
                                    json.dumps(data['classification']),
                                    data['text_reference_id']
                                )
                                log.info(sql)
                                cur.execute(sql)
                                con.commit()

                    elif type == 'hierarchy':
                        for data in text_serializer.data:
                            if data['hierarchy']:
                                sql = "Update {}.{} set ml_clusters='{}' WHERE analysis_unique_id={}".format(
                                    analysis_setting['extras'][0]['database']['schema'],
                                    analysis['analysis_request']['table_name'],
                                    json.loads(json.dumps(data['hierarchy'])),
                                    data['text_reference_id']
                                )
                                log.info(sql)
                                cur.execute(sql)
                                con.commit()

                    elif type == 'sentiment':
                        for data in text_serializer.data:
                            # sentiment = json.dumps(data['intent']) if data['intent'] else {}
                            sentiment = str(data['sentiment']) if data['sentiment'] else {}
                            if sentiment:
                                sql = "Update {}.{} set ml_sentiment='{}' WHERE analysis_unique_id={}".format(
                                    analysis_setting['extras'][0]['database']['schema'],
                                    analysis['analysis_request']['table_name'],
                                    sentiment,
                                    data['text_reference_id']
                                )
                                log.info(sql)
                                cur.execute(sql)
                                con.commit()
                        log.info('sentiment analysis updated in superset successfully')

                    elif type=='predictive':
                        for data in text_serializer.data:
                            # sentiment = json.dumps(data['intent']) if data['intent'] else {}
                            sentiment = str(data['predictive']) if data['predictive'] else {}
                            if sentiment:
                                sql = "Update {}.{} set ml_predictive='{}' WHERE analysis_unique_id={}".format(
                                    analysis_setting['extras'][0]['database']['schema'],
                                    analysis['analysis_request']['table_name'],
                                    sentiment,
                                    data['text_reference_id']
                                )
                                log.info(sql)
                                cur.execute(sql)
                                con.commit()
                        log.info('predictive analysis updated in superset successfully')
        except psycopg2.DatabaseError as e:
            log.error(e)
            raise e
        except Exception as e:
            log.error(e)
            raise e
        finally:
            if con:
                con.close()

    def call_hierarchical_clustering(self, file_id, training_id, analysis_request_id=0):
        con = None
        try:
            log.info("Preparing dataset for hierarchical clustering model")
            # Establish database connection
            con = psycopg2.connect(database=settings.DATABASES['default']['NAME'],
                                   user=settings.DATABASES['default']['USER'],
                                   password=settings.DATABASES['default']['PASSWORD'],
                                   port=settings.DATABASES['default']['PORT'],
                                   host=settings.DATABASES['default']['HOST'])
            cur = con.cursor()

            # Query to extract data from table
            query = "SELECT text_id as id,text as content FROM text_master WHERE file_id_id=" + str(file_id)

            # Copy queryset data into CSV
            outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)

            # Write content into CSV and save
            filename = "training/training_data_set_hierarchical_clustering_" + str(training_id) + ".csv"
            with open(settings.MEDIA_ROOT + '/' + filename, 'w') as f:
                cur.copy_expert(outputquery, f)

            log.info("Dataset file created Successfully. File name is " + str(filename))
            self.call_hierarchical_clustering_api(settings.APP_URL + settings.DOWNLOAD_URL + filename, training_id)

            # Update classification id in analysis_request, if so
            if analysis_request_id:
                self.update_analysis_request(
                    analysis_request_id=analysis_request_id,
                    key="hierarchy",
                    json_data={
                        "training_id": 0,
                        "status": 'Inprogress'
                    }
                )

        except psycopg2.DatabaseError as e:
            log.error(e)
            raise e
        except Exception as e:
            log.error(e)
            raise e
        finally:
            if con:
                con.close()
        return False

    def call_hierarchical_clustering_api(self, file_path, reference_id=''):
        try:
            log.info("Sending file to hierarchical clustering API")
            request_data = {
                "training_file": file_path,
                "callback": settings.HIERARCHICAL_CLUSTERING_CALLBACK_URL,
                "reference_id": reference_id
            }
            log.info(request_data)
            log.info(settings.HIERARCHICAL_CLUSTERING_URL)
            response = requests.post(
                settings.HIERARCHICAL_CLUSTERING_URL,
                json=request_data)

            if response.status_code == 200:
                log.info("Hierarchical clustering request sucess")
                log.info(response.json())
                return response.json()
            else:
                log.info("Hierarchical clustering request failed")
                log.error(response.text)
                return False
        except Exception as e:
            raise e
