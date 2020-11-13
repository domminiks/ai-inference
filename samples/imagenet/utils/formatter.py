import numpy as np

import json
import cv2
import os

models_path = os.environ['MODELS_ROOT_PATH_INFERENCE']

data_path = os.path.join(models_path, 'imagenet', '1', 'utils', 'data')

class_idx = json.load(
    open(os.path.join(data_path, "imagenet_classes.json")))


def pre_process(input_):
    img = cv2.resize(input_, (224, 224))
    return np.expand_dims(np.divide(img.astype(np.float32), 255), 0)


def post_process(output):
    out = output[0].argmax() - 1
    # tf model has 1001 classes, hence negative 1
    return {"class": class_idx[str(out)]}
