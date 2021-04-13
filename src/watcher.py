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
    data = []

    @staticmethod
    def on_any_event(event):
        image_path = event.src_path
        image_name = get_image_name(image_path)
        if image_path[0] == "/":
            arr = image_path.split('/')
        else:
            arr = image_path.split('\\')
        if event.is_directory:
            return None
        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % image_path)
            Handler.data.append({'name': arr[-1], 'distance_map': None})
        # Need to handle if name of image is changed (change it in data.json file as well)
        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            new_image_name = get_image_name(event.src_path)
            if image_name != new_image_name:
                with open('data.json') as data_file:
                    read_list = json.load(data_file)
                for element in read_list:
                    if element['name'] == image_name:
                        element['name'] = new_image_name
                print("Received modified event - %s." % new_image_name)

        elif event.event_type == 'deleted':
            # Taken any action here when a file is modified.
            print("Received deleted event - %s." % event.src_path)
            with open('data.json') as data_file:
                read_list = json.load(data_file)
            for element in read_list:
                if element['name'] == arr[-1]:
                    read_list.remove(element)
            Handler.data = read_list

        with open('data.json', 'w') as outfile:
            json.dump(Handler.data, outfile)
