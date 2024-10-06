from sqlalchemy import Column, SmallInteger, String, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentTask(Base):
    __tablename__ = 'pdf_question_tb'  # Replace with the actual table name

    serial_num = Column(SmallInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(40), nullable=True)
    question = Column(String(2000), nullable=True)
    file_path = Column(String(500), nullable=True)
    pymupdf_output = Column(JSON, nullable=True)
    docai_output = Column(JSON, nullable=True)

