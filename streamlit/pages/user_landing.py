import os
from fastapi import FastAPI
import streamlit as st
import pandas as pd
from pages.db import DBConnection
from io import BytesIO
import requests

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

def trigger_airflow_dag(dag_id, api_chosen):
    # Airflow API URL
    airflow_url = f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns"
    
    # Data to trigger the DAG with PDF path and username
    data = {
        "conf": {
            "api_chosen": api_chosen  # Pass only the chosen API method
        }
    }


    response = requests.post(airflow_url, json=data, auth=("airflow", "airflow"))
    if response.status_code == 200:
        st.success("Airflow DAG triggered successfully!")
        return response.json()  # Capture the response from the DAG
    else:
        st.error(f"Failed to trigger DAG: {response.text}")
        return None



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

        # if st.button("Extract PDF"):
        #     username = st.session_state.get('username', 'default_username')  # Retrieve the username from session state
        #     trigger_airflow_dag("api_chosen_dag", file_path, username)

        if st.button("Extract PDF"):
            #username = st.session_state.get('username', 'default_username')  # Retrieve the username from session state
            output = trigger_airflow_dag("api_chosen_dag", api_chosen)  # Get output from the DAG
            print(output)

            # Check if the output is valid and display it
            if output:
                api_chosen_output = output['conf'].get('api_chosen')  # Extract the relevant output
                # st.write(api_chosen_output)
                st.text_area(value=api_chosen_output,label="PDF extraction output", height=150)  # Display the output
            else:
                st.error("Failed to extract PDF. Please try again.")

        st.write("LLM Output: Test output 1344")

        # Print the selected values
        st.write(f"Selected PDF Extraction Type: {api_chosen}")
        st.write(f"Selected LLM Model: {llm_chosen}")

if __name__ == "__main__":
    user_landing()
