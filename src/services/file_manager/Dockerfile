FROM python:3.8

ENV MODELS_ROOT_PATH=/models

ADD . /file_manager

WORKDIR /file_manager

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app", "-w", "3"]