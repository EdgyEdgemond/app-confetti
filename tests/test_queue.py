import json
from datetime import datetime
from decimal import Decimal
from unittest import mock

import pytest

from clt_util import queue


class TestRedisQueue:
    def test_init(self, monkeypatch):
        monkeypatch.setattr(queue.redis, "Redis", mock.MagicMock())

        q = queue.RedisQueue(["testqueue", "testqueue2"], host="test", port=1234)

        assert q.conn == queue.redis.Redis.return_value
        assert queue.redis.Redis.call_args == mock.call(host="test", port=1234, db=0)
        assert q.queues == ["testqueue", "testqueue2"]
        assert q.queue == "testqueue"

    def test_push_val_exists(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = True

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.push("value")

        assert conn.sismember.call_args == mock.call("testqueue-uniq", "value")
        assert conn.rpush.call_count == 0

    def test_push_val_key_exists(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = True

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.push("value", "key")

        assert conn.sismember.call_args == mock.call("testqueue-uniq", "key")
        assert conn.rpush.call_count == 0

    def test_push_val_exists_non_default_queue(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = True

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.push("value", queue="myqueue")

        assert conn.sismember.call_args == mock.call("myqueue-uniq", "value")
        assert conn.rpush.call_count == 0

    def test_push_new_complex_val(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = False

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))
        value = {
            "account_number": 60733123,
            "asset": "GBPUSD",
            "close_price": Decimal("1.30561"),
            "close_time": datetime.today(),
            "comment": "",
            "meta": "",
            "open_price": Decimal("1.30546"),
            "open_time": "2020-08-12T11:42:25",
            "order_type": 1,
            "pnl_cash": Decimal("-0.57"),
            "pnl_pips": Decimal("-1.5"),
            "risking": None,
            "sl_pips": 0,
            "sl_price": Decimal("0.0"),
            "spread": 0,
            "status": "open",
            "swap": 0.0,
            "ticket": 55301005,
            "tp_pips": 0,
            "tp_price": Decimal("0.0"),
            "volume": 0.05,
        }

        q = queue.RedisQueue(["testqueue"])
        q.push(value, key="key")

        assert conn.sismember.call_args == mock.call("testqueue-uniq", "key")
        assert conn.rpush.call_args == mock.call(q.queue, json.dumps(["key", value], cls=queue.CltEncoder))
        assert conn.sadd.call_args == mock.call("testqueue-uniq", "key")

    def test_push_new_val(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = False

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.push("value")

        assert conn.sismember.call_args == mock.call("testqueue-uniq", "value")
        assert conn.rpush.call_args == mock.call(q.queue, json.dumps(["value", "value"]))
        assert conn.sadd.call_args == mock.call("testqueue-uniq", "value")

    def test_push_new_val_non_default_queue(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = False

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.push("value", queue="myqueue")

        assert conn.sismember.call_args == mock.call("myqueue-uniq", "value")
        assert conn.rpush.call_args == mock.call("myqueue", json.dumps(["value", "value"]))
        assert conn.sadd.call_args == mock.call("myqueue-uniq", "value")

    def test_push_new_val_key(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = False

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.push("value", "key")

        assert conn.sismember.call_args == mock.call("testqueue-uniq", "key")
        assert conn.rpush.call_args == mock.call(q.queue, json.dumps(["key", "value"]))
        assert conn.sadd.call_args == mock.call("testqueue-uniq", "key")

    def test_pop_no_value(self, monkeypatch):
        conn = mock.Mock()
        conn.blpop.return_value = None

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue", "testqueue2"])
        v = q.pop()

        assert v is None
        assert conn.blpop.call_args == mock.call(["testqueue", "testqueue2"], 30)
        assert conn.srem.call_count == 0

    def test_pop_with_value(self, monkeypatch):
        conn = mock.Mock()
        conn.blpop.return_value = (b"testqueue", b'["key", "value"]')

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        r = q.pop()

        assert r == ("testqueue", "value")
        assert conn.blpop.call_args == mock.call(["testqueue"], 30)
        assert conn.srem.call_args == mock.call("testqueue-uniq", "key")

    def test_locked_doesnt_remove_from_set(self, monkeypatch):
        conn = mock.Mock()
        conn.blpop.return_value = (b"testqueue", b'["key", "value"]')

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q._lock = True
        r = q.pop()

        assert r == ("testqueue", "value")
        assert conn.blpop.call_args == mock.call(["testqueue"], 30)
        assert conn.srem.call_count == 0

    def test_pop_no_value_as_context_manager(self, monkeypatch):
        conn = mock.Mock()
        conn.blpop.return_value = None

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        with q as q_:
            r = q_.pop()
            assert q_._lock is True

        assert q_._lock is False
        assert r is None
        assert conn.blpop.call_args == mock.call(["testqueue"], 30)
        assert conn.srem.call_count == 0

    def test_pop_as_context_manager(self, monkeypatch):
        conn = mock.Mock()
        conn.blpop.return_value = (b"testqueue", b'["key", "value"]')

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        with q as q_:
            r = q_.pop()
            assert q_._lock is True

        assert q_._lock is False
        assert r == ("testqueue", "value")
        assert conn.blpop.call_args == mock.call(["testqueue"], 30)
        assert conn.srem.call_args == mock.call("testqueue-uniq", "key")

    def test_update(self, monkeypatch):
        conn = mock.Mock()
        conn.sismember.return_value = False

        monkeypatch.setattr(queue.redis, "Redis", mock.Mock(return_value=conn))

        q = queue.RedisQueue(["testqueue"])
        q.update(["value", "value2", "value3"])

        assert conn.sismember.call_args_list == [
            mock.call("testqueue-uniq", "value"),
            mock.call("testqueue-uniq", "value2"),
            mock.call("testqueue-uniq", "value3"),
        ]
        assert conn.rpush.call_args_list == [
            mock.call(q.queue, json.dumps(["value", "value"])),
            mock.call(q.queue, json.dumps(["value2", "value2"])),
            mock.call(q.queue, json.dumps(["value3", "value3"])),
        ]
        assert conn.sadd.call_args_list == [
            mock.call("testqueue-uniq", "value"),
            mock.call("testqueue-uniq", "value2"),
            mock.call("testqueue-uniq", "value3"),
        ]


class TestCltEncoder:
    def test_converts_datetime(self):
        d = datetime.today()
        v = json.dumps({"d": d}, cls=queue.CltEncoder)
        assert v == '{"d": {"_type": "datetime", "value": "' + d.isoformat() + '"}}'

    def test_converts_decimal(self):
        d = Decimal("1.23")
        v = json.dumps({"d": d}, cls=queue.CltEncoder)
        assert v == '{"d": {"_type": "decimal", "value": "1.23"}}'

    def test_raises_unsupported(self):
        with pytest.raises(TypeError):
            json.dumps({"d": set()}, cls=queue.CltEncoder)


class TestCltDecoder:
    def test_converts_datetime(self):
        d = datetime.today()
        v = '{"d": {"_type": "datetime", "value": "' + d.isoformat() + '"}}'
        assert json.loads(v, cls=queue.CltDecoder) == {"d": d}

    def test_converts_decimal(self):
        d = Decimal("1.23")
        v = '{"d": {"_type": "decimal", "value": "1.23"}}'
        assert json.loads(v, cls=queue.CltDecoder) == {"d": d}

    def test_raises_unsupported(self):
        with pytest.raises(TypeError):
            json.loads('{"d": {"_type": "unknown"}}', cls=queue.CltDecoder)
