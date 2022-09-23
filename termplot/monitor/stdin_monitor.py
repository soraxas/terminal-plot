import sys
import threading

from termplot.monitor import AbstractMonitor


class StdinMonitor(AbstractMonitor):
    def __init__(self):
        self.buffer = []
        self.modified_event = threading.Event()
        self.watcher = threading.Thread(target=self._watcher_loop)
        self.watcher.start()

    def _watcher_loop(self):
        for line in sys.stdin:
            self.buffer.append(line)
            self.modified_event.set()

    def should_refresh(self) -> bool:
        return self.modified_event.is_set()

    def stop(self) -> None:
        self.watcher.join()

    def set_should_refresh(self):
        self.modified_event.set()

    def reset_condition(self):
        self.modified_event.clear()

    def wait_till_new_modification(self):
        if self.should_refresh():
            return
        self.reset_condition()
        self.modified_event.clear()
        self.modified_event.wait()

    def get_latest(self):
        self.reset_condition()
        return "".join(self.buffer)
