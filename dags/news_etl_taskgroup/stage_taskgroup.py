from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.contrib.operators.bigquery_operator import BigQueryOperator
from airflow.utils.task_group import TaskGroup
from airflow.models import DAG
from google.cloud import bigquery
from google.cloud import storage
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator

import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/airflow/airflow/dags/stockprediction_servicekey.json'
storage_client = storage.Client()
bucket = storage_client.get_bucket('stock_prediction_is3107')
STAGING_DATASET = 'stock_prediction_staging_dataset'
PROJECT_ID = 'stockprediction-344203'

def build_stage_taskgroup(dag: DAG) -> TaskGroup:
    stage_taskgroup = TaskGroup(group_id = "stage_taskgroup")

    # Load data from GCS to BQ
    stage_yahoofinance = GCSToBigQueryOperator(
        task_id = 'stage_yahoofinance',
        bucket = 'stock_prediction_is3107',
        source_objects = ['yahoofinance_news.parquet'],
        destination_project_dataset_table = f'{PROJECT_ID}:{STAGING_DATASET}.yahoofinance_news',
        write_disposition='WRITE_TRUNCATE',
        autodetect = True,
        source_format = 'PARQUET',
        dag = dag
    )

    stage_sginvestor = GCSToBigQueryOperator(
        task_id = 'stage_sginvestor',
        bucket = 'stock_prediction_is3107',
        source_objects = ['sginvestor_news.parquet'],
        destination_project_dataset_table = f'{PROJECT_ID}:{STAGING_DATASET}.sginvestor_news',
        write_disposition='WRITE_TRUNCATE',
        autodetect = True,
        source_format = 'PARQUET',
        dag = dag
    )

    stage_sginvestor_blog = GCSToBigQueryOperator(
        task_id = 'stage_sginvestor_blog',
        bucket = 'stock_prediction_is3107',
        source_objects = ['sginvestor_blog_news.parquet'],
        destination_project_dataset_table = f'{PROJECT_ID}:{STAGING_DATASET}.sginvestor_blog_news',
        write_disposition='WRITE_TRUNCATE',
        autodetect = True,
        source_format = 'PARQUET',
        dag = dag
    )

    start_staging = DummyOperator(
        task_id = 'start_staging',
        dag = dag
    )

    end_staging = DummyOperator(
        task_id="end_staging",
        dag=dag
    )

    start_staging >> [stage_yahoofinance, stage_sginvestor, stage_sginvestor_blog] >> end_staging
    return stage_taskgroup