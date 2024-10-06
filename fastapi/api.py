from fastapi import FastAPI, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import mysql.connector
from fastapi.security import OAuth2PasswordBearer

# Secret key for JWT
SECRET_KEY = "bigdataintelligenceandanalytics"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing and verifying
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


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
    query = "SELECT questions FROM pdf_question_tb"
    cursor.execute(query, (logged_in,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    return data
