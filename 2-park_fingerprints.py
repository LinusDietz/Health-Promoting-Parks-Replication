import argparse
import math
import sys
from collections import Counter

import pandas as pd

from tqdm import tqdm

from osmium_extractor.couchdb import CouchDBUtil

parser = argparse.ArgumentParser()

parser.add_argument('--couchdb')
parser.add_argument('--city')

args = parser.parse_args()
print(args)


couchdb_util = CouchDBUtil(args.couchdb, args.city)


activity_map = pd.read_csv('data/GPT4-annotations.csv')



def extract_nodes(green):
    collected_nodes = Counter()
    for node in green['nodes']:
        node_tag_matched = Counter()
        for key, value in couchdb_util.db[node]['tags'].items():
            matched_activity = activity_map[(activity_map['key'] == key) & (activity_map['value'] == value)]
            if len(matched_activity.index):
                for index, row in matched_activity.iterrows():
                    node_tag_matched[matched_activity.loc[index, 'activity_category']] += 1

        del node_tag_matched['none']

        for act, c in node_tag_matched.items():
            collected_nodes[act] += c / sum(node_tag_matched.values())

    return collected_nodes


def extract_areas(green):
    collected_area = Counter()
    if 'children' not in green:
        return collected_area
    for way, way_area in green['children']:
        way_tag_matched = Counter()

        way_entry = couchdb_util.db[way]
        if way_entry['type'] == 'area':
            for key, value in way_entry['tags'].items():
                matched_activity = activity_map[(activity_map['key'] == key) & (activity_map['value'] == value)]
                tag_activites = set()
                if len(matched_activity.index):
                    for index, row in matched_activity.iterrows():
                        tag_activites.add(matched_activity.loc[index, 'activity_category'])
                        way_tag_matched[matched_activity.loc[index, 'activity_category']] += 1
                del way_tag_matched['none']
            for act, c in way_tag_matched.items():
                collected_area[act] += (c / sum(way_tag_matched.values())) * float(way_area)
    return collected_area




characterization = []

parks_city = list(couchdb_util.db.find({'selector': {'type': 'park'},'limit':10**7}))
for i, green in tqdm(enumerate(parks_city, 1), desc=args.city, total=len(parks_city)):
    if not green['tags'].get('name', ''):
        continue
    activities_nodes = extract_nodes(green)
    activities_area = extract_areas(green)

    characterization.append(
        {'osm_id': green.id, 'name': green['tags'].get('name', ''), 'area': green['area'], 'total_nodes': len(green['nodes']),'total_spaces': len(green['children'])} |
        {f"{category}_nodes": count for category, count in activities_nodes.most_common()} |
        {f"{category}_area": area for category, area in activities_area.most_common()}
    )


result = pd.DataFrame(characterization)
result = result.fillna(0)

rs = result[~result['name'].isna()]
rs = rs.assign(percent_matched=rs[['social_area', 'physical_area', 'cultural_area', 'nature_area', 'environmental_area']].sum(axis=1, skipna=True) / rs['area'])
rs_norm = rs[rs['percent_matched'] <= 1]
rs_floor = rs[rs['percent_matched'] > 1]
rs_floor = rs_floor.assign(social_area=rs_floor['social_area'] / rs_floor['percent_matched'])
rs_floor = rs_floor.assign(physical_area=rs_floor['physical_area'] / rs_floor['percent_matched'])
rs_floor = rs_floor.assign(cultural_area=rs_floor['cultural_area'] / rs_floor['percent_matched'])
rs_floor = rs_floor.assign(nature_area=rs_floor['nature_area'] / rs_floor['percent_matched'])
rs_floor = rs_floor.assign(environmental_area=rs_floor['environmental_area'] / rs_floor['percent_matched'])
floored = pd.concat([rs_norm, rs_floor])

floored[["osm_id","name","area","total_nodes","total_spaces","cultural_nodes","social_nodes","cultural_area","physical_nodes","environmental_nodes","physical_area","nature_nodes","nature_area","social_area","environmental_area"]].to_csv(f"results/park_fingerprints_{args.city}.csv", index=None)
