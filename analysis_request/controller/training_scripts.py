
import requests
from django.conf import settings
import logging
from rest_framework import status
log = logging.getLogger(__name__)

def verify_and_validate_args(request):
    required_data = ['ml_training_id','ml_training_details_id','training_model_name','algorithm_type','file_path','call_back_url']
    for data in required_data:
        if data not in request.data:
            raise Exception('{} not exist in request'.format(data))

def hit_ml_model_training_api(request):
    try:
        request_data = {
            "ml_training_id" :  request.data['ml_training_id'],
            "ml_training_details_id" : request.data['ml_training_details_id'],
            "training_model_name" : request.data['training_model_name'],
            "algorithm_type" : request.data['algorithm_type'],
            "file_path" : request.data['file_path'],
            "call_back_url" : request.data['call_back_url']
        }

        log.info(request_data)
        ml_model_training_url = "{}{}".format(settings.FAST_API_MODEL_TRAINING,settings.ML_MODEL_TRAINING_URL)
        if settings.FAST_API is None:
            ml_model_training_url = 'http://10.10.50.20:4102/pycaret/training'
        response = requests.post(
            ml_model_training_url,
            json=request_data)
        log.info("ml_model_training - status code {}".format(response.status_code))
        if response.status_code == 200:
            log.info("Supervised Model training request passed")
        return  {"error": False, "message": 'success', 'status': status.HTTP_200_OK}
    except Exception as e:
        log.info(str(e))
        raise Exception('calling supervised training failed')