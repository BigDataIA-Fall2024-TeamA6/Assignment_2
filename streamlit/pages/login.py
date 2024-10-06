import streamlit as st
import bcrypt
from pages.db import DBConnection
from fastapi import FastAPI
import mysql.connector
import requests

app = FastAPI()
FASTAPI_URL = "http://127.0.0.1:8000"


def create_connection():
    """Create a database connection."""
    try:
        connection = mysql.connector.connect(
            host='database-1.cdwumcckkqqt.us-east-1.rds.amazonaws.com',
            user='admin',
            password='amazonrds7245',
            database='gaia_benchmark_dataset_validation'
        )
        return connection
    except mysql.connector.Error as err:
        st.error(f"Error connecting to database: {err}")
        return None


def main():
    st.header("Login Page")

    username = st.text_input("Username",key='uname')
    password = st.text_input("password",type="password",key='pword')
    user_type = st.selectbox("Choose User type",options=['user','admin'],key='select_user_type')

    if st.button("Login",key='login'):

        response = requests.post(f"{FASTAPI_URL}/token", json={"username":username,"password": password,"user_type":user_type})
        if response.status_code == 200:
            st.session_state.username = username
            if user_type == 'user':
                st.switch_page("pages/user_landing.py")
            elif user_type == 'admin':
                st.switch_page("pages/admin.py")
        elif response.status_code == 500:
            st.error(f"Error {response.status_code} Server down :(")
        else:
            st.error(f"Error {response.status_code} Please check credentials or user type!")
        
                

    if st.button("Create User",key='create_user'):
        st.switch_page("pages/create_user.py") 


if __name__ == "__main__":
    main()
