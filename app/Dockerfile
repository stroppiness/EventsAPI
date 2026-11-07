FROM python:3.12-slim

WORKDIR /code

COPY app/requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY app ./app

ENV PYTHONPATH=/code/app
WORKDIR /code/app

CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
#CMD ["sh", "-c", "python reset_db.py && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]