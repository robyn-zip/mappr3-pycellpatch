from alive_progress import alive_bar
import logging
from models import CellObservation, RadioTechEnum
from pathlib import Path


RAT_MAP = {
    'gsm': RadioTechEnum.gsm,
    'umts': RadioTechEnum.umts,
    'lte': RadioTechEnum.lte,
    'nr': RadioTechEnum.nr
}


# Turns cell ID into eNB and sector ID
def decompose_cid(cid: int) -> (int, int):
    binstr = bin(cid)
    sid = int(binstr[-8:], 2)
    nid = int(binstr[:-8], 2)

    return nid, sid


def create_observation_from_csv_row(row: list) -> CellObservation:
    enb, sid = decompose_cid(int(row[4]))

    return CellObservation(
        rat=RAT_MAP.get(row[0], RadioTechEnum.unknown),
        mcc=int(row[1]),
        mnc=int(row[2]),
        area=int(row[3]),
        cid=int(row[4]),
        pci=int(row[5] or 0),
        coordinates=f'POINT({row[6]} {row[7]})',
        range=int(row[8]),
        samples=int(row[9]),
        created=row[11],
        updated=row[12],
        average_signal=int(row[13] or 0),
        nid=enb,
        sid=sid
    )


def list_files_in_dir(dir_path: str) -> list[Path]:
    path = Path(dir_path)
    if path.is_dir():
        files = [file for file in path.iterdir() if file.is_file() and file.suffix == '.csv']
        return files
    else:
        logging.error(f"{dir_path} is not a valid directory.")
        return []


def count_file_lines(file_path: str) -> int:
    with open(file_path, "rb") as f:
        num_lines = sum(1 for _ in f)

    return num_lines


def read_cell_observations(file_path: str) -> list[CellObservation]:
    line_number = 0
    line_total = count_file_lines(file_path)
    cell_observations = []

    with alive_bar(line_total) as bar:
        # Note: We are not using and CSV reading functions here as they're slower than what we are about to do :)
        # https://codereview.stackexchange.com/questions/79449/need-fast-csv-parser-for-python-to-parse-80gb-csv-file
        with open(file_path) as f:
            line = f.readline()

            while line:
                line_number += 1
                bar()

                line = f.readline().strip()
                if ',' not in line:
                    logging.warning(f'No CSV data at line: {line_number} in: {file_path}')
                    continue

                # https://ichnaea.readthedocs.io/en/latest/import_export.html
                row = line.split(',')

                # Skip rows that aren't LTE data points
                if row[0] != 'LTE':
                    continue
                if row[1] != '234':
                    continue

                # Check Cell ID is valid
                cid = int(row[4])
                if cid < 256:
                    continue

                observation = create_observation_from_csv_row(row)

                cell_observations.append(observation)

    return cell_observations


if __name__ == '__main__':
    # print(count_file_lines('../import/MLS-full-cell-export-2024-02-12T000000.csv'))
    # read_cell_observations('../import/MLS-full-cell-export-2024-02-12T000000.csv')
    read_cell_observations('../import/MLS-diff-cell-export-2024-02-14T200000.csv')
