import os
from fastapi import FastAPI
import streamlit as st
import pandas as pd
from pages.db import DBConnection
from io import BytesIO
 
 
app = FastAPI()

st.title("XtractPDF App")

try:
    db = DBConnection.get_instance()
    cursor = db.get_cursor()
except Exception as e:
        st.error(f"Error connecting to the database: {e}")

@app.get("/questions")
def get_questions():
    cursor.execute('SELECT serial_num,task_id, question,file_path FROM pdf_question_tb;')
    pdf_ques_tb = cursor.fetchall()
    test_cases = pd.DataFrame(pdf_ques_tb, columns=cursor.column_names)
    return test_cases

    
def user_landing():
    # Connect to Amazon RDS Database
        test_cases = get_questions()
        test_cases_dict = dict(zip(test_cases['serial_num'], test_cases['question']))
        selected_test_case = st.selectbox("Select a Test Case:", options=test_cases["serial_num"], key="select_test_case")
        if selected_test_case:
            selected_question = test_cases_dict[selected_test_case]
            file_path = test_cases[test_cases['serial_num'] == selected_test_case]['file_path'].values[0]  # Get file path
            api_chosen = st.selectbox("Select a Method to extract PDF:", options=["PymuPDF","DocumentAI"], key="api_chosen")
        
            st.session_state['selected_test_case'] = selected_test_case  # Save selected test case in session state
            st.session_state['selected_question'] = selected_question    # Save selected question in session state
    
            # Display selected question
            st.write(f"Question: {selected_question}")
            st.write(f"Accessing File: {str(file_path).split("/")[-1]}")  # Print the file name with extension

            if st.button("Xtract PDF"):
                  st.switch_page('pages/extract_pdf.py')
    
             
        # Add the "Go to Summary" button
        if st.button("Go to Summary"):
                st.session_state["page"] = "summary"

if __name__ == "__main__":
    user_landing()
 
