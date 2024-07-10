import os

import osmium
import shapely.wkb
import shapely
import geopandas as gpd
from haversine import Unit, haversine
from osmium import SimpleHandler
from shapely import Point

from osmium_extractor.osmium_handlers import ParkCollector

wkbfab = osmium.geom.WKBFactory()


class City:
    def __init__(self, name, osm_id, file, lat=0, lon=0, radius=0):
        print(f"City is {name}.")
        self.osm_file = file
        self.name = name
        self.osm_id = osm_id
        self.geo = self._get_geo()
        if lat and lon:
            self.lat = lat
            self.lon = lon
        else:
            centroid = self.geo.centroid
            self.lon = centroid.x
            self.lat = centroid.y
        self.radius = radius

    def contains_point(self,lat,lon):
        dist = -1
        if self.radius:
            dist = haversine((self.lat, self.lon), (lat, lon), unit=Unit.KILOMETERS)
        return dist < self.radius and any(self.geo.contains(Point(lon,lat)))

    def get_parks(self):
        return ParkCollector(self.osm_file).collect_parks(self.geo,self.lat,self.lon,self.radius)

    def __repr__(self):
        return f"{self.name} ({self.osm_id})"

    def __str__(self):
        return f"{self.name} ({self.osm_id})"

    def _get_geo(self):
        os.system(f"osmium getid -O --verbose-ids {self.osm_file} r{self.osm_id} -o osmium_extractor/cities_geojson/{self.name}.pbf -r")
        os.system(f"osmium export osmium_extractor/cities_geojson/{self.name}.pbf -o osmium_extractor/cities_geojson/{self.name}.geojson  -f geojson -O")
        city = gpd.read_file(f"osmium_extractor/cities_geojson/{self.name}.geojson")
        return city.dissolve()

    def __contains__(self, point):
        if self.radius:
            res = haversine((self.lat, self.lon), (point.y, point.x), unit=Unit.KILOMETERS) < self.radius
            return res
        return any(self.geo.contains(point))


class CityHandler(SimpleHandler):
    def __init__(self, osm_id):
        osmium.SimpleHandler.__init__(self)
        self.osm_id = osm_id
        self.geopandas_geo = None

    def area(self, area):
        if area.orig_id() == self.osm_id:
            wkb = wkbfab.create_multipolygon(area)
            poly = shapely.wkb.loads(wkb, hex=True)
            self.geopandas_geo = gpd.GeoDataFrame({'geometry': [poly]}, crs='EPSG:4326')
            print(f'Found geometry for {self.osm_id}, {float(self.geopandas_geo.to_crs("epsg:32633").area) / 1000000:.2f}km^2')

