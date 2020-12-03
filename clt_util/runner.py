import abc


class AbstractRunner(metaclass=abc.ABCMeta):
    def __init__(self, event_loop):
        self.runner_loop = event_loop
        self._run = True

    def start(self):
        self.runner_loop.run_until_complete(self._loop())

    def stop(self):
        self._run = False

    def running(self):
        return self._run

    @abc.abstractmethod
    async def _loop(self):
        """
        Example:
            while self.running():
                time.sleep(5)
        """
        pass
