from ml2rt import load_model

import os
import json
import logging
import redisai

MODELS_PATH = os.environ['MODELS_ROOT_PATH']

model_extensions = {"tensorflow": "pb",
                    "spark": "onnx",
                    "sklearn": "onnx",
                    "pytorch": "pt",
                    "onnx": "onnx"}

redis_backend = {"tensorflow": "TF",
                 "tensorflow_lite": "TFLITE",
                 "spark": "ONNX",
                 "sklearn": "ONNX",
                 "pytorch": "TORCH",
                 "onnx": "ONNX"}

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redisai.Client(host='redisai', port=6379)


def add_model_to_redis():
    try:
        while True:
            new_model = redis_client.blpop('models_to_add')[1].decode('utf-8')

            logger.info("New model to add: '" + new_model + "'")

            [model_name, model_version] = new_model.split('/')

            model_path = os.path.join(MODELS_PATH,
                                      model_name,
                                      model_version)

            json_path = os.path.join(model_path, model_name + ".json")

            if os.path.isfile(json_path):
                with open(json_path) as json_file:
                    model_data = json.load(json_file)
                    model = model_data['model']

            model_file = os.path.join(model_path,
                                      model_name +
                                      '.' +
                                      model_extensions[model['backend']['type']])

            logger.info("Loading model: '" + new_model + "'")
            loaded_model = load_model(model_file)

            logger.info("Model '" + new_model +
                        "' loaded. Registering model in RedisAI...")

            if (model['backend']['type'] == 'tensorflow'):
                redis_client.modelset(new_model,
                                      redis_backend[model['backend']['type']],
                                      'CPU',
                                      inputs=model['backend']['parameters']['input']['labels'],
                                      outputs=model['backend']['parameters']['output']['labels'],
                                      data=loaded_model)
            else:
                redis_client.modelset(new_model,
                                      model_extensions[model['backend']
                                                       ['type']],
                                      'CPU',
                                      loaded_model)

            logger.info("New model added to RedisAI: '" + new_model + "'")
    except Exception as err:
        logger.error("Error during model registration to RedisAI: " + str(err))
