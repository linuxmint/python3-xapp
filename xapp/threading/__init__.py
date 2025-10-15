import gi
import threading

from gi.repository import GLib

# Decorator to run things in the background
def run_async(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

# Decorator to run things in the main Gtk loop
def run_idle(func):
    def wrapper(*args):
        GLib.idle_add(func, *args)
    return wrapper

__all__ = ["run_async", "run_idle"]
