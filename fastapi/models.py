from sqlalchemy import Column, SmallInteger, String, JSON, Integer, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Model for the pdf_question_tb table
class DocumentTask(Base):
    __tablename__ = 'pdf_question_tb'  # Replace with the actual table name

    serial_num = Column(SmallInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(40), nullable=True)
    question = Column(String(2000), nullable=True)
    file_path = Column(String(500), nullable=True)
    pymupdf_output = Column(JSON, nullable=True)
    docai_output = Column(JSON, nullable=True)

    # Adding an index for task_id to speed up lookups
    __table_args__ = (
        Index('idx_task_id', 'task_id'),
    )

# Model for the log_tb table
class LogEntry(Base):
    __tablename__ = 'log_tb'  # Replace with the actual table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=True)
    task_id = Column(String(30), nullable=True)
    question = Column(String(2000), nullable=True)
    method = Column(String(50), nullable=True)
    method_output = Column(String(4000), nullable=True)
    llm_output = Column(String(2000), nullable=True)

