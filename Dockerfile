FROM tiangolo/meinheld-gunicorn:python3.6

COPY ./app /app

RUN pip install -r /app/requirements.txt

