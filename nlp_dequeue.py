from datetime import date, datetime, timedelta

from airflow.models import DAG, Variable, XCom
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python_operator import (BranchPythonOperator,
                                               PythonOperator)
from airflow.providers.postgres.operators.postgres import PostgresOperator
from helper.get_execution_date import get_most_recent_dag_run
from airflow.utils.timezone import make_aware
from operators.rabbitmq_pull import RabbitMQPullOperator
from operators.redis_task_queue import RedisTaskQueueOperator

dag_tags = ['opexwise', "superset"]

NLP_QUEUE = Variable.get("NLP_QUEUE_NAME", default_var="NLP_DEV_LOCAL")

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

doc_md = """
            #### super set Analysis Process
            Dequeue's data from "NLP" queue and stores in XCOM 
            Then sends the data to super set analysis process
            """


def choose_destination(**kwargs):
        input_data = kwargs["input_data"]
        if input_data is not None and input_data != '':
            return ['NLP', 'CLEAR_XCOM']
        else:
            return 'END'

with DAG(dag_id='NLP_DEQUEUE_TASKS',
        default_args=default_args,
        schedule_interval="*/2 * * * *",
        tags=dag_tags, catchup=False) as dag:

    DEQUEUE_NLP = RabbitMQPullOperator(
        channel=NLP_QUEUE,
        rabbitmq_conn_id="rabbitmq",
        task_id="DEQUEUE_NLP",
    )

    if DEQUEUE_NLP.execution_date:
        execution_date_ = DEQUEUE_NLP.execution_date
    else:
        execution_date_ = make_aware(datetime.utcnow())

    input_data = XCom.get_one(
                execution_date=execution_date_,
                key=DEQUEUE_NLP.key,
                task_id='DEQUEUE_NLP',
                include_prior_dates=True
                )

    CHOOSE_DESTINATION = BranchPythonOperator(
        task_id="CHOOSE_DESTINATION",
        provide_context=True,
        python_callable=choose_destination,
        op_kwargs={"input_data":input_data}
    )

    NLP =  TriggerDagRunOperator(
        task_id="NLP",
        trigger_dag_id="NLP_CALL",
        conf=input_data
    )

    CLEAR_XCOM_TASK = PostgresOperator(
        task_id='CLEAR_XCOM',
        postgres_conn_id='airflow_db',
        sql="delete from xcom where dag_id='{{dag.dag_id}}' and execution_date='{{ts}}'",
        autocommit=True,
        trigger_rule='one_success'
    )

    END = DummyOperator(task_id='END')

    DEQUEUE_NLP >> CHOOSE_DESTINATION >> \
        [NLP, CLEAR_XCOM_TASK, END]
