# airflow/dags/api_chosen_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Function to print the selected API method
def print_api_chosen(**kwargs):
    # Get the 'api_chosen' parameter from the DAG run configuration
    api_chosen = kwargs['dag_run'].conf.api('api_chosen', 'No API chosen')
    print(f"Selected API for PDF extraction: {api_chosen}")
    return api_chosen  # Return the API chosen

# Define the DAG
default_args = {
    'owner': 'user',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 10, 1)
}

dag = DAG(
    'api_chosen_dag',
    default_args=default_args,
    description='A DAG to print the selected API method for PDF extraction',
    schedule_interval=None  # Manual trigger only
)

# Define the task
print_api_task = PythonOperator(
    task_id='print_api_chosen_task',
    python_callable=print_api_chosen,
    provide_context=True,  # Passes context to the Python callable
    dag=dag
)

print_api_task
