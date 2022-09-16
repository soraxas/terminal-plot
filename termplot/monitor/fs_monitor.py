import os
import threading
from pathlib import Path

from termplot.monitor import AbstractMonitor

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class TerminateCondition:
    def __init__(self):
        self.stored_boolean = True

    def __bool__(self):
        return self.stored_boolean

    def set_val(self, val):
        self.stored_boolean = bool(val)


class MyHandler(FileSystemEventHandler):
    def __init__(self, root_dir, callback):
        self.root = os.path.normpath(root_dir)
        self.callback = callback

    def on_created(self, event):
        self.callback(event)

    def on_modified(self, event):
        self.callback(event)


class FilesystemMonitor(AbstractMonitor):
    def __init__(self, folder: str):
        self.folder = folder
        self.new_modify = threading.Event()
        # self.created_new_file = TerminateCondition()
        self._created_new_file = False

        event_handler = MyHandler(folder, callback=self.callback)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=folder, recursive=True)
        self.observer.start()

    def should_refresh(self):
        return self._created_new_file

    def set_should_refresh(self):
        self._created_new_file = True

    def reset_condition(self):
        self._created_new_file = False

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()

    def get_latest(self):
        folders = sorted(Path(self.folder).iterdir(), key=os.path.getmtime)
        return folders[-1]

    def callback(self, event):
        if event.event_type == "created":
            # print("on_created", event.src_path)
            self.set_should_refresh()
        self.new_modify.set()

    def wait_till_new_modification(self):
        self.new_modify.wait()
        self.new_modify.clear()
