'''Import system modules'''
import logging

'''Import Django modules'''
from django.conf import settings
from django.utils import timezone

'''Import Django third party libraries'''
from background_task import background

'''Import application modules'''
from analysis_request.models import AnalysisRequest
# from analysis_request.controller.common_controller import CommonController

# Get an instance of a logging
log = logging.getLogger(__name__)


@background(schedule=timezone.now())
def text_analysis_training_process(analysis_settings, request, analysis_request_id=0):
    print("summarization coming to text_analysis_training_process")
    log.info("summarization coming to text_analysis_training_process")
    try:
        if analysis_settings:
            '''Import application modules'''
            from analysis_request.controller.common_controller import CommonController

            AnalysisRequest.objects.filter(analysis_request_id=analysis_request_id).update(status='Inprogress')

            common = CommonController()
            for data in analysis_settings['analysis_features']:
                data_path = common.connect_data_source(analysis_settings, data['source_type'], request,
                                                       analysis_request_id)
                if data_path:
                    common.send_file_to_analysis(data_path, analysis_request_id, request,analysis_settings)
                    print(data_path)
    except Exception as e:
        log.error(e)
        AnalysisRequest.objects.filter(analysis_request_id=analysis_request_id).update(status='Failed')
        raise e
