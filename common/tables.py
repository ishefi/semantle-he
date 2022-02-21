from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class Word2Vec(BaseModel):
    __tablename__ = "word2vec"
    word = Column(String(128), nullable=False, primary_key=True)
    vec = Column(LargeBinary, nullable=False)
    secret_date = Column(Date, default=False)
