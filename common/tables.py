from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

BaseModel = declarative_base()


class Word2Vec(BaseModel):
    __tablename__ = "word2vec"
    word = Column(String(128), nullable=False, primary_key=True)
    vec = Column(LargeBinary, nullable=False)
#
#
# class Nearby(BaseModel):
#     __tablename__ = "nearby"
#     # TODO: unique index for word & neigbor
#     word = Column(String(512), ForeignKey("word2vec.word"), nullable=False)
#     neighbor = Column(String(512), ForeignKey("word2vec.word"), nullable=False)
#     similarity = Column(Float(2), nullable=False)
#     percentile = Column(Integer, nullable=False)
#
#





