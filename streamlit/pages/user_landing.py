import os
from fastapi import FastAPI
import streamlit as st
import pandas as pd
from pages.db import DBConnection
from io import BytesIO
 
 
app = FastAPI()


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
        col1,col2 = st.columns(2)
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
            st.write(f"Accessing File: {str(file_path).split("/")[-1]}")  # Print the file name with extension

            #api_chosen = st.selectbox("Select a Method to extract PDF:", options=["PymuPDF","DocumentAI"], key="api_chosen")
            
            
            c1,c2 =  st.columns(2)
            with c1:
                st.selectbox("PDF Extraction Type",options=['pymupdf','documentAi'],key='api_chosen')

            with c2:
                st.selectbox("LLM Model",options=['GPT4','GPT4o'],key="LLM_choosen")

            # Retrieve the selected values
            pdf_extraction = st.session_state.api_chosen
            llm_chosen = st.session_state.LLM_choosen

            if st.button("Extract PDF"):
                  st.switch_page('pages/extract_pdf.py')
    
            st.text_area(label="PDF extraction output",height=200)
            st.write("LLM Output: Test output 1344  ")
            
            # Print the selected values
            st.write(f"Selected PDF Extraction Type: {pdf_extraction}")
            st.write(f"Selected LLM Model: {llm_chosen}")
             
        # # Add the "Go to Summary" button
        # if st.button("Go to Summary"):
        #         st.session_state["page"] = "summary"

if __name__ == "__main__":
    user_landing()
 
