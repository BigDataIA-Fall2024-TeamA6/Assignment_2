import os
import json
import boto3
import mysql.connector
from airflow import DAG
from dotenv import load_dotenv
from google.cloud import documentai
from datetime import datetime, timedelta
from google.oauth2 import service_account
from google.api_core.client_options import ClientOptions
from airflow.operators.python import PythonOperator

load_dotenv()


# AWS credentials (use environment variables in production)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = "us"

SERV_ACC = f'docai-serv-acc@{PROJECT_ID}.iam.gserviceaccount.com'
PROCESSOR_ID = os.getenv("PROCESSOR_ID")

MIME_TYPE = "application/pdf"
assert PROJECT_ID, "PROJECT_ID is undefined"
assert LOCATION in ("us", "eu"), "API_LOCATION is incorrect"


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
        local_pdf_path = '/tmp/pdf.pdf'
        with open(local_pdf_path, 'wb') as f:
            f.write(content)

        print(f"PDF successfully downloaded to: {local_pdf_path}")  # Log the file path
        return local_pdf_path  # Return the path to the local PDF file

    except Exception as e:
        print(f"Error processing S3 file: {e}")
        raise





def convert_pdf_to_text(**kwargs):
    local_pdf_path = kwargs['ti'].xcom_pull(task_ids='fetch_s3_file_content')
    try:
        info_var = os.getenv("INFO")
        info_dict = json.loads(info_var)
        credentials = service_account.Credentials.from_service_account_info(info=info_dict)
        # Instantiates a client
        docai_client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com"),credentials=credentials)

        RESOURCE_NAME = docai_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
        # Read the file into memory
        with open(local_pdf_path, "rb") as pdf:
            image_content = pdf.read()

        # Load Binary Data into Document AI RawDocument Object
        raw_document = documentai.RawDocument(content=image_content, mime_type=MIME_TYPE)

        # Configure the process request
        request = documentai.ProcessRequest(name=RESOURCE_NAME, raw_document=raw_document)

        # Use the Document AI client to process the sample form
        result = docai_client.process_document(request=request)

        document_object = result.document
        json_text = json.dumps({"text": document_object.text})
        
        file_path = kwargs['dag_run'].conf['file_path']  #actual file path
    
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
        SET docai_output = %s 
        WHERE file_path = %s
        """
        cursor.execute(update_query, (json_text, file_path))
        connection.commit()
        print(f"Updated database with extracted text for file: {file_path}")
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
    'docai_dag',
    default_args=default_args,
    description='A DAG to fetch a PDF from S3, convert it to text using Google DocumentAI, and log the result',
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

convert_pdf_to_text_docai_task = PythonOperator(
    task_id='convert_pdf_to_text_docai',
    python_callable=convert_pdf_to_text,
    provide_context=True,
    dag=dag
)

# Set task dependencies
fetch_s3_file_content_task >> convert_pdf_to_text_docai_task






