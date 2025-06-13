from dataclasses import dataclass
from fastapi import UploadFile
from unboil_fastapi_file.models import FileInfo
from unboil_fastapi_file.utils import AsyncSignal


class Events:
    
    def __init__(self):
        self.before_upload = AsyncSignal[[BeforeFileUploadContext], None]()
        self.after_upload = AsyncSignal[[AfterFileUploadContext], None]()
        

@dataclass(kw_only=True)
class BeforeFileUploadContext:
    purpose: str
    upload: UploadFile

@dataclass(kw_only=True)
class AfterFileUploadContext:
    purpose: str
    info: FileInfo
    upload: UploadFile
    
    
