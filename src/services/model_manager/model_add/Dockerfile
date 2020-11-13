FROM python:3.8

ENV MODELS_ROOT_PATH=/models

ADD . /model_add

WORKDIR /model_add

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "wsgi:add_model_to_redis()", "-w", "3", "--timeout", "0"]