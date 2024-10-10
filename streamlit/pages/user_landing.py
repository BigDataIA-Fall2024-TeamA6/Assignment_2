import os
from fastapi import FastAPI
import streamlit as st
import pandas as pd
from pages.db import DBConnection
import requests
import json
from openai import OpenAI

app = FastAPI()
FASTAPI_URL = "http://127.0.0.1:8000"

api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    api_key = st.secrets["OPENAI_API_KEY"]

try:
    db = DBConnection.get_instance()
    cursor = db.get_cursor()
except Exception as e:
    st.error(f"Error connecting to the database: {e}")
    
def insert_log_into_log_tb(task_id, question, method, username, method_output):
    try:
        # Treat method_output as plain text (not JSON)
        method_output_text = str(method_output)

        insert_query = """
        INSERT INTO log_tb (task_id, question, method, username, method_output)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (task_id, question, method, username, method_output_text))
        db.get_connection().commit()  # Commit the transaction
        st.success("Log successfully inserted into log_tb!")
    except Exception as e:
        st.error(f"Error inserting into log_tb: {e}")
        db.get_connection().rollback()

# Function to update log_tb with LLM output
def update_log_with_llm_output(task_id, llm_output):
    try:
        update_query = """
        UPDATE log_tb SET llm_output = %s WHERE task_id = %s
        """
        cursor.execute(update_query, (llm_output, task_id))
        db.get_connection().commit()  # Commit the transaction
        st.success("LLM output successfully updated in log_tb!")
    except Exception as e:
        st.error(f"Error updating LLM output in log_tb: {e}")
        db.get_connection().rollback()

def get_questions():
    # response = requests.get(f"{FASTAPI_URL}/questions")
    # if response.status_code == 200:
    cursor.execute('SELECT serial_num, task_id, question, file_path FROM pdf_question_tb;')
    pdf_ques_tb = cursor.fetchall()
    test_cases = pd.DataFrame(pdf_ques_tb, columns=cursor.column_names)
    return test_cases
    # elif response.status_code == 500:
    #     st.error(f"Error {response.status_code} Server down :(")
    #     return "Error fetching questions"
    # else: st.error (f"Error : {response.status_code} : {response.text}")

def get_llm_output(question, extraction_output):
    try:
        api_url = "http://localhost:8000/get_llm_output"
        response = requests.post(api_url, json={"question": question, "extracted_output": extraction_output})
        if response.status_code == 200:
            return response.json().get("llm_output", "Value not found")
        elif response.status_code == 422:
            st.error(f"LLM Output failed: {response.status_code} {response.text}")
            return ""
    except Exception as e:
        st.error(f"Error calling LLM API: {e}")
        return ""

        


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
        # st.success("Airflow DAG triggered successfully!")
        dag_run_id = response.json()["dag_run_id"]  # Capture the DAG run ID
        return dag_run_id
    else:
        st.error(f"Failed to trigger DAG: {response.text}")
        return None
    
def trigger_docai(dag_id, api_chosen, file_path):
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
        st.success("DocAI Airflow DAG triggered successfully!")
        dag_run_id = response.json()["dag_run_id"]  # Capture the DAG run ID
        return dag_run_id
    else:
        st.error(f"Failed to trigger DAG: {response.text}")
        return None
    

def get_dag_run_output(dag_id, dag_run_id,api_chosen,selected_test_case):
    airflow_dag_run_url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
    
    while True:
        response = requests.get(airflow_dag_run_url, auth=("airflow", "airflow"))
        if response.status_code == 200:
            dag_run_info = response.json()
            state = dag_run_info['task_instances'][1]['state']
            
            if state == "success":
                st.success("DAG run completed successfully!")
                r = requests.get(url=f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances",auth=("airflow", "airflow"))
                return True
            

            elif state == "failed":
                st.error("DAG run failed!")
                return False
            
        else:
            st.error(f"Failed to fetch DAG run status: {response.text}")
            return False
        

def fetch_from_db(output_col: str, selected_test_case: int):
    url = f"{FASTAPI_URL}/fetchrecords/?output_col={output_col}&selected_test_case={selected_test_case}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error calling API:", response.status_code, response.text)


    
def user_landing():
    if "pdf_extracted" not in st.session_state:
        st.session_state.pdf_extracted = False

    col1, col2 = st.columns(2)
    with col1:
        st.header("XtractPDF App")
    with col2:
        if st.button("Go to Summary"):
            st.switch_page("pages/summary.py")
        
    if 'username' not in st.session_state:
        st.error("You need to log in first!")
        st.stop()
        
    username = st.session_state['username']
    
    test_cases = get_questions()
    test_cases_dict = dict(zip(test_cases['serial_num'], test_cases['question']))
    selected_test_case = st.selectbox("Select a Test Case:", options=test_cases["serial_num"], key="select_test_case")

    if selected_test_case:
        selected_question = test_cases_dict[selected_test_case]
        file_path = test_cases[test_cases['serial_num'] == selected_test_case]['file_path'].values[0]  # Get file path

        st.session_state['selected_test_case'] = selected_test_case  # Save selected test case in session state

        question = st.text_area("Question:", value=selected_question, key="edited_question")
        st.session_state['selected_question'] = question    # Save selected question in session state
        st.write(f"Accessing File: {str(file_path).split('/')[-1]}")  # Print the file name with extension

        serial_num = selected_test_case
        task_id = serial_num
        
        c1, c2 = st.columns(2)
        with c1:
            api_chosen = st.selectbox("PDF Extraction Type", options=['PyMuPDF', 'documentAi'])
        with c2:
            st.selectbox("LLM Model", options=['GPT4', 'GPT4o'], key="LLM_chosen")

        dag_name = "api_chosen_dag" if api_chosen == 'PyMuPDF' else "docai_dag"
        st.session_state["api_chosen"] = api_chosen

        if st.button("Extract PDF"):
                dag_run_id = trigger_airflow_dag(dag_name, api_chosen, file_path)  # Get DAG run ID
                if dag_run_id:
                    # Poll for the DAG result and fetch the extracted text
                    dag_state = get_dag_run_output(dag_name, dag_run_id, 
                                                        api_chosen=api_chosen, selected_test_case=selected_test_case)
                    if dag_state:
                        output_col = 'pymupdf_output' if api_chosen == 'PyMuPDF' else 'docai_output'
                        result = fetch_from_db(output_col,selected_test_case)
                        try:
                            res_json = json.loads(result[output_col])
                            pdf_text = res_json.get('text',None)
                            st.text_area(value = pdf_text, label="PDF extraction output", height=150)
                            st.session_state.method_output = pdf_text
                            st.session_state.pdf_extracted = True
                            insert_log_into_log_tb(task_id, question, api_chosen, username, pdf_text)
    
                        except json.JSONDecodeError as j:
                            st.error(j)
                            pass
                    else:
                        st.error("No output found for the selected test case.")
                        
    if st.session_state.pdf_extracted:
        if(st.button("LLM Output")):
            question = st.session_state.get('selected_question')
            pdf_text = st.session_state.get('method_output')
            task_id = st.session_state.get('selected_test_case')
            llm_output = get_llm_output(question, pdf_text)
            st.text_area(value = llm_output, label="LLM output", height=150)
            update_log_with_llm_output(task_id, llm_output)
                        
                        
                        



if __name__ == "__main__":
    user_landing()
