import geopandas as gpd
import osmium
import shapely
from shapely import Point
from haversine import haversine, Unit

wkbfab = osmium.geom.WKBFactory()


class Park:
    def __init__(self, osm_id, name, tags):
        self.osm_id = osm_id
        self.name = name
        self.tags = tags

    def compute_shape_osmium(self, geojson, write=False):
        geometry = geojson[geojson['@id'] == self.osm_id].geometry
        if write:
            gpd.GeoDataFrame(geometry).to_file(f"osmium_extractor/parks_geojson/{self.osm_id}.geojson")
        return geometry

    def __repr__(self):
        return f"{self.name} -- osm_id: {self.osm_id}"


class ParkCollectorHandler(osmium.SimpleHandler):
    def __init__(self, city_limits, lat=0, lon=0, radius=0):
        osmium.SimpleHandler.__init__(self, )
        self.city_limits = city_limits
        self.parks = []

        self.lat = lat
        self.lon = lon
        self.radius = radius
        new_df = gpd.GeoSeries(Point(lon, lat), crs='EPSG:4326')
        new_df = new_df.to_crs("epsg:32633")
        self.buffer = new_df.buffer(radius, resolution=20).to_crs(crs='EPSG:4326')

    def area(self, area):
        dist = -1
        if area.tags.get('leisure') == 'park':
            try:
                wkb = wkbfab.create_multipolygon(area)
                poly = shapely.wkb.loads(wkb, hex=True)
                area_geo = gpd.GeoDataFrame({'geometry': [poly]}, crs='EPSG:4326')
                if self.radius:
                    centroid = area_geo.to_crs({'proj': "cea"}).centroid.to_crs(crs='EPSG:4326')

                    dist = haversine((self.lat, self.lon), (float(centroid.iloc[0].y), float(centroid.iloc[0].x)), unit=Unit.KILOMETERS)
                if dist < self.radius and any(self.city_limits.contains(area_geo)):
                    tags = {}
                    for tag in area.tags:
                        tags[tag.k] = tag.v
                    park = Park(area.orig_id(), area.tags.get('name', ""), tags)
                    print(park)
                    self.parks.append(park)

            except RuntimeError as e:
                print(e)


class ParkCollector:
    def __init__(self, file):
        self.file = file

    def collect_parks(self, city_limits, lat, lon, radius):
        h = ParkCollectorHandler(city_limits, lat, lon, radius)
        h.apply_file(self.file)
        return h.parks


class CollectorHandler(osmium.SimpleHandler):
    def __init__(self, parent_area):
        osmium.SimpleHandler.__init__(self)
        self.parent_area = parent_area
        self.nodes = []
        self.ways = []
        self.areas = []

    def node(self, node):
        tags = {}
        for tag in node.tags:
            tags[tag.k] = tag.v
        if tags and any(self.parent_area.intersects(Point(node.location.lon, node.location.lat), align=False)):
            self.nodes.append((node.id, tags))

    def area(self, area):
        try:
            tags = {}
            for tag in area.tags:
                tags[tag.k] = tag.v
            if tags:
                wkb = wkbfab.create_multipolygon(area)
                poly = shapely.wkb.loads(wkb, hex=True)
                park_space = gpd.GeoDataFrame({'geometry': [poly]}, crs='EPSG:4326')
                if any(self.parent_area.contains(park_space, align=False)):
                    park_space_area = park_space.to_crs({'proj': "cea"}).area / 10000
                    self.areas.append((area.orig_id(), tags, float(park_space_area.iloc[0])))
                else:
                    intersection_area_of_park = park_space.to_crs({'proj': "cea"}).intersection(self.parent_area.to_crs({'proj': "cea"}), align=False).area
                    intersection_area_ha = float(intersection_area_of_park.iloc[0]) / 10000
                    if intersection_area_ha > 0:
                        self.areas.append((area.orig_id(), tags, intersection_area_ha))
        except RuntimeError as rte:
            print(rte)


class AreaFind(osmium.SimpleHandler):
    def __init__(self, id_find):
        osmium.SimpleHandler.__init__(self)
        self.osm_id = id_find
        self.name = ""

    def area(self, area):
        if self.osm_id == area.orig_id():
            self.name = area.tags.get("name", "")
            tags = {}
            for tag in area.tags:
                tags[tag.k] = tag.v
            self.tags = tags
