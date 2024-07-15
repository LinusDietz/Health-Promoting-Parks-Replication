import argparse
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

activity_map = pd.read_csv('data/lexicon.csv')


def extract_elements(park):
    collected_elements = Counter()
    for node in park['elements']:
        node_tag_matched = Counter()
        for key, value in couchdb_util.db[node]['tags'].items():
            matched_activity = activity_map[(activity_map['key'] == key) & (activity_map['value'] == value)]
            if len(matched_activity.index):
                for index, row in matched_activity.iterrows():
                    node_tag_matched[matched_activity.loc[index, 'activity_category']] += 1

        del node_tag_matched['none']

        for act, c in node_tag_matched.items():
            collected_elements[act] += c / sum(node_tag_matched.values())

    return collected_elements


def extract_spaces(park):
    collected_space = Counter()
    if 'children' not in park:
        return collected_space
    for way, way_area in park['children']:
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
                collected_space[act] += (c / sum(way_tag_matched.values())) * float(way_area)
    return collected_space


def adjust_overlaps(park_fingerprints):
    park_fingerprints = park_fingerprints.fillna(0)
    rs = park_fingerprints[~park_fingerprints['name'].isna()]
    rs = rs.assign(percent_matched=rs[['social_spaces', 'physical_spaces', 'cultural_spaces', 'nature_spaces', 'environmental_spaces']].sum(axis=1, skipna=True) / rs['area'])
    parks_overlaps = rs[rs['percent_matched'] > 1]
    parks_overlaps = parks_overlaps.assign(social_spaces=parks_overlaps['social_spaces'] / parks_overlaps['percent_matched'])
    parks_overlaps = parks_overlaps.assign(physical_spaces=parks_overlaps['physical_spaces'] / parks_overlaps['percent_matched'])
    parks_overlaps = parks_overlaps.assign(cultural_spaces=parks_overlaps['cultural_spaces'] / parks_overlaps['percent_matched'])
    parks_overlaps = parks_overlaps.assign(nature_spaces=parks_overlaps['nature_spaces'] / parks_overlaps['percent_matched'])
    parks_overlaps = parks_overlaps.assign(environmental_spaces=parks_overlaps['environmental_spaces'] / parks_overlaps['percent_matched'])
    return pd.concat([(rs[rs['percent_matched'] <= 1]), parks_overlaps])


characterizations = []
parks_of_city = list(couchdb_util.db.find({'selector': {'type': 'park'}, 'limit': 10 ** 7}))
for i, park in tqdm(enumerate(parks_of_city, 1), desc=args.city, total=len(parks_of_city)):
    if not park['tags'].get('name', ''):
        continue
    activities_elements = extract_elements(park)
    activities_spaces = extract_spaces(park)

    characterizations.append(
        {'osm_id': park.id, 'name': park['tags'].get('name', ''), 'area': park['area'], 'total_elements': len(park['elements']), 'total_spaces': len(park['children'])} |
        {f"{category}_elements": count for category, count in activities_elements.most_common()} |
        {f"{category}_spaces": space for category, space in activities_spaces.most_common()}
    )

fingerprints = adjust_overlaps(pd.DataFrame(characterizations))
fingerprints[["osm_id", "name", "area", "total_elements", "total_spaces", "cultural_elements", "social_elements", "cultural_spaces", "physical_elements", "environmental_elements", "physical_spaces",
              "nature_elements",
              "nature_spaces", "social_spaces", "environmental_spaces"]].to_csv(f"results/park_fingerprints_{args.city}.csv", index=None)
