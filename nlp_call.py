from os import pread
import re
from airflow.models import DAG,XCom
from airflow.utils.timezone import make_aware
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from helper.utils import _cluster_logging
from helper.metadata_without_error import get_metadata_without_error
import requests
import json
from sqlalchemy import MetaData, select, func
from airflow.providers.postgres.hooks.postgres import PostgresHook


post_gres_hook = PostgresHook(postgres_conn_id="postgresopex")
engine = post_gres_hook.get_sqlalchemy_engine()
request_url = Variable.get("NLP_URL", default_var="http://localhost:8080")
callback_url = Variable.get("NLP_CALLBACK_URL", default_var="http://localhost:8080")
workflow_algorithm_callback = Variable.get("WORKFLOW_ALGORITHM_CALLBACK", default_var = "https://dev.opexwise.ai:8002/workflow/algorithm/callback/")


dag_tags = ['opexwise', "textanalysis"]
default_args = {
    'owner': 'Parthiban.S',
    'depends_on_past': False,
    'start_date': datetime(2021, 8, 18),
    'email': ['parthiban.sivasamy@iopex.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
    'concurrency': 1,
    'max_active_runs': 1,
    'catchup_by_default': False
}

def call_nlp(**kwargs):
    print("************",kwargs)
    
    table_name = kwargs["params"]["table_name"]
    
    execution_date_ = make_aware(datetime.utcnow())
    data_fields = kwargs["params"]["params"]["file_field"]
    data_fields_dict = {}
    print("file_list",kwargs["params"]["params"]["file_field"])
    for field in data_fields:
        data_fields_dict[field["field_name"]] = field["field_backend_name"].lower()
    print(data_fields_dict)

    extra_params = XCom.get_one(
        execution_date=execution_date_,
        key="{}_extra_params".format(kwargs["params"]["params"]["key"]),
        task_id="json_dag",
        include_prior_dates=True,
    )

    min_id = XCom.get_one(
                execution_date=execution_date_,
                key="{}_min".format(table_name),
                task_id='nlp_call',
                include_prior_dates=True
                )
    if min_id:
        min_id = min_id + 1
    if not min_id:
        min_id = XCom.get_one(
                    execution_date=execution_date_,
                    key="{}_min".format(table_name),
                    task_id='CreateOrAlterTable',
                    include_prior_dates=True
                    )

    metadata = get_metadata_without_error(engine)
    destination_table_name = metadata.tables.get(table_name)
    if destination_table_name is not None:
        query = select([func.max(destination_table_name.c.analysis_unique_id)]).select_from(destination_table_name)
        with engine.connect() as con:
            max_id = con.execute(query).scalar()
            kwargs['ti'].xcom_push(key='{}_min'.format(table_name), value=max_id)
    # content = "{}_col".format(str.lower(kwargs["params"]["content"][0]))
    cluster_job_ids = kwargs["params"].get("cluster_job_ids")
    content = ""
    sentimental_content = ""
    summarization_content = ""
    predictive_content = ""
    predictive_destination_content = ""
    predictive_analysis_auto_ml_type = ""
    forecast_date_field = ""
    predictive_analysis_type = ""
    predictive_content_col = []
    request_type_list = []
    print("outside content")
    try:
        _content = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("textAnalysisColumn")
        if _content:
            content = _content[0]
            field_backend_name = data_fields_dict[content]
            data_fields_dict[content] = str(field_backend_name+"_col").lower()
            content = data_fields_dict[content]
            request_type_list.append("text_analysis")
    except IndexError:
        content = ""

    try:
        _sentimental_content = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("sentimentAnalysisColumn")
        if _sentimental_content:
            sentimental_content = data_fields_dict[_sentimental_content[0]]
            request_type_list.append("sentimental_analysis")
    except IndexError:
        sentimental_content = ""

    try:
        _summarization_content = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("summarizationColumn")
        if _summarization_content:
            summarization_content = data_fields_dict[_summarization_content[0]]
            request_type_list.append("summarization")
    except IndexError:
        summarization_content = ""

    try:
        _predictive_destination_content = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("predictive_analysis_destination")
        if _predictive_destination_content:
            predictive_destination_content = data_fields_dict[_predictive_destination_content[0]]
            _predictive_source_col = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("predictiveAnalysisColumn")
            predictive_analysis_type = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("predictiveAnalysisType")[0]
            predictive_analysis_auto_ml_type = str(kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("predictiveAnalysisAutoMLType", "")).lower()
            _forecast_date_field = kwargs["params"]["params"]["analysis_input"]["analysis_fields"].get("forecast_date_field")[0]
            if _forecast_date_field:
                forecast_date_field = data_fields_dict[_forecast_date_field]
            request_type_list.append("predictive_analysis")

            if predictive_analysis_type == "manual":
                for coloumn in _predictive_source_col:
                    predictive_content_col.append(data_fields_dict[coloumn])
            if predictive_analysis_type == "auto":
                    predictive_content_col = list(data_fields_dict.values())
                    predictive_content_col.remove(predictive_destination_content)
            predictive_content = ",".join(predictive_content_col).lower()

    except IndexError:
        predictive_content = ""

    request_type = ",".join(request_type_list) 

    # print("*********", sentimental_content)
    content_class = kwargs["params"]["content_class"]
    category = content_class[0] if content_class else None
    reference_id = kwargs['params']["reference_id"]
    solution_field = kwargs["params"]["solution_field"]
    resolution = solution_field[0] if solution_field else None

    if category and re.search("\w\s\w|\(|\)", category):
        category = re.sub("\s+","_",category)
        category = re.sub("\(|\)","",category)
        category = str.lower(category)

    if resolution and re.search("\w\s\w|\(|\)", resolution):
        resolution = re.sub("\s+","_",resolution)
        resolution = re.sub("\(|\)","",resolution)
        resolution = str.lower(resolution)

    payload = {
        "table_name": table_name,
        "client_name":"opexwisedev",
        "cluster_job_ids":cluster_job_ids,
        "request_type": request_type,
        "content": content,
        "sentimental_content":sentimental_content,
        "summarization_content":summarization_content,
        "predictive_content":predictive_content,
        "predictive_type":predictive_analysis_type,
        "predictive_destination_coloumn":predictive_destination_content,
        "predictive_analysis_auto_ml_type":predictive_analysis_auto_ml_type,
        "forecast_date_field":forecast_date_field,
        "category": category,
        "callback_url": callback_url,
        "reference_id": reference_id,
        "resolution": resolution,
        "col_name": "analysis_unique_id",
        "workflow_algorithm_callback": workflow_algorithm_callback,
        "min_id": min_id,
        "max_id": max_id
    }



    if extra_params:
        payload.update({
            "ml_algorithm_detail" : extra_params,
        })
    
    print(payload)
    header={'Content-Type': 'application/json'}
    try:
        print("Request URL : " + str(request_url))
        print("Request Payload : " + str(json.dumps(payload)))
        response = requests.request(
            "POST",
            request_url,
            headers=header,
            data=json.dumps(payload),
            verify=False)
        print("Response : " + str(response.content))
        _logging = _cluster_logging(kwargs, cluster_job_ids=cluster_job_ids, data_map_id = reference_id)

        _logging.info(msg_short="NLP API is called",
                    msg_full="NLP CALL sent")
        return True
    except Exception as e:
        print("Exception : " + str(e))
        return None


with DAG(dag_id='NLP_CALL',
         default_args=default_args,
         schedule_interval=None,
         tags=['nlp'],
         max_active_runs=1,
         catchup=False) as dag:

    dag.doc_md = """
            #### NLP
            Triggered by dequeue dag
            Performs NLP call
            """

    task_super_set = PythonOperator(
        task_id="nlp_call",
        provide_context=True,
        python_callable=call_nlp,
    )
