FROM python:3.8

ADD . /tensor_remove

WORKDIR /tensor_remove

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "wsgi:remove_tensor_from_redis()", "-w", "3", "--timeout", "0"]