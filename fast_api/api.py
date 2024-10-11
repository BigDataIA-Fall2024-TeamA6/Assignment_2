import os
import streamlit as st
from openai import OpenAI
from fastapi import FastAPI, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import mysql.connector
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

# Secret key for JWT
SECRET_KEY = "bigdataintelligenceandanalytics"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing and verifying
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  

app = FastAPI()


api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=api_key)

# Database connection
def get_db_connection():
    connection = mysql.connector.connect(
        host="database-1.cdwumcckkqqt.us-east-1.rds.amazonaws.com",
        user="admin",
        password="amazonrds7245",
        database="gaia_benchmark_dataset_validation"
    )
    return connection

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str
    user_type: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    
class LLMRequest(BaseModel):
    question: str
    extracted_output: str

# Hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Create JWT token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify token
def verify_access_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# Authenticate user
def authenticate_user(username: str,password: str,user_type: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT username,password,user_type FROM login WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user if user and verify_password(password,user.get('password')) and user_type==user.get('user_type') else False

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    user = authenticate_user(form_data.username,form_data.password,form_data.user_type)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/questions")
async def fetch_questions(token: str = Depends(oauth2_scheme)):
    logged_in = verify_access_token(token)
    # Query data for the logged-in user
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT serial_num, task_id, question, file_path FROM pdf_question_tb where username = %s"
    cursor.execute(query, (logged_in,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return data

@app.get("/fetchrecords")
async def fetch(output_col: str, selected_test_case: int):
    try:
        query = (f"SELECT {output_col} FROM pdf_question_tb WHERE serial_num = {selected_test_case}")
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        records = cursor.fetchone()
        if records is None:
            raise HTTPException(status_code=404, detail="Record not found")
        return records
    except Exception as e:
        raise HTTPException(status_code=500)
    
@app.post("/get_llm_output")
async def get_llm_output(llm_request: LLMRequest):
    question = llm_request.question
    extracted_output = llm_request.extracted_output

    # Call GPT-4 API using the OpenAI library
    messages = [
        {"role": "system", "content": "You are an AI assistant that helps users extract information from PDF documents."},
        {"role": "user", "content": f"Question: {question}\n\nPDF Extraction Output: {extracted_output}\n\nPlease provide an answer based on the extraction."}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=3000
        )
        llm_output = response.choices[0].message.content
        return {"llm_output": llm_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling GPT-4 API: {e}")

    
