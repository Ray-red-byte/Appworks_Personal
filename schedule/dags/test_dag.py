from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pendulum





script_good_house_url_location = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/crawler/crawler_goodhouse_url_update.py"
script_good_house_info_location = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/crawler/crawler_goodhouse_info.py"
script_happy_house_url_location = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/crawler/crawler_haphouse_url_update.py"
script_happy_house_info_location = "/Users/hojuicheng/Desktop/personal_project/Appworks_Personal/crawler/crawler_haphouse_info.py"

with DAG(
    dag_id='test',
    description='Extract data from website',
    start_date=pendulum.datetime(2024, 4, 11, tz="UTC"),
    schedule_interval=timedelta(minutes=30),
) as dag:
    
    run_good_house_url_task = BashOperator(
        task_id='run__good_house_urlt',
        bash_command=f'python {script_good_house_url_location}',
        dag=dag,
    )

    run_good_house_info_task = BashOperator(
        task_id='run_good_house_infot',
        bash_command=f'python {script_good_house_url_location}',
        dag=dag,
    )

    run_happy_house_url_task = BashOperator(
        task_id='run_happy_house_url',
        bash_command=f'python {script_good_house_url_location}',
        dag=dag,
    )

    run_happy_house_info_task = BashOperator(
        task_id='run_happy_house_info',
        bash_command=f'python {script_good_house_url_location}',
        dag=dag,
    )

    run_good_house_url_task >> run_good_house_info_task 
    run_happy_house_url_task >> run_happy_house_info_task