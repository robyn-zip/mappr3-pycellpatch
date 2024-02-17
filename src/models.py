import enum
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, Enum, Boolean, BigInteger, SmallInteger
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class RadioTechEnum(enum.Enum):
    unknown = 0
    gsm = 1
    umts = 2
    lte = 3
    nr = 4


# MLS base data goes in this table
class CellObservation(Base):
    __tablename__ = 'raw_observations'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Network identifier
    mcc = Column(SmallInteger, nullable=False)
    mnc = Column(SmallInteger, nullable=False)

    # Cell identifiers
    rat = Column(Enum(RadioTechEnum), nullable=False)
    area = Column(Integer)

    # For LTE: eNB, SectorID
    nid = Column(Integer)
    sid = Column(SmallInteger)

    cid = Column(Integer)
    pci = Column(SmallInteger, default=0)

    # Cell location information
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326))
    range = Column(Integer)

    # Cell meta-data
    samples = Column(Integer)
    created = Column(BigInteger)
    updated = Column(BigInteger)
    average_signal = Column(SmallInteger, default=0)

    # Pending update of other data tables
    pending_update = Column(Boolean, default=True)

    def __repr__(self):
        return f"<CellObservation({self.mcc=}, {self.mnc=}, {self.id=}, {self.nid=}, {self.cid=}, {self.coordinates=})>"


class CellNodes(Base):
    __tablename__ = 'calculated_nodes'

    id = Column(Integer, primary_key=True, autoincrement=True)