FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
EXPOSE 8501

CMD ["bash", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501"]
