'''Import system modules'''
import json
import logging
import re
from datetime import datetime

""" Import Django libraries """
from django.conf import settings

""" Import rest framework libraries """
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework import status

"""Import application related modules"""
from analysis_request.models import AnalysisRequest, AnalysisRequestSetting, AnalysisRequestSolution
from analysis_request.seralizers import AnalysisRequestSettingViewSerializer, AnalysisRequestSolutionSerializer, \
    AnalysisRequestSolutionListSerializer, AnalysisRequestSolutionMappingListSerializer
from analysis_request.controller.common_controller import CommonController

from analysis_request.controller.background.callback import intent_entity_callback, classification_callback, \
    hierarchical_clustering_callback,sentiment_analysis_callback,predictive_analysis_callback
from analysis_request.controller.background.retrain import check_retrain_completion
from analysis_request.controller.training_scripts import verify_and_validate_args,hit_ml_model_training_api
from training.models import TrainingDetails

# Get an instance of a logging
log = logging.getLogger(__name__)


class AnalysisRequestView(ViewSet):

    def create(self, request):
        log.info("summarization coming")
        print("summarization coming")
        """
        Analysis request create api is used to make new analysis request, this api will
        receive client request information and process based on its requirement defined
        in the table analysis_request_setting.

        Input Json
        =============
            {
                "table_name": ,
                "client_name":,
                "request_type":,
                "callback_url":,
                "reference_id":,
                "content":,
                "category":,
                "resolution":,
            }

        Output Json
        ============
            {
                "table_name": ,
                "client_name":,
                "request_type":,
                "callback_url":,
                "reference_id":,
                "training_id":,
                "content":,
                "category":,
                "resolution":,
            }
        Return a http response
        """
        try:
            # Application sucess content
            if request.data:
                print(request)
                log.info(request)
                if 'client_name' in request.data:
                    client_name = re.sub(' +', ' ', request.data['client_name'])
                    client_name = re.sub('[^A-Za-z0-9 ]+', '', client_name)
                    code = str(client_name).replace(' ', '_')
                    try:
                        settings_data = AnalysisRequestSetting.objects.get(client_code=code, status='Active')
                        setting_serializer = AnalysisRequestSettingViewSerializer(settings_data)
                        if setting_serializer.data:
                            common_obj = CommonController()
                            obj = common_obj.create_analysis_request(request.data, settings_data)
                            common_obj.raise_analysis_request(request.data, setting_serializer.data,
                                                              obj.analysis_request_id)
                            response_content = {"error": False, "message": "Success", "status": 200}
                            return Response(response_content, status=status.HTTP_200_OK)
                        else:
                            return Response({"error": False, "message": 'client information not found', "status": 400},
                                            status=status.HTTP_400_BAD_REQUEST)
                    except AnalysisRequestSetting.DoesNotExist:
                        return Response({"error": False, "message": 'client information not found', "status": 400},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": False, "message": 'Invalid client information', "status": 400},
                                    status=status.HTTP_400_BAD_REQUEST)


            else:
                return Response({"error": False, "message": 'Invalid connection', "status": 400},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Application failure content
            log.error(e)
            return Response({"error": False, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)

    def intent_entity(self, request):
        try:
            log.info("intent_entity callback response. {}".format(request.data))
            if 'output_file' in request.data and 'reference_id' in request.data:
                intent_entity_callback(request.data['reference_id'], request.data['output_file'])
            return Response({"error": False, "message": "sucess", "status": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)

    def sentiment_analysis(self, request):
        try:
            log.info("sentiment_analysis_callback callback response. {}".format(request.data))
            if 'output_file' in request.data and 'reference_id' in request.data:
                sentiment_analysis_callback(request.data['reference_id'], request.data['output_file'])
            return Response({"error": False, "message": "sucess", "status": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)

    def predictive_analysis(self, request):
        try:
            log.info("predictive_analysis callback response. {}".format(request.data))
            if 'output_file' in request.data and 'reference_id' in request.data:
                predictive_analysis_callback(request.data['reference_id'], request.data['output_file'])
            return Response({"error": False, "message": "sucess", "status": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)

    def classification_callback(self, request):
        try:
            log.info("Classification callback response. {}".format(request.data))
            if 'output_file' in request.data and 'reference_id' in request.data:
                classification_callback(request.data['reference_id'], request.data['output_file'])
            return Response({"error": False, "message": "sucess", "status": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)

    def bert_intent_callback(self, request):
        try:
            log.info("Intent callback response. {}".format(request.data))
            train = TrainingDetails.objects.filter(classification_training_id=request.data['reference_id'])
            train.update(intent_model=request.data)
            check_retrain_completion(request.data['reference_id'])
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)

    def hierarchical_clustering_callback(self, request):
        try:
            log.info("Hierarchical clustering callback response. {}".format(request.data))
            if 'output_file' in request.data and 'reference_id' in request.data:
                hierarchical_clustering_callback(request.data['reference_id'], request.data['output_file'])
            return Response({"error": False, "message": "sucess", "status": 200}, status=status.HTTP_200_OK)
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)


class AddSolutionAnalysisRequest(APIView):
    def post(self, request):
        try:
            if "analysis_request_id" and "text_id" and "solution_master_id" in request.data:
                if (int(request.data["solution_master_id"]) == 0):
                    seralizer = AnalysisRequestSolutionSerializer(data=request.data)
                    if (seralizer.is_valid()):
                        seralizer.save(created_by=1, status='Active')
                        # Get Lastest ID.
                        latestId = AnalysisRequestSolution.objects.values_list('solution_master_id').latest(
                            'solution_master_id')
                        # Update Solution Ids in text master table.
                        common_obj = CommonController()
                        common_obj.updateSolutionMapping(text_id=request.data["text_id"], mapping_id=latestId[0],
                                                         analysis_request_id=int(request.data["analysis_request_id"]))
                        return Response(
                            {"error": False, "message": "Data Added", "data": {"solution_master_id": int(latestId[0])},
                             "status": 200})
                    else:
                        return Response({"error": True, "message": seralizer.errors, "status": 400})
                else:
                    # Update Solution Ids in text master table.
                    common_obj = CommonController()
                    common_obj.updateSolutionMapping(text_id=request.data["text_id"],
                                                     mapping_id=int(request.data["solution_master_id"]),
                                                     analysis_request_id=int(request.data["analysis_request_id"]))
                    return Response({"error": False, "message": "Data Added",
                                     "data": {"solution_master_id": request.data["solution_master_id"]}, "status": 200})
            else:
                return Response({"error": True, "message": "Invalid Input Field", "status": 400})

        except KeyError:
            return Response({"error": True, "message": "Invalid Input Field", "status": 400})

        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)


class UpdateSolutionAnalysisRequest(APIView):
    def post(self, request):
        try:
            if "solution_master_id" in request.data:
                response = AnalysisRequestSolution.objects.get(
                    solution_master_id=int(request.data["solution_master_id"]))
                seralizer = AnalysisRequestSolutionSerializer(response, data=request.data)
                if seralizer.is_valid():
                    seralizer.save(updated_by=1, updated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    return Response({"error": False, "message": "Data Updated", "status": 200})
                else:
                    return Response({"error": True, "message": seralizer.errors, "status": 400})
            else:
                return Response({"error": True, "message": "Invalid Input Field", "status": 400})

        except KeyError:
            return Response({"error": True, "message": "Invalid Input Field", "status": 400})

        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)


class DeleteSolutionAnalysisRequest(APIView):
    def post(self, request):
        try:
            if "analysis_request_id" and "text_id" and "remove_mappining_id" in request.data:
                common_obj = CommonController()
                if common_obj.deleteSolutionMapping(text_id=request.data["text_id"],
                                                    mapping_id=request.data["remove_mappining_id"],
                                                    analysis_request_id=request.data["analysis_request_id"]):
                    return Response({"error": False, "message": "Data Removed", "status": 200})
                else:
                    return Response({"error": True, "message": "Something Went Wrong", "status": 400})
            else:
                return Response({"error": True, "message": "Invalid Input Field", "status": 400})

        except KeyError:
            return Response({"error": True, "message": "Invalid Input Field", "status": 400})

        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)


class SolutionAnalysisRequestList(APIView):
    def post(self, request):
        try:
            if "analysis_request_id" in request.data:
                response = AnalysisRequestSolution.objects.filter(
                    analysis_request_id=int(request.data["analysis_request_id"])).order_by("solution_text")
                seralizer = AnalysisRequestSolutionListSerializer(response, many=True)
                return Response({"error": False, "data": seralizer.data, "status": 200})
            else:
                return Response({"error": True, "message": "Invalid Input Field", "status": 400})
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)


class SolutionAnalysisMappingDataList(APIView):
    def post(self, request):
        try:
            if "text_id" in request.data:
                common_obj = CommonController()
                mappingList = common_obj.getSolutionMappingList(text_id=request.data["text_id"])
                response = AnalysisRequestSolution.objects.filter(solution_master_id__in=mappingList)
                seralizer = AnalysisRequestSolutionMappingListSerializer(response, many=True)
                return Response({"error": False, "data": seralizer.data, "status": 200})
            else:
                return Response({"error": True, "message": "Invalid Input Field", "status": 400})
        except Exception as e:
            log.error(e)
            return Response({"error": True, "message": str(e), "status": 400}, status=status.HTTP_400_BAD_REQUEST)



class SupervisedModelTraining(APIView):
    def post(self,request):
        try:
            verify_and_validate_args(request)
            result = hit_ml_model_training_api(request)
        except Exception as e:
            result = {"error": True, "message": str(e), 'status': status.HTTP_400_BAD_REQUEST}
            log.error(str(e))
        return Response(result)

