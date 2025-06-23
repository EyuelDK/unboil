from sqlalchemy.orm import DeclarativeBase


class Models:
    
    def __init__(self):

        class Base(DeclarativeBase):
            pass
        
        self.Base = Base