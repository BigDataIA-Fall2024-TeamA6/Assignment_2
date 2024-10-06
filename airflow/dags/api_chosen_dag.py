from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import boto3
import fitz  # PyMuPDF library for PDF text extraction
import os
import mysql.connector
import json
from dotenv import load_dotenv

load_dotenv()

# AWS credentials (use environment variables in production)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client with credentials
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1'
)

# Function to fetch PDF from S3
def get_s3_file_content(s3_url, **kwargs):
    try:
        # Determine the S3 bucket and object key from the URL
        if "s3.amazonaws.com" in s3_url:
            parts = s3_url.split('/')
            bucket_name = parts[2].split('.')[0]  # Extract bucket name
            object_key = '/'.join(parts[3:])      # Extract object key
        else:
            raise ValueError("Invalid S3 URL format")
        
        # Fetch the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read()  # Reading the PDF file content
        
        # Save the PDF to a local file
        local_pdf_path = '/tmp/temp_pdf.pdf'
        with open(local_pdf_path, 'wb') as f:
            f.write(content)

        print(f"PDF successfully downloaded to: {local_pdf_path}")  # Log the file path
        return local_pdf_path  # Return the path to the local PDF file

    except Exception as e:
        print(f"Error processing S3 file: {e}")
        raise

import mysql.connector  # Make sure to install this library if not already done

def convert_pdf_to_text(**kwargs):
    local_pdf_path = kwargs['ti'].xcom_pull(task_ids='fetch_s3_file_content')

    try:
        pdf_document = fitz.open(local_pdf_path)
        
        pdf_text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            pdf_text += page.get_text()

        # Wrap the pdf_text in a JSON-compatible format
        json_text = json.dumps({"text": pdf_text})

        # Get the file_path from the DAG run configuration to identify the row to update
        file_path = kwargs['dag_run'].conf['file_path']

        # Update the database with the extracted text
        connection = mysql.connector.connect(
            host='database-1.cdwumcckkqqt.us-east-1.rds.amazonaws.com',
            user='admin',
            password='amazonrds7245',
            database='gaia_benchmark_dataset_validation'
        )
        cursor = connection.cursor()

        # SQL query to update the corresponding row in the table
        update_query = """
        UPDATE pdf_question_tb 
        SET pymupdf_output = %s 
        WHERE file_path = %s
        """
        cursor.execute(update_query, (json_text, file_path))
        connection.commit()
        print(f"Updated database with extracted text for file: {file_path}")
        print(json_text)
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error converting PDF to text: {e}")
        raise

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
    description='A DAG to fetch a PDF from S3, convert it to text using PyMuPDF, and log the result',
    schedule_interval=None  # Manual trigger only
)

# Define tasks
fetch_s3_file_content_task = PythonOperator(
    task_id='fetch_s3_file_content',
    python_callable=get_s3_file_content,
    op_kwargs={'s3_url': '{{ dag_run.conf["file_path"] }}'},  # Pass the file path from conf
    provide_context=True,
    dag=dag
)

convert_pdf_to_text_task = PythonOperator(
    task_id='convert_pdf_to_text',
    python_callable=convert_pdf_to_text,
    provide_context=True,
    dag=dag
)

# Set task dependencies
fetch_s3_file_content_task >> convert_pdf_to_text_task
