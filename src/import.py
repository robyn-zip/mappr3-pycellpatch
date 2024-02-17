from db import CellDatabase
from dotenv import load_dotenv
from sqlalchemy import and_
import logging
from os import environ
from helpers import list_files_in_dir, read_cell_observations
from models import CellObservation


IMPORT_DIR = 'import'


def main():
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

    # Parse all files in the import folder
    file_data = {}
    for file in list_files_in_dir(IMPORT_DIR):
        if 'diff' in file.name:
            logging.info(f'Parsing file: {file}')
            file_data[file.name] = read_cell_observations(f"{IMPORT_DIR}/{file.name}")

    # Loop all observations
    for file in file_data:
        sess = db.get_session()

        total, updates, errors, additions = 0, 0, 0, 0
        for cell in file_data[file]:
            total += 1

            # Check if cell id already exists for network
            filter_condition = and_(
                CellObservation.mcc == cell.mcc,
                CellObservation.mnc == cell.mnc,
                CellObservation.cid == cell.cid
            )
            observations = sess.query(CellObservation).filter(filter_condition).all()

            # If cell doesn't exist, add it
            if len(observations) == 0:
                sess.add(cell)
                additions += 1
                continue

            if len(observations) > 1:
                logging.error(f'There is more than one {cell.mcc}-{cell.mnc}: {cell.cid}!')
                errors += 1
                continue

            # Always take the newer measurement
            if cell.updated > observations[0].updated:
                logging.info(f'Updating {cell.mcc}-{cell.mnc}: {cell.cid}!')
                sess.delete(observations[0])
                sess.add(cell)
                updates += 1

        logging.info(f'Updated {total} cells, {additions} additions, {errors} errors, {updates} updates from {file}')
        db.commit()


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s - %(message)s')

    main()
