'''Import system modules'''
import logging

""" Import Django libraries """
from django.conf import settings
from django.utils import timezone

'''Import Django third party libraries'''
from background_task import background

"""Import application related modules"""
from analysis_request.controller.common_controller import CommonController

# Get an instance of a logging
log = logging.getLogger(__name__)

@background(schedule=timezone.now())
def intent_entity_callback(training_id, file_url):
    try:
        common = CommonController()
        common.process_intent_entity_callback(
            training_id= training_id,
            file_url= file_url
        )
    except Exception as e:
        log.error(e)
        raise e

@background(schedule=timezone.now())
def sentiment_analysis_callback(training_id, file_url):
    try:
        common = CommonController()
        common.process_sentiment_analysis_callback(
            training_id= training_id,
            file_url= file_url
        )
    except Exception as e:
        log.error(e)
        raise e

@background(schedule=timezone.now())
def predictive_analysis_callback(training_id, file_url):
    try:
        common = CommonController()
        common.process_predictive_analysis_callback(
            training_id= training_id,
            file_url= file_url
        )
    except Exception as e:
        log.error(e)
        raise e

@background(schedule=timezone.now())
def classification_callback(training_id, file_url):
    try:
        common = CommonController()
        common.process_clustr_classification_callback(
            training_id= training_id,
            file_url= file_url
        )
    except Exception as e:
        log.error(e)
        raise e

@background(schedule=timezone.now())
def hierarchical_clustering_callback(training_id, file_url):
    try:
        common = CommonController()
        common.process_hierarchical_clustering_callback(
            training_id= training_id,
            file_url= file_url
        )
    except Exception as e:
        log.error(e)
        raise e
