import plotly.graph_objs as go
import logging
from dotenv import load_dotenv
from db import CellDatabase
from models import CellObservation
from os import environ
from geoalchemy2.functions import ST_Within, ST_GeomFromText
from geoalchemy2.shape import to_shape


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

    # UK bounaries
    min_lon = -7
    min_lat = 50
    max_lon = 1
    max_lat = 60

    # Create a polygon from the bounding box
    bounds = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    bounding_box = ST_GeomFromText(bounds, 4326)

    # all_points = db.get_session().query(CellObservation).all()
    points_within_area = db.get_session().query(CellObservation).filter(
        ST_Within(CellObservation.coordinates, bounding_box)
    ).all()

    lat = []
    lng = []

    for cell in points_within_area:
        point = to_shape(cell.coordinates)
        print(point)
        print(point.wkt)
        lat += [point.y]
        lng += [point.x]

    scatter_trace = go.Scattermapbox(
        lat=lat,
        lon=lng,
        mode='markers',
        marker=dict(size=10, color='red')
    )

    layout = go.Layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lon=0, lat=0),
            zoom=1
        )
    )

    fig = go.Figure(data=[scatter_trace], layout=layout)
    fig.show()


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s - %(message)s')

    main()
