import os
from fastapi import FastAPI
import streamlit as st
import pandas as pd
from pages.db import DBConnection
import requests
import time  # For polling the DAG run status
import json

app = FastAPI()

try:
    db = DBConnection.get_instance()
    cursor = db.get_cursor()
except Exception as e:
    st.error(f"Error connecting to the database: {e}")

@app.get("/questions")
def get_questions():
    cursor.execute('SELECT serial_num, task_id, question, file_path FROM pdf_question_tb;')
    pdf_ques_tb = cursor.fetchall()
    test_cases = pd.DataFrame(pdf_ques_tb, columns=cursor.column_names)
    return test_cases

def trigger_airflow_dag(dag_id, api_chosen, file_path):
    # Airflow API URL
    airflow_url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns"
    
    # Data to trigger the DAG with API chosen and file path
    data = {
        "conf": {
            "api_chosen": api_chosen,
            "file_path": file_path  # Pass the file path
        }
    }

    # Trigger the DAG
    response = requests.post(airflow_url, json=data, auth=("airflow", "airflow"))
    
    if response.status_code == 200:
        st.success("Airflow DAG triggered successfully!")
        dag_run_id = response.json()["dag_run_id"]  # Capture the DAG run ID
        return dag_run_id
    else:
        st.error(f"Failed to trigger DAG: {response.text}")
        return None


def get_dag_run_output(dag_id, dag_run_id, api_chosen, selected_test_case):
    airflow_dag_run_url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
    
    while True:
        response = requests.get(airflow_dag_run_url, auth=("airflow", "airflow"))
        #st.write(response.json())
        if response.status_code == 200:
            dag_run_info = response.json()
            state = dag_run_info["state"]
            
            if state == "success":
                st.success("DAG run completed successfully!")
                return True
            
                

            elif state == "failed":
                st.error("DAG run failed!")
                return False
           
        else:
            st.error(f"Failed to fetch DAG run status: {response.text}")
            return False


def user_landing():
    col1, col2 = st.columns(2)
    with col1:
        st.header("XtractPDF App")
    with col2:
        if st.button("Go to Summary"):
            st.session_state["page"] = "summary"

    test_cases = get_questions()
    test_cases_dict = dict(zip(test_cases['serial_num'], test_cases['question']))
    selected_test_case = st.selectbox("Select a Test Case:", options=test_cases["serial_num"], key="select_test_case")

    if selected_test_case:
        selected_question = test_cases_dict[selected_test_case]
        file_path = test_cases[test_cases['serial_num'] == selected_test_case]['file_path'].values[0]  # Get file path

        st.session_state['selected_test_case'] = selected_test_case  # Save selected test case in session state
        st.session_state['selected_question'] = selected_question    # Save selected question in session state

        # Display selected question
        st.write(f"Question: {selected_question}")
        st.write(f"Accessing File: {str(file_path).split('/')[-1]}")  # Print the file name with extension

        c1, c2 = st.columns(2)
        with c1:
            api_chosen = st.selectbox("PDF Extraction Type", options=['PyMuPDF', 'documentAi'], key='api_chosen')
        with c2:
            st.selectbox("LLM Model", options=['GPT4', 'GPT4o'], key="LLM_chosen")

        llm_chosen = st.session_state.LLM_chosen

        # Extract PDF button
        if st.button("Extract PDF"):
            dag_run_id = trigger_airflow_dag("api_chosen_dag", api_chosen, file_path)  # Get DAG run ID
            if dag_run_id:
                # Poll for the DAG result and fetch the extracted text
                dag_state = get_dag_run_output("api_chosen_dag", dag_run_id, 
                                                api_chosen=api_chosen, selected_test_case=selected_test_case)

                # If DAG state is successful, display success message and Preview PDF button
                if dag_state:
                    st.success("PDF Preview is ready!")
                    st.session_state['preview_ready'] = True
                else:
                    st.error("Failed to extract PDF. Please try again.")
            else:
                st.error("Failed to extract PDF. Please try again.")

        # Preview PDF button (only shown if preview is ready)
        if st.session_state.get('preview_ready'):
            if st.button("Preview PDF"):
                output_col = 'pymupdf_output' if api_chosen == 'PyMuPDF' else 'docai_output'

                # Query the database to get the extracted text based on the selected serial number
                cursor.execute(f"SELECT {output_col} FROM pdf_question_tb WHERE serial_num = %s", (selected_test_case,))
                result = cursor.fetchone()

                if result:
                    extracted_text = result[0]
                    try:
                        # Attempt to parse JSON formatted text
                        extracted_json = json.loads(extracted_text)
                    except (TypeError, json.JSONDecodeError) as e:
                        st.error(f"Failed to load JSON: {str(e)}")
                        extracted_json = {}

                    pdf_text = extracted_json.get('text', extracted_text)  # Fallback to extracted_text if not JSON
                    st.text_area(value=pdf_text, label="PDF extraction output", height=150)  # Display the extracted text

                    
                else:
                    st.error("No output found for the selected test case.")
            
        st.write("LLM Output: Test output 1344")

        # Print the selected values
        st.write(f"Selected PDF Extraction Type: {api_chosen}")
        st.write(f"Selected LLM Model: {llm_chosen}")

if __name__ == "__main__":
    user_landing()
