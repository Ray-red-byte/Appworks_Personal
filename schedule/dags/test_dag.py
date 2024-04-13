from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from datetime import datetime, timedelta
import pendulum


script_good_house_url_location = "./scripts/crawler_goodhouse_url_update.py"
script_good_house_info_location = "./scripts/crawler_goodhouse_info.py"
script_happy_house_url_location = "./scripts/crawler_haphouse_url_update.py"
script_happy_house_info_location = "./scripts/crawler_haphouse_info.py"



with DAG(
    dag_id='test',
    description='Extract data from website',
    start_date=pendulum.datetime(2024, 4, 13, tz="UTC"),
    schedule_interval=timedelta(minutes=120),
) as dag:
    
    run_good_house_url_task = SSHOperator(
        task_id='run_good_house_url',
        ssh_conn_id='ssh',
        command=f'python {script_good_house_url_location}',
        dag=dag,
    )

    run_good_house_info_task = SSHOperator(
        task_id='run_good_house_info',
        ssh_conn_id='ssh',
        command=f'python {script_good_house_info_location}',
        dag=dag,
    )

    run_happy_house_url_task = SSHOperator(
        task_id='run_happy_house_url',
        ssh_conn_id='ssh',
        command=f'python {script_happy_house_url_location}',
        dag=dag,
    )

    run_happy_house_info_task = SSHOperator(
        task_id='run_happy_house_info',
        ssh_conn_id='ssh',
        command=f'python {script_happy_house_info_location}',
        dag=dag,
    )

    run_good_house_url_task >> run_good_house_info_task 
    run_happy_house_url_task >> run_happy_house_info_task