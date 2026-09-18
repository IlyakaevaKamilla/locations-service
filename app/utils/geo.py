from geoalchemy2.elements import WKTElement


def make_coords(latitude: float, longitude: float) -> WKTElement:
    return WKTElement(
        f"POINT({longitude} {latitude})", srid=4326
    )  # POINT(lon lat) — сначала долгота, потом широта
