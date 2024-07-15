import argparse
import os

import geopandas as gpd
import osmium
import requests
from clint.textui import progress

from osmium_extractor.city import City
from osmium_extractor.couchdb import CouchDBUtil
from osmium_extractor.osmium_handlers import CollectorHandler

wkbfab = osmium.geom.WKBFactory()

parser = argparse.ArgumentParser()
parser.add_argument('--couchdb')
parser.add_argument('--city')
parser.add_argument('--osm_id')
parser.add_argument('--region')
parser.add_argument('--lat', required=False, default=0, type=float)
parser.add_argument('--lon', required=False, default=0, type=float)
parser.add_argument('--radius', required=False, default=0, type=float)

args = parser.parse_args()
print(args)

region_key = args.region.replace("/", "-")

print(requests.put(f'{args.couchdb}/osm_tags_cache_osmium_{args.city}'))
if not os.path.isfile(f"osmium_extractor/{region_key}.osm.pbf"):
    print(f"Downloading OSM region file for {args.city}")
    r = requests.get(f"https://download.geofabrik.de/{args.region}-latest.osm.pbf", stream=True)
    path = f"osmium_extractor/{region_key}.osm.pbf"
    with open(path, 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()

CITY = City(args.city, args.osm_id, f"osmium_extractor/{region_key}.osm.pbf", args.lat, args.lon, args.radius)

PBF_REGION = f"osmium_extractor/{region_key}"

couchdb_util = CouchDBUtil(args.couchdb, CITY.name)

os.system(f"osmium export {PBF_REGION}.osm.pbf -o {PBF_REGION}.geojson -a 'id' --geometry-types=polygon --overwrite -c osmium_extractor/export-config.json")

shapes_file = gpd.read_file(f"{PBF_REGION}.geojson")

for i, park in enumerate(filter(lambda p: p.name, CITY.get_parks()), 1):
    try:
        shape_of_park = park.compute_shape_osmium(shapes_file, write=True)
    except Exception as e:
        print(f"{park.osm_id}: {e}\n")
        continue
    print(f"{i} :: Processing {park.name}")
    boundary = f"osmium_extractor/parks_geojson/{park.osm_id}.geojson"
    output_file_name = f"osmium_extractor/parks_geojson/{park.osm_id}_elements.pbf"

    os.system(f"osmium extract -p '{boundary}' --output={output_file_name} --overwrite '{PBF_REGION}.osm.pbf' --strategy=smart")
    collection_handler = CollectorHandler(gpd.GeoDataFrame(shape_of_park))
    collection_handler.apply_file(output_file_name, locations=True, idx='flex_mem')
    park_elements = collection_handler.elements
    park_spaces = list(filter(lambda a: a[0] != park.osm_id, collection_handler.spaces))

    for node in filter(lambda p: len(p[1]), park_elements):
        couchdb_util.save_node(node)
    for space in park_spaces:
        couchdb_util.save_area(space)

    if len(park_spaces) + len(park_elements):
        area_of_park = shape_of_park.to_crs({'proj': "cea"}).area / 10000
        couchdb_util.save_park({'tags': park.tags,
                                '_id': str(park.osm_id),
                                'type': 'park',
                                'area': float(area_of_park.iloc[0]),
                                'elements': list(set([str(n[0]) for n in park_elements])),
                                'children': list(set([(str(n[0]), str(n[2])) for n in park_spaces]))
                                })

print(f"Saved {i} parks to the couchDB.")
