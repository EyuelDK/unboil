from dataclasses import dataclass

@dataclass(kw_only=True)
class Config:
    database_url: str