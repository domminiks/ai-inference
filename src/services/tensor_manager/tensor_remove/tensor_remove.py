import logging
import redisai

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redisai.Client(host='redisai', port=6379)


def remove_tensor_from_redis():
    while True:
        tensor = redis_client.blpop('tensors_to_delete')[1].decode('utf-8')
        logger.info("New tensor to remove: '" + tensor + "'")

        try:
            redis_client.delete(tensor)
            logger.info("Tensor '" + tensor + "' removed from RedisAI")
        except Exception as err:
            logger.info("An error occured while removing tensor '" +
                        tensor + "' from RedisAI")
