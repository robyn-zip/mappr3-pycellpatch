from alive_progress import alive_bar
import logging
from models import CellObservation, RadioTechEnum


# Turns cell ID into eNB and sector ID
def decompose_cid(cid: int) -> (str, str):
    binstr = bin(cid)
    sid = str(int(binstr[-8:], 2))
    nid = str(int(binstr[:-8], 2))

    return nid, sid


def count_file_lines(file_path: str) -> int:
    with open(file_path, "rb") as f:
        num_lines = sum(1 for _ in f)

    return num_lines


def read_csv_to_dict(file_path: str) -> list[CellObservation]:
    line_number = 0
    line_total = count_file_lines(file_path)
    cell_observations = []

    rat_map = {
        'gsm': RadioTechEnum.gsm,
        'umts': RadioTechEnum.umts,
        'lte': RadioTechEnum.lte,
        'nr': RadioTechEnum.nr
    }

    with alive_bar(line_total) as bar:
        # Note: We are not using and CSV reading functions here as they're slower than what we are about to do :)
        # https://codereview.stackexchange.com/questions/79449/need-fast-csv-parser-for-python-to-parse-80gb-csv-file
        with open(file_path) as f:
            line = f.readline()

            while line:
                line_number += 1

                line = f.readline()
                if ',' not in line:
                    logging.warning(f'No CSV data at line: {line_number} in: {file_path}')
                    continue

                # https://ichnaea.readthedocs.io/en/latest/import_export.html
                row = line.split(',')

                # Skip rows that aren't LTE data points
                if row[0] != 'LTE':
                    continue

                # Check Cell ID is valid
                cid = int(row[4])
                if cid < 256:
                    continue

                enb, sid = decompose_cid(cid)

                observation = CellObservation(
                    rat=rat_map.get(row[0], RadioTechEnum.unknown),
                    mcc=row[1],
                    mnc=row[2],
                    area=row[3],
                    cid=cid,
                    pci=row[5],
                    coordinates=f'POINT({row[6]} {row[7]})',
                    range=row[8],
                    samples=row[9],
                    created=row[11],
                    updated=row[12],
                    average_signal=row[13] or 0,
                    nid=enb,
                    sid=sid
                )

                if observation.mcc == "234":
                    print(observation)

                cell_observations.append(observation)
                bar()

    return cell_observations


if __name__ == '__main__':
    #print(count_file_lines('../import/MLS-full-cell-export-2024-02-12T000000.csv'))
    #read_csv_to_dict('../import/MLS-full-cell-export-2024-02-12T000000.csv')
    read_csv_to_dict('../import/MLS-diff-cell-export-2024-02-14T200000.csv')
