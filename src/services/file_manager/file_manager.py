from schemas.create_request_schema import create_request_schema
from schemas.file_schema import file_schema

from jsonschema import validate, exceptions

from flask import Flask, jsonify, request

from stringcase import snakecase

import os
import json
import gdown
import shutil
import redisai
import logging
import threading

MODELS_PATH = os.environ['MODELS_ROOT_PATH']  # 'models'

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

redis_client = redisai.Client(host='redisai', port=6379)

model_extensions = {"tensorflow": "pb",
                    "spark": "onnx",
                    "sklearn": "onnx",
                    "pytorch": "pt",
                    "onnx": "onnx"}


def register_model(model_name, model_version):
    redis_client.lpush('models_to_add',
                       model_name + "/" + str(model_version))


def unregister_model(model_name, model_version):
    redis_client.lpush('models_to_delete',
                       model_name + "/" + str(model_version))


# Downloads a .zip file from Google Drive using gdown
def download_zip_file(url, model_name, model_path, model_version=None):
    '''
    Args:
        url (string): URL for downloading the .zip file
            Ex: https://drive.google.com/uc?id=<file_ID_on_Google_Drive>
        model_name (string): the name of the file
            Ex: model_1
        model_path (string): the destination path to hold the model .zip file
            Ex: /path/to/model
    '''
    # file = requests.get(url, stream=True)
    with app.app_context():
        destination_path = os.path.join(model_path, model_name)
        try:
            logger.info("Downloading .zip file for model '" +
                        model_name + "'...")
            gdown.download(url, destination_path + ".zip", quiet=False)
            logger.info("Extracting files for model '" + model_name + "'...")
            gdown.extractall(destination_path + ".zip", model_path)
            logger.info("Removing .zip file for model '" + model_name + "'...")
            os.remove(destination_path + ".zip")

        except OSError as err:
            logger.error(".zip file removal failed")
            return False, str(err)

        except Exception as err:
            logger.error(str(err))
            return False, str(err)

        logger.info("Files for model '" +
                    model_name + "' downloaded end extracted sucessfully")

        if model_version:
            is_validated, status_code = validate_model_files(model_name,
                                                             model_version)
            if status_code == 200:
                register_model(model_name, model_version)
                logger.info("Model '" + model_name + "/" +
                            model_version + "' triggered to Redis")
            else:
                delete_model_version_thread(model_name, model_version)
                logger.error("Download request for model '" + model_name + "' version '" +
                             model_version + "' failed. Model validation failed.")
                return False, is_validated

        return True, "Files for model '" + model_name + "' downloaded end extracted sucessfully"


def delete_folder(path):
    shutil.rmtree(path)


@app.route('/models/', methods=['GET'])
def get_models():
    models = [model.name
              for model in os.scandir(MODELS_PATH)
              if model.is_dir()]
    # Showing models in order...
    models.sort()

    if not models:
        return jsonify(message="No models are available"), 200

    return jsonify(models=models)


@app.route('/models/<model_name>', methods=['GET'])
def get_model_details(model_name):
    model_path = os.path.join(MODELS_PATH, model_name)
    if os.path.exists(model_path):
        versions = {version.name: ""
                    for version in os.scandir(model_path)
                    if version.is_dir()}

        # Mounts a 'dict' structure describing versions and files inside each version folder.
        for i, version in enumerate(versions):
            versions[version] = [file
                                 for file in os.listdir(os.path.join(model_path,
                                                                     version))]
        # Showing versions in order...
        versions = dict(sorted(versions.items()))
        return jsonify(model_name=model_name, versions=versions)

    return jsonify(error="Not Found",
                   message="Model does not exist"), 404


@app.route('/models/check/<model_name>/<model_version>/', methods=['GET'])
def validate_model_files_wrapper(model_name, model_version):
    is_validated, status_code = validate_model_files(model_name, model_version)
    if status_code != 200:
        delete_model_version_thread(model_name, model_version)
    return is_validated, status_code


# Checks if <model>.json is present.
# If True, it checks if model file (according to the backend) and formatter.py (if model implements it) are present inside model's folder
def validate_model_files(model_name, model_version):
    model_path = os.path.join(MODELS_PATH, model_name, model_version)
    try:
        if os.path.exists(model_path):
            json_path = os.path.join(model_path, model_name + ".json")
            if os.path.isfile(json_path):
                with open(json_path) as json_file:
                    model_data = json.load(json_file)
                    validate(model_data, file_schema)

                    logger.info("'" + model_name + ".json' for model '" +
                                model_name + "' is valid")

                    model = model_data['model']

                    if model_name != str(model['name']):
                        return jsonify(error="Conflict",
                                       message="Model name on request than model name on JSON file"), 409

                    if model_version != str(model['version']):
                        return jsonify(error="Conflict",
                                       message="Model folder version '" + model_version +
                                               "' for model '" + model_name +
                                               "' is different than version '" + str(model['version']) + "' on JSON file"), 409

                    model_file = os.path.join(MODELS_PATH,
                                              model_name,
                                              model_version,
                                              model_name + '.' + model_extensions[model['backend']['type']])

                    if not os.path.isfile(model_file):

                        return jsonify(error="Not Found",
                                       message="'" + model_name + '.' + model_extensions[model['backend']['type']] +
                                               "' for model '" + model_name + '/' + model_version +
                                               "' using backend '" + model['backend']['type'] + "' not found"), 404

                    script_folder = os.path.join(MODELS_PATH,
                                                 model['name'],
                                                 str(model['version']),
                                                 model['script']['folder'])
                    if os.path.exists(script_folder):
                        script_file = os.path.join(script_folder,
                                                   "formatter.py")
                        if not os.path.isfile(script_file):
                            delete_model_version_thread(
                                model_name, model_version)
                            return jsonify(error="Not Found",
                                           message="'formatter.py' for model '" + model_name + '/' + model_version + "' not found"), 404
                    else:
                        delete_model_version_thread(
                            model_name, model_version)
                        return jsonify(error="Not Found",
                                       message="Folder '" + model['script']['folder'] + "' for model '" + model_name + '/' + model_version + "' not found"), 404
            else:

                return jsonify(error="Not Found",
                               message="'" + model_name + ".json' for model '" + model_name + '/' + model_version + "' not found"), 404
        else:

            return jsonify(error="Not Found",
                           message="Model not found"), 404
    except OSError as err:
        logger.error(str(err))
        return jsonify(error="Internal Server Error",
                       message=str(err)), 500
    except exceptions.ValidationError as err:
        logger.error(str(err))
        return jsonify(error="Validation Error",
                       message=err.message), 400

    except json.decoder.JSONDecodeError as err:
        logger.error(str(err))
        return jsonify(error="JSONDecodeError",
                       message="JSON is invalid. Please, validate your JSON file"), 400

    return jsonify(message="Model '" + model_name + '/' + model_version + "' is valid and ready to go"), 200


