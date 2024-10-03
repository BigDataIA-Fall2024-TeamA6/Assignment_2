import os
import json
import boto3
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# AWS S3 configuration
s3 = boto3.client('s3')
bucket_name = 'bdia-assignment-2'

# Function to list objects in S3 bucket for specific directories
def list_s3_objects(prefix):
    objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    return [obj['Key'] for obj in objects.get('Contents', []) if obj['Key'].endswith('.pdf')]

# Function to load metadata.jsonl file from S3
def load_metadata_from_s3(metadata_path):
    try:
        metadata_file = s3.get_object(Bucket=bucket_name, Key=metadata_path)['Body'].read().decode('utf-8')
        metadata_lines = metadata_file.strip().split('\n')
        metadata_records = [json.loads(line) for line in metadata_lines]
        return pd.DataFrame(metadata_records)
    except s3.exceptions.NoSuchKey:
        print(f"The key {metadata_path} does not exist in the bucket {bucket_name}. Please check the file path.")
        return None

# Load PDF files from TestData/ and ValidationData/ directories
test_data_files = list_s3_objects('TestData/')
validation_data_files = list_s3_objects('ValidationData/')
pdf_files = test_data_files + validation_data_files

# Load metadata from TestData/ and ValidationData/
test_metadata_df = load_metadata_from_s3('TestData/metadata.jsonl')
validation_metadata_df = load_metadata_from_s3('ValidationData/metadata.jsonl')

# Combine both metadata DataFrames
metadata_df = pd.concat([test_metadata_df, validation_metadata_df], ignore_index=True)

# Connect to Amazon RDS Database
connection = mysql.connector.connect(
    host='database-1.cdwumcckkqqt.us-east-1.rds.amazonaws.com',
    user='admin',
    password='amazonrds7245',
    database='gaia_benchmark_dataset_validation',
    allow_local_infile=True
)

# Create the SQLAlchemy engine to insert data into the MySQL table
engine = create_engine("mysql+mysqlconnector://admin:amazonrds7245@database-1.cdwumcckkqqt.us-east-1.rds.amazonaws.com/gaia_benchmark_dataset_validation")

# Step 1: Fetch the maximum serial_num from the table to avoid duplicates
query = "SELECT MAX(serial_num) FROM pdf_question_tb"
max_serial_num = pd.read_sql(query, con=engine).iloc[0, 0]

if pd.isna(max_serial_num):
    max_serial_num = 0  # If the table is empty, start from 0

# Filter out necessary columns: task_id, Question (with capital 'Q'), and match file_name from metadata to pdf_files
matched_records = []
serial_num = max_serial_num + 1
for _, row in metadata_df.iterrows():
    task_id = row['task_id']
    question = row['Question']  # Ensure the key is correctly capitalized
    
    # Find a matching PDF file in the S3 files using task_id (which is the same as the PDF file name)
    matching_file = next((f for f in pdf_files if task_id in f), None)
    
    if matching_file:
        # Create the full S3 URL for the matched file
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{matching_file}"
        
        matched_records.append({
            'serial_num': serial_num,  # Increment serial_num for each new record
            'task_id': task_id,
            'question': question,
            'file_path': s3_url,  # Store the full S3 URL in file_path
            'pymupdf_output': None,  # Will be NULL in DB
            'docai_output': None  # Will be NULL in DB
        })
        serial_num += 1

# Create a DataFrame with the matched data
pdf_question_df = pd.DataFrame(matched_records)

# Insert data into the pdf_question_tb table
pdf_question_df.to_sql(con=engine, name='pdf_question_tb', if_exists='append', index=False)

# Commit and close the connection
connection.commit()
connection.close()

print("Data successfully uploaded to RDS")
