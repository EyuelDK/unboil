from fastapi import FastAPI

from unboil_utils_events import AsyncEvent


class Events:
    
    def __init__(self):
        self.on_startup = AsyncEvent[[FastAPI], None]()
        self.on_shutdown = AsyncEvent[[FastAPI], None]()