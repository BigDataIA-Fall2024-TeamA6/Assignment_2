import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from pages.db import DBConnection

# Header for the admin page
st.header("Summary Log")
st.write(f"You are logged in as Admin.")

# Fetch the data from the 'log_tb' table for a specific user
def fetch_log_table_data(username):
    db_instance = DBConnection.get_instance()
    cursor = db_instance.get_cursor()

    # Query to get logs filtered by the logged-in username
    query = "SELECT * FROM log_tb WHERE username = %s"
    cursor.execute(query, (username,))
    
    # Fetch the results and get the column names
    records = cursor.fetchall()
    column_names = [i[0] for i in cursor.description]

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(records, columns=column_names)
    
    return df

# Ensure the admin is logged in and has a session state username
if 'username' not in st.session_state:
    st.error("You need to log in first!")
    st.stop()

# Fetch and display the data for the logged-in user from the 'log_tb' table
username = st.session_state['username']
log_data = fetch_log_table_data(username)

st.write("Log Table Data:")
st.dataframe(log_data)
