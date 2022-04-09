from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python import BranchPythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, date
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
import json
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.email_operator import EmailOperator
import cchardet
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.request
import os
from google.cloud import storage
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.utils.task_group import TaskGroup

from financials_extract_taskgroup import build_financials_extract_taskgroup
from financials_gcs_taskgroup import build_financials_gcs_taskgroup
from financials_transform_taskgroup import build_financials_transform_taskgroup
from financials_load_taskgroup import build_financials_load_taskgroup
from financials_schema_taskgroup import build_financials_schema_taskgroup
from financials_postgres_taskgroup import build_financials_postgres_taskgroup
from financials_stage_taskgroup import build_financials_stage_taskgroup



headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"}

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/airflow/airflow/dags/stockprediction_servicekey.json'
storage_client = storage.Client()
bucket = storage_client.get_bucket('stock_prediction_is3107')
STAGING_DATASET = 'stock_prediction_staging_dataset'
PROJECT_ID = 'stockprediction-344203'
DWH_DATASET = 'stock_prediction_datawarehouse'

default_args = {
     'owner': 'airflow',
     'depends_on_past': False,
     'email': ['user@gmail.com'],
     'email_on_failure': True,
     'email_on_retry': True,
     'retries': 0,
     'start_date': datetime(2022, 3, 6)
    }

with DAG(
    dag_id="yearly_dag_etl",
    schedule_interval="@yearly",
    description = 'DAG for creation of data warehouse (Yearly)',
    default_args=default_args,
    catchup = False
) as dag:
    # importing the various taskgroups that make up the main yearly dag
    
    with TaskGroup("tgpostgres", prefix_group_id=False) as section_postgres:
        financials_postgres_taskgroup = build_financials_postgres_taskgroup(dag=dag)
    with TaskGroup("tg0", prefix_group_id=False) as section_0:
        financials_schema_taskgroup = build_financials_schema_taskgroup(dag=dag)
    with TaskGroup("tg1", prefix_group_id=False) as section_1:
        financials_extract_taskgroup = build_financials_extract_taskgroup(dag=dag)
    with TaskGroup("tg2", prefix_group_id=False) as section_2:
        financials_gcs_taskgroup = build_financials_gcs_taskgroup(dag=dag)
    with TaskGroup("tg3", prefix_group_id=False) as section_3:
        financials_stage_taskgroup = build_financials_stage_taskgroup(dag=dag)
    with TaskGroup("tg4", prefix_group_id=False) as section_4:
        financials_transform_taskgroup = build_financials_transform_taskgroup(dag=dag)
    with TaskGroup("tg5", prefix_group_id=False) as section_5:
        financials_load_taskgroup = build_financials_load_taskgroup(dag=dag)

    # task dependencies
    section_0 >> section_1 >> section_2 >> section_3 >> section_4 >> section_postgres >> section_5
    
    
    #section_3 >> [section_postgres, section_0]
    

