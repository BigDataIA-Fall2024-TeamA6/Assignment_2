from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

# Define a simple Python function
def my_task_function():
    print("Hello, Airflow!")

# Define default arguments for the DAG
default_args = {
    'owner': 'Sahiti',
    'depends_on_past': False,
    'start_date': datetime(2023, 10, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Instantiate the DAG
dag = DAG(
    'my_first_dag',  # DAG ID
    default_args=default_args,
    description='PyMuPDF workflow',
    schedule_interval=timedelta(days=1),  # Run every day
)

# Define a task using the PythonOperator
task_1 = PythonOperator(
    task_id='print_hello',
    python_callable=my_task_function,  # Function to run
    dag=dag,
)

