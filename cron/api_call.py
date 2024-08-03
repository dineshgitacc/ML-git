import logging
import requests
from django_cron import CronJobBase, Schedule
from django.conf import settings
from training.models import FileDetails, TrainingDetails, ModelDetails

from analysis_request.controller.background.retrain import check_retrain_completion

logger = logging.getLogger()

class ProcessingRequestCronJob(CronJobBase):
    try:
        RUN_EVERY_MINS = settings.PROCESSING_REQUEST_TIME  # every 10 minute
        schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
        code = 'cron.api_call.ProcessingRequestCronJob'  # a unique code

        def do(self):
            try:
                processing_status = TrainingDetails.objects.filter(status_id=2) # processing
                for status in processing_status:
                    status_save = TrainingDetails.objects.filter(classification_training_id=status.classification_training_id)
                    model_status_save = ModelDetails.objects.filter(classification_training_id=status.classification_training_id,is_default=1)
                    post_data = {"training_master_id":status.nlp_training_id}

                    classification_server = settings.CLASSIFICATION_SERVER+'training_details'
                    r = requests.post(classification_server, data=post_data)
                    if r:
                        result_json = r.json()
                        logger.info("Text classification pending response {} for training_id {}".format(result_json, status.classification_training_id))
                        if 'error' in result_json:
                            if (result_json["error"] == False):

                                model_status_save.update(nlp_model_id=result_json["result"]["model_details"]["model_master_id"])
                                model_status_save.update(data=result_json["result"])
                                accuracy = result_json["result"]["model_details"]["result"]["validation_score"]
                                model_status_save.update(accuracy=accuracy)

                                if (result_json["result"]["status_master"] == 5):
                                    status_save.update(status_id=3) # completed
                                    model_status_save.update(status_id=3) # completed
                                elif (result_json["result"]["status_master"] == 6):
                                    status_save.update(status_id=4) # failed
                                    model_status_save.update(status_id=4) # failed
                                else:
                                    pass
            except Exception as e:
                logger.error("Exception in pending_request : {}".format(str(e)))
    except Exception as e:
        logger.error("Error occurred : {}".format(str(e)))

class AnalysisRetrainRequestClassificationCronJob(CronJobBase):
    try:
        RUN_EVERY_MINS = settings.PROCESSING_REQUEST_TIME  # every 10 minute
        schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
        code = 'cron.api_call.AnalysisRetrainRequestClassificationCronJob'  # a unique code

        def do(self):
            try:
                processing_status = TrainingDetails.objects.filter(status_id=9) # processing
                for status in processing_status:
                    post_data = {"training_master_id":status.classification_model['training_master_id']}

                    classification_server = settings.CLASSIFICATION_SERVER+'training_details'
                    r = requests.post(classification_server, data=post_data)
                    if r:
                        result_json = r.json()
                        if 'error' in result_json:
                            if (result_json["error"] == False):
                                 TrainingDetails.objects.filter(
                                    classification_training_id=status.classification_training_id
                                ).update(
                                    status_id=3,
                                    classification_model=result_json['result']
                                )
                                check_retrain_completion(status.training_id)
            except Exception as e:
                logger.error("Exception in pending analysis retrain request : {}".format(str(e)))
    except Exception as e:
        logger.error("Error occurred : {}".format(str(e)))
