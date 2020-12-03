import datetime
import decimal
import json

import redis
from dateutil import parser


class CltEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return {
                "_type": "datetime",
                "value": obj.isoformat(),
            }
        if isinstance(obj, decimal.Decimal):
            return {
                "_type": "decimal",
                "value": str(obj),
            }
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class CltDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if "_type" not in obj:
            return obj
        type_ = obj["_type"]
        if type_ == "datetime":
            return parser.parse(obj["value"])
        if type_ == "decimal":
            return decimal.Decimal(obj["value"])
        raise TypeError("_type {} unknown".format(type_))


class RedisQueue:
    def __init__(self, queues, host="localhost", port=6379):
        self.conn = redis.Redis(host=host, port=port, db=0)
        self.queue = queues[0]
        self.queues = queues
        self._lock = False
        self._key, self._queue = None, None

    def push(self, value, key=None, queue=None):
        key = key or value

        queue = queue or self.queue
        uniq_queue = queue + "-uniq"

        if not self.conn.sismember(uniq_queue, key):
            self.conn.sadd(uniq_queue, key)
            value = json.dumps((key, value), cls=CltEncoder)
            self.conn.rpush(queue, value)

    def pop(self):
        r = self.conn.blpop(self.queues, 30)
        if r:
            queue, value = r

            queue = queue.decode("utf-8")
            uniq_queue = queue + "-uniq"

            value = json.loads(value.decode("utf-8"), cls=CltDecoder)
            key, value = value

            if self._lock:
                self._key = key
                self._queue = queue
            else:
                self.conn.srem(uniq_queue, key)
            return queue, value

    def update(self, values, queue=None):
        for value in values:
            self.push(value, queue=queue)

    def __enter__(self):
        self._lock = True
        self._key = None
        self._queue = None
        return self

    def __exit__(self, *exc):
        if self._key:
            uniq_queue = self._queue + "-uniq"
            self.conn.srem(uniq_queue, self._key)

        self._lock = False
        self._key = None
        self._queue = None