@app.route('/models/', methods=['POST'])
def create_model():
    try:
        create_request_data = request.get_json(force=True)

        validate(create_request_data, create_request_schema)

        model_name = snakecase(create_request_data['name'])
        model_version = create_request_data['version']
        model_url = "https://drive.google.com/u/0/uc?id=" + \
            create_request_data['id']

        if 'async_request' in create_request_data:
            is_async_request = create_request_data['async_request']
        else:
            is_async_request = True

        model_path = os.path.join(MODELS_PATH, model_name, str(model_version))

        os.makedirs(model_path)

        if is_async_request:
            x = threading.Thread(name=model_name,
                                 target=download_zip_file,
                                 args=(model_url,
                                       model_name,
                                       model_path,
                                       str(model_version)))
            x.start()
            return jsonify(message="Successfully registered request for new model. It will be downloaded soon and will be checked"), 201

        downloaded, msg = download_zip_file(model_url,
                                            model_name,
                                            model_path)
        validated, status_code = validate_model_files(model_name,
                                                      str(model_version))

        if status_code == 200:
            register_model(model_name, model_version)
        else:
            delete_model_version_thread(model_name, str(model_version))

        return validated, status_code

    except OSError as err:
        return jsonify(error="Internal Server Error",
                       message="Model creation failed"), 500

    except exceptions.ValidationError as err:
        return jsonify(error="Validation Error",
                       message=err.message), 400


@ app.route('/models/<model_name>', methods=['DELETE'])
def delete_model(model_name):
    model_path = os.path.join(MODELS_PATH, model_name)
    try:
        if os.path.exists(model_path):
            unregister_model(model_name, '*')
            delete_folder(model_path)
        else:
            return jsonify(error="Not Found",
                           message="Model not found"), 404

    except OSError as err:
        return jsonify(error="Internal Server Error",
                       message="Model could not be removed"), 500

    return jsonify(message="Model successfully removed"), 200


@ app.route('/models/<model_name>/<model_version>', methods=['DELETE'])
def delete_model_version(model_name, model_version):
    # Since we can also call 'delete_model_version' from a Thread and this function may call
    # 'delete_folder' (another function defined here), we have to set the same context,
    # so the Thread can find the function 'delete_folder'
    with app.app_context():
        model_path = os.path.join(MODELS_PATH, model_name)
        model_version_path = os.path.join(MODELS_PATH,
                                          model_name,
                                          model_version)
        try:
            if os.path.exists(model_version_path):
                unregister_model(model_name, model_version)
                delete_folder(model_version_path)
            else:
                return jsonify(error="Not Found",
                               message="Model or version not found"), 404

            # If dir /<model_name> is empty, delete /<model_name>
            if not os.listdir(model_path):
                delete_folder(model_path)

        except OSError as err:
            return jsonify(error="Internal Server Error",
                           message="Model directory removal failed"), 500

        return jsonify(message="Model version '" + model_version + "' from model '" + model_name + "' successfully removed"), 200


def delete_model_version_thread(model_name, model_version):
    delete_thread = threading.Thread(name=delete_model_version,
                                     target=delete_model_version,
                                     args=(model_name,
                                           str(model_version)),)
    delete_thread.start()


@ app.route('/models/', methods=['PUT'])
def update_model_version():
    try:
        update_request_data = request.get_json(force=True)

        validate(update_request_data, create_request_schema)

        model_name = snakecase(update_request_data['name'])
        model_version = update_request_data['version']
        model_path = os.path.join(MODELS_PATH, model_name, str(model_version))

        if 'async_request' in update_request_data:
            is_async_request = update_request_data['async_request']
        else:
            is_async_request = True

        delete_folder(model_path)
        created, staus_code = create_model()

        if staus_code not in [200, 201]:
            return jsonify(error="Internal Server Error",
                           message="Model update failed"), 500

    except OSError as err:
        return jsonify(error="Internal Server Error",
                       message="Model update failed"), 500

    except exceptions.ValidationError as err:
        return jsonify(error="Validation Error",
                       message=err.message), 400

    if is_async_request:
        return jsonify(message="Update for model '" + model_name + "' version '" + str(model_version) + "' was registred. Files will be replaced soon"), 200

    return jsonify(message="Model '" + model_name + "' version '" + str(model_version) + "' is updated and ready to go"), 200


# To-Do
'''
@ app.route('/models/<model_name>/<version>', methods=['GET'])
def get_model_version_details(model_name, version):
    return jsonify(id=id,
                   app='file_manager',
                   host=os.uname()[1],
                   worker=os.getpid())
'''
