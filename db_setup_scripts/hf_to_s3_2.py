import boto3
from huggingface_hub import HfApi, hf_hub_download
import os

# Initialize S3 client
s3_client = boto3.client('s3', region_name='us-east-1')

# Define constants
HUGGINGFACE_REPO_ID = "gaia-benchmark/GAIA"  # Base repo ID for the dataset
S3_BUCKET_NAME = "bdia-assignment-2"  # Updated bucket name
S3_VALIDATION_PREFIX = "ValidationData/"
S3_TEST_PREFIX = "TestData/"
HUGGINGFACE_TOKEN = "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"  # Replace with your Hugging Face token

# Hugging Face API instance with token
api = HfApi()

def upload_to_s3(file_path, s3_bucket, s3_key):
    """Upload file content to S3."""
    try:
        with open(file_path, 'rb') as f:
            s3_client.upload_fileobj(f, s3_bucket, s3_key)
        print(f"Successfully uploaded {s3_key} to s3://{s3_bucket}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload {s3_key} to S3: {str(e)}")

def main():
    # List files in the repository, specifying repo_type as 'dataset'
    repo_files = api.list_repo_files(HUGGINGFACE_REPO_ID, repo_type="dataset")

    # Filter for PDF files in 'test/' and 'validation/' subfolders (both under '2023/')
    pdf_files = [f for f in repo_files if f.endswith('.pdf') and (f.startswith("2023/test/") or f.startswith("2023/validation/"))]

    # Download and move each file to S3
    for file_name in pdf_files:
        # Download each file from Hugging Face Hub (use subfolder path in filename)
        local_file_path = hf_hub_download(repo_id=HUGGINGFACE_REPO_ID, filename=file_name, repo_type="dataset", use_auth_token=HUGGINGFACE_TOKEN)

        # Define the S3 key based on the folder (Test or Validation)
        if 'test/' in file_name:
            s3_key = f"{S3_TEST_PREFIX}{file_name.split('/')[-1]}"  # Place files in TestData/ for test files
        else:
            s3_key = f"{S3_VALIDATION_PREFIX}{file_name.split('/')[-1]}"  # Place files in ValidationData/ for validation files

        # Upload the file to S3
        upload_to_s3(local_file_path, S3_BUCKET_NAME, s3_key)

        # Remove the local file after uploading
        os.remove(local_file_path)

if __name__ == "__main__":
    main()
