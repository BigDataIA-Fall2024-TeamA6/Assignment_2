import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from openai import OpenAI
from pages.db import DBConnection  # Assuming DBConnection is in pages/db.py
import requests
import json
import time  # For polling the DAG run status

# Load environment variables from a .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    api_key = st.secrets["OPENAI_API_KEY"]


client = OpenAI(api_key=api_key)

# Establish database connection
try:
    db = DBConnection.get_instance()
    cursor = db.get_cursor()
except Exception as e:
    st.error(f"Error connecting to the database: {e}")

# Function to insert log into log_tb with extracted PDF output in method_output column
def insert_log_into_log_tb(task_id, question, method, username, method_output):
    try:
        insert_query = """
        INSERT INTO log_tb (task_id, question, method, username, method_output)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (task_id, question, method, username, method_output))
        db.get_connection().commit()  # Commit the transaction
        st.success("Log successfully inserted into log_tb!")
    except Exception as e:
        st.error(f"Error inserting into log_tb: {e}")
        db.get_connection().rollback()

# Function to fetch test cases from pdf_question_tb
def get_questions():
    try:
        cursor.execute('SELECT serial_num, task_id, question, file_path, pymupdf_output, docai_output FROM pdf_question_tb;')
        pdf_ques_tb = cursor.fetchall()
        test_cases = pd.DataFrame(pdf_ques_tb, columns=[desc[0] for desc in cursor.description])  # Ensure column names match
        return test_cases
    except Exception as e:
        st.error(f"Error fetching questions: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

# Function to call OpenAI GPT-4 API using ChatCompletion
def get_llm_output(question, extraction_output):
    try:
        messages = [
            {"role": "system", "content": "You are an AI assistant that helps users extract information from PDF documents."},
            {"role": "user", "content": f"Question: {question}\n\nPDF Extraction Output: {extraction_output}\n\nPlease provide an answer based on the extraction."}
        ]
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=3000
        )
        llm_output = response.choices[0].message.content.strip()
        return llm_output
    except Exception as e:
        st.error(f"Error calling GPT-4 API: {e}")
        return ""

# Function to trigger the Airflow DAG
def trigger_airflow_dag(dag_id, api_chosen, file_path):
    airflow_url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns"
    data = {
        "conf": {
            "api_chosen": api_chosen,
            "file_path": file_path  # Pass the file path
        }
    }
    response = requests.post(airflow_url, json=data, auth=("airflow", "airflow"))
    if response.status_code == 200:
        st.success("Airflow DAG triggered successfully!")
        dag_run_id = response.json()["dag_run_id"]  # Capture the DAG run ID
        return dag_run_id
    else:
        st.error(f"Failed to trigger DAG: {response.text}")
        return None

# Function to get the DAG run output
def get_dag_run_output(dag_id, dag_run_id, api_chosen, selected_test_case):
    airflow_dag_run_url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
    while True:
        response = requests.get(airflow_dag_run_url, auth=("airflow", "airflow"))
        if response.status_code == 200:
            dag_run_info = response.json()
            state = dag_run_info["state"]
            if state == "success":
                st.success("DAG run completed successfully!")
                return True
            elif state == "failed":
                st.error("DAG run failed!")
                return False
            time.sleep(2)
        else:
            st.error(f"Failed to fetch DAG run status: {response.text}")
            return False

# User landing page function
def user_landing():
    col1, col2 = st.columns(2)
    with col1:
        st.header("XtractPDF App")
    with col2:
        if st.button("Go to Summary"):
            st.session_state["page"] = "summary"

    if 'username' not in st.session_state:
        st.error("You need to log in first!")
        st.stop()

    username = st.session_state['username']

    test_cases = get_questions()
    if not test_cases.empty:
        test_cases_dict = dict(zip(test_cases['serial_num'], test_cases['question']))
        selected_test_case = st.selectbox("Select a Test Case:", options=test_cases["serial_num"], key="select_test_case")

        if selected_test_case:
            selected_question = test_cases_dict[selected_test_case]
            file_path = test_cases[test_cases['serial_num'] == selected_test_case]['file_path'].values[0]

            serial_num = selected_test_case
            task_id = serial_num

            question = st.text_area("Question:", value=selected_question, key="edited_question")

            st.session_state['selected_test_case'] = selected_test_case  
            st.session_state['selected_question'] = question    

            st.write(f"Accessing File: {str(file_path).split('/')[-1]}")

            c1, c2 = st.columns(2)
            with c1:
                api_chosen = st.selectbox("PDF Extraction Type", options=['PyMuPDF', 'documentAi'], key='api_chosen')
            with c2:
                st.selectbox("LLM Model", options=['GPT4', 'GPT4o'], key="LLM_chosen")

            llm_chosen = st.session_state.LLM_chosen

            if st.button("Extract PDF"):
                dag_run_id = trigger_airflow_dag("api_chosen_dag", api_chosen, file_path)
                if dag_run_id:
                    dag_state = get_dag_run_output("api_chosen_dag", dag_run_id, api_chosen=api_chosen, selected_test_case=selected_test_case)
                    if dag_state:
                        output_col = 'pymupdf_output' if api_chosen == 'PyMuPDF' else 'docai_output'
                        cursor.execute(f"SELECT {output_col} FROM pdf_question_tb WHERE serial_num = %s", (selected_test_case,))
                        result = cursor.fetchone()
                        st.write(result)
                        if result:
                            extracted_text = result[0]
                            try:
                                extracted_json = json.loads(extracted_text)
                                pdf_text = extracted_json.get('text', None)
                                st.text_area(value=pdf_text, label="PDF extraction output", height=150)
                            except json.JSONDecodeError as j:
                                st.error(j)
                        else:
                            st.error("No output found for the selected test case.")
                    else:
                        st.error("Failed to extract PDF.")
                else:
                    st.error("Failed to trigger the DAG. Please try again.")

            st.write(f"Selected PDF Extraction Type: {api_chosen}")
            st.write(f"Selected LLM Model: {llm_chosen}")

            if st.button("Get LLM Output"):
                method_output = st.session_state.get('method_output', '')
                if method_output:
                    llm_output = get_llm_output(question, method_output)
                    st.text_area("LLM Output:", value=llm_output, height=200)
                else:
                    st.error("Please extract the PDF content first before generating LLM output!")

if __name__ == "__main__":
    user_landing()
