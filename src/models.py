from sqlalchemy import Column, Integer, String, Float, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


Base = declarative_base()


class CellObservation(Base):
    __tablename__ = 'raw_observations'

    id = Column(Integer, primary_key=True)
    radio = Column(String)
    mcc = Column(Integer)
    net = Column(Integer)
    area = Column(Integer)
    cell = Column(Integer)
    unit = Column(Integer)
    lon = Column(Float)
    lat = Column(Float)
    range = Column(Integer)
    samples = Column(Integer)
    changeable = Column(Boolean)
    created = Column(BigInteger)
    updated = Column(BigInteger)
    averageSignal = Column(Integer, default=0)