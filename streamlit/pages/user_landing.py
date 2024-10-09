import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import openai  # Replace OpenAI with openai
from pages.db import DBConnection  # Assuming DBConnection is in pages/db.py
import json
import requests

# Load environment variables from a .env file
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key is None:
    api_key = st.secrets["OPENAI_API_KEY"]

openai.api_key = api_key  # Set API key

# Establish database connection
try:
    db = DBConnection.get_instance()
    cursor = db.get_cursor()
except Exception as e:
    st.error(f"Error connecting to the database: {e}")

# Function to insert log into log_tb with extracted PDF output in method_output column
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

# Function to get LLM output via FastAPI
def get_llm_output(question, extraction_output):
    try:
        api_url = "http://localhost:8000/get_llm_output"
        response = requests.post(api_url, json={"question": question, "extracted_output": extraction_output})
        if response.status_code == 200:
            return response.json().get("llm_output", "")
        else:
            st.error(f"Failed to fetch LLM output: {response.text}")
            return ""
    except Exception as e:
        st.error(f"Error calling LLM API: {e}")
        return ""

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
                # Directly fetch from the database instead of triggering a DAG
                output_col = 'pymupdf_output' if api_chosen == 'PyMuPDF' else 'docai_output'
                cursor.execute(f"SELECT {output_col} FROM pdf_question_tb WHERE serial_num = %s", (selected_test_case,))
                result = cursor.fetchone()
                if result:
                    extracted_text = result[0]
                    try:
                        extracted_json = json.loads(extracted_text)
                        pdf_text = extracted_json.get('text', None)
                        st.text_area(value=pdf_text, label="PDF extraction output", height=150)
                        st.session_state['method_output'] = pdf_text  # Save the extracted output for later use

                        # Insert into log_tb after displaying PDF content
                        insert_log_into_log_tb(task_id, question, api_chosen, username, pdf_text)

                    except json.JSONDecodeError as j:
                        st.error(j)
                else:
                    st.error("No output found for the selected test case.")

            if st.button("Get LLM Output"):
                method_output = st.session_state.get('method_output', '')
                if method_output:
                    llm_output = get_llm_output(question, method_output)
                    st.text_area("LLM Output:", value=llm_output, height=200)

                    # Update log_tb with LLM output
                    update_log_with_llm_output(task_id, llm_output)
                else:
                    st.error("Please extract the PDF content first before generating LLM output!")

if __name__ == "__main__":
    user_landing()
