FROM python:3.8

ADD . /model_remove

WORKDIR /model_remove

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "wsgi:remove_model_from_redis()", "-w", "3", "--timeout", "0"]