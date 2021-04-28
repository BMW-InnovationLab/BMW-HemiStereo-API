from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from methods import *
import os


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

    @staticmethod
    def on_any_event(event):

        if event.is_directory:
            return None
        # Removes the pickle file specific to the image deleted
        elif event.event_type == 'deleted':
            image_path = event.src_path
            image_name = get_image_name(image_path)
            image_name = image_name[0:image_name.index('.p')]
            os.remove('pickle_files/' + image_name)



