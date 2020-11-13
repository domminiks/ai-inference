import logging
import redisai

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redisai.Client(host='redisai', port=6379)


def remove_model_from_redis():
    while True:
        model = redis_client.blpop('models_to_delete')[1].decode('utf-8')

        [model_name, model_version] = model.split('/')

        if model_version == '*':
            logger.info("Removing all versions of model '" +
                        model_name + "' from RedisAI...")
        else:
            logger.info("Removing model '" + model + "' from RedisAI...")

        try:
            for redis_model in redis_client.scan_iter(match=model):
                redis_client.delete(redis_model)
        except Exception as err:
            if model_version == '*':
                logger.info("An error occured while removing all versions of model '" +
                            model_name + "' from RedisAI")
            else:
                logger.info("An error occured while removing model '" +
                            model + "' from RedisAI")

        if model_version == '*':
            logger.info("All versions of model '" +
                        model_name + "' were removed from RedisAI")
        else:
            logger.info("Model '" + model + "' was removed from RedisAI")
