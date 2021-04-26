import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
from methods import *


class Watcher:

    def __init__(self):
        self.observer = Observer()
        self.DIRECTORY_TO_WATCH = ""

    def run(self, directory):
        self.DIRECTORY_TO_WATCH = directory
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):
    # data = []

    @staticmethod
    def on_any_event(event):
        image_path = event.src_path
        image_name = get_image_name(image_path)
        if event.is_directory:
            return None

        elif event.event_type == 'deleted':
            # Taken any action here when a file is modified.
            data_file = open('data.json', 'r')
            read_list = json.load(data_file)
            for element in read_list:
                if element['name'] == image_name:
                    read_list.remove(element)
            data_file.close()
            data_file = open('data.json', 'w')
            json.dump(read_list, data_file)
            data_file.close()

