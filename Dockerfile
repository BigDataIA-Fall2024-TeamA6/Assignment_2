# Step 1: Specify the base image
FROM python:3.12-slim

# Step 2: Set a working directory inside the container
WORKDIR /app

# Step 3: Copy your project files (including pyproject.toml and lockfile) into the container
COPY pyproject.toml poetry.lock /app/
COPY streamlit/ /app/

# Step 4: Install Poetry and project dependencies
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Step 5: Expose port 8501
EXPOSE 8501 

# Step 6: Specify the command to run your application
CMD ["poetry", "run", "streamlit", "run", "/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
