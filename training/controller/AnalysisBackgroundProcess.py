'''Import System Modules'''
import csv
import json
import logging

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
from training.controller.Analysis_request_type_handler import text_analysis_process,sentiment_analysis_process,predictive_analysis_process

# Get an instance of a logging
log = logging.getLogger(__name__)


@background(schedule=timezone.now())
def analysis_training_process(training_id, json_data, user, host='', request='',req_name='',file_path=''):
    if req_name=='text_analysis':
        # if 'text_analysis' in request['request_type']:
            text_analysis_process(training_id, request)
    elif req_name=='sentiment_analysis':
        # if 'sentiment_analysis' in request['request_type']:
            sentiment_analysis_process(training_id, request)
    elif req_name=='predictive_analysis':
            log.info('predictive analysis processing')
            predictive_analysis_process(training_id, request,file_path)
    else:
        raise Exception('request type not present in the given request')

