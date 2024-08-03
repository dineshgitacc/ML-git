import requests
import json
import psycopg2
from analysis_request.models import AnalysisRequestSetting
from analysis_request.seralizers import AnalysisRequestSettingViewSerializer

class Classification:
    # Demo Server.
    LEXMARK_INFERENCE_API = "http://10.10.50.33:8200/api/intent/inference/lexmark"
    
    # Test Server.
    # LEXMARK_INFERENCE_API = "http://10.10.50.20:8200/api/intent/inference/lexmark"
    
    # Dev Server.
    # LEXMARK_INFERENCE_API = "http://10.20.245.154:8200/api/intent/inference/lexmark"
    
    LIMIT = 2
    OFFSET = 0

    # Demo Server.
    analysis_request_setting_id = 4
    
    # Test Server.
    #analysis_request_setting_id = 4

    analysis_unique_id = []

    def __init__(self):
        try:
            self.get_analysis_request_setting()
        except Exception as e:
            return False


    def get_analysis_request_setting(self):
        try:
            # Retrive Connecting Database Details.
            response = AnalysisRequestSetting.objects.filter(analysis_request_setting_id = self.analysis_request_setting_id)
            serailizer = AnalysisRequestSettingViewSerializer(response,many=True)
            print(serailizer.data[0]["extras"])
            if isinstance(serailizer.data[0]["extras"], str):
                serailizer.data[0]["extras"] = json.loads(serailizer.data[0]["extras"])
            self.connect_ETL_database(serailizer.data[0]["extras"])
        
        except Exception as e:
            print(str(e))
            return False

    def connect_ETL_database(self,extras):
        try:
            if extras:
                # Connect database and execute query.
                connection = extras[0]["database"]
                con = psycopg2.connect(database=connection['database'], user=connection['username'], password=connection['password'], port=connection['port'], host=connection['hostname'])
                cursor = con.cursor()
                is_response = True
                while is_response:
                    query = "SELECT analysis_unique_id,description_col FROM workflow_11_fileupload_superset_11 LIMIT {} OFFSET {}".format(self.LIMIT,self.OFFSET)
                    cursor.execute(query)
                    response = cursor.fetchall()
                    print(response)
                    if(len(response) > 0):
                        description_col = []
                        self.analysis_unique_id = []
                        for i in response:
                            self.analysis_unique_id.append(i[0])
                            description_col.append(i[1])
                        self.call_ML_API(request_data = description_col, extras = extras)
                        return True
                    else:
                        is_response = False
                    print("EXECUTION END")
                    return False
        
        except psycopg2.DatabaseError as e:
            print(str(e))
            return False

        except Exception as e:
            print(str(e))
            return False


    def call_ML_API(self,request_data,extras):
        try:
            request_data = {"ticket_description": request_data} 
            # Call Lexmark inference api.
            response = requests.post(url = self.LEXMARK_INFERENCE_API, json = request_data)
            if response.content in response:
                if isinstance(response.content, str):
                    response.content = json.loads(response.content)
                if self.update_ML_response_content(response_data = response.content, extras = extras):
                    return True
            return False

        except Exception as e:
            print(str(e))
            return False


    def update_ML_response_content(self,response_data, extras):
        try:
            count = 0
            if(response_data["error"] == False):
                # Each data update in Workflow11FileuploadSuperset11 Model.
                connection = extras[0]["database"]
                con = psycopg2.connect(database=connection['database'], user=connection['username'], password=connection['password'], port=connection['port'], host=connection['hostname'])
                cursor = con.cursor()  
                for data in response_data["result"]:                           
                    query = "UPDATE workflow_11_fileupload_superset_11 SET ml_classification = '{}',status = 1,created_by = 1 WHERE analysis_unique_id = {}".format(json.dumps([data]),self.analysis_unique_id[count])
                    cursor.execute(query)
                    con.commit()
                    count +=1
                self.OFFSET += self.LIMIT
                self.get_analysis_request_setting()
                return True
            return False

        except Exception as e:
            print(str(e))
            return False


# Calling
Classification()