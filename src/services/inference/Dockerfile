FROM python:3.8

ENV MODELS_ROOT_PATH=/models

ENV MODELS_ROOT_PATH_INFERENCE=/inference/models

ADD . /inference

WORKDIR /inference

RUN apt-get update

RUN apt-get install ffmpeg libsm6 libxext6 -y

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "wsgi:app", "-w", "3"]