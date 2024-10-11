
---

## **Assignment 2 - Automated Text Extraction & Client Application for GAIA Dataset**

### **Contributors**:
- Sahiti Nallamolu    33%
- Vishodhan Krishnan  33%
- Vismay Devjee       33%



### **Project Resources**:
---
a. **Diagrams**: [GAIA Model Evaluation Workflow](https://github.com/BigDataIA-Fall2024-TeamA6/Assignment_2)  
b. **Fully Documented Code Labs**: [Codelabs Preview](https://codelabs-preview.appspot.com/?file_id=1ZGC6z68GhI9cBCVnVT5GIKWnzV1W4MHhyUIaEwnXQ-Q/edit)  
c. **Video of the Submission**: [Zoom Recording](https://northeastern.zoom.us/rec/share/MQzuXGKgKpGnDPtB6VAmGLEtU0ioh_46KcFMUtSH9CtFNUAalQ6dVYT5xFjuA7iw.V3glsyZ5cz9BKUDt)  
d. **Link to Working Application**: [Streamlit App](https://team6app1.streamlit.app/)  
e. **GitHub Project**: [GitHub Repository](https://github.com/BigDataIA-Fall2024-TeamA6/Assignment_2)



## Synopsis

This project centers on creating an **automated pipeline** for **text extraction** from the ***GAIA dataset***, utilizing both **open-source methods** (such as **PyMuPDF**) and **enterprise solutions** (like **Google Document AI**). These extraction methods are seamlessly integrated with a **client-facing application** built on **Streamlit**, enabling users to interact with the processed PDF documents, query their contents, and visualize the results. The backend is secured by **FastAPI** with **JWT authentication**, ensuring safe access to the API endpoints.


### Technologies Used:
- **Apache Airflow**: Automation and scheduling of PDF extraction pipelines.
- **FastAPI**: API backend for managing extraction logic and querying models.
- **Streamlit**: Frontend for user interaction and display of results.
- **AWS RDS**: Database for storing logs and extracted information.
- **Amazon S3**: Storage of processed PDF files.
- **Google Document AI**: API-based text extraction.
- **PyMuPDF**: Open-source PDF extraction.
- **OpenAI GPT-4**: Language model for generating insights from extracted PDFs.
- **Docker**: Containerization of FastAPI and Streamlit apps for deployment.

## Problem Statement

The aim of this project is to develop a **comprehensive text extraction and analysis tool** that supports multiple extraction methods and offers a user-friendly interface for interacting with the results. The project addresses:
- Automating PDF extraction using Airflow pipelines.
- Integration with both open-source and API-based PDF extraction methods (PyMuPDF and Google Document AI).
- Secure, role-based access using FastAPI's authentication.
- Querying and answering questions using extracted PDF data via OpenAI GPT-4.
- User logging and history tracking for admins and regular users.


## Desired Outcome

The tool offers:
- **Selection of text extraction methods** ***(PyMuPDF*** or ***Google Document AI)***.
- **Automatic PDF processing** with **Airflow DAGs**.
- **Integration with GPT-4** for **question-answering** based on extracted content.
- **User authentication** and **logs** of processed tasks.
- **Admin panel** for viewing **extraction logs** and **system statistics**.
---

## File Structure

```bash
Assignment_2/
  ├── airflow/
  │   ├── dags/
  │   │   └── api_chosen_dag.py     #DAG definition for triggering PDF extractions using PyMuPDF
  │   │   └── docai_dag.py          #DAG definition for triggering PDF extractions using Google Document AI
  │   └── docker-compose.yaml   #Airflow deployment configuration
  ├── streamlit/
  │   ├── app.py                #Main Streamlit application
  │   ├── pages/
  │   │   └── admin.py              #Admin page for viewing logs
  │   │   └── create_user.py        #User creation form
  │   │   └── db.py                 #Define db Connections
  │   │   └── summary.py:           #User summary page to view Log Reports
  │   │   └── user_landing.py       #Main landing page for users
  │   └── .env                  #Configuration file for API keys and database connection
  ├── FastAPI/
  │   └── main.py               #FastAPI application for PDF extraction and GPT-4 integration
  │   └── models.py             #FastAPI application for PDF extraction and GPT-4 integration (Change description)
  ├── diagrams/
  │   └── architecture_diagram.py   #Python code for generating the system diagram
  ├── poetry.lock               #Poetry dependencies lock file
  └── README.md                 #Project documentation
```


## How It Works
1. **PDF Extraction**: Users can select PDFs from the GAIA dataset to be processed using either PyMuPDF or Google Document AI. The extraction process is automated using Airflow DAGs, which schedule and trigger the PDF extraction tasks.
2. **Custom Prompt**: After the PDF is processed, users can enter a custom prompt to interact with the extracted content, refining the input before querying the model.
3. **Model Querying**: The extracted content, along with the custom prompt, is passed to OpenAI's GPT-4 model. The model generates answers to user-defined questions based on the content of the PDF.
4. **Authentication**: Users are authenticated via FastAPI, ensuring secure access to the system. Each task performed is logged, and users can track their history and interactions.
5. **Admin Panel**: Admin users have access to a panel where they can view detailed logs of all extraction tasks, including user queries, extracted content, and the model’s responses. This allows for system monitoring and auditing.

## Diagrams

Include architecture diagrams (e.g., workflow, data flow) to illustrate the system setup and interactions.

---

This structure follows your project and provides a detailed overview of how to set up, run, and interact with your system. Feel free to modify it further based on your requirements or preferences.


---

### **Desired Outcome**

The application will allow users to:
- Register and securely log in using JWT-based authentication.
- Query extracted text from PDF documents, selecting between open-source or API-based extraction methods.
- View extracted information and interact with the system in a user-friendly manner.

---

### **Steps to Run this Application**

1. **Clone this repository** to your local machine:

   ```bash
   git clone https://github.com/your-repo.git
   ```

2. **Install all required dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Add your credentials** to a `.env` file under the `/streamlit` and `/airflow` folders:

   - AWS Access Key
   - AWS Secret Access Key
   - OpenAI API Key (if applicable)
   - Database credentials for Amazon RDS

4. **Run the applications**:

   - **Airflow** (for pipeline automation):

     ```bash
     docker-compose -f airflow/docker-compose.yaml up
     ```

   - **Streamlit** (for the user interface):

     ```bash
     streamlit run streamlit/app.py
     ```

5. **Using the Application**:
   - **Register and Log in**: Create an account, log in, and access the application.
   - **Query PDF Documents**: Choose between opensource or API-based extraction and query PDF extracts.
   - **View Results**: Visualize the extracted text and document data.

---
### **Architecture Diagram**

The architecture of the application includes a frontend (Streamlit), a backend (FastAPI), an Airflow pipeline for automating text extraction, and storage on AWS (S3 and RDS). The diagram provides a visual breakdown of these components and their interactions.

---

### **References**

1. [Airflow Documentation](https://airflow.apache.org/)
2. [FastAPI Documentation](https://fastapi.tiangolo.com/)
3. [Streamlit Documentation](https://docs.streamlit.io/)
4. [AWS Textract Documentation](https://aws.amazon.com/textract/)
5. [PyPDF Documentation](https://pypdf.readthedocs.io/)

---
