import time
from unittest import mock

import pytest

from clt_util import runner


class RunnerTest(runner.AbstractRunner):
    async def _loop(self):
        while self.running():
            time.sleep(1)


@pytest.fixture
def running_patch(monkeypatch):
    monkeypatch.setattr(RunnerTest, "running", mock.Mock(side_effect=[True, False]))


class TestApiHealth:
    def test_init(self):
        event_loop = mock.Mock()

        r = RunnerTest(event_loop=event_loop)

        assert r.runner_loop == event_loop
        assert r._run is True

    def test_start(self, monkeypatch):
        event_loop = mock.Mock()
        r = RunnerTest(event_loop=event_loop)

        monkeypatch.setattr(r, "_loop", mock.Mock())

        r.start()

        assert r._run is True
        assert r.runner_loop.run_until_complete.call_args == mock.call(
            r._loop.return_value,
        )

    def test_stop(self, monkeypatch):
        event_loop = mock.Mock()
        r = RunnerTest(event_loop=event_loop)

        r.stop()

        assert r._run is False

    @pytest.mark.parametrize("run, expected", [(True, True), (False, False)])
    def test_running(self, run, expected):
        event_loop = mock.Mock()
        r = RunnerTest(event_loop=event_loop)

        r._run = run

        assert r.running() == expected

    @pytest.mark.asyncio
    async def test_loop(self, running_patch, monkeypatch):
        monkeypatch.setattr(time, "sleep", mock.Mock())

        event_loop = mock.Mock()
        r = RunnerTest(event_loop=event_loop)

        await r._loop()

        assert time.sleep.call_count == 1
