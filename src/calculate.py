from alive_progress import alive_it
from db import CellDatabase
from dotenv import load_dotenv
from geoalchemy2.shape import to_shape
from sqlalchemy import and_, distinct
import logging
from os import environ
from math import log
from models import CellObservation, LTECellNode, LTECellSector
from statistics import mean, stdev


def get_cells_to_update(cdb: CellDatabase, mcc: int, mnc: int) -> list[CellObservation]:
    return cdb.get_session().query(CellObservation).filter(
        and_(
            CellObservation.pending_update == True,
            CellObservation.mcc == mcc,
            CellObservation.mnc == mnc
        )
    ).all()


def get_unique_networks(cdb: CellDatabase) -> list:
    return cdb.get_session().query(distinct(CellObservation.mcc), CellObservation.mnc).filter(
        CellObservation.pending_update==True
    ).all()


def calculate_node_location(sectors: dict) -> tuple[float, float]:
    # If only 1 sector, not enough data to do this...
    if len(sectors) == 1:
        key = list(sectors.keys())[0]
        point = to_shape(sectors[key].coordinates)
        return point.y, point.x

    lat, lon = [], []
    for sector_id in sectors:
        sector = sectors[sector_id]
        point = to_shape(sector.coordinates)
        lat.append(point.y)
        lon.append(point.x)

    # t_lat, t_lon = sum(lat), sum(lon)
    m_lat, m_lon = mean(lat), mean(lon)
    sd_lat, sd_lon = stdev(lat), stdev(lon)

    # If deviation from mean is 0 we already have the best location
    if sd_lat == 0 and sd_lon == 0:
        return m_lat, m_lon

    # Weight each sector depending on deviation
    temp_lat, temp_lon, temp_weight = 0, 0, 0
    for sector_id in sectors:
        sector = sectors[sector_id]
        point = to_shape(sector.coordinates)
        sector_deviation_lat = abs((m_lat - point.y) / sd_lat)
        sector_deviation_lon = abs((m_lon - point.x) / sd_lon)
        sector_deviation = sector_deviation_lat + sector_deviation_lon

        # print(f'lat deviations from mean: {(m_lat - point.y)}, so: {sector_deviation_lat}')
        # print(f'lon deviations from mean: {(m_lon - point.x)}, so: {sector_deviation_lon}')

        weight = -1 * log(sector_deviation**len(sectors) + 1) + 1.5
        if weight < 0:
            weight = 0

        temp_lat += point.y * weight
        temp_lon += point.x * weight
        temp_weight += weight

    return temp_lat / temp_weight, temp_lon / temp_weight


def create_calculated_models(node_data, node_id, mcc, mnc) -> tuple[LTECellNode, list[LTECellSector]]:
    lat, lon = calculate_node_location(node_data)

    # TODO: Calculate max sector range
    # TODO: Calculate total sector samples
    # TODO: Calculate created / updated dates
    # TODO: Get TAC and check for deviation between sectors (get newest)

    # Add node and sectors to database
    node = LTECellNode(
        enb=node_id,
        mcc=mcc,
        mnc=mnc,
        coordinates=f'POINT({lon} {lat})',
        range=10,
        samples=10,
        created=10,
        updated=10,
        area=10
    )


def update_network_data(cdb: CellDatabase, mcc: int, mnc: int) -> None:
    cell_observations = get_cells_to_update(cdb, mcc, mnc)
    logging.info(f"Found {len(cell_observations)} cells to update")

    sectors = {}
    for observation in cell_observations:
        if observation.nid not in sectors:
            sectors[observation.nid] = {}

        if observation.sid in sectors[observation.nid]:
            logging.info('Dupe found')
            logging.info(sectors[observation.nid][observation.sid])
            logging.info(observation)

        sectors[observation.nid][observation.sid] = observation

    for node in sectors:
        node, sector_models = create_calculated_models(sectors[node], node, mcc, mnc)
        db.get_session().add(node)
        for sector in sector_models:
            db.get_session().add(sector)

    db.commit()


def main(cdb: CellDatabase) -> None:

    networks = get_unique_networks(cdb)
    logging.info(f"Found {len(networks)} unique networks in database that have cells needing updates")

    for network in alive_it(networks):
        logging.info(f"Updating {network[0]}-{network[1]}")
        update_network_data(cdb, network[0], network[1])


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s - %(message)s')

    db = CellDatabase(
        driver='postgresql+psycopg',
        username=environ['CELLS_DB_USERNAME'],
        password=environ['CELLS_DB_PASSWORD'],
        hostname=environ['CELLS_DB_HOSTNAME'],
        port=5432,
        database='mappr3_cells',
        query={
            'client_encoding': 'utf8'
        }
    )

    main(db)
