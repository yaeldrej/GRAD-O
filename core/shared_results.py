
import tkinter as tk

_save_listeners = []
_delete_listeners = []


def subscribe(on_save=None, on_delete=None):
    if on_save:
        _save_listeners.append(on_save)
    if on_delete:
        _delete_listeners.append(on_delete)


def publish_save(result):
    for listener in list(_save_listeners):
        try:
            listener(result)
        except tk.TclError:
            _save_listeners.remove(listener)


def publish_delete(result):
    for listener in list(_delete_listeners):
        try:
            listener(result)
        except tk.TclError:
            _delete_listeners.remove(listener)