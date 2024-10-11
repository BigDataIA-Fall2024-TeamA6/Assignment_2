from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.onprem.workflow import Airflow
from diagrams.onprem.analytics import Pypdf
from diagrams.onprem.client import Users
from diagrams.onprem.network import Internet
from diagrams.onprem.container import Docker
from diagrams.saas.chat import GoogleChat
from diagrams.programming.language import Python
from diagrams.generic.blank import Blank

with Diagram("GAIA Dataset Workflow", show=False):
    users = Users("Users")

    with Cluster("GAIA Dataset"):
        gaia_dataset = S3("GAIA Dataset (PDF Files)")

    with Cluster("Apache Airflow (Data Pipeline)"):
        airflow = Airflow("Apache Airflow")

    with Cluster("Text Extraction"):
        with Cluster("Options"):
            open_source = Pypdf("PyPDF (Open-source Option)")
            google_ai = GoogleChat("Google Document AI (API Option)")
        
        text_extraction = [open_source, google_ai]
    
    with Cluster("Data Storage"):
        aws_rds = RDS("AWS RDS")

    with Cluster("Backend"):
        fastapi = Python("FastAPI (with JWT Auth)")

    with Cluster("Frontend"):
        streamlit = Python("Streamlit Frontend")

    with Cluster("Docker Containers"):
        docker_airflow = Docker("Airflow Container")
        docker_fastapi = Docker("FastAPI Container")
        docker_streamlit = Docker("Streamlit Container")

    with Cluster("Cloud Platform"):
        cloud = EC2("Cloud (AWS, GCP, Azure)")

    users >> Edge(label="Interaction") >> streamlit
    streamlit >> fastapi >> aws_rds
    airflow >> text_extraction >> aws_rds
    gaia_dataset >> airflow
    docker_airflow - docker_fastapi - docker_streamlit >> cloud
