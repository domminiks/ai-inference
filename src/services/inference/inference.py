from flask import Flask, jsonify, request
from skimage import io

import os
import time
import json
import redis
import redisai
import logging
import importlib


app = Flask(__name__)

redis_client = redisai.Client(host='redisai', port=6379)

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

model_extensions = {"tensorflow": "pb",
                    "tensorflow_lite": "pb",
                    "spark": "onnx",
                    "sklearn": "onnx",
                    "pytorch": "pt",
                    "onnx": "onnx"}


def unregister_tensor(tensor):
    redis_client.lpush('tensors_to_delete', tensor)


def create_outputs(model_name, model_version, size):
    model_outputs = []
    for i in range(size):
        model_outputs.append(model_name + "_" +
                             model_version + "_output_" + str(i) + "_" + str(time.time()))
    return model_outputs


def get_outputs(model_outputs):
    model_output_data = []
    try:
        for output in model_outputs:
            model_output_data.append(redis_client.tensorget(output))
    except redis.exceptions.ResponseError as err:
        pass
    return model_output_data


@ app.route('/inference/<model_name>/<model_version>/')
def run_inference(model_name, model_version):
    try:
        model_name_redis = model_name + '/' + model_version

        # Model path was mounted inside /inference because this script needs to import /utils for some models.
        # For Python, is better to use modules that are already inside the current folder.
        model_path = os.path.join('models',
                                  model_name,
                                  model_version)

        json_path = os.path.join(model_path,
                                 model_name + ".json")

        with open(json_path) as json_file:
            model_data = json.load(json_file)
            model = model_data['model']

        logger.info("JSON file for model '" + model_name_redis + "'opened.")

        model_utils_python_path = os.path.join(model_path,
                                               model['script']['folder']).replace(os.path.sep, '.')

        logger.info("Importing module 'formatter.py' from '" +
                    model_utils_python_path + "' for model '" + model_name_redis + "'")

        formatter = importlib.reload(importlib.import_module('.formatter',
                                                             model_utils_python_path))

        logger.info("Module 'formatter.py' for model '" +
                    model_name_redis + "' imported.")

        input_request = ''
        model_output_labels = []
        model_input_label = model_name + "_" + \
            model_version + "_input_" + str(time.time())

        logger.info("Parsing request...")

        if model['backend']['parameters']['input']['type'] == 'image':
            if model['backend']['type']:
                if request.files:
                    if 'image' in request.files:
                        logger.info("Getting input image from request...")
                        image = request.files['image']

                        input_parameter = io.imread(image)
                        logger.info("Image opened.")

                        input_ = formatter.pre_process(input_parameter)
                        logger.info("Image pre-processed.")

                        redis_client.tensorset(model_input_label, input_)
                        logger.info("Tensor set.")

                        model_output_labels = create_outputs(model_name,
                                                             model_version,
                                                             len(model['backend']['parameters']['output']['labels']))
                    else:
                        tag_name = list(request.files.keys())[0]
                        return jsonify(error="Bad Request",
                                       message="Image for inference must be place under a tag named 'image'. Tag name was '" + tag_name + "'"), 400
                else:
                    return jsonify(error="Bad Request",
                                   message="No input file provided. This request must be a 'multipart/form-data' request"), 400
            else:
                return jsonify(error="Bad Request",
                               message="Sorry, but only tensorflow models support images as input"), 400
        else:
            inference_request = request.get_json(force=True)
            input_parameter = inference_request['input']

            input_ = formatter.pre_process(input_parameter)

            redis_client.tensorset(model_input_label,
                                   input_,
                                   dtype=model['backend']['parameters']['input']['dtype'],
                                   shape=tuple(model['backend']['parameters']['input']['shape']))

            # For now we are assuming that our input shape is always [1, x], so we only need to get the second value.
            model_output_labels = create_outputs(model_name,
                                                 model_version,
                                                 model['backend']['parameters']['output']['shape'][1])

        redis_client.modelrun(model_name_redis,
                              [model_input_label],
                              model_output_labels)

        model_output_data = get_outputs(model_output_labels)

        logger.info("Post-processing...")
        output_ = formatter.post_process(model_output_data)

        if not isinstance(output_, dict):
            logger.error("Model '" + model_name_redis +
                         "' not found in RedisAI")
            return jsonify(error="Bad Request", message="'post_process' module did not return a valid dict"), 400

        return jsonify(output=output_)

    except IndexError as err:
        logger.error("Index selected probably inside 'post_process' module for model '" +
                     model_name_redis + "' is invalid.")
        logger.error(str(err))
        return jsonify(error="Conflict", message="Index selected probably inside 'post_process' module for model '" +
                       model_name_redis + "' is invalid.", details=str(err)), 409

    except TypeError as err:
        logger.error("Tensor type for model '" +
                     model_name_redis + "' is invalid.")
        logger.error(str(err))
        return jsonify(error="Bad Request", message="Tensor type for model '" + model_name_redis + "' is invalid", details=str(err)), 404

    except redis.exceptions.ResponseError as err:
        err_message = str(err)
        if err_message == "model key is empty":
            logger.error("Model '" + model_name_redis +
                         "' not registered in RedisAI")
            logger.error(str(err))
            return jsonify(error="Not Found", message="Model '" + model_name_redis + "' is not loaded"), 404
        logger.error("Error inferencing model '" + model_name_redis + "'")
        logger.error(str(err))
        return jsonify(error="Internal Server Error", message="Error inferencing model '" + model_name_redis + "'", details=str(err)), 500

    except OSError as err:
        logger.error("Model '" + model_name_redis + "' not found")
        logger.error(str(err))
        return jsonify(error="Not Found", message="Model not loaded"), 404

    except Exception as err:
        logger.error("Error during inference for model '" +
                     model_name_redis + "'")
        logger.error(str(err))
        return jsonify(error="Internal Server Error", message="Inference failed for model '" + model_name_redis + "'", details=str(err)), 404
    finally:
        unregister_tensor(model_input_label)
        for label in model_output_labels:
            unregister_tensor(label)
