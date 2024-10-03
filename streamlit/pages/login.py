import streamlit as st
import bcrypt
from pages.db import DBConnection
from fastapi import FastAPI
import mysql.connector

app = FastAPI()

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

        
    if st.button("Log in",key='login'):
        is_valid, user_type_db = verify_user(username, password)
        if is_valid and user_type_db == user_type:
            if user_type == 'user':
                st.success(f"Welcome {username}!")
                st.switch_page("pages/user_landing.py")
            elif user_type == 'admin':
                st.success(f"Welcome Admin!")
                st.switch_page("pages/admin.py")
        else:
            st.error("Invalid credentials!")
                

    if st.button("Create User",key='create_user'):
        st.switch_page("pages/create_user.py") 


def verify_user(uname,pword):
    db = create_connection()
    cursor = db.cursor()
    cursor.execute("SELECT password, user_type FROM login WHERE username = %s", (uname,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result:
        hashed_password = result[0].encode('utf-8')
        if bcrypt.checkpw(pword.encode('utf-8'), hashed_password):
            return True, result[1]  # Return user type
    return False, None  # Invalid credentials

if __name__ == "__main__":
    main()
