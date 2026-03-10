FROM python:3.11-slim
COPY ./app /app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends graphviz && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip
RUN pip install  -r requirements.txt
CMD ["streamlit", "run", "app.py"]
