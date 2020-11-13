import pickle
import os

import logging

from flask import jsonify

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

models_path = os.environ['MODELS_ROOT_PATH_INFERENCE']

data_path = os.path.join(models_path, 'sentiment', '1', 'utils', 'data')

sentiment = {0: "This is bad!", 1: "This is good!"}


def pre_process(text):
    tdif = pickle.load(open(data_path + '/tdif.pkl', 'rb'))
    count = pickle.load(open(data_path + '/count.pkl', 'rb'))
    return tdif.transform(count.transform([text])).toarray()


def post_process(output):
    return {"sentiment": sentiment[int(output[0][0])]}
