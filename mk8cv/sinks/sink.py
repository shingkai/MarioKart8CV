import json
from enum import Enum

import redis

from mk8cv.data.state import StateMessage, StateEncoder


class SinkType(Enum):
    NONE = 0
    REDIS = 1

# Option 1: Redis Pub/Sub
def publish_to_redis(redis_client: redis.Redis, channel: str, message: StateMessage):
    redis_client.publish(channel, json.dumps(message, cls=StateEncoder))